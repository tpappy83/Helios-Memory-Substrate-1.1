
import numpy as np
from dataclasses import dataclass
from typing import List

@dataclass
class VectorRecord:
    id: str
    content: str
    vector: List[float]

class HeliosDistributedCore:
    def __init__(self):
        self.clusters = {}
        self.drift_factor = 0.05

    def calculate_importance_score(self, similarity, tier, age=0):
        tier_weight = {1: 1.0, 2: 0.7, 3: 0.4}.get(tier, 0.1)
        return (similarity * tier_weight) / (1 + (self.drift_factor * age))
