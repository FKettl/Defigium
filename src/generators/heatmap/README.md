# Generator Strategy: Heatmap

## 1. Introduction

The primary objective of this strategy is to synthesize a workload that mimics the statistical characteristics of the original operational trace, enabling the generation of workloads with arbitrary durations.

The generation process is strictly divided into two phases: Characterization and Synthesis.

## 2. Characterization Phase (Analysis)

During this phase, the generator constructs a probabilistic "heatmap" model of the original trace.

It partitions the total trace duration into temporal "slices" or intervals, governed by the `percentage_interval` parameter. For instance, setting `percentage_interval: 1.0` divides the workload into 100 distinct 1% slices.

For each interval, the module extracts three independent probability distributions:

1.  **Command Composition:** The probability mass function of each `op_type` (e.g., 50% `HMSET`, 40% `HGETALL`).
2.  **Resource Popularity (Hotspots):** The probability of accessing a specific `target` (key), *given* a specific `op_type` (e.g., the key "user123" accounts for 30% of all `HGETALL` accesses *within* this slice).
3.  **Workload Rhythm (Inter-arrival Times):** The continuous probability distribution of time deltas (in milliseconds) between consecutive events.

## 3. Synthesis Phase (Generation)

In this phase, the generative engine synthesizes a novel workload from scratch, iterating until the configured `simulation_duration_s` is reached.

At each step, it first resolves the currently active temporal slice within the simulated clock, and then samples the probabilistic model of that specific interval to perform a **sequence of stochastic draws** (`random.choices`):

1.  Samples an `op_type`.
2.  Samples a `target` identifier.
3.  Samples a `delta_ms` to dictate the chronological placement of the *next* event.

### 3.1. State Management

The generator simulates the data lifecycle. It maintains a dynamic pool of active keys to ensure that `READ` or `DELETE` operations are never executed against targets that have not yet been created in the synthetic timeline.

### 3.2. Dependency Injection

For state-mutating operations, the generator invokes the `parser.generate_args()` method (injected via the `ParserFactory`) to instantiate realistic synthetic arguments and payloads.

## 4. Temporal Mapping

The framework can extrapolate workloads that extend beyond the duration of the original baseline by employing a `time_expansion_strategy`:

* **`cyclic`:** Repeats the learned statistical pattern. If the original trace spans 10 seconds and the simulation is configured for 30 seconds, the 10-second pattern will be executed 3 consecutive times.
* **`stretch`:** Elongates the pattern. Under the same conditions, the duration of each temporal "slice" from the original model will be proportionally stretched to last 3 times longer.

## 5. Configuration

To employ this strategy, define the following directives in the `config.yaml` file:

```yaml
generator:
  type: heatmap

  # (Required) Total duration of the synthetic workload in seconds
  simulation_duration_s: 120

  # (Optional) Analytical granularity. (Default: 5.0)
  # 1.0 = 100 slices, 5.0 = 20 slices, 50.0 = 2 slices
  percentage_interval: 1.0

  # (Optional) Temporal expansion strategy for extended durations. (Default: 'cyclic')
  # 'cyclic' = repeats the pattern
  # 'stretch' = proportionally elongates the pattern
  time_expansion_strategy: cyclic
```
