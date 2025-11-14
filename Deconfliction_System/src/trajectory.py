from typing import List, Optional, Tuple
import numpy as np
from models import DroneMission, Waypoint

class TrajectoryInterpolator:  
    def __init__(self, mission: DroneMission):
        self.mission = mission
        self.waypoints_array = np.array([wp.to_array() for wp in mission.waypoints])
        self._precompute_segments()
    
    def _precompute_segments(self):
        self.segment_vectors = np.diff(self.waypoints_array, axis=0)
        self.segment_lengths = np.linalg.norm(self.segment_vectors, axis=1)
        self.cumulative_distances = np.concatenate([[0], np.cumsum(self.segment_lengths)])
        self.total_distance = self.cumulative_distances[-1]
    
    def interpolate_position(self, time: float) -> Optional[np.ndarray]:
        if not self.mission.time_window.contains(time):
            return None
        
        progress = (time - self.mission.time_window.start) / self.mission.time_window.duration()
        target_distance = progress * self.total_distance
        
        segment_idx = np.searchsorted(self.cumulative_distances, target_distance) - 1
        segment_idx = max(0, min(segment_idx, len(self.segment_lengths) - 1))
        
        distance_in_segment = target_distance - self.cumulative_distances[segment_idx]
        segment_progress = distance_in_segment / self.segment_lengths[segment_idx] if self.segment_lengths[segment_idx] > 0 else 0
        segment_progress = min(1.0, segment_progress)
        
        start_pos = self.waypoints_array[segment_idx]
        end_pos = self.waypoints_array[segment_idx + 1]
        position = start_pos + segment_progress * (end_pos - start_pos)
        
        return position
    
    def get_trajectory_samples(self, num_samples: int = 100) -> List[Tuple[float, np.ndarray]]:
        times = np.linspace(
            self.mission.time_window.start,
            self.mission.time_window.end,
            num_samples
        )
        
        samples = []
        for t in times:
            pos = self.interpolate_position(t)
            if pos is not None:
                samples.append((t, pos))
        
        return samples
