from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class Waypoint:
    x: float
    y: float
    z: float
    
    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])
    
    def __repr__(self):
        return f"Waypoint(x={self.x:.1f}, y={self.y:.1f}, z={self.z:.1f})"


@dataclass
class TimeWindow:
    start: float 
    end: float   
    
    def duration(self) -> float:
        return self.end - self.start
    
    def contains(self, time: float) -> bool:
        return self.start <= time <= self.end


@dataclass
class DroneMission:
    id: str
    waypoints: List[Waypoint]
    time_window: TimeWindow
    
    def __post_init__(self):
        if len(self.waypoints) < 2:
            raise ValueError("Mission must have at least 2 waypoints")
        if self.time_window.duration() <= 0:
            raise ValueError("Time window must have positive duration")


@dataclass
class Conflict:
    time: float
    primary_location: Waypoint
    other_drone_id: str
    other_location: Waypoint
    distance: float
    safety_buffer: float
    
    def severity(self) -> float:
        return 1.0 - (self.distance / self.safety_buffer)
    
    def __repr__(self):
        return (f"Conflict(time={self.time:.1f}s, drone={self.other_drone_id}, "
                f"distance={self.distance:.2f}m, location={self.primary_location})")


@dataclass
class DeconflictionReport:
    status: str
    conflicts: List[Conflict]
    primary_mission: DroneMission
    other_missions: List[DroneMission]
    safety_buffer: float
    analysis_time: float
    
    def is_clear(self) -> bool:
        return self.status == "CLEAR"
    
    def conflict_summary(self) -> str:
        if self.is_clear():
            return "Mission CLEAR for execution. No conflicts detected."
        
        summary = [f"CONFLICT DETECTED: {len(self.conflicts)} conflict(s) found\n"]
        summary.append(f"Safety Buffer: {self.safety_buffer}m\n")
        
        conflicts_by_drone = {}
        for conflict in self.conflicts:
            if conflict.other_drone_id not in conflicts_by_drone:
                conflicts_by_drone[conflict.other_drone_id] = []
            conflicts_by_drone[conflict.other_drone_id].append(conflict)
        
        for drone_id, drone_conflicts in conflicts_by_drone.items():
            summary.append(f"\n  Conflicting with {drone_id}:")
            for i, conflict in enumerate(drone_conflicts[:3], 1):
                summary.append(
                    f"    {i}. Time: {conflict.time:.1f}s, "
                    f"Location: {conflict.primary_location}, "
                    f"Distance: {conflict.distance:.2f}m"
                )
            if len(drone_conflicts) > 3:
                summary.append(f"    ... and {len(drone_conflicts) - 3} more")
        
        return "".join(summary)
