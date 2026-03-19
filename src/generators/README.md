# Generator Strategy: Replay

## 1. Introduction

The `ReplayGenerator` is the most fundamental generation strategy within the Defigium framework. It implements a strict pass-through logic.

Its primary objective is not to synthesize a novel workload, but rather to serve as an analytical baseline to validate the operational fidelity of the Executor Module.

When employed, the resulting synthetic trace is an identical replica of the original input trace. This facilitates a direct, isolated comparison between the theoretical workload the Executor is instructed to dispatch and the physical workload it actually executes over the network.

## 2. Implementation

The implementation is intentionally minimalist, strictly adhering to the `IGenerator` interface contract.

The `generate` method receives the chronological sequence of Intermediate Event Format (IEF) objects from the parsed original trace and directly returns the exact same sequence without any modifications. No statistical characterization, probabilistic modeling, or data synthesis is performed during this process.

## 3. Configuration

To utilize this strategy, define the following directive in the central `config.yaml` orchestration file:

```yaml
generator:
  type: replay
```
