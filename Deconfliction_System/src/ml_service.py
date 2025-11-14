import numpy as np
import pickle
import os
import time
from typing import List, Dict, Union
import matplotlib.pyplot as plt 
from models import DroneMission, DeconflictionReport, Waypoint
from deconfliction_service import DeconflictionService

class FeatureExtractor:
    @staticmethod
    def calculate_bounding_box(mission: DroneMission) -> Dict:
        waypoints = np.array([wp.to_array() for wp in mission.waypoints])
        return {
            'x': (waypoints[:, 0].min(), waypoints[:, 0].max()),
            'y': (waypoints[:, 1].min(), waypoints[:, 1].max()),
            'z': (waypoints[:, 2].min(), waypoints[:, 2].max())
        }
    
    @staticmethod
    def box_overlap_amount(box1: Dict, box2: Dict) -> float:
        x_overlap = max(0, min(box1['x'][1], box2['x'][1]) - max(box1['x'][0], box2['x'][0]))
        y_overlap = max(0, min(box1['y'][1], box2['y'][1]) - max(box1['y'][0], box2['y'][0]))
        z_overlap = max(0, min(box1['z'][1], box2['z'][1]) - max(box1['z'][0], box2['z'][0]))
        return x_overlap * y_overlap * z_overlap
    
    @staticmethod
    def time_overlap_duration(mission1: DroneMission, mission2: DroneMission) -> float:
        tw1 = mission1.time_window
        tw2 = mission2.time_window
        overlap_start = max(tw1.start, tw2.start)
        overlap_end = min(tw1.end, tw2.end)
        return max(0, overlap_end - overlap_start)
    
    @staticmethod
    def min_waypoint_distance(mission1: DroneMission, mission2: DroneMission) -> float:
        min_dist = float('inf')
        for wp1 in mission1.waypoints:
            for wp2 in mission2.waypoints:
                dist = np.linalg.norm(wp1.to_array() - wp2.to_array())
                min_dist = min(min_dist, dist)
        return min_dist
    
    @staticmethod
    def altitude_overlap(mission1: DroneMission, mission2: DroneMission) -> float:
        alt1_min = min(wp.z for wp in mission1.waypoints)
        alt1_max = max(wp.z for wp in mission1.waypoints)
        alt2_min = min(wp.z for wp in mission2.waypoints)
        alt2_max = max(wp.z for wp in mission2.waypoints)
        return max(0, min(alt1_max, alt2_max) - max(alt1_min, alt2_min))
    
    @staticmethod
    def path_length_ratio(mission1: DroneMission, mission2: DroneMission) -> float:
        def path_length(mission):
            total = 0
            for i in range(len(mission.waypoints) - 1):
                wp1 = mission.waypoints[i].to_array()
                wp2 = mission.waypoints[i + 1].to_array()
                total += np.linalg.norm(wp2 - wp1)
            return total
        
        len1 = path_length(mission1)
        len2 = path_length(mission2)
        if len1 == 0 or len2 == 0:
            return 0
        return min(len1, len2) / max(len1, len2)
    
    @staticmethod
    def average_speed_difference(mission1: DroneMission, mission2: DroneMission) -> float:
        def avg_speed(mission):
            total_distance = 0
            for i in range(len(mission.waypoints) - 1):
                wp1 = mission.waypoints[i].to_array()
                wp2 = mission.waypoints[i + 1].to_array()
                total_distance += np.linalg.norm(wp2 - wp1)
            duration = mission.time_window.duration()
            return total_distance / duration if duration > 0 else 0
        return abs(avg_speed(mission1) - avg_speed(mission2))
    
    def extract_features(self, mission1: DroneMission, mission2: DroneMission) -> np.ndarray:
        bbox1 = self.calculate_bounding_box(mission1)
        bbox2 = self.calculate_bounding_box(mission2)
        
        features = [
            self.box_overlap_amount(bbox1, bbox2),
            self.time_overlap_duration(mission1, mission2),
            self.min_waypoint_distance(mission1, mission2),
            self.altitude_overlap(mission1, mission2),
            max(0, max(bbox1['x'][0], bbox2['x'][0]) - min(bbox1['x'][1], bbox2['x'][1])),
            max(0, max(bbox1['y'][0], bbox2['y'][0]) - min(bbox1['y'][1], bbox2['y'][1])),
            max(0, max(bbox1['z'][0], bbox2['z'][0]) - min(bbox1['z'][1], bbox2['z'][1])),
            self.path_length_ratio(mission1, mission2),
            self.average_speed_difference(mission1, mission2),
            max(0, max(mission1.time_window.start, mission2.time_window.start) - 
                     min(mission1.time_window.end, mission2.time_window.end))
        ]
        
        return np.array(features, dtype=np.float32).reshape(1, -1)

class MLEnhancedDeconflictionService:
    def __init__(
        self, 
        ml_model: Union[object, None], 
        safety_buffer: float = 15.0,
        ml_threshold: float = 0.2
    ):
        self.ml_model = ml_model
        self.feature_extractor = FeatureExtractor()
        self.geometric_checker = DeconflictionService(
            safety_buffer=safety_buffer,
            time_resolution=0.5
        )
        self.ml_threshold = ml_threshold
        
        self.stats = {
            'total_checks': 0,
            'ml_filtered': 0,
            'geometric_checks': 0,
            'total_time_ml': 0,
            'total_time_geometric': 0
        }
    
    @classmethod
    def from_pretrained_model(
        cls, 
        model_path: str = "ml_models/conflict_model.pkl",
        safety_buffer: float = 15.0,
        ml_threshold: float = 0.2
    ):
        ml_model = None
        
        if not os.path.exists(model_path) or os.path.getsize(model_path) == 0:
            print(f"Warning: Model file not found or empty at {model_path}. Running in GEOMETRIC ONLY mode.")
        else:
            try:
                print(f"Loading pre-trained model from: {model_path}")
                with open(model_path, 'rb') as f:
                    model_package = pickle.load(f)

                ml_model = model_package.get('model', model_package) 
                print("Model loaded successfully.")
                if isinstance(model_package, dict) and 'training_info' in model_package:
                    info = model_package['training_info']
                    print(f"  Model Info: Accuracy={info.get('validation_accuracy', 'N/A')}, ROC-AUC={info.get('roc_auc', 'N/A')}")
            except Exception as e:
                print(f"ERROR loading model: {e}. Defaulting to GEOMETRIC ONLY mode.")
                
        return cls(ml_model, safety_buffer, ml_threshold)
    
    def verify_mission(
        self, 
        primary_mission: DroneMission,
        other_missions: List[DroneMission],
        verbose: bool = False
    ) -> DeconflictionReport:
        start_time = time.time()
        self.stats['total_checks'] += 1
        
        if len(other_missions) == 0:
            return self.geometric_checker.verify_mission(primary_mission, [])
        
        ml_start = time.time()
        high_risk_missions = []
        
        if self.ml_model:
            features_matrix = np.vstack([
                self.feature_extractor.extract_features(primary_mission, other) 
                for other in other_missions
            ])
            
            probabilities = self.ml_model.predict_proba(features_matrix)[:, 1]
            
            high_risk_indices = np.where(probabilities >= self.ml_threshold)[0]
            high_risk_missions = [other_missions[i] for i in high_risk_indices]
            
            ml_time = time.time() - ml_start
            self.stats['total_time_ml'] += ml_time
            self.stats['ml_filtered'] += len(other_missions) - len(high_risk_missions)
            self.stats['geometric_checks'] += len(high_risk_missions)
            
            if verbose:
                print(f"ML Pre-Screening (Threshold: {self.ml_threshold*100:.0f}%):")
                print(f"  Total Missions: {len(other_missions)}, Filtered (Safe): {self.stats['ml_filtered']}, High-Risk (Check Needed): {len(high_risk_missions)}")
                print(f"  ML Time: {ml_time*1000:.2f}ms")
        else:
            high_risk_missions = other_missions
            self.stats['geometric_checks'] += len(other_missions)
            if verbose:
                print("ML Filter is DISABLED. Running full Geometric Check.")

        geom_start = time.time()
        report = self.geometric_checker.verify_mission(
            primary_mission, 
            high_risk_missions
        )
        geom_time = time.time() - geom_start
        self.stats['total_time_geometric'] += geom_time
        
        total_time = time.time() - start_time
        
        if verbose:
            print(f"Geometric Check Time: {geom_time*1000:.2f}ms. Total Time: {total_time*1000:.2f}ms")
            print(f"Conflicts found: {len(report.conflicts)}")
        
        report.analysis_time = total_time
        
        return report
    
    def get_statistics(self) -> Dict:
        stats = self.stats.copy()
        
        if stats['total_checks'] > 0:
            avg_ml_time = stats['total_time_ml'] / stats['total_checks']
            avg_geom_time = stats['total_time_geometric'] / stats['total_checks']
            stats['avg_ml_time_ms'] = avg_ml_time * 1000
            stats['avg_geometric_time_ms'] = avg_geom_time * 1000
            stats['avg_total_time_ms'] = (stats['total_time_ml'] + stats['total_time_geometric']) / stats['total_checks'] * 1000
            
            total_missions = stats['ml_filtered'] + stats['geometric_checks']
            stats['filter_rate'] = stats['ml_filtered'] / total_missions if total_missions > 0 else 0
            
        return stats
    
    def print_statistics(self):
        stats = self.get_statistics()
        # print("\n" + "="*70)
        print("ML-ENHANCED DECONFLICTION PERFORMANCE STATISTICS")
        # print("="*70)
        print(f"Total mission verifications:       {stats['total_checks']}")
        print(f"Missions screened/considered:      {stats['ml_filtered'] + stats['geometric_checks']}")
        print(f"Missions FILTERED by ML:           {stats['ml_filtered']}")
        print(f"Missions GEOMETRICALLY CHECKED:    {stats['geometric_checks']}")
        print(f"ML Filter Rate:                    {stats.get('filter_rate', 0)*100:.1f}%")
        print(f"\nAverage Time Per Mission Check:")
        print(f"  ML Screening Time:     {stats.get('avg_ml_time_ms', 0):6.2f}ms")
        print(f"  Geometric Check Time:  {stats.get('avg_geometric_time_ms', 0):6.2f}ms")
        print(f"  Total Avg Time:        {stats.get('avg_total_time_ms', 0):6.2f}ms")
        # print("="*70)
        
    def reset_statistics(self):
        self.stats = {
            'total_checks': 0,
            'ml_filtered': 0,
            'geometric_checks': 0,
            'total_time_ml': 0,
            'total_time_geometric': 0
        }