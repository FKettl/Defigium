#pragma once
#include "../interfaces.h"
#include <memory>
#include <regex>

namespace sw { namespace redis { class Redis; } }

class RedisExecutorStrategy : public IExecutorStrategy {
public:
    RedisExecutorStrategy();
    ~RedisExecutorStrategy();

    void connect(const YAML::Node& config) override;
    ExecutionResult execute(const Command& command) override;
    std::optional<Task> parse_line(const std::string& log_line) override;

private:
    std::unique_ptr<sw::redis::Redis> m_redis_client;
    std::vector<std::string> parse_command_args(const std::string& command_str);
};
