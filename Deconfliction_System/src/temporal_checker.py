from typing import List
from models import Conflict, Waypoint
from trajectory import TrajectoryInterpolator
from spatial_checker import SpatialConflictChecker

class TemporalConflictChecker:
    def __init__(self, spatial_checker: SpatialConflictChecker, time_resolution: float = 0.5):
        self.spatial_checker = spatial_checker
        self.time_resolution = time_resolution
    
    def detect_conflicts(
        self,
        primary_interpolator: TrajectoryInterpolator,
        other_interpolator: TrajectoryInterpolator
    ) -> List[Conflict]:
        conflicts = []
        
        time_start = max(
            primary_interpolator.mission.time_window.start,
            other_interpolator.mission.time_window.start
        )
        time_end = min(
            primary_interpolator.mission.time_window.end,
            other_interpolator.mission.time_window.end
        )
        
        if time_start >= time_end:
            return conflicts
        
        current_time = time_start
        while current_time <= time_end:
            primary_pos = primary_interpolator.interpolate_position(current_time)
            other_pos = other_interpolator.interpolate_position(current_time)
            
            if primary_pos is not None and other_pos is not None:
                distance = self.spatial_checker.distance_3d(primary_pos, other_pos)
                
                if distance < self.spatial_checker.safety_buffer:
                    conflict = Conflict(
                        time=current_time,
                        primary_location=Waypoint(*primary_pos),
                        other_drone_id=other_interpolator.mission.id,
                        other_location=Waypoint(*other_pos),
                        distance=distance,
                        safety_buffer=self.spatial_checker.safety_buffer
                    )
                    conflicts.append(conflict)
            
            current_time += self.time_resolution
        
        return self._filter_duplicate_conflicts(conflicts)
    
    def _filter_duplicate_conflicts(
        self,
        conflicts: List[Conflict],
        time_threshold: float = 5.0
    ) -> List[Conflict]:
        if not conflicts:
            return conflicts
        
        sorted_conflicts = sorted(conflicts, key=lambda c: c.time)
        filtered = [sorted_conflicts[0]]
        
        for conflict in sorted_conflicts[1:]:
            if conflict.time - filtered[-1].time >= time_threshold:
                filtered.append(conflict)
        
        return filtered
