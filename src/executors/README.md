# Executor Module

## 1. Introduction

The Executor Module represents the final stage of the Defigium pipeline. It is responsible for transforming the synthetic trace (`synthetic_trace.log`) into concrete network interactions against a target system.

Unlike the analytical modules (which are written in Python), the Executor is implemented entirely in **C++** to guarantee high performance and granular temporal control. Its core responsibility is temporal fidelity: it does not merely dispatch operations, but does so while strictly adhering to the exact cadence and rhythm defined in the generated trace file.

## 2. Architecture and Implementation

The Executor's architecture relies on a multithreaded Manager-Worker pattern to achieve high concurrency and precise scheduling.

### 2.1. 'main' Thread (Manager)

The `main` thread acts as the central Manager, orchestrating the execution lifecycle. Its primary functions are:

* **Configuration:** Loads the `config.yaml` file (utilizing `yaml-cpp`) to retrieve the trace path, the required number of worker threads, and target system parameters.
* **Worker Initialization:** Instantiates a thread pool (`std::thread`) and provisions an independent, thread-safe queue (`ThreadSafeQueue`) for each worker.
* **Parsing and Dispatching:** Reads the `synthetic_trace.log` line by line. For each entry, it:
    1. Utilizes an `IExecutorStrategy` instance (instantiated via `ExecutorFactory`) to invoke `parse_line`, deserializing the log string into a manageable `Task` object.
    2. Calculates the absolute `target_time` of the operation by adding the trace's relative time delta to the baseline execution start time.
    3. Enqueues the `Task_Worker` payload (encapsulating the `target_time` and the `Command`) into a worker's queue using a round-robin scheduling approach.
* **Termination:** Upon dispatching all tasks, it issues a termination signal to each worker queue and synchronizes their completion via `join()`.

### 2.2. 'worker_function' Threads (Workers)

The worker threads are responsible for the physical execution of operations over the network. Each worker operates independently:

* **Initialization:** Creates its *own instance* of the designated `IExecutorStrategy` (via `ExecutorFactory`).
* **Connection:** Invokes the `connect()` method of its strategy to establish an independent, persistent connection with the target system.
* **Execution Loop:** Enters a continuous loop where it:
    1. Awaits a `Task_Worker` payload from its assigned queue.
    2. Evaluates if the payload constitutes a termination signal to gracefully exit.
    3. **Timed Execution:** Employs `std::this_thread::sleep_until(task.target_time)` to halt thread execution until the precise scheduled nanosecond, minimizing CPU busy-waiting overhead.
    4. At the exact scheduled moment, invokes `executor->execute(task.command)` to dispatch the operation against the target.
* **Reporting:** Registers the success or failure of the operation by incrementing global atomic counters.

### 2.3. Interface: `IExecutorStrategy`

Consistent with the overall framework design, the Executor employs the Strategy Pattern. The `IExecutorStrategy` interface defines the abstract contract that each target system integration must fulfill:

* **`connect(config)`:** Encapsulates the logic required to establish a connection with the target system.
* **`execute(command)`:** Translates the generic `Command` structure into a specific client library network invocation.
* **`parse_line(log_line)`:** Provides the Manager thread with the parsing logic to convert a raw log string back into a C++ `Task` structure.

## 3. Extensibility and Compilation

Integrating support for a new target system (e.g., HTTP) is a dual-layered process involving C++ implementation and build system configuration.

### 3.1. Conditional Compilation

Defigium employs **conditional compilation** to ensure the final executable remains lightweight and free of unused dependencies. The `ExecutorFactory` only links the source code of a specific strategy (e.g., `RedisExecutorStrategy`) if a designated preprocessor flag (e.g., `BUILD_REDIS_STRATEGY`) is declared during the build stage.

### 3.2. Makefile

The `Makefile` orchestrates this modular build process. To introduce a new strategy (e.g., `http`):

1.  **Source Code:** The developer implements the `HttpExecutorStrategy` and registers it within `factory.cpp` encapsulated by an `#ifdef BUILD_HTTP_STRATEGY` block.
2.  **Makefile Target:** A new build target is appended to the `Makefile` (e.g., `http:`).
3.  **Build Flags:** This target must supply two critical directives to the C++ compiler:
    * `CXXFLAGS`: The preprocessor flag (e.g., `-DBUILD_HTTP_STRATEGY`).
    * `LIBS`: The required external dependencies (e.g., `-lcurl`).

The user can then compile the desired configuration (e.g., `make redis` or `make http`), yielding an executable strictly tailored to that specific strategy without linking unnecessary libraries.

### 3.3. Dependencies

The core dependencies of the C++ Executor include:

* `yaml-cpp`: For configuration parsing.
* `pthread`: For multithreading infrastructure.
* Conditional Client Libraries:
    * **Redis:** `redis++` and `hiredis`.
    * **(Example) HTTP:** `curl`.
