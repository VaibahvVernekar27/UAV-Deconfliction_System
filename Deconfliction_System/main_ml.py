import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src'))

from models import Waypoint, TimeWindow, DroneMission, DeconflictionReport
from visualization import TrajectoryVisualizer
from ml_service import MLEnhancedDeconflictionService 
import time as time_module 


def create_conflict_scenario():
    primary = DroneMission(
        id="PRIMARY",
        waypoints=[
            Waypoint(0, 0, 50),
            Waypoint(50, 50, 60),
            Waypoint(100, 50, 70),
            Waypoint(150, 0, 50)
        ],
        time_window=TimeWindow(30, 150) 
    )
    
    other_drones = [
        DroneMission(
            id="Drone-A",
            waypoints=[
                Waypoint(150, 100, 55),
                Waypoint(100, 75, 65),
                Waypoint(35, 50, 60),
                Waypoint(0, 25, 50)
            ],
            time_window=TimeWindow(30, 150)
        ),
        DroneMission(
            id="Drone-B",
            waypoints=[
                Waypoint(25, 100, 45),
                Waypoint(75, 75, 55),
                Waypoint(125, 50, 65),
                Waypoint(150, 25, 70)
            ],
            time_window=TimeWindow(0, 100)
        )
    ]
    
    return primary, other_drones


def create_clear_scenario():
    primary = DroneMission(
        id="PRIMARY",
        waypoints=[
            Waypoint(0, 0, 50),
            Waypoint(50, 25, 60),
            Waypoint(100, 25, 70),
            Waypoint(150, 0, 50)
        ],
        time_window=TimeWindow(0, 120)
    )
    
    other_drones = [
        DroneMission(
            id="Drone-A",
            waypoints=[
                Waypoint(0, 100, 100),
                Waypoint(50, 100, 110),
                Waypoint(100, 100, 120),
                Waypoint(150, 100, 100)
            ],
            time_window=TimeWindow(0, 120)
        ),
        DroneMission(
            id="Drone-B",
            waypoints=[
                Waypoint(150, 50, 30),
                Waypoint(100, 75, 25),
                Waypoint(50, 75, 20),
                Waypoint(0, 50, 30)
            ],
            time_window=TimeWindow(50, 170)
        )
    ]
    
    return primary, other_drones


def main():
    # print("=" * 80)
    print("UAV STRATEGIC DECONFLICTION SYSTEM (ML Enhanced)")
    # print("=" * 80)
    ml_service = MLEnhancedDeconflictionService.from_pretrained_model(
        model_path="ml_models/conflict_model.pkl", 
        safety_buffer=15.0, 
        ml_threshold=0.2 
    )
    visualizer = TrajectoryVisualizer()

    ml_service.reset_statistics()

    print("\n--- SCENARIO 1: CONFLICT DETECTION ---")
    primary, others = create_conflict_scenario()

    report1 = ml_service.verify_mission(primary, others, verbose=True) 
    
    print(report1.conflict_summary())
    print(f"Total Analysis completed in {report1.analysis_time:.4f} seconds")

    visualizer.plot_3d_trajectories(report1, save_path="Result_images/ML_images/conflict_3d_ml.png")
    visualizer.plot_2d_views(report1, save_path="Result_images/ML_images/conflict_2d_ml.png")

    print("\n--- GENERATING CONFLICT ANIMATION ---")
    visualizer.create_animation(
        report1, 
        save_path="Result_images/conflict_animation.gif", 
        duration=15.0,
        fps=15         
    )

    print("\n--- SCENARIO 2: CLEAR FOR TAKEOFF (ML SHOULD FILTER MOST) ---")
    primary, others = create_clear_scenario()
    report2 = ml_service.verify_mission(primary, others, verbose=True) 
    
    print(report2.conflict_summary())
    print(f"Total Analysis completed in {report2.analysis_time:.4f} seconds")
    
    visualizer.plot_3d_trajectories(report2, save_path="Result_images/ML_images/clear_3d_ml.png")
    visualizer.plot_2d_views(report2, save_path="Result_images/ML_images/clear_2d_ml.png")

    ml_service.print_statistics()
    
    # print("\n" + "=" * 80)
    print("DEMO COMPLETE - ML-Enhanced Visualizations saved as PNG files")
    # print("=" * 80)


if __name__ == "__main__":
    main()