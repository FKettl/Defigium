#include "ThreadPool.h"
#include "factory.h"

ThreadPool::ThreadPool(size_t num_workers, const YAML::Node& executor_config)
	: m_num_workers(num_workers), m_executor_config(executor_config)
{
	m_workers.reserve(num_workers);
	for (size_t i = 0; i < num_workers; ++i)
		m_workers.emplace_back(&ThreadPool::worker_function, this, i);
}

ThreadPool::~ThreadPool() {
	for (size_t i = 0; i < m_num_workers; ++i) {
		Task_Worker poison;
		poison.target_time = std::chrono::steady_clock::now();
		poison.command.op_type = "POISON_PILL";
		m_queue.push(poison);
	}

	for (std::thread &worker : m_workers)
		if (worker.joinable())
			worker.join();
}

void ThreadPool::enqueue_task(Task_Worker task) {
	m_queue.push(std::move(task));
}

bool ThreadPool::is_work_complete() {
	return m_queue.empty();
}

void ThreadPool::worker_function(int id) {
	std::unique_ptr<IExecutorStrategy> executor = nullptr;

    try {
        executor = ExecutorFactory::create(m_executor_config["type"].as<std::string>());
        executor->connect(m_executor_config);

        while (true) {
            Task_Worker task = m_queue.pop();
            if (task.command.op_type == "POISON_PILL") break;

			std::this_thread::sleep_until(task.target_time);

            ExecutionResult result = executor->execute(task.command);

            if (result.success) {
                success_count++;
				auto cur_lat = total_latency_ns.load();
				while(!total_latency_ns.compare_exchange_weak(cur_lat, cur_lat + result.latency_ns));
            } else {
                error_count++;
            }
        }
    } catch (const std::exception &e) {
        std::cerr << "Error in Thread " << id << ": " << e.what() << std::endl;
        error_count++;
    }

    if (executor) {
        executor.reset();
    }
}

