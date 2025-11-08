from typing import Any, Dict
from ..parsers.interfaces import IParser
from .interfaces import IGenerator


class GeneratorFactory:
    """Instantiates the IGenerator implementation based on config."""

    def create_generator(
        self,
        config: Dict[str, Any],
        parser: IParser
    ) -> IGenerator:

        generator_type = config.get('type')

        if generator_type == 'replay':
            from .replay.replay_generator import ReplayGenerator

            return ReplayGenerator()

        elif generator_type == 'heatmap':
            from .heatmap.heatmap_generator import HeatmapGenerator

            interval = config.get('percentage_interval', 5)
            simulation_duration_s = config.get('simulation_duration_s', 30)
            time_expansion_strategy = config.get('time_expansion_strategy', 'cyclic')

            return HeatmapGenerator(
                parser=parser,
                percentage_interval=interval,
                simulation_duration_s=simulation_duration_s,
                time_expansion_strategy=time_expansion_strategy 
            )
        else:
            raise ValueError(f"Generator type '{generator_type}' is not supported.")