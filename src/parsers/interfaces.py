from abc import ABC, abstractmethod
from typing import Iterator, List
from ..models.fei import FEIEvent


class IParser(ABC):
    """
    Interface for a domain-specific adapter that handles parsing, formatting,
    and synthetic argument generation.
    """

    @abstractmethod
    def parse(self, file_path: str) -> Iterator[FEIEvent]:
        """Reads a raw log file and yields a stream of FEIEvent objects."""
        pass

    @abstractmethod
    def format(self, event: FEIEvent) -> str:
        """Takes a single FEIEvent and formats it into a raw log line string."""
        pass

    @abstractmethod
    def generate_args(self, op_type: str, target: str, available_pool: List[str]) -> List[str]:
        """Generates a list of synthetic raw arguments for a given operation type."""
        pass