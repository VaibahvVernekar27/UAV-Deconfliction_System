import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, AlertTriangle, CheckCircle, Zap, Upload, Database } from 'lucide-react';
import './App.css'

const API_BASE_URL = 'http://localhost:5000/api';

const App = () => {
  const [scenarios, setScenarios] = useState({});
  const [selectedScenario, setSelectedScenario] = useState('conflict');
  const [primaryMission, setPrimaryMission] = useState(null);
  const [otherMissions, setOtherMissions] = useState([]);
  const [verificationResult, setVerificationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [useML, setUseML] = useState(false);
  const [mlAvailable, setMLAvailable] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [trajectories, setTrajectories] = useState({});
  const [view3D, setView3D] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then(res => res.json())
      .then(data => {
        setMLAvailable(data.ml_available);
        console.log('Backend connected:', data);
      })
      .catch(err => console.error('Backend not available:', err));

    fetch(`${API_BASE_URL}/scenarios`)
      .then(res => res.json())
      .then(data => {
        setScenarios(data);
        loadScenario('conflict', data);
      })
      .catch(err => console.error('Error loading scenarios:', err));
  }, []);

  const loadScenario = (scenarioKey, scenariosData = scenarios) => {
    const scenario = scenariosData[scenarioKey];
    if (scenario) {
      setPrimaryMission(scenario.primary);
      setOtherMissions(scenario.others);
      setSelectedScenario(scenarioKey);
      setVerificationResult(null);
      setCurrentTime(0);
      setIsPlaying(false);
    }
  };

  const verifyMission = async () => {
    if (!primaryMission || otherMissions.length === 0) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          primary: primaryMission,
          others: otherMissions,
          useML: useML && mlAvailable
        })
      });

      const result = await response.json();
      setVerificationResult(result);

      await loadTrajectories();
    } catch (error) {
      console.error('Verification error:', error);
      alert('Error connecting to backend. Make sure the Flask server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadTrajectories = async () => {
    const allMissions = [primaryMission, ...otherMissions];
    const trajData = {};

    for (const mission of allMissions) {
      try {
        const response = await fetch(`${API_BASE_URL}/trajectory`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mission, numSamples: 50 })
        });
        const data = await response.json();
        trajData[mission.id] = data.trajectory;
      } catch (error) {
        console.error(`Error loading trajectory for ${mission.id}:`, error);
      }
    }

    setTrajectories(trajData);
  };

  useEffect(() => {
    if (!isPlaying || !primaryMission) return;

    const maxTime = primaryMission.timeWindow.end;
    const interval = setInterval(() => {
      setCurrentTime(t => {
        if (t >= maxTime) {
          setIsPlaying(false);
          return maxTime;
        }
        return t + 1;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [isPlaying, primaryMission]);

  const getPositionAtTime = (trajectory, time) => {
    if (!trajectory || trajectory.length === 0) return null;
    
    let closest = trajectory[0];
    let minDiff = Math.abs(trajectory[0].time - time);
    
    for (const sample of trajectory) {
      const diff = Math.abs(sample.time - time);
      if (diff < minDiff) {
        minDiff = diff;
        closest = sample;
      }
    }
    
    return closest.position;
  };

  const render3DView = () => {
    if (!primaryMission) return null;

    const scale = 2.5;
    const offsetX = 200;
    const offsetY = 300;

    const project = (x, y, z) => ({
      x: offsetX + (x - y) * Math.cos(Math.PI / 6) * scale,
      y: offsetY - z * scale * 0.8 + (x + y) * Math.sin(Math.PI / 6) * scale
    });

    const renderPath = (waypoints, color, opacity = 0.4) => {
      const points = waypoints.map(w => project(w.x, w.y, w.z));
      const pathD = points.map((p, i) => 
        `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
      ).join(' ');

      return (
        <>
          <path d={pathD} stroke={color} strokeWidth="2" fill="none" opacity={opacity} strokeDasharray="5,5" />
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="3" fill={color} opacity={opacity} />
          ))}
        </>
      );
    };

    const renderDrone = (missionId, color, label) => {
      const trajectory = trajectories[missionId];
      if (!trajectory) return null;

      const pos = getPositionAtTime(trajectory, currentTime);
      if (!pos) return null;

      const p = project(pos.x, pos.y, pos.z);
      return (
        <g>
          <circle cx={p.x} cy={p.y} r="8" fill={color} stroke="white" strokeWidth="2" />
          <text x={p.x} y={p.y - 15} fill={color} fontSize="11" fontWeight="bold" textAnchor="middle">
            {label}
          </text>
        </g>
      );
    };

    return (
      <svg width="800" height="600" className="border border-gray-700 rounded bg-gray-900">
        {/* Grid */}
        {[...Array(8)].map((_, i) => (
          <g key={i} opacity="0.1">
            <line x1={offsetX + i * 50} y1={offsetY - 200} x2={offsetX + i * 50} y2={offsetY + 100} stroke="white" />
            <line x1={offsetX - 200} y1={offsetY + i * 30} x2={offsetX + 400} y2={offsetY + i * 30} stroke="white" />
          </g>
        ))}

        {/* Paths */}
        {primaryMission && renderPath(primaryMission.waypoints, '#3b82f6', 0.5)}
        {otherMissions.map((drone, i) => 
          renderPath(drone.waypoints, i === 0 ? '#ef4444' : '#f59e0b', 0.3)
        )}

        {/* Conflict zones */}
        {verificationResult?.conflicts.map((conflict, i) => {
          const p = project(conflict.location.x, conflict.location.y, conflict.location.z);
          return (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r={15 * scale}
              fill="red"
              opacity="0.2"
              stroke="red"
              strokeWidth="2"
            />
          );
        })}

        {/* Drones */}
        {primaryMission && renderDrone(primaryMission.id, '#3b82f6', 'PRIMARY')}
        {otherMissions.map((drone, i) => 
          renderDrone(drone.id, i === 0 ? '#ef4444' : '#f59e0b', drone.id)
        )}

        {/* Legend */}
        <g transform="translate(20, 20)">
          <rect width="160" height="80" fill="rgba(0,0,0,0.7)" rx="5" />
          <circle cx="15" cy="20" r="6" fill="#3b82f6" />
          <text x="30" y="25" fill="white" fontSize="11">Primary</text>
          <circle cx="15" cy="45" r="6" fill="#ef4444" />
          <text x="30" y="50" fill="white" fontSize="11">Drone-A</text>
          <circle cx="15" cy="70" r="6" fill="#f59e0b" />
          <text x="30" y="75" fill="white" fontSize="11">Drone-B</text>
        </g>
      </svg>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            UAV Deconfliction System - For Traffic Management
          </h1>
          <p className="text-gray-400">Full-stack 4D spatiotemporal conflict detection</p>
          <div className="flex gap-2 mt-2">
            <span className="px-2 py-1 bg-green-900 text-green-300 rounded text-xs">
              ● Backend Connected
            </span>
            {mlAvailable && (
              <span className="px-2 py-1 bg-purple-900 text-purple-300 rounded text-xs">
                ● ML Available
              </span>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Scenario Selection */}
          <div className="bg-gray-800 p-4 rounded-lg">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Database className="w-5 h-5" />
              Load Scenario
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => loadScenario('conflict')}
                className={`flex-1 px-4 py-2 rounded ${
                  selectedScenario === 'conflict'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Conflict Scenario
              </button>
              <button
                onClick={() => loadScenario('clear')}
                className={`flex-1 px-4 py-2 rounded ${
                  selectedScenario === 'clear'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Clear Scenario
              </button>
            </div>
          </div>

          {/* Verification */}
          <div className="bg-gray-800 p-4 rounded-lg">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Verify Mission
            </h3>
            <div className="flex gap-2">
              <button
                onClick={verifyMission}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Verify
                  </>
                )}
              </button>
              {mlAvailable && (
                <button
                  onClick={() => setUseML(!useML)}
                  className={`px-4 py-2 rounded flex items-center gap-2 ${
                    useML ? 'bg-purple-600' : 'bg-gray-700'
                  }`}
                >
                  <Zap className="w-4 h-4" />
                  {useML ? 'ML ON' : 'ML OFF'}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Results */}
        {verificationResult && (
          <div className={`mb-6 p-6 rounded-lg ${
            verificationResult.status === 'CLEAR' 
              ? 'bg-green-900/30 border border-green-700' 
              : 'bg-red-900/30 border border-red-700'
          }`}>
            <div className="flex items-center gap-3 mb-4">
              {verificationResult.status === 'CLEAR' ? (
                <CheckCircle className="w-8 h-8 text-green-400" />
              ) : (
                <AlertTriangle className="w-8 h-8 text-red-400" />
              )}
              <div className="flex-1">
                <h2 className="text-2xl font-bold">
                  {verificationResult.status}
                </h2>
                <div className="text-sm text-gray-400 flex gap-4 mt-1">
                  <span>Analysis: {(verificationResult.analysisTime * 1000).toFixed(2)}ms</span>
                  {verificationResult.mlUsed && (
                    <span className="text-purple-400">
                      ML: {verificationResult.mlStats?.filtered} filtered, {verificationResult.mlStats?.checked} checked
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            {verificationResult.conflicts.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-semibold text-red-300">Conflicts Detected:</h3>
                {verificationResult.conflicts.slice(0, 3).map((conflict, i) => (
                  <div key={i} className="bg-black/30 p-3 rounded text-sm">
                    <p><strong>Time:</strong> {conflict.time.toFixed(1)}s</p>
                    <p><strong>Drone:</strong> {conflict.otherDroneId}</p>
                    <p><strong>Location:</strong> ({conflict.location.x.toFixed(1)}, {conflict.location.y.toFixed(1)}, {conflict.location.z.toFixed(1)})</p>
                    <p><strong>Distance:</strong> {conflict.distance.toFixed(2)}m</p>
                  </div>
                ))}
                {verificationResult.conflicts.length > 3 && (
                  <p className="text-gray-400 text-sm">
                    ... and {verificationResult.conflicts.length - 3} more conflicts
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Animation Controls */}
        {Object.keys(trajectories).length > 0 && (
          <div className="mb-6 flex items-center gap-4 bg-gray-800 p-4 rounded-lg">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              {isPlaying ? 'Pause' : 'Play'}
            </button>
            <button
              onClick={() => {
                setCurrentTime(0);
                setIsPlaying(false);
              }}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2"
            >
              <RotateCcw className="w-5 h-5" />
              Reset
            </button>
            <div className="flex-1 px-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Time:</span>
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${primaryMission ? (currentTime / primaryMission.timeWindow.end) * 100 : 0}%`
                    }}
                  />
                </div>
                <span className="text-sm font-mono">{currentTime.toFixed(1)}s</span>
              </div>
            </div>
            <button
              onClick={() => setView3D(!view3D)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
            >
              {view3D ? '3D View' : '2D View'}
            </button>
          </div>
        )}

        {/* Visualization */}
        <div className="flex justify-center">
          {render3DView()}
        </div>

        {/* Backend Status */}
        <div className="mt-6 bg-gray-800 p-4 rounded-lg text-sm">
          <h3 className="font-semibold mb-2">Backend Status</h3>
          <div className="grid grid-cols-2 gap-2 text-gray-400">
            <div>API Endpoint: <span className="text-white">{API_BASE_URL}</span></div>
            <div>ML Service: <span className={mlAvailable ? 'text-green-400' : 'text-red-400'}>
              {mlAvailable ? 'Available' : 'Not Available'}
            </span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;