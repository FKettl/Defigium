#ifndef THREAD_POOL_HPP
#define THREAD_POOL_HPP


#include "interfaces.h"
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <atomic>
#include <string>
#include <chrono>
#include <iostream>
#include <memory>
#include <yaml-cpp/yaml.h>

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

	bool empty() {
		std::lock_guard<std::mutex> lock(m_mutex);
		return m_queue.empty();
	}
private:
	std::queue<T> m_queue;
	std::mutex m_mutex;
	std::condition_variable m_cond;
};

class ThreadPool {
public:
	ThreadPool(size_t num_workers, const YAML::Node& executor_config);
	~ThreadPool();

	void enqueue_task(Task_Worker task);
	bool is_work_complete();

	std::atomic<long long> success_count{0};
	std::atomic<long long> error_count{0};
	std::atomic<long long> total_latency_ns{0};

private:
	void worker_function(int id);
	
	size_t m_num_workers;
	const YAML::Node& m_executor_config;

	ThreadSafeQueue<Task_Worker> m_queue;
	std::vector<std::thread> m_workers;
};

#endif
