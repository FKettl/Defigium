import os
from src.config_loader import load_config
from src.parsers.factory import ParserFactory
from src.generators.factory import GeneratorFactory

def run_python_pipeline():
    """
    Orchestrates the parsing and generation stages in-memory.
    Runs the generation multiple times to ensure statistical robustness.
    """
    print("\n--- STARTING WORKLOAD GENERATION PIPELINE (MULTI-RUN MODE) ---")

    config = load_config('config.yaml')
    pipeline_config = config.get('pipeline', {})
    components_config = config.get('components', {})
    parser_config = components_config.get('parser', {})
    generator_config = components_config.get('generator', {})

    parser_factory = ParserFactory()
    parser = parser_factory.create_parser(parser_config)

    input_log_file = pipeline_config.get('input_log_file')
    output_log_base = pipeline_config.get('generator_log_file')

    if not all([input_log_file, output_log_base]):
        raise KeyError(
            "'input_log_file' or 'generator_log_file' not found in config.yaml"
        )

    print(f"Parsing '{input_log_file}' into memory (Single Pass)...")
    event_iterator = parser.parse(input_log_file)
    loaded_events = list(event_iterator)
    print(f"Parsing complete. {len(loaded_events)} events loaded into memory.")

    NUM_RUNS = 30

    filename, ext = os.path.splitext(output_log_base)

    print(f"\nStarting {NUM_RUNS} generation rounds for statistical robustness...")

    for i in range(1, NUM_RUNS + 1):
        print(f"\n[Run {i}/{NUM_RUNS}] processing...")

        # Instantiate a fresh generator for each run to ensure independent randomization
        generator_factory = GeneratorFactory()
        generator = generator_factory.create_generator(generator_config, parser)

        print(" -> Starting Synthesis Phase...")
        synthetic_events = generator.generate(loaded_events)

        current_output_file = f"{filename}_{i}{ext}"

        print(f"   -> Formatting and saving {len(synthetic_events)} events to '{current_output_file}'...")
        with open(current_output_file, 'w', encoding='utf-8') as f:
            for event in synthetic_events:
                log_line = parser.format(event)
                f.write(log_line + '\n')

    print(f"\nPipeline completed. {NUM_RUNS} synthetic logs generated.")

if __name__ == "__main__":
    run_python_pipeline()
