# Strategy: RedisExecutorStrategy

## 1. Introduction

This is the implementation of the `IExecutorStrategy` specialized for interacting with a **Redis** server.

This C++ class is the target-system driver for Redis. It fulfills the three core responsibilities of the `IExecutorStrategy` interface:

1.  **`parse_line(log_line)`:** Converts a log line (in `MONITOR` format) into a `Task` object. This function is used by the *Manager thread*.
2.  **`connect(config)`:** Establishes and manages the connection to the Redis server using the `redis++` library. This function is used by each *Worker thread*.
3.  **`execute(command)`:** Translates the generic `Command` object into a specific `redis++` API call (e.g., `m_redis_client->hmset(...)`). This function is used by each *Worker thread*.

---

## 2. Implementation

### 2.1. Parsing (Log -> Task)

The `parse_line` method is designed to parse the specific syntax of the Redis `MONITOR` log.

* **Initial Regex:** A regular expression (`line_splitter_regex`) splits the line into three components: `timestamp`, `[client_id]`, and the `full command string`.
* **Custom Command Parser:** Similar to the `RedisParser` (Python), this class uses a parser (`parse_command_args`) that understands the separation rule by `" "` (quotes and a space), treating arguments as raw strings.
* **Attribute Mapping:** The parser populates the `Task` struct, which contains the `original_timestamp` and the `Command` (with `op_type`, `target`, and `additional_data["raw_args"]`).

### 2.2. Connection

The `connect` method is called once per *worker thread*. It reads the `host` and `port` from the configuration node (`executor_config`).

Crucially, it sets connection and socket *timeouts* (e.g., 1 second). This is vital to ensure that the *worker thread* does not hang indefinitely on a network operation (especially during the `m_redis_client.reset()` destructor), allowing the program to terminate gracefully.

### 2.3. Command Execution

The `execute` method is the core of the *worker thread*. It implements a `switch` (using `if-else if` statements) over `command.op_type` to translate the generic task into a `redis++` library call.

* **Argument Translation:** The `execute` logic is responsible for formatting the arguments. For example, for `HMSET`, it converts the `std::vector<std::string>` from `raw_args` into a `std::vector<std::pair<std::string, std::string>>`, which is the format required by the `redis++` library.

### 2.4. Supported Commands

The current implementation supports a subset of commands focused on the YCSB workload (Workload A):

* `HMSET`
* `SET`
* `GET`
* `HGETALL`
* `DEL`
* `ZADD`

Adding new commands (e.g., `HGET`) would require adding a new `else if (command.op_type == "HGET")` block within the `execute` method.

---

## 3. Dependencies

This strategy introduces external C++ dependencies that must be linked during compilation:

* **`redis++`:** The C++ client library for Redis.
* **`hiredis`:** The low-level C library that `redis++` relies on.

---

## 4. Compilation

To compile the Executor with this strategy, use the `Makefile` with the `redis` target:

```bash
make redis
```
