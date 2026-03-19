from typing import Any, Dict, TypedDict, List


class FEIEvent(TypedDict):
    """
    Defines the structure of the Intermediate Event Format (FEI).

    This is the canonical data structure that connects the different stages
    of the Python pipeline (Parser and Generator).
    """
    timestamp: float
    client_id: str
    op_type: str
    semantic_type: List[str]
    target: str
    additional_data: Dict[str, Any]