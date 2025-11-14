import time as time_module
from typing import List
from models import DroneMission, DeconflictionReport
from trajectory import TrajectoryInterpolator
from spatial_checker import SpatialConflictChecker
from temporal_checker import TemporalConflictChecker

class DeconflictionService:  
    def __init__(self, safety_buffer: float = 15.0, time_resolution: float = 0.5):
        self.safety_buffer = safety_buffer
        self.spatial_checker = SpatialConflictChecker(safety_buffer)
        self.temporal_checker = TemporalConflictChecker(
            self.spatial_checker,
            time_resolution
        )
    
    def verify_mission(
        self,
        primary_mission: DroneMission,
        other_missions: List[DroneMission]
    ) -> DeconflictionReport:
        start_time = time_module.time()
        primary_interpolator = TrajectoryInterpolator(primary_mission)
        all_conflicts = []
        for other_mission in other_missions:
            other_interpolator = TrajectoryInterpolator(other_mission)
            conflicts = self.temporal_checker.detect_conflicts(
                primary_interpolator,
                other_interpolator
            )
            all_conflicts.extend(conflicts)
        
        status = "CLEAR" if len(all_conflicts) == 0 else "CONFLICT"
        analysis_time = time_module.time() - start_time
        
        return DeconflictionReport(
            status=status,
            conflicts=all_conflicts,
            primary_mission=primary_mission,
            other_missions=other_missions,
            safety_buffer=self.safety_buffer,
            analysis_time=analysis_time
        )