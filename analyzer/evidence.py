from dataclasses import dataclass, field
from typing import List


# --------------------------------
# INDIVIDUAL EVIDENCE
# --------------------------------

@dataclass
class Evidence:

    url: str

    page_type: str

    text: str

    similarity: float

    strength: str

    category: str


# --------------------------------
# STRUCTURED EVIDENCE GRAPH
# --------------------------------

@dataclass
class EvidenceGraph:

    semantic: List[Evidence] = field(default_factory=list)

    technical: List[Evidence] = field(default_factory=list)

    behavioral: List[Evidence] = field(default_factory=list)

    organizational: List[Evidence] = field(default_factory=list)


    # --------------------------------
    # ADD EVIDENCE
    # --------------------------------

    def add(self, evidence: Evidence):

        if evidence.category in [
            "product_ai",
            "internal_ai",
            "research_ai",
            "marketing_ai",
            "governance_ai",
            "consulting_ai"
        ]:

            self.semantic.append(evidence)

        elif evidence.category == "technical_ai":

            self.technical.append(evidence)

        elif evidence.category == "behavioral_ai":

            self.behavioral.append(evidence)

        else:

            self.organizational.append(evidence)


    # --------------------------------
    # GET ALL EVIDENCE
    # --------------------------------

    def all(self):

        return (
            self.semantic
            + self.technical
            + self.behavioral
            + self.organizational
        )