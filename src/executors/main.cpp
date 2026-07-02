#include "factory.h"
#include "ThreadPool.h"
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

int main() {
    YAML::Node config;
    try {
        config = YAML::LoadFile("config.yaml");
    } catch (const std::exception& e) {
        std::cerr << "Error loading config.yaml: " << e.what() << std::endl;
        return 1;
    }

    const auto& pipeline_config = config["pipeline"];
    const auto& executor_config = config["components"]["executor"];

    const std::string input_log_path = pipeline_config["generator_log_file"].as<std::string>();

    std::ifstream input_log_file(input_log_path);
    if (!input_log_file.is_open()) {
        std::cerr << "Error: Could not open synthetic log file: " << input_log_path << std::endl;
        return 1;
    }

    auto command_parser = ExecutorFactory::create(executor_config["type"].as<std::string>());

    std::cout << "Parsing events from synthetic log file into memory..." << std::endl;
    std::vector<Task> all_tasks;
    std::string line;
    int line_count = 0;

    while (std::getline(input_log_file, line)) {
        line_count++;
        std::optional<Task> task_opt = command_parser->parse_line(line);
        if (!task_opt) {
            std::cerr << "Warning: Skipping malformed log line " << line_count << ": " << line << std::endl;
            continue;
        }
        all_tasks.push_back(std::move(*task_opt));
    }

    std::cout << "Parsing complete. " << all_tasks.size() << " operations loaded." << std::endl;

    if (all_tasks.empty()) {
        std::cerr << "Error: No valid tasks found in the log file." << std::endl;
        return 1;
    }

    double trace_start_timestamp = all_tasks[0].original_timestamp;

    const int num_workers = executor_config["max_workers"].as<int>();
	ThreadPool pool(num_workers, executor_config);

	std::vector<Task_Worker> benchmark_set;

    auto benchmark_start = std::chrono::steady_clock::now();

    for (const auto& parsed_task : all_tasks) {
        long long relative_ns = static_cast<long long>((parsed_task.original_timestamp - trace_start_timestamp) * 1e9);
        auto target_time = benchmark_start + std::chrono::nanoseconds(relative_ns);

        Task_Worker worker_task = {target_time, parsed_task.command};
		benchmark_set.push_back(worker_task);
    }

	// Force order
	std::sort(benchmark_set.begin(), benchmark_set.end(), [](const Task_Worker& a, const Task_Worker& b){
		return a.target_time < b.target_time;
	});

	std::cout << "Firing benchmark timeline into the pool..." << std::endl;

	for (auto& task : benchmark_set)
		pool.enqueue_task(std::move(task));

    std::cout << "Dispatching complete. Waiting for workers to finish execution..." << std::endl;

	long long expected_total = benchmark_set.size();
	while (!pool.is_work_complete() || (pool.success_count + pool.error_count) < expected_total) {
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	}

	long long success_count = pool.success_count;
	long long error_count = pool.error_count;
    long long total_executed = success_count + error_count;
	long long avg_latency = success_count > 0 ? pool.total_latency_ns.load() / success_count : 0;
    std::cout << "\n--- EXECUTION SUMMARY ---" << std::endl;
    std::cout << "Total Operations Attempted: " << total_executed << std::endl;
    std::cout << "Successful Operations:      " << success_count << std::endl;
    std::cout << "Failed Operations:          " << error_count << std::endl;
	std::cout << "Average Latency (ns):       " << avg_latency << std::endl;
    if (total_executed > 0) {
        double success_rate = (static_cast<double>(pool.success_count) / total_executed) * 100.0;
        printf("Success Rate:               %.2f%%\n", success_rate);
    }
    std::cout << "-------------------------\n" << std::endl;

    return 0;
}
