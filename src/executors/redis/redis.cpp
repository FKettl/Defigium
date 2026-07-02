#include "redis.h"
#include <sw/redis++/redis++.h>
#include <vector>
#include <iterator>
#include <iostream>
#include <sstream>
#include <yaml-cpp/yaml.h>

RedisExecutorStrategy::RedisExecutorStrategy() = default;
RedisExecutorStrategy::~RedisExecutorStrategy() = default;

void RedisExecutorStrategy::connect(const YAML::Node& config) {
    const std::string host = config["host"].as<std::string>();
    const int port = config["port"].as<int>();

    sw::redis::ConnectionOptions connection_options;
    connection_options.host = host;
    connection_options.port = port;

    connection_options.socket_timeout = std::chrono::seconds(1);

    connection_options.connect_timeout = std::chrono::seconds(1);

	std::stringstream ss;
    ss << "Connecting to Redis at: tcp://" << host << ":" << port
              << " with 1s timeout" << std::endl;
	std::cout << ss.str();
    m_redis_client = std::make_unique<sw::redis::Redis>(connection_options);
}

ExecutionResult RedisExecutorStrategy::execute(const Command& command) {
	std::chrono::steady_clock::time_point start_time, end_time;
	bool timing_started = false;
	

    try {
        const auto& args_map = command.additional_data;
        const auto it = args_map.find("raw_args");
        const std::vector<std::string> raw_args = (it != args_map.end()) ? it->second : std::vector<std::string>();

        if (command.op_type == "HMSET") {
            if (!raw_args.empty() && raw_args.size() % 2 == 0) {
                std::vector<std::pair<std::string, std::string>> field_values;
                for (size_t i = 0; i < raw_args.size(); i += 2) {
                    field_values.emplace_back(raw_args[i], raw_args[i + 1]);
                }
				start_time = std::chrono::steady_clock::now();
				timing_started = true;
                m_redis_client->hmset(command.target, field_values.begin(), field_values.end());
				end_time = std::chrono::steady_clock::now();

            }
        } else if (command.op_type == "SET") {
            if (!raw_args.empty()) {
				start_time = std::chrono::steady_clock::now();
				timing_started = true;
                m_redis_client->set(command.target, raw_args[0]);
				end_time = std::chrono::steady_clock::now();
            }
        } else if (command.op_type == "GET") {
			start_time = std::chrono::steady_clock::now();
			timing_started = true;
            m_redis_client->get(command.target);
			end_time = std::chrono::steady_clock::now();
        } else if (command.op_type == "HGETALL") {
            std::vector<std::pair<std::string, std::string>> result;
			start_time = std::chrono::steady_clock::now();
			timing_started = true;
            m_redis_client->hgetall(command.target, std::back_inserter(result));
			end_time = std::chrono::steady_clock::now();
        } else if (command.op_type == "DEL") {
			start_time = std::chrono::steady_clock::now();
			timing_started = true;
            m_redis_client->del(command.target);
			end_time = std::chrono::steady_clock::now();
        } else if (command.op_type == "ZADD") {
            if (raw_args.size() >= 2) {
				start_time = std::chrono::steady_clock::now();
				timing_started = true;
                m_redis_client->zadd(command.target, raw_args[1], std::stod(raw_args[0]));
				end_time = std::chrono::steady_clock::now();
            }
        }
        // For more commands, add additional else-if blocks here.
		long long latency_ns = 0;
		if (timing_started) {
			auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time);
			latency_ns = elapsed.count();
		}
        return {latency_ns, true};
    } catch (const std::exception& e) {
        std::stringstream ss;
		ss << "ERRO ao executar comando [" << command.op_type << "] no alvo [" << command.target << "]: " << e.what() << std::endl;
		std::cerr << ss.str();
        return {0, false};
    }
}

std::vector<std::string> RedisExecutorStrategy::parse_command_args(const std::string& command_str) {
    std::vector<std::string> args;
    std::string current_arg;
    bool in_quotes = false;

    size_t i = 0;
    while (i < command_str.length()) {
        char c = command_str[i];

        if (!in_quotes) {
            if (c == '"') {
                in_quotes = true;
            }
            i++;
            continue;
        }

        bool is_end_of_string = (i + 1 == command_str.length());
        bool is_separator = (i + 2 < command_str.length() && command_str[i+1] == ' ' && command_str[i+2] == '"');

        if (c == '"' && (is_end_of_string || is_separator)) {
            in_quotes = false;
            args.push_back(current_arg);
            current_arg.clear();
        } else {
            current_arg += c;
        }
        i++;
    }
    return args;
}


std::optional<Task> RedisExecutorStrategy::parse_line(const std::string& log_line) {
    static const std::regex line_splitter_regex(R"(^(\S+)\s+\[([^\]]+)\]\s+(.*)\s*$)");

    std::smatch line_parts;
    if (!std::regex_match(log_line, line_parts, line_splitter_regex)) {
        std::cout << "Parse FAILED: Line does not match basic structure.\n" << std::endl;
        return std::nullopt;
    }

    Task task;
    try {
        task.original_timestamp = std::stod(line_parts[1].str());
    } catch (const std::invalid_argument&) {
        std::cout << "Parse FAILED: Invalid timestamp.\n" << std::endl;
        return std::nullopt;
    }

    task.command.client_id = line_parts[2].str();

    std::vector<std::string> all_args = parse_command_args(line_parts[3].str());

    if (all_args.empty()) {
        std::cout << "Parse FAILED: No arguments found.\n" << std::endl;
        return std::nullopt;
    }

    task.command.op_type = all_args[0];
    if (all_args.size() > 1) {
        task.command.target = all_args[1];
    }
    if (all_args.size() > 2) {
        task.command.additional_data["raw_args"] = {all_args.begin() + 2, all_args.end()};
    }

    return task;
}
