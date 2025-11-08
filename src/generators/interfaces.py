from abc import ABC, abstractmethod
from typing import List
from ..models.fei import FEIEvent


class IGenerator(ABC):
    """
    Interface for strategies that transform a list of FEI events into a new
    list of synthetic FEI events.
    """

    @abstractmethod
    def generate(self, events: List[FEIEvent]) -> List[FEIEvent]:
        pass