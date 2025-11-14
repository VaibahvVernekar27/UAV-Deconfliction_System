from typing import Optional
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
from models import DeconflictionReport
from trajectory import TrajectoryInterpolator

class TrajectoryVisualizer:  
    def __init__(self, figsize=(14, 10)):
        self.figsize = figsize
    
    def plot_3d_trajectories(
        self,
        report: DeconflictionReport,
        show_conflicts: bool = True,
        save_path: Optional[str] = None
    ):
        fig = plt.figure(figsize=self.figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        primary_waypoints = np.array([
            wp.to_array() for wp in report.primary_mission.waypoints
        ])
        ax.plot(
            primary_waypoints[:, 0],
            primary_waypoints[:, 1],
            primary_waypoints[:, 2],
            'b-o', linewidth=2, markersize=8, label='Primary Drone'
        )
        
        colors = ['red', 'orange', 'purple', 'cyan', 'magenta']
        for i, mission in enumerate(report.other_missions):
            waypoints = np.array([wp.to_array() for wp in mission.waypoints])
            color = colors[i % len(colors)]
            ax.plot(
                waypoints[:, 0],
                waypoints[:, 1],
                waypoints[:, 2],
                # f'{color[0]}--o', linewidth=1.5, markersize=6,
                # alpha=0.6, label=mission.id
                linestyle='--', 
                marker='o',
                color=color,   
                linewidth=1.5, 
                markersize=6,
                alpha=0.6, 
                label=mission.id
            )
        
        if show_conflicts and report.conflicts:
            conflict_points = np.array([
                c.primary_location.to_array() for c in report.conflicts
            ])
            ax.scatter(
                conflict_points[:, 0],
                conflict_points[:, 1],
                conflict_points[:, 2],
                c='red', s=200, marker='X', alpha=0.7,
                edgecolors='darkred', linewidths=2,
                label='Conflicts'
            )
        
        ax.set_xlabel('X (m)', fontsize=12)
        ax.set_ylabel('Y (m)', fontsize=12)
        ax.set_zlabel('Z - Altitude (m)', fontsize=12)
        ax.set_title(
            f'UAV Trajectory Deconfliction - Status: {report.status}',
            fontsize=14, fontweight='bold'
        )
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved 3D plot: {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_2d_views(
        self,
        report: DeconflictionReport,
        save_path: Optional[str] = None
    ):
        """Plot 2D projection views (XY, XZ, YZ)."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        primary_wp = np.array([
            wp.to_array() for wp in report.primary_mission.waypoints
        ])
        
        projections = [
            (0, 1, 'X (m)', 'Y (m)', 'Top View (X-Y)'),
            (0, 2, 'X (m)', 'Z - Altitude (m)', 'Side View (X-Z)'),
            (1, 2, 'Y (m)', 'Z - Altitude (m)', 'Side View (Y-Z)')
        ]
        
        for ax, (dim1, dim2, xlabel, ylabel, title) in zip(axes, projections):
            ax.plot(
                primary_wp[:, dim1], primary_wp[:, dim2],
                'b-o', linewidth=2, markersize=8, label='Primary'
            )
            
            colors = ['red', 'orange', 'purple', 'cyan']
            for i, mission in enumerate(report.other_missions):
                wp = np.array([w.to_array() for w in mission.waypoints])
                color = colors[i % len(colors)]
                ax.plot(
                    wp[:, dim1], wp[:, dim2],
                    # f'{color[0]}--o', linewidth=1.5, markersize=6,
                    # alpha=0.6, label=mission.id
                    linestyle='--', marker='o', color=color, linewidth=1.5, markersize=6,
                    alpha=0.6, label=mission.id
                )
            
            if report.conflicts:
                conflicts = np.array([
                    c.primary_location.to_array() for c in report.conflicts
                ])
                ax.scatter(
                    conflicts[:, dim1], conflicts[:, dim2],
                    c='red', s=200, marker='X', alpha=0.7,
                    edgecolors='darkred', linewidths=2
                )
            
            ax.set_xlabel(xlabel, fontsize=11)
            ax.set_ylabel(ylabel, fontsize=11)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9)
            ax.set_aspect('equal', adjustable='box')
        
        plt.suptitle(
            f'UAV Deconfliction - 2D Projections (Status: {report.status})',
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved 2D plots: {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def create_animation(
        self,
        report: DeconflictionReport,
        save_path: str,
        duration: float = 10.0,
        fps: int = 30
    ):
        """Create animated visualization of mission."""
        fig = plt.figure(figsize=self.figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        primary_interp = TrajectoryInterpolator(report.primary_mission)
        other_interps = [
            TrajectoryInterpolator(m) for m in report.other_missions
        ]
        
        max_time = max(
            report.primary_mission.time_window.end,
            max(m.time_window.end for m in report.other_missions)
        )
        num_frames = int(duration * fps)
        times = np.linspace(0, max_time, num_frames)
        
        def init():
            ax.clear()
            return []
        
        def animate(frame):
            ax.clear()
            current_time = times[frame]
            
            for mission in [report.primary_mission] + report.other_missions:
                wp = np.array([w.to_array() for w in mission.waypoints])
                ax.plot(
                    wp[:, 0], wp[:, 1], wp[:, 2],
                    '--', linewidth=1, alpha=0.3
                )
            
            primary_pos = primary_interp.interpolate_position(current_time)
            if primary_pos is not None:
                ax.scatter(*primary_pos, c='blue', s=200, marker='o',
                          edgecolors='darkblue', linewidths=2,
                          label='Primary')
            
            colors = ['red', 'orange', 'purple']
            for i, interp in enumerate(other_interps):
                pos = interp.interpolate_position(current_time)
                if pos is not None:
                    ax.scatter(*pos, c=colors[i % len(colors)], s=150,
                             marker='o', alpha=0.7,
                             label=interp.mission.id)
            
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            ax.set_title(f'Time: {current_time:.1f}s - Status: {report.status}')
            ax.legend()
            
            return []
        
        anim = FuncAnimation(
            fig, animate, init_func=init,
            frames=num_frames, interval=1000/fps, blit=True
        )
        
        writer = PillowWriter(fps=fps)
        anim.save(save_path, writer=writer)
        plt.close()
        
        print(f"Animation saved to {save_path}")

