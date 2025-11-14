"""
Flask Backend API for UAV Deconfliction System
==============================================

This Flask server provides REST API endpoints for the React frontend.
It connects to your existing deconfliction code.

Setup:
1. Save as: backend/app.py
2. Install: pip install flask flask-cors
3. Run: python backend/app.py
4. Server runs on: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add src directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
SRC_PATH = os.path.join(PROJECT_ROOT, 'Deconfliction_System', 'src')
sys.path.insert(0, SRC_PATH)

# Import your existing code
from models import Waypoint, TimeWindow, DroneMission, DeconflictionReport
from deconfliction_service import DeconflictionService
from trajectory import TrajectoryInterpolator

# Try to import ML service (optional)
try:
    from ml_service import MLEnhancedDeconflictionService
    ML_AVAILABLE = True
except:
    ML_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize services
geometric_service = DeconflictionService(safety_buffer=15.0, time_resolution=0.5)

if ML_AVAILABLE:
    try:
        ml_service = MLEnhancedDeconflictionService.from_pretrained_model(
            model_path="../Deconfliction_System/ml_models/conflict_model.pkl"
        )
        print("✓ ML service loaded successfully")
    except:
        ml_service = None
        print("⚠ ML model not found, using geometric only")
else:
    ml_service = None


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'ml_available': ml_service is not None,
        'geometric_available': True
    })


@app.route('/api/verify', methods=['POST'])
def verify_mission():
    """
    Verify a drone mission for conflicts.
    
    Request body:
    {
        "primary": {
            "id": "PRIMARY",
            "waypoints": [
                {"x": 0, "y": 0, "z": 50},
                {"x": 100, "y": 100, "z": 60}
            ],
            "timeWindow": {"start": 0, "end": 120}
        },
        "others": [
            {
                "id": "DRONE-A",
                "waypoints": [...],
                "timeWindow": {...}
            }
        ],
        "useML": true
    }
    """
    try:
        data = request.json
        
        # Parse primary mission
        primary_data = data['primary']
        primary_mission = parse_mission(primary_data)
        
        # Parse other missions
        other_missions = [parse_mission(m) for m in data.get('others', [])]
        
        # Choose service
        use_ml = data.get('useML', False) and ml_service is not None
        service = ml_service if use_ml else geometric_service
        
        # Verify mission
        report = service.verify_mission(primary_mission, other_missions)
        
        # Convert report to JSON
        response = {
            'status': report.status,
            'conflicts': [
                {
                    'time': c.time,
                    'location': {
                        'x': c.primary_location.x,
                        'y': c.primary_location.y,
                        'z': c.primary_location.z
                    },
                    'otherDroneId': c.other_drone_id,
                    'distance': c.distance,
                    'safetyBuffer': c.safety_buffer
                }
                for c in report.conflicts
            ],
            'safetyBuffer': report.safety_buffer,
            'analysisTime': report.analysis_time,
            'mlUsed': use_ml
        }
        
        # Add ML stats if available
        if use_ml and hasattr(service, 'get_statistics'):
            stats = service.get_statistics()
            response['mlStats'] = {
                'filtered': stats.get('ml_filtered', 0),
                'checked': stats.get('geometric_checks', 0),
                'filterRate': stats.get('filter_rate', 0)
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'ERROR'
        }), 400


@app.route('/api/trajectory', methods=['POST'])
def get_trajectory():
    """
    Get trajectory samples for visualization.
    
    Request body:
    {
        "mission": {
            "id": "PRIMARY",
            "waypoints": [...],
            "timeWindow": {...}
        },
        "numSamples": 100
    }
    """
    try:
        data = request.json
        mission = parse_mission(data['mission'])
        num_samples = data.get('numSamples', 100)
        
        # Create interpolator
        interpolator = TrajectoryInterpolator(mission)
        
        # Get samples
        samples = interpolator.get_trajectory_samples(num_samples)
        
        # Convert to JSON
        trajectory = [
            {
                'time': t,
                'position': {
                    'x': float(pos[0]),
                    'y': float(pos[1]),
                    'z': float(pos[2])
                }
            }
            for t, pos in samples
        ]
        
        return jsonify({
            'missionId': mission.id,
            'trajectory': trajectory
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get predefined demo scenarios."""
    scenarios = {
        'conflict': {
            'name': 'Conflict Scenario',
            'primary': {
                'id': 'PRIMARY',
                'waypoints': [
                    {'x': 0, 'y': 0, 'z': 50},
                    {'x': 50, 'y': 50, 'z': 60},
                    {'x': 100, 'y': 50, 'z': 70},
                    {'x': 150, 'y': 0, 'z': 70}
                ],
                'timeWindow': {'start': 30, 'end': 150}
            },
            'others': [
                {
                    'id': 'Drone-A',
                    'waypoints': [
                        {'x': 150, 'y': 100, 'z': 55},
                        {'x': 100, 'y': 75, 'z': 65},
                        {'x': 70, 'y': 50, 'z': 60},
                        {'x': 0, 'y': 25, 'z': 50}
                    ],
                    'timeWindow': {'start': 30, 'end': 150}
                },
                {
                    'id': 'Drone-B',
                    'waypoints': [
                        {'x': 25, 'y': 100, 'z': 45},
                        {'x': 75, 'y': 75, 'z': 55},
                        {'x': 125, 'y': 50, 'z': 65},
                        {'x': 150, 'y': 25, 'z': 70}
                    ],
                    'timeWindow': {'start': 0, 'end': 100}
                }
            ]
        },
        'clear': {
            'name': 'Clear Scenario',
            'primary': {
                'id': 'PRIMARY',
                'waypoints': [
                    {'x': 0, 'y': 0, 'z': 50},
                    {'x': 50, 'y': 25, 'z': 60},
                    {'x': 100, 'y': 25, 'z': 70},
                    {'x': 150, 'y': 0, 'z': 50}
                ],
                'timeWindow': {'start': 0, 'end': 120}
            },
            'others': [
                {
                    'id': 'Drone-A',
                    'waypoints': [
                        {'x': 0, 'y': 100, 'z': 100},
                        {'x': 50, 'y': 100, 'z': 110},
                        {'x': 100, 'y': 100, 'z': 120},
                        {'x': 150, 'y': 100, 'z': 100}
                    ],
                    'timeWindow': {'start': 0, 'end': 120}
                },
                {
                    'id': 'Drone-B',
                    'waypoints': [
                        {'x': 150, 'y': 50, 'z': 30},
                        {'x': 100, 'y': 75, 'z': 25},
                        {'x': 50, 'y': 75, 'z': 20},
                        {'x': 0, 'y': 50, 'z': 30}
                    ],
                    'timeWindow': {'start': 50, 'end': 170}
                }
            ]
        }
    }
    
    return jsonify(scenarios)


@app.route('/api/ml-stats', methods=['GET'])
def get_ml_stats():
    """Get ML service statistics."""
    if ml_service and hasattr(ml_service, 'get_statistics'):
        stats = ml_service.get_statistics()
        return jsonify(stats)
    else:
        return jsonify({'error': 'ML service not available'}), 404


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def parse_mission(mission_data):
    """Parse mission data from JSON to DroneMission object."""
    waypoints = [
        Waypoint(
            x=wp['x'],
            y=wp['y'],
            z=wp['z']
        )
        for wp in mission_data['waypoints']
    ]
    
    time_window = TimeWindow(
        start=mission_data['timeWindow']['start'],
        end=mission_data['timeWindow']['end']
    )
    
    return DroneMission(
        id=mission_data['id'],
        waypoints=waypoints,
        time_window=time_window
    )


# ==============================================================================
# RUN SERVER
# ==============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("UAV DECONFLICTION API SERVER")
    print("="*60)
    print(f"Geometric service: ✓ Available")
    print(f"ML service: {'✓ Available' if ml_service else '✗ Not available'}")
    print("\nServer running on: http://localhost:5000")
    print("API endpoints:")
    print("  - GET  /api/health")
    print("  - POST /api/verify")
    print("  - POST /api/trajectory")
    print("  - GET  /api/scenarios")
    print("  - GET  /api/ml-stats")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)