#include "factory.h"
#include <stdexcept>

#ifdef BUILD_REDIS_STRATEGY
    #include "redis/redis.h"
#endif

// Example of adding another strategy
#ifdef BUILD_HTTP_STRATEGY
    #include "http/http.h"
#endif


std::unique_ptr<IExecutorStrategy> ExecutorFactory::create(const std::string& type) {

    #ifdef BUILD_REDIS_STRATEGY
        if (type == "redis") {
            return std::make_unique<RedisExecutorStrategy>();
        }
    #endif

    // Example of adding another strategy
    #ifdef BUILD_HTTP_STRATEGY
        if (type == "http") {
            return std::make_unique<HttpExecutorStrategy>();
        }
    #endif

    throw std::runtime_error("Executor type not recognized " + type);
}