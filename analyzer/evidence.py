from dataclasses import dataclass


@dataclass
class Evidence:
    url: str
    page_type: str
    text: str
    similarity: float
    strength: str
    category: str