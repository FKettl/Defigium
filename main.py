import json 
from src.config_loader import load_config
from src.parsers.factory import ParserFactory
from src.generators.factory import GeneratorFactory


def run_python_pipeline():
    """Orchestrates the parsing and generation stages in-memory."""
    print("\n--- STARTING WORKLOAD GENERATION PIPELINE ---")
    
    # --- 1. Load Configurations ---
    config = load_config('config.yaml')
    pipeline_config = config.get('pipeline', {})
    components_config = config.get('components', {})
    parser_config = components_config.get('parser', {})
    generator_config = components_config.get('generator', {})

    # --- 2. Instantiate Components and Dependencies ---
    # The Parser is created first, as it's the domain expert.
    parser_factory = ParserFactory()
    parser = parser_factory.create_parser(parser_config)

    # The Generator is created, injecting the 'parser' as a dependency
    # so it can use its domain-specific methods (like generate_args).
    generator_factory = GeneratorFactory()
    generator = generator_factory.create_generator(generator_config, parser)

    # --- 3. Execute the Pipeline ---
    input_log_file = pipeline_config.get('input_log_file')
    output_log_file = pipeline_config.get('generator_log_file')

    if not all([input_log_file, output_log_file]):
        raise KeyError(
            "'input_log_file' or 'generator_log_file' not found in config.yaml"
        )

    # Stage 1: Parse the raw log into an in-memory list of events
    print(f"Parsing '{input_log_file}' into memory...")
    event_iterator = parser.parse(input_log_file)
    loaded_events = list(event_iterator)
    print(f"Parsing complete. {len(loaded_events)} events loaded into memory.")

    # Stage 2: Generate the synthetic events list in-memory
    print(f"Running '{generator_config.get('type')}' strategy to generate events...")
    synthetic_events = generator.generate(loaded_events)

    # Stage 3: Format and write the output using the parser's format method
    print(f"Formatting and saving {len(synthetic_events)} events to '{output_log_file}'...")
    with open(output_log_file, 'w', encoding='utf-8') as f:
        for event in synthetic_events:
            log_line = parser.format(event)
            f.write(log_line + '\n')

    print(f"\nPipeline completed. Synthetic log saved to '{output_log_file}'.")

if __name__ == "__main__":
    run_python_pipeline()