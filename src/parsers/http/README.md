# Parser Strategy: HTTP

## 1. Introduction

This document details the implementation of the `IParser` strategy dedicated to interacting with **HTTP web servers**, specifically structured to process high-volume access logs following the extended Combined Log Format (common in Apache and Nginx).

The `HttpParser` module acts as a domain adapter for web traffic environments, fulfilling the core responsibilities defined by the framework's interface:

1.  **Parsing (Ingestion):** Processes raw web server access logs and converts them into a continuous stream of Intermediate Event Format (IEF) objects. It employs a multiprocessing architecture to handle massive datasets efficiently.
2.  **Formatting (Exporting):** Performs the inverse operation, translating synthetic IEF events back into the native Combined Log Format syntax to ensure compatibility with standard HTTP benchmarking tools.
3.  **Synthetic Argument Generation:** Provides baseline logic to synthesize realistic supplementary arguments (e.g., standard User-Agent strings) for synthetic network requests.

## 2. Implementation and Features

### 2.1. Ingestion and Parsing (Log to IEF)

The `HttpParser` architecture was explicitly designed to handle large-scale data ingestion by parallelizing the text-processing workload.

* **Multiprocessing Architecture:** To process millions of log entries efficiently, the parser divides the input file into chunks (e.g., 20,000 lines per batch) and distributes them across a pool of worker processes (`multiprocessing.Pool`). This significantly reduces the parsing overhead for massive datasets.
* **Regular Expression Extraction:** A compiled regular expression (`LOG_PATTERN`) segments each log line into structural components: IP address, timestamp, HTTP method, URL target, protocol, status code, response size, referer, and user agent.
* **Temporal Granularity and Baseline Mapping:** Date strings are parsed and converted to UNIX epoch timestamps, rounded to a configurable granularity. Crucially, the parser captures the `baseline_epoch` (the absolute timestamp of the very first event) to allow relative time tracking during the generation phase.
* **Structural Mapping:**
    * `op_type`: Extracted as the HTTP method (e.g., "GET", "POST").
    * `target`: Extracted as the request URI path.
    * `additional_data`: Encapsulates web-specific metadata (status, size, referer, user agent, protocol) to preserve the structural fidelity of the payload.
* **Semantic Mapping:** To enable domain-agnostic statistical modeling, the parser abstracts HTTP methods into universal semantic categories. Data-mutating methods (`POST`, `PUT`, `PATCH`, `DELETE`) are mapped to `UPDATE`, while standard retrieval requests default to `READ`.

### 2.2. Formatting (IEF to Log)

The formatting routine (`format`) reconstructs valid Combined Log Format strings from synthetic IEF events. Because synthetic events operate on relative timestamps (deltas from zero) to facilitate temporal scaling, the formatter dynamically recalculates the absolute operational time by adding the synthetic delta to the original `baseline_epoch`. It then converts this absolute epoch back into the standard `dd/MMM/yyyy:HH:MM:SS +0000` string format.

### 2.3. Argument Synthesis

The `generate_args` method provides deterministic synthesis for supplementary HTTP headers when the generative engine creates non-deterministic operations. Currently, it supplies a standard synthetic User-Agent string (`"Mozilla/5.0 (Synthetic Defigium Client)"`) to distinguish generative requests from original traffic during downstream execution or analysis.

### 2.4. Supported Commands Scope

This implementation natively supports the parsing and semantic classification of standard RESTful HTTP methods, ensuring accurate representation of both idempotent and state-mutating web operations:

* `GET`
* `POST`
* `PUT`
* `PATCH`
* `DELETE`

Malformed log lines or entries that drastically deviate from the extended Combined Log Format are caught by an internal exception handler and silently bypassed to ensure uninterrupted parallel processing.

## 3. Dependencies

Despite its parallelized nature, the `HttpParser` implementation is structurally self-sufficient and introduces no external dependencies (e.g., `pip` packages). The entire parsing, regex, and multiprocessing infrastructure relies exclusively on the Python standard library.

## 4. Configuration

Activating this parsing module requires setting the following directive in the central `config.yaml` orchestration file:

```yaml
parser:
  type: http
```
