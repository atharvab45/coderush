import os
import json
import random
import numpy as np
from datetime import datetime, timedelta

# Ensure the results directory exists
os.makedirs('data/mock', exist_ok=True)

def generate_road_network(rows=5, cols=5):
    """Generate a mock road network with a grid layout"""
    roads = []
    intersections = []
    road_id = 0
    
    # Create intersections
    for i in range(rows):
        for j in range(cols):
            intersection_id = i * cols + j
            intersections.append({
                'id': intersection_id,
                'x': j * 100,
                'y': i * 100,
                'roads': [],
                'traffic_lights': [
                    {
                        'id': f"tl_{intersection_id}_0",
                        'state': 'GREEN',
                        'direction': 'NORTH_SOUTH',
                        'duration': random.randint(20, 40)
                    },
                    {
                        'id': f"tl_{intersection_id}_1",
                        'state': 'RED',
                        'direction': 'EAST_WEST',
                        'duration': random.randint(20, 40)
                    }
                ]
            })
    
    # Create horizontal roads
    for i in range(rows):
        for j in range(cols - 1):
            road = {
                'id': road_id,
                'start_intersection': i * cols + j,
                'end_intersection': i * cols + j + 1,
                'length': 100,
                'type': 'URBAN',
                'congestion': random.uniform(0, 50),
                'vehicles': []
            }
            roads.append(road)
            
            # Add road to intersections
            intersections[i * cols + j]['roads'].append(road_id)
            intersections[i * cols + j + 1]['roads'].append(road_id)
            
            road_id += 1
    
    # Create vertical roads
    for i in range(rows - 1):
        for j in range(cols):
            road = {
                'id': road_id,
                'start_intersection': i * cols + j,
                'end_intersection': (i + 1) * cols + j,
                'length': 100,
                'type': 'URBAN',
                'congestion': random.uniform(0, 50),
                'vehicles': []
            }
            roads.append(road)
            
            # Add road to intersections
            intersections[i * cols + j]['roads'].append(road_id)
            intersections[(i + 1) * cols + j]['roads'].append(road_id)
            
            road_id += 1
    
    return roads, intersections

def generate_vehicles(count=100, roads=None):
    """Generate mock vehicles"""
    if not roads:
        return []
    
    vehicles = []
    vehicle_types = ['REGULAR', 'EMERGENCY', 'PUBLIC_TRANSPORT']
    vehicle_type_weights = [0.85, 0.05, 0.1]  # 85% regular, 5% emergency, 10% public transport
    
    for i in range(count):
        vehicle_type = random.choices(vehicle_types, weights=vehicle_type_weights)[0]
        current_road = random.choice(roads)
        
        # Create a route with 3-10 roads
        route_length = random.randint(3, 10)
        route = [current_road['id']]
        current_intersection = current_road['end_intersection']
        
        for _ in range(route_length - 1):
            # Find roads connected to the current intersection
            connected_roads = [r['id'] for r in roads if current_intersection in [r['start_intersection'], r['end_intersection']]]
            
            # Remove the road we just came from to avoid going back
            if route[-1] in connected_roads:
                connected_roads.remove(route[-1])
            
            # If no more roads to choose from, break
            if not connected_roads:
                break
            
            # Choose a random road
            next_road_id = random.choice(connected_roads)
            route.append(next_road_id)
            
            # Update current intersection
            next_road = next(r for r in roads if r['id'] == next_road_id)
            if next_road['start_intersection'] == current_intersection:
                current_intersection = next_road['end_intersection']
            else:
                current_intersection = next_road['start_intersection']
        
        # Create the vehicle
        vehicle = {
            'id': i,
            'type': vehicle_type,
            'position': random.uniform(0, current_road['length']),
            'speed': random.uniform(30, 60) if vehicle_type == 'REGULAR' else 
                     random.uniform(60, 90) if vehicle_type == 'EMERGENCY' else 
                     random.uniform(20, 40),  # public transport
            'route': route,
            'current_road_index': 0,
            'waiting_time': 0,
            'travel_time': 0,
            'completed': False
        }
        
        vehicles.append(vehicle)
        
        # Add vehicle to its current road
        current_road['vehicles'].append(i)
    
    return vehicles

def generate_baseline_stats(duration=300, interval=10):
    """Generate baseline simulation statistics"""
    stats = []
    start_time = datetime.now()
    
    for i in range(0, duration, interval):
        # Simulate increasing congestion and travel time over time
        progress_factor = i / duration
        congestion = 30 + progress_factor * 40  # 30% to 70%
        travel_time = 180 + progress_factor * 120  # 3 min to 5 min
        waiting_time = 60 + progress_factor * 60  # 1 min to 2 min
        speed = 40 - progress_factor * 15  # 40 km/h to 25 km/h
        
        # Add some randomness
        congestion += random.uniform(-5, 5)
        travel_time += random.uniform(-10, 10)
        waiting_time += random.uniform(-5, 5)
        speed += random.uniform(-2, 2)
        
        # Ensure values are within reasonable ranges
        congestion = max(0, min(100, congestion))
        travel_time = max(60, travel_time)
        waiting_time = max(0, waiting_time)
        speed = max(5, speed)
        
        timestamp = (start_time + timedelta(seconds=i)).strftime('%H:%M:%S')
        
        stat = {
            'timestamp': timestamp,
            'second': i,
            'optimization_enabled': False,
            'active_vehicles': 100 - int(progress_factor * 20),  # Decreasing active vehicles
            'completed_vehicles': int(progress_factor * 20),  # Increasing completed vehicles
            'avg_travel_time': travel_time,
            'avg_waiting_time': waiting_time,
            'avg_speed': speed,
            'avg_congestion': congestion
        }
        
        stats.append(stat)
    
    return stats

def generate_optimized_stats(baseline_stats):
    """Generate optimized simulation statistics based on baseline"""
    optimized_stats = []
    
    for i, stat in enumerate(baseline_stats):
        # Copy the baseline stat
        opt_stat = stat.copy()
        
        # Apply optimization improvements
        progress_factor = i / len(baseline_stats)
        improvement_factor = min(0.3, progress_factor * 0.4)  # Max 30% improvement, gradually increasing
        
        # Update stats with improvements
        opt_stat['optimization_enabled'] = True
        opt_stat['avg_travel_time'] *= (1 - improvement_factor)
        opt_stat['avg_waiting_time'] *= (1 - improvement_factor * 1.2)  # More improvement in waiting time
        opt_stat['avg_speed'] *= (1 + improvement_factor * 0.8)
        opt_stat['avg_congestion'] *= (1 - improvement_factor * 1.1)
        
        # Adjust completed vehicles
        if i > len(baseline_stats) // 3:  # After 1/3 of the simulation
            opt_stat['completed_vehicles'] = int(stat['completed_vehicles'] * (1 + improvement_factor * 0.5))
            opt_stat['active_vehicles'] = max(0, 100 - opt_stat['completed_vehicles'])
        
        optimized_stats.append(opt_stat)
    
    return optimized_stats

def generate_comparison_results(baseline_stats, optimized_stats):
    """Generate comparison results between baseline and optimized simulations"""
    # Get the last stats from each simulation
    final_baseline = baseline_stats[-1]
    final_optimized = optimized_stats[-1]
    
    # Calculate improvements
    travel_time_improvement = ((final_baseline['avg_travel_time'] - final_optimized['avg_travel_time']) / 
                             final_baseline['avg_travel_time'] * 100)
    waiting_time_improvement = ((final_baseline['avg_waiting_time'] - final_optimized['avg_waiting_time']) / 
                              final_baseline['avg_waiting_time'] * 100)
    speed_improvement = ((final_optimized['avg_speed'] - final_baseline['avg_speed']) / 
                       final_baseline['avg_speed'] * 100)
    congestion_improvement = ((final_baseline['avg_congestion'] - final_optimized['avg_congestion']) / 
                            final_baseline['avg_congestion'] * 100)
    
    results = {
        'baseline': {
            'avg_travel_time': final_baseline['avg_travel_time'],
            'avg_waiting_time': final_baseline['avg_waiting_time'],
            'avg_speed': final_baseline['avg_speed'],
            'avg_congestion': final_baseline['avg_congestion'],
            'active_vehicles': final_baseline['active_vehicles'],
            'completed_vehicles': final_baseline['completed_vehicles']
        },
        'optimized': {
            'avg_travel_time': final_optimized['avg_travel_time'],
            'avg_waiting_time': final_optimized['avg_waiting_time'],
            'avg_speed': final_optimized['avg_speed'],
            'avg_congestion': final_optimized['avg_congestion'],
            'active_vehicles': final_optimized['active_vehicles'],
            'completed_vehicles': final_optimized['completed_vehicles']
        },
        'improvements': {
            'travel_time': travel_time_improvement,
            'waiting_time': waiting_time_improvement,
            'speed': speed_improvement,
            'congestion': congestion_improvement
        },
        'parameters': {
            'vehicle_count': 100,
            'duration': 300,
            'emergency_ratio': 0.05,
            'public_transport_ratio': 0.1
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return results

def generate_all_mock_data():
    """Generate all mock data and save to files"""
    print("Generating mock data...")
    
    # Generate road network
    roads, intersections = generate_road_network(5, 5)
    print(f"Generated {len(roads)} roads and {len(intersections)} intersections")
    
    # Generate vehicles
    vehicles = generate_vehicles(100, roads)
    print(f"Generated {len(vehicles)} vehicles")
    
    # Generate simulation statistics
    baseline_stats = generate_baseline_stats(300, 10)
    optimized_stats = generate_optimized_stats(baseline_stats)
    print(f"Generated {len(baseline_stats)} baseline and optimized statistics")
    
    # Generate comparison results
    comparison = generate_comparison_results(baseline_stats, optimized_stats)
    print("Generated comparison results")
    
    # Save data to files
    with open('data/mock/roads.json', 'w') as f:
        json.dump(roads, f, indent=2)
    
    with open('data/mock/intersections.json', 'w') as f:
        json.dump(intersections, f, indent=2)
    
    with open('data/mock/vehicles.json', 'w') as f:
        json.dump(vehicles, f, indent=2)
    
    with open('data/mock/baseline_stats.json', 'w') as f:
        json.dump(baseline_stats, f, indent=2)
    
    with open('data/mock/optimized_stats.json', 'w') as f:
        json.dump(optimized_stats, f, indent=2)
    
    with open('data/mock/comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print("All mock data saved to data/mock/ directory")

if __name__ == "__main__":
    generate_all_mock_data()
