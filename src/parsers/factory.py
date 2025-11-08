from typing import Dict, Any
from .interfaces import IParser


class ParserFactory:
    """
    Factory responsible for creating Parser instances.
    """
    def create_parser(self, config: Dict[str, Any]) -> IParser:
        parser_type = config.get('type')

        if parser_type == 'redis':
            from .redis.redis_parser import RedisParser

            granularity = config.get('timestamp_granularity', 6)
            return RedisParser(timestamp_granularity=granularity)

        """ Example for future parsers:
        if parser_type == 'mongodb':
            from .mongodb.mongodb_parser import MongoDBParser

            granularity = config.get('timestamp_granularity', 6)
            return MongoDBParser(timestamp_granularity=granularity)
        """
        raise ValueError(f"Parser of type '{parser_type}' is not supported.")