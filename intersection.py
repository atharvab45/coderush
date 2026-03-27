import numpy as np
from enum import Enum
import time

class LightState(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3

class TrafficLight:
    """Represents a traffic light at an intersection."""
    
    def __init__(self, light_id, road_id, default_timings=(30, 5, 30)):
        """
        Initialize a traffic light.
        
        Args:
            light_id: Unique identifier for the traffic light
            road_id: ID of the road this light controls
            default_timings: Tuple of (green_time, yellow_time, red_time) in seconds
        """
        self.id = light_id
        self.road_id = road_id
        self.state = LightState.RED
        self.default_timings = default_timings
        self.green_time = default_timings[0]
        self.yellow_time = default_timings[1]
        self.red_time = default_timings[2]
        self.time_in_state = 0
        self.manual_override = False
        self.last_state_change = time.time()
    
    def update(self, dt):
        """
        Update the traffic light state based on timing.
        
        Args:
            dt: Time step in seconds
        """
        if self.manual_override:
            return
        
        self.time_in_state += dt
        
        if self.state == LightState.GREEN and self.time_in_state >= self.green_time:
            self.state = LightState.YELLOW
            self.time_in_state = 0
            self.last_state_change = time.time()
        
        elif self.state == LightState.YELLOW and self.time_in_state >= self.yellow_time:
            self.state = LightState.RED
            self.time_in_state = 0
            self.last_state_change = time.time()
        
        elif self.state == LightState.RED and self.time_in_state >= self.red_time:
            self.state = LightState.GREEN
            self.time_in_state = 0
            self.last_state_change = time.time()
    
    def set_state(self, state):
        """
        Manually set the traffic light state.
        
        Args:
            state: New state (LightState enum)
        """
        self.state = state
        self.time_in_state = 0
        self.manual_override = True
        self.last_state_change = time.time()
    
    def reset_to_automatic(self):
        """
        Reset the traffic light to automatic timing control.
        """
        self.manual_override = False
    
    def adjust_timings(self, green_time=None, yellow_time=None, red_time=None):
        """
        Adjust the timing settings for the traffic light.
        
        Args:
            green_time: New green light duration in seconds
            yellow_time: New yellow light duration in seconds
            red_time: New red light duration in seconds
        """
        if green_time is not None:
            self.green_time = green_time
        if yellow_time is not None:
            self.yellow_time = yellow_time
        if red_time is not None:
            self.red_time = red_time
    
    def reset_timings(self):
        """
        Reset timings to default values.
        """
        self.green_time = self.default_timings[0]
        self.yellow_time = self.default_timings[1]
        self.red_time = self.default_timings[2]
    
    def is_green(self):
        """
        Check if the light is green.
        
        Returns:
            bool: True if green, False otherwise
        """
        return self.state == LightState.GREEN
    
    def get_stats(self):
        """
        Get statistics about the traffic light.
        
        Returns:
            dict: Traffic light statistics
        """
        return {
            'id': self.id,
            'road_id': self.road_id,
            'state': self.state.name,
            'time_in_state': self.time_in_state,
            'manual_override': self.manual_override,
            'green_time': self.green_time,
            'yellow_time': self.yellow_time,
            'red_time': self.red_time
        }

class Intersection:
    """Represents an intersection in the traffic simulation."""
    
    def __init__(self, intersection_id, position=(0, 0)):
        """
        Initialize an intersection.
        
        Args:
            intersection_id: Unique identifier for the intersection
            position: (x, y) coordinates of the intersection
        """
        self.id = intersection_id
        self.position = position
        self.incoming_roads = []  # List of road IDs entering this intersection
        self.outgoing_roads = []  # List of road IDs leaving this intersection
        self.traffic_lights = {}  # Dict mapping road_id to TrafficLight
        self.vehicle_count = 0    # Number of vehicles currently at the intersection
        self.waiting_vehicles = {}  # Dict mapping road_id to list of waiting vehicles
        self.congestion_level = 0  # 0 to 1, where 1 is completely congested
    
    def add_incoming_road(self, road_id):
        """
        Add an incoming road to the intersection.
        
        Args:
            road_id: ID of the incoming road
        """
        if road_id not in self.incoming_roads:
            self.incoming_roads.append(road_id)
            self.waiting_vehicles[road_id] = []
    
    def add_outgoing_road(self, road_id):
        """
        Add an outgoing road to the intersection.
        
        Args:
            road_id: ID of the outgoing road
        """
        if road_id not in self.outgoing_roads:
            self.outgoing_roads.append(road_id)
    
    def add_traffic_light(self, road_id, default_timings=(30, 5, 30)):
        """
        Add a traffic light to control an incoming road.
        
        Args:
            road_id: ID of the road to control
            default_timings: Tuple of (green_time, yellow_time, red_time) in seconds
        """
        if road_id in self.incoming_roads and road_id not in self.traffic_lights:
            light_id = f"light_{self.id}_{road_id}"
            self.traffic_lights[road_id] = TrafficLight(light_id, road_id, default_timings)
    
    def update(self, dt):
        """
        Update the intersection state.
        
        Args:
            dt: Time step in seconds
        """
        # Update all traffic lights
        for light in self.traffic_lights.values():
            light.update(dt)
        
        # Update congestion level
        total_capacity = len(self.incoming_roads) * 5  # Simple model: 5 vehicles per incoming road
        self.congestion_level = min(1.0, self.vehicle_count / total_capacity) if total_capacity > 0 else 0
    
    def add_waiting_vehicle(self, road_id, vehicle):
        """
        Add a vehicle waiting at this intersection.
        
        Args:
            road_id: ID of the road the vehicle is on
            vehicle: Vehicle object
        """
        if road_id in self.waiting_vehicles:
            self.waiting_vehicles[road_id].append(vehicle)
            self.vehicle_count += 1
            self._update_congestion()
    
    def remove_waiting_vehicle(self, road_id, vehicle):
        """
        Remove a vehicle that was waiting at this intersection.
        
        Args:
            road_id: ID of the road the vehicle was on
            vehicle: Vehicle object
        """
        if road_id in self.waiting_vehicles and vehicle in self.waiting_vehicles[road_id]:
            self.waiting_vehicles[road_id].remove(vehicle)
            self.vehicle_count -= 1
            self._update_congestion()
    
    def _update_congestion(self):
        """
        Update the congestion level based on the number of vehicles.
        """
        total_capacity = len(self.incoming_roads) * 5  # Simple model: 5 vehicles per incoming road
        self.congestion_level = min(1.0, self.vehicle_count / total_capacity) if total_capacity > 0 else 0
    
    def optimize_traffic_lights(self, priority_road_id=None):
        """
        Optimize traffic light timings based on current traffic conditions.
        
        Args:
            priority_road_id: ID of a road to prioritize (e.g., for emergency vehicles)
        """
        if not self.traffic_lights:
            return
        
        # Count waiting vehicles for each road
        waiting_counts = {road_id: len(vehicles) for road_id, vehicles in self.waiting_vehicles.items()}
        
        # Check for emergency vehicles
        emergency_roads = []
        for road_id, vehicles in self.waiting_vehicles.items():
            if any(v.type.name == 'EMERGENCY' for v in vehicles):
                emergency_roads.append(road_id)
        
        # Prioritize roads with emergency vehicles or the specified priority road
        if emergency_roads:
            for road_id in emergency_roads:
                if road_id in self.traffic_lights:
                    self.traffic_lights[road_id].set_state(LightState.GREEN)
                    # Set other lights to red
                    for other_road, light in self.traffic_lights.items():
                        if other_road != road_id:
                            light.set_state(LightState.RED)
            return
        
        if priority_road_id and priority_road_id in self.traffic_lights:
            self.traffic_lights[priority_road_id].set_state(LightState.GREEN)
            # Set other lights to red
            for road_id, light in self.traffic_lights.items():
                if road_id != priority_road_id:
                    light.set_state(LightState.RED)
            return
        
        # Adjust timings based on waiting vehicles
        if waiting_counts:
            total_waiting = sum(waiting_counts.values())
            if total_waiting > 0:
                for road_id, count in waiting_counts.items():
                    if road_id in self.traffic_lights:
                        # Adjust green time proportionally to waiting vehicles
                        proportion = count / total_waiting
                        base_cycle = 60  # 60-second base cycle
                        green_time = max(10, int(base_cycle * proportion))
                        self.traffic_lights[road_id].adjust_timings(green_time=green_time)
    
    def reset_traffic_lights(self):
        """
        Reset all traffic lights to their default timings and automatic control.
        """
        for light in self.traffic_lights.values():
            light.reset_timings()
            light.reset_to_automatic()
    
    def get_stats(self):
        """
        Get statistics about the intersection.
        
        Returns:
            dict: Intersection statistics
        """
        return {
            'id': self.id,
            'position': self.position,
            'incoming_roads': self.incoming_roads,
            'outgoing_roads': self.outgoing_roads,
            'vehicle_count': self.vehicle_count,
            'congestion_level': self.congestion_level,
            'traffic_lights': {road_id: light.get_stats() for road_id, light in self.traffic_lights.items()}
        }
        
    def get_connected_roads(self):
        """
        Get all roads connected to this intersection.
        
        Returns:
            list: Road objects connected to this intersection
        """
        # This should return actual Road objects, but we need to get them from the simulation engine
        # For now, we'll return the road IDs which is what we have access to
        return self.incoming_roads + self.outgoing_roads
