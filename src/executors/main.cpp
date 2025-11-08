#include "factory.h"
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <fstream>
#include <string>
#include <yaml-cpp/yaml.h>
#include <atomic>


struct Task_Worker {
    std::chrono::steady_clock::time_point target_time;
    Command command;
};

template <typename T>
class ThreadSafeQueue {
public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_queue.push(std::move(value));
        m_cond.notify_one();
    }
    T pop() {
        std::unique_lock<std::mutex> lock(m_mutex);
        m_cond.wait(lock, [this]{ return !m_queue.empty(); });
        T value = std::move(m_queue.front());
        m_queue.pop();
        return value;
    }
private:
    std::queue<T> m_queue;
    std::mutex m_mutex;
    std::condition_variable m_cond;
};

void worker_function(
    int id,
    const YAML::Node& executor_config,
    ThreadSafeQueue<Task_Worker>& queue,
    std::atomic<long long>& success_count,
    std::atomic<long long>& error_count
) {
    std::unique_ptr<IExecutorStrategy> executor = nullptr;

    try {
        executor = ExecutorFactory::create(executor_config["type"].as<std::string>());
        executor->connect(executor_config);

        while (true) {
            Task_Worker task = queue.pop();
            if (task.command.op_type == "POISON_PILL") break;

            std::this_thread::sleep_until(task.target_time);

            ExecutionResult result = executor->execute(task.command);

            if (result.success) {
                success_count++;
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

int main() {
    YAML::Node config;
    try {
        config = YAML::LoadFile("../../config.yaml"); 
    } catch (const std::exception& e) {
        std::cerr << "Error loading config.yaml: " << e.what() << std::endl;
        return 1;
    }
    
    const auto& pipeline_config = config["pipeline"];
    const auto& executor_config = config["components"]["executor"];
    
    const std::string input_log_path = pipeline_config["generator_log_file"].as<std::string>();

    std::ifstream input_log_file("../../" + input_log_path);
    if (!input_log_file.is_open()) {
        std::cerr << "Error: Could not open synthetic log file: " << input_log_path << std::endl;
        return 1;
    }

    auto command_parser = ExecutorFactory::create(executor_config["type"].as<std::string>());

    const int num_workers = executor_config["max_workers"].as<int>();
    std::vector<ThreadSafeQueue<Task_Worker>> queues(num_workers);
    std::vector<std::thread> workers;
    std::atomic<long long> success_count(0);
    std::atomic<long long> error_count(0);

    for (int i = 0; i < num_workers; ++i) {
        workers.emplace_back(
            worker_function, i, std::cref(executor_config),
            std::ref(queues[i]), std::ref(success_count), std::ref(error_count)
        );
    }

    std::cout << "Dispatching events from synthetic log file..." << std::endl;
    auto benchmark_start = std::chrono::steady_clock::now();
    
    std::string line;
    double trace_start_timestamp = -1.0;
    int worker_idx = 0;
    int line_count = 0;

    while (std::getline(input_log_file, line)) {
        line_count++;
        std::optional<Task> task_opt = command_parser->parse_line(line);
        if (!task_opt) {
            std::cerr << "Warning: Skipping malformed log line " << line_count << ": " << line << std::endl;
            continue;
        }

        Task parsed_task = *task_opt;

        if (trace_start_timestamp < 0) {
            trace_start_timestamp = parsed_task.original_timestamp;
        }
        
        long long relative_ns = static_cast<long long>((parsed_task.original_timestamp - trace_start_timestamp) * 1e9);
        auto target_time = benchmark_start + std::chrono::nanoseconds(relative_ns);

        Task_Worker worker_task = {target_time, parsed_task.command};

        queues[worker_idx % num_workers].push(worker_task);
        worker_idx++;
    }

    std::cout << "Dispatching complete. " << line_count << " lines processed." << std::endl;

    for (int i = 0; i < num_workers; ++i) {
        queues[i].push({{}, {"POISON_PILL", "", ""}});
    }

    for (auto& worker : workers) {
        worker.join();
    }

    long long total_executed = success_count + error_count;
    std::cout << "\n--- EXECUTION SUMMARY ---" << std::endl;
    std::cout << "Total Operations Attempted: " << total_executed << std::endl;
    std::cout << "Successful Operations:      " << success_count << std::endl;
    std::cout << "Failed Operations:          " << error_count << std::endl;
    if (total_executed > 0) {
        double success_rate = (static_cast<double>(success_count) / total_executed) * 100.0;
        printf("Success Rate:               %.2f%%\n", success_rate);
    }
    std::cout << "-------------------------\n" << std::endl;

    return 0;
}