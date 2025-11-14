from typing import List, Tuple
import numpy as np

class SpatialConflictChecker:
    
    def __init__(self, safety_buffer: float = 15.0):
        self.safety_buffer = safety_buffer
    
    @staticmethod
    def distance_3d(pos1: np.ndarray, pos2: np.ndarray) -> float:
        return np.linalg.norm(pos1 - pos2)
    
    def check_collision(self, pos1: np.ndarray, pos2: np.ndarray) -> bool:
        return self.distance_3d(pos1, pos2) < self.safety_buffer
    
    def find_minimum_distance(
        self,
        trajectory1: List[Tuple[float, np.ndarray]],
        trajectory2: List[Tuple[float, np.ndarray]]
    ) -> Tuple[float, float, float]:
        min_dist = float('inf')
        min_time1 = 0
        min_time2 = 0
        
        for t1, pos1 in trajectory1:
            for t2, pos2 in trajectory2:
                dist = self.distance_3d(pos1, pos2)
                if dist < min_dist:
                    min_dist = dist
                    min_time1 = t1
                    min_time2 = t2
        
        return min_dist, min_time1, min_time2
