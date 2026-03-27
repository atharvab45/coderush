import os
import sys
import json
import random
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to import simulation module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.simulation_engine import SimulationEngine
from simulation.vehicle import VehicleType

class DataGenerator:
    def __init__(self):
        self.simulation_engine = SimulationEngine()
        self.vehicle_count = 0
        self.emergency_ratio = 0.05  # 5% emergency vehicles
        self.public_transport_ratio = 0.1  # 10% public transport
        
    def generate_grid_network(self, rows=5, cols=5):
        """Generate a grid network of roads and intersections"""
        self.simulation_engine.create_grid_network(rows, cols)
        print(f"Generated grid network with {rows}x{cols} intersections and {len(self.simulation_engine.roads)} roads")
    
    def generate_random_vehicles(self, count=100):
        """Generate random vehicles with different types"""
        self.vehicle_count = count
        self.simulation_engine.generate_random_vehicles(
            count, 
            self.emergency_ratio, 
            self.public_transport_ratio
        )
        print(f"Generated {count} random vehicles")
        
        # Print vehicle type distribution
        vehicle_types = {}
        for vehicle in self.simulation_engine.vehicles:
            if vehicle.type.name in vehicle_types:
                vehicle_types[vehicle.type.name] += 1
            else:
                vehicle_types[vehicle.type.name] = 1
        
        for vtype, count in vehicle_types.items():
            print(f"  {vtype}: {count} vehicles")
    
    def run_baseline_simulation(self, duration=300):
        """Run a baseline simulation without optimization"""
        print(f"Running baseline simulation for {duration} seconds...")
        self.simulation_engine.set_optimization_enabled(False)
        
        # Run simulation for specified duration
        steps = duration // 1  # 1 second per step
        stats_history = []
        
        for _ in range(steps):
            self.simulation_engine.update()
            stats = self.simulation_engine.get_statistics()
            stats_history.append(stats)
        
        # Calculate average statistics
        avg_stats = self._calculate_average_stats(stats_history)
        print("Baseline simulation completed")
        print(f"  Average travel time: {avg_stats['avg_travel_time']:.2f} seconds")
        print(f"  Average waiting time: {avg_stats['avg_waiting_time']:.2f} seconds")
        print(f"  Average speed: {avg_stats['avg_speed']:.2f} km/h")
        print(f"  Average congestion: {avg_stats['avg_congestion']:.2f}%")
        
        return avg_stats
    
    def run_optimized_simulation(self, duration=300):
        """Run an optimized simulation with traffic light optimization"""
        print(f"Running optimized simulation for {duration} seconds...")
        self.simulation_engine.reset()
        self.generate_random_vehicles(self.vehicle_count)
        self.simulation_engine.set_optimization_enabled(True)
        
        # Run simulation for specified duration
        steps = duration // 1  # 1 second per step
        stats_history = []
        
        for _ in range(steps):
            self.simulation_engine.update()
            stats = self.simulation_engine.get_statistics()
            stats_history.append(stats)
        
        # Calculate average statistics
        avg_stats = self._calculate_average_stats(stats_history)
        print("Optimized simulation completed")
        print(f"  Average travel time: {avg_stats['avg_travel_time']:.2f} seconds")
        print(f"  Average waiting time: {avg_stats['avg_waiting_time']:.2f} seconds")
        print(f"  Average speed: {avg_stats['avg_speed']:.2f} km/h")
        print(f"  Average congestion: {avg_stats['avg_congestion']:.2f}%")
        
        return avg_stats
    
    def compare_simulations(self, duration=300, vehicle_count=100):
        """Compare baseline and optimized simulations"""
        print(f"Comparing baseline and optimized simulations with {vehicle_count} vehicles for {duration} seconds each")
        
        # Set vehicle count
        self.vehicle_count = vehicle_count
        
        # Run baseline simulation
        self.simulation_engine.reset()
        self.generate_random_vehicles(vehicle_count)
        baseline_stats = self.run_baseline_simulation(duration)
        
        # Run optimized simulation
        self.simulation_engine.reset()
        self.generate_random_vehicles(vehicle_count)
        optimized_stats = self.run_optimized_simulation(duration)
        
        # Calculate improvements
        travel_time_improvement = ((baseline_stats['avg_travel_time'] - optimized_stats['avg_travel_time']) / 
                                 baseline_stats['avg_travel_time'] * 100)
        waiting_time_improvement = ((baseline_stats['avg_waiting_time'] - optimized_stats['avg_waiting_time']) / 
                                  baseline_stats['avg_waiting_time'] * 100)
        speed_improvement = ((optimized_stats['avg_speed'] - baseline_stats['avg_speed']) / 
                           baseline_stats['avg_speed'] * 100)
        congestion_improvement = ((baseline_stats['avg_congestion'] - optimized_stats['avg_congestion']) / 
                                baseline_stats['avg_congestion'] * 100)
        
        print("\nSimulation Comparison Results:")
        print(f"  Travel time improvement: {travel_time_improvement:.2f}%")
        print(f"  Waiting time improvement: {waiting_time_improvement:.2f}%")
        print(f"  Speed improvement: {speed_improvement:.2f}%")
        print(f"  Congestion improvement: {congestion_improvement:.2f}%")
        
        # Save comparison results to file
        results = {
            'baseline': baseline_stats,
            'optimized': optimized_stats,
            'improvements': {
                'travel_time': travel_time_improvement,
                'waiting_time': waiting_time_improvement,
                'speed': speed_improvement,
                'congestion': congestion_improvement
            },
            'parameters': {
                'vehicle_count': vehicle_count,
                'duration': duration,
                'emergency_ratio': self.emergency_ratio,
                'public_transport_ratio': self.public_transport_ratio
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self._save_results(results)
        
        return baseline_stats, optimized_stats
    
    def generate_time_series_data(self, duration=3600, interval=60, optimization_switch_time=1800):
        """Generate time series data with optimization switched on halfway through"""
        print(f"Generating time series data for {duration} seconds with optimization switch at {optimization_switch_time} seconds")
        
        self.simulation_engine.reset()
        self.generate_random_vehicles(self.vehicle_count)
        self.simulation_engine.set_optimization_enabled(False)
        
        time_series = []
        current_time = datetime.now()
        
        # Run simulation and collect data at intervals
        for second in range(duration):
            # Switch optimization on at the specified time
            if second == optimization_switch_time:
                print("Switching optimization ON")
                self.simulation_engine.set_optimization_enabled(True)
            
            # Update simulation
            self.simulation_engine.update()
            
            # Collect data at specified intervals
            if second % interval == 0:
                stats = self.simulation_engine.get_statistics()
                timestamp = (current_time + timedelta(seconds=second)).strftime('%H:%M:%S')
                
                data_point = {
                    'timestamp': timestamp,
                    'second': second,
                    'optimization_enabled': second >= optimization_switch_time,
                    'active_vehicles': stats['active_vehicles'],
                    'completed_vehicles': stats['completed_vehicles'],
                    'avg_travel_time': stats['avg_travel_time'],
                    'avg_waiting_time': stats['avg_waiting_time'],
                    'avg_speed': stats['avg_speed'],
                    'avg_congestion': stats['avg_congestion']
                }
                
                time_series.append(data_point)
                
                # Print progress
                if second % 300 == 0:
                    print(f"  Processed {second} seconds ({second/duration*100:.1f}%)")
        
        # Save time series data
        self._save_time_series(time_series)
        
        print("Time series data generation completed")
        return time_series
    
    def _calculate_average_stats(self, stats_history):
        """Calculate average statistics from a history of stats"""
        if not stats_history:
            return {
                'avg_travel_time': 0,
                'avg_waiting_time': 0,
                'avg_speed': 0,
                'avg_congestion': 0,
                'active_vehicles': 0,
                'completed_vehicles': 0
            }
        
        # Filter out entries with zero values (beginning of simulation)
        valid_stats = [s for s in stats_history if s['avg_travel_time'] > 0]
        
        if not valid_stats:
            valid_stats = stats_history
        
        # Calculate averages
        avg_stats = {
            'avg_travel_time': np.mean([s['avg_travel_time'] for s in valid_stats]),
            'avg_waiting_time': np.mean([s['avg_waiting_time'] for s in valid_stats]),
            'avg_speed': np.mean([s['avg_speed'] for s in valid_stats]),
            'avg_congestion': np.mean([s['avg_congestion'] for s in valid_stats]),
            'active_vehicles': stats_history[-1]['active_vehicles'],
            'completed_vehicles': stats_history[-1]['completed_vehicles']
        }
        
        return avg_stats
    
    def _save_results(self, results):
        """Save comparison results to a JSON file"""
        os.makedirs('results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results/comparison_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def _save_time_series(self, time_series):
        """Save time series data to a JSON file"""
        os.makedirs('results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results/time_series_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(time_series, f, indent=2)
        
        print(f"Time series data saved to {filename}")

# Example usage
if __name__ == "__main__":
    generator = DataGenerator()
    
    # Generate network
    generator.generate_grid_network(5, 5)
    
    # Run comparison with different vehicle counts
    for vehicle_count in [50, 100, 200]:
        generator.compare_simulations(duration=300, vehicle_count=vehicle_count)
    
    # Generate time series data
    generator.generate_time_series_data(duration=3600, interval=60, optimization_switch_time=1800)
