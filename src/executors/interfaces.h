#pragma once
#include <string>
#include <memory>
#include <vector>
#include <map>
#include <optional>
#include <chrono>
#include <yaml-cpp/yaml.h>

struct Command {
    std::string op_type;
    std::string target;
    std::string client_id;
    std::map<std::string, std::vector<std::string>> additional_data;
};

struct Task {
    double original_timestamp;
    Command command;
};

struct ExecutionResult {
    long long latency_ns;
    bool success;
};

class IExecutorStrategy {
public:
    virtual ~IExecutorStrategy() = default;
    virtual void connect(const YAML::Node& config) = 0;
    virtual ExecutionResult execute(const Command& command) = 0;
    virtual std::optional<Task> parse_line(const std::string& log_line) = 0;
};