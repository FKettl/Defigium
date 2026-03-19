# Defigium: A Modular Framework for Trace-Based Workload Generation

Defigium is a modular benchmark framework designed to generate customized, high-fidelity workloads. It is grounded in the analysis of real operational traces and the application of statistical models to capture specific usage patterns.

The primary motivation of the framework is to address the limitations of standardized benchmarks, which frequently fail to replicate the complexity and dynamic characteristics of real-world production workloads.

## 1. Architecture and Workflow

The architecture of Defigium is its primary contribution. It features a three-stage pipeline that utilizes a dual-language (Python/C++) approach to balance analytical flexibility with execution performance.

The workflow is structured as follows:

1. Parser Module (Python): Acts as a bidirectional translator. It ingests a raw trace (e.g., trace.log) and converts it into a standardized Intermediate Event Format (IEF).
2. Generator Module (Python): The logical core. It consumes the IEF events and applies a designated strategy (such as Heatmap or Replay) to characterize the trace and synthesize a new workload. The output is stored as a synthetic trace (e.g., synthetic_trace.log).
3. Executor Module (C++): The execution engine. Implemented in C++ for high performance and temporal precision, it reads the synthetic trace and dispatches it against a target system (e.g., Redis), strictly adhering to the exact cadence and timing of the generated model.

## 2. Usage

The framework execution is a two-step process orchestrated by a single config.yaml file.

### 2.1. Prerequisites

* Python: Python 3.x, pip, and the PyYAML library.
* C++: A C++17 compiler, make, and development libraries for yaml-cpp.
* Client Libraries: C++ libraries for the target system to be compiled (e.g., libredis++-dev, libhiredis-dev for Redis).

### 2.2. Configuration (config.yaml)

The entire framework is controlled by the config.yaml file located in the project root. It defines which modules to instantiate and their respective parameters.

### 2.3. Stage 1: Generation (Python)

First, execute the Python process to analyze the input trace and generate the synthetic workload file.

```bash
# 1. Execute the main generation script
python main.py
```

This step runs the configured Parser and Generator, saving the output to the path specified in generator_log_file.

### 2.4. Stage 2: Execution (C++)

Next, compile and run the C++ process to dispatch the synthetic load against the target system.

```bash
# 1. Navigate to the executor directory
cd src/executors

# 2. Compile the C++ target for the desired strategy (e.g., redis)
make redis

# 3. Run the compiled binary
./executor
```

The C++ Executor reads the same config.yaml, establishes a connection to the target system, and begins dispatching operations from synthetic_trace.log with temporal precision.

## 3. Extensibility

The framework is designed for extensibility through the Strategy and Factory Method patterns.

* New Parser (Python): Implement the IParser interface (src/parsers/interfaces) and register it in the ParserFactory (src/parsers/factory.py).
* New Generator (Python): Implement the IGenerator interface (src/generators/interfaces) and register it in the GeneratorFactory (src/generators/factory.py).
* New Executor (C++): Implement the IExecutorStrategy interface (src/executors/interfaces.h), register it in the ExecutorFactory (src/executors/factory.cpp) using a conditional compilation flag, and add a new target to the Makefile.

## 4. Citation

This repository contains the practical implementation of the research developed by Felipe Backes Kettl (UFSC, 2025). If you use this work, please cite the original document.
