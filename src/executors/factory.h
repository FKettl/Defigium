#pragma once
#include "interfaces.h"
#include <string>
#include <memory>

class ExecutorFactory {
public:
    static std::unique_ptr<IExecutorStrategy> create(const std::string& type);
};