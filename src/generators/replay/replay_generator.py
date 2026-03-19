from typing import List
from ..interfaces import IGenerator
from ...models.fei import FEIEvent


class ReplayGenerator(IGenerator):
    """
    A simple pass-through strategy that returns the input event list unchanged.
    """

    def generate(self, events: List[FEIEvent]) -> List[FEIEvent]:
        """
        Returns the input list of events without modification.
        """
        print(f"ReplayGenerator: Passing through {len(events)} events.")
        return events

    def _characterize(self, events: List[FEIEvent]) -> dict:
        """
        For the ReplayGenerator, characterization is trivial: we just need to capture the baseline epoch.
        """
        if not events:
            raise ValueError("No events provided for characterization.")
