from flask import Flask, render_template, jsonify, request, session
import os
import sys
import json
from datetime import datetime

# Add parent directory to path to import simulation and server modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import simulation engine
from simulation.simulation_engine import SimulationEngine
from server.auth import require_api_key, require_manager, require_admin

app = Flask(__name__)
app.secret_key = 'traffic_simulation_secret_key'  # Change this in production

# Create simulation engine instance
simulation_engine = SimulationEngine()

# In-memory storage for simulation data
simulation_data = {
    'active_vehicles': 0,
    'completed_vehicles': 0,
    'avg_travel_time': 0,
    'avg_waiting_time': 0,
    'avg_speed': 0,
    'avg_congestion': 0,
    'travel_time_improvement': 0,
    'history': {
        'travel_times': [],
        'congestion_levels': [],
        'timestamps': []
    },
    'running': False,
    'optimization_enabled': False
}

# Mock user database
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'manager': {'password': 'manager123', 'role': 'manager'},
    'user': {'password': 'user123', 'role': 'user'}
}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in users and users[username]['password'] == password:
        session['username'] = username
        session['role'] = users[username]['role']
        return jsonify({
            'success': True,
            'username': username,
            'role': users[username]['role']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return jsonify({'success': True})

@app.route('/api/auth/status')
def auth_status():
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session['username'],
            'role': session['role']
        })
    else:
        return jsonify({'authenticated': False})

# Simulation control routes
@app.route('/api/simulation/start', methods=['POST'])
@require_api_key
def start_simulation():
    data = request.json
    vehicle_count = data.get('vehicle_count', 50)
    emergency_ratio = data.get('emergency_ratio', 5)
    public_transport_ratio = data.get('public_transport_ratio', 10)
    optimization_enabled = data.get('optimization_enabled', False)
    
    try:
        # Create a grid network if not already created
        if not simulation_engine.roads:
            simulation_engine.create_grid_network(5, 5)  # 5x5 grid
        
        # Generate random vehicles
        simulation_engine.generate_random_vehicles(
            vehicle_count, 
            emergency_ratio / 100, 
            public_transport_ratio / 100
        )
        
        # Set optimization flag
        simulation_data['optimization_enabled'] = optimization_enabled
        simulation_engine.set_optimization_enabled(optimization_enabled)
        
        # Start simulation
        simulation_data['running'] = True
        
        # Start a thread to run the simulation (in a real app)
        # Here we'll just update the simulation once
        simulation_engine.update()
        update_simulation_data()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/simulation/stop', methods=['POST'])
@require_api_key
def stop_simulation():
    try:
        simulation_data['running'] = False
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/simulation/reset', methods=['POST'])
@require_api_key
def reset_simulation():
    try:
        simulation_engine.reset()
        reset_simulation_data()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/simulation/toggle_optimization', methods=['POST'])
@require_api_key
def toggle_optimization():
    data = request.json
    enabled = data.get('enabled', False)
    
    try:
        simulation_data['optimization_enabled'] = enabled
        simulation_engine.set_optimization_enabled(enabled)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Traffic light control routes
@app.route('/api/traffic_light/set_state', methods=['POST'])
@require_manager
def set_traffic_light_state():
    data = request.json
    intersection_id = data.get('intersection_id')
    road_id = data.get('road_id')
    state = data.get('state')
    
    try:
        # Find the intersection
        intersection = next((i for i in simulation_engine.intersections if i.id == intersection_id), None)
        if not intersection:
            return jsonify({'success': False, 'message': 'Intersection not found'})
        
        # Find the traffic light
        traffic_light = next((tl for tl in intersection.traffic_lights if tl.road_id == road_id), None)
        if not traffic_light:
            return jsonify({'success': False, 'message': 'Traffic light not found'})
        
        # Set the state
        traffic_light.set_state(state)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/traffic_light/reset', methods=['POST'])
@require_manager
def reset_traffic_lights():
    try:
        for intersection in simulation_engine.intersections:
            for traffic_light in intersection.traffic_lights:
                traffic_light.reset()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Data retrieval routes
@app.route('/api/simulation/stats')
@require_api_key
def get_simulation_stats():
    # In a real app, this would get real-time data from the simulation
    # Here we'll just return the current simulation data
    if simulation_data['running']:
        simulation_engine.update()
        update_simulation_data()
    
    return jsonify({
        'activeVehicles': simulation_data['active_vehicles'],
        'completedVehicles': simulation_data['completed_vehicles'],
        'avgTravelTime': simulation_data['avg_travel_time'],
        'avgWaitingTime': simulation_data['avg_waiting_time'],
        'avgSpeed': simulation_data['avg_speed'],
        'avgCongestion': simulation_data['avg_congestion'],
        'travelTimeImprovement': simulation_data['travel_time_improvement']
    })

@app.route('/api/simulation/history')
@require_api_key
def get_simulation_history():
    return jsonify({
        'travelTimes': simulation_data['history']['travel_times'],
        'congestionLevels': simulation_data['history']['congestion_levels'],
        'timestamps': simulation_data['history']['timestamps']
    })

@app.route('/api/roads')
@require_api_key
def get_roads():
    roads_data = []
    for road in simulation_engine.roads:
        roads_data.append({
            'id': road.id,
            'start_intersection_id': road.start_intersection_id,
            'end_intersection_id': road.end_intersection_id,
            'length': road.length,
            'speed_limit': road.speed_limit,
            'congestion': road.congestion,
            'direction': 'horizontal' if road.start_intersection_id % 5 == road.end_intersection_id % 5 else 'vertical'
        })
    return jsonify(roads_data)

@app.route('/api/intersections')
@require_api_key
def get_intersections():
    intersections_data = []
    for i, intersection in enumerate(simulation_engine.intersections):
        # Calculate grid position (for visualization)
        x = i % 5 * 100  # Assuming 5x5 grid
        y = i // 5 * 100
        
        intersections_data.append({
            'id': intersection.id,
            'x': x,
            'y': y
        })
    return jsonify(intersections_data)

@app.route('/api/intersections/details')
@require_api_key
def get_intersection_details():
    intersections_data = []
    for intersection in simulation_engine.intersections:
        traffic_lights_data = []
        for tl in intersection.traffic_lights:
            traffic_lights_data.append({
                'road_id': tl.road_id,
                'state': tl.state.name
            })
        
        intersections_data.append({
            'id': intersection.id,
            'vehicle_count': len(intersection.waiting_vehicles),
            'congestion_level': intersection.calculate_congestion() * 100,
            'traffic_lights': traffic_lights_data
        })
    return jsonify(intersections_data)

@app.route('/api/vehicles')
@require_api_key
def get_vehicles():
    vehicles_data = []
    for vehicle in simulation_engine.vehicles:
        if vehicle.current_road:
            # Calculate position on the road
            start_intersection = next((i for i in simulation_engine.intersections if i.id == vehicle.current_road.start_intersection_id), None)
            end_intersection = next((i for i in simulation_engine.intersections if i.id == vehicle.current_road.end_intersection_id), None)
            
            if start_intersection and end_intersection:
                # Calculate grid position (for visualization)
                start_x = start_intersection.id % 5 * 100  # Assuming 5x5 grid
                start_y = start_intersection.id // 5 * 100
                end_x = end_intersection.id % 5 * 100
                end_y = end_intersection.id // 5 * 100
                
                # Interpolate position based on progress
                progress = vehicle.position / vehicle.current_road.length
                x = start_x + (end_x - start_x) * progress
                y = start_y + (end_y - start_y) * progress
                
                vehicles_data.append({
                    'id': vehicle.id,
                    'type': vehicle.type.name,
                    'x': x,
                    'y': y,
                    'speed': vehicle.speed,
                    'waiting_time': vehicle.waiting_time
                })
    return jsonify(vehicles_data)

@app.route('/api/simulation/compare', methods=['POST'])
@require_api_key
def compare_simulations():
    data = request.json
    duration = data.get('duration', 300)  # Default 5 minutes
    vehicle_count = data.get('vehicle_count', 100)
    
    try:
        # Run comparison simulation
        baseline_stats, optimized_stats = simulation_engine.run_comparison(
            duration=duration,
            vehicle_count=vehicle_count
        )
        
        return jsonify({
            'success': True,
            'baseline': {
                'avg_travel_time': baseline_stats['avg_travel_time'],
                'avg_waiting_time': baseline_stats['avg_waiting_time'],
                'avg_speed': baseline_stats['avg_speed']
            },
            'optimized': {
                'avg_travel_time': optimized_stats['avg_travel_time'],
                'avg_waiting_time': optimized_stats['avg_waiting_time'],
                'avg_speed': optimized_stats['avg_speed']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Helper functions
def update_simulation_data():
    stats = simulation_engine.get_statistics()
    
    simulation_data['active_vehicles'] = stats['active_vehicles']
    simulation_data['completed_vehicles'] = stats['completed_vehicles']
    simulation_data['avg_travel_time'] = stats['avg_travel_time']
    simulation_data['avg_waiting_time'] = stats['avg_waiting_time']
    simulation_data['avg_speed'] = stats['avg_speed']
    simulation_data['avg_congestion'] = stats['avg_congestion']
    
    # Calculate improvement if optimization is enabled
    if simulation_data['optimization_enabled'] and stats['baseline_travel_time'] > 0:
        improvement = (stats['baseline_travel_time'] - stats['avg_travel_time']) / stats['baseline_travel_time'] * 100
        simulation_data['travel_time_improvement'] = improvement
    
    # Update history
    timestamp = datetime.now().strftime('%H:%M:%S')
    simulation_data['history']['travel_times'].append(stats['avg_travel_time'])
    simulation_data['history']['congestion_levels'].append(stats['avg_congestion'])
    simulation_data['history']['timestamps'].append(timestamp)
    
    # Keep history at a reasonable size
    max_history = 100
    if len(simulation_data['history']['timestamps']) > max_history:
        simulation_data['history']['travel_times'] = simulation_data['history']['travel_times'][-max_history:]
        simulation_data['history']['congestion_levels'] = simulation_data['history']['congestion_levels'][-max_history:]
        simulation_data['history']['timestamps'] = simulation_data['history']['timestamps'][-max_history:]

def reset_simulation_data():
    simulation_data['active_vehicles'] = 0
    simulation_data['completed_vehicles'] = 0
    simulation_data['avg_travel_time'] = 0
    simulation_data['avg_waiting_time'] = 0
    simulation_data['avg_speed'] = 0
    simulation_data['avg_congestion'] = 0
    simulation_data['travel_time_improvement'] = 0
    simulation_data['history'] = {
        'travel_times': [],
        'congestion_levels': [],
        'timestamps': []
    }
    simulation_data['running'] = False

if __name__ == '__main__':
    # Create a grid network for testing
    simulation_engine.create_grid_network(5, 5)  # 5x5 grid
    app.run(debug=True, port=5000)
