"""
Campus data structure containing buildings, intersections, and paths
This represents a configurable college campus layout loaded from JSON
"""

import networkx as nx
import math
import json
import os
from typing import Tuple, Dict, List

# Global variables to hold campus data
BUILDINGS = {}
INTERSECTIONS = {}
CAMPUS_CONFIG = {}
MAP_CENTER = (40.7831, -73.9712)
MAP_BOUNDS_KM = 2.0

def load_campus_config():
    """Load campus configuration from JSON file"""
    global BUILDINGS, INTERSECTIONS, CAMPUS_CONFIG, MAP_CENTER, MAP_BOUNDS_KM
    
    config_file = 'campus_config.json'
    
    try:
        with open(config_file, 'r') as f:
            CAMPUS_CONFIG = json.load(f)
        
        # Load buildings
        BUILDINGS = {}
        for building_id, building_data in CAMPUS_CONFIG['buildings'].items():
            BUILDINGS[building_id] = {
                'name': building_data['name'],
                'coordinates': tuple(building_data['coordinates']),
                'description': building_data['description'],
                'type': building_data.get('type', 'general')
            }
        
        # Load intersections
        INTERSECTIONS = {}
        for intersection_id, coordinates in CAMPUS_CONFIG['intersections'].items():
            INTERSECTIONS[intersection_id] = tuple(coordinates)
        
        # Load map settings
        MAP_CENTER = tuple(CAMPUS_CONFIG['map_settings']['center_coordinates'])
        MAP_BOUNDS_KM = CAMPUS_CONFIG['map_settings']['map_bounds_km']
        
        print(f"Loaded campus config: {len(BUILDINGS)} buildings, {len(INTERSECTIONS)} intersections")
        
    except FileNotFoundError:
        print(f"Warning: {config_file} not found. Using default configuration.")
        _load_default_config()
    except Exception as e:
        print(f"Error loading config: {e}. Using default configuration.")
        _load_default_config()

def _load_default_config():
    """Load default campus configuration if JSON file is not available"""
    global BUILDINGS, INTERSECTIONS, CAMPUS_CONFIG, MAP_CENTER, MAP_BOUNDS_KM
    
    # Default buildings (same as before)
    BUILDINGS = {
        'Main_Library': {
            'name': 'Main Library',
            'coordinates': (40.7831, -73.9712),
            'description': 'Central library with study spaces and resources',
            'type': 'academic'
        },
        'Engineering_Building': {
            'name': 'Engineering Building',
            'coordinates': (40.7851, -73.9732),
            'description': 'Home to all engineering departments',
            'type': 'academic'
        },
        'Student_Center': {
            'name': 'Student Center',
            'coordinates': (40.7811, -73.9692),
            'description': 'Dining, events, and student activities',
            'type': 'student_services'
        },
        'Science_Building': {
            'name': 'Science Building',
            'coordinates': (40.7871, -73.9752),
            'description': 'Physics, Chemistry, and Biology labs',
            'type': 'academic'
        },
        'Business_School': {
            'name': 'Business School',
            'coordinates': (40.7791, -73.9672),
            'description': 'Business administration and economics',
            'type': 'academic'
        },
        'Arts_Building': {
            'name': 'Arts Building',
            'coordinates': (40.7801, -73.9722),
            'description': 'Fine arts, theater, and music departments',
            'type': 'academic'
        },
        'Dormitory_A': {
            'name': 'Dormitory A',
            'coordinates': (40.7821, -73.9682),
            'description': 'First-year student housing',
            'type': 'residential'
        },
        'Dormitory_B': {
            'name': 'Dormitory B',
            'coordinates': (40.7841, -73.9702),
            'description': 'Upper-class student housing',
            'type': 'residential'
        },
        'Cafeteria': {
            'name': 'Main Cafeteria',
            'coordinates': (40.7821, -73.9712),
            'description': 'Main dining facility',
            'type': 'dining'
        },
        'Gym': {
            'name': 'Recreation Center',
            'coordinates': (40.7861, -73.9682),
            'description': 'Fitness center and sports facilities',
            'type': 'recreation'
        }
    }
    
    # Default intersections
    INTERSECTIONS = {
        'intersection_1': (40.7831, -73.9692),
        'intersection_2': (40.7841, -73.9712),
        'intersection_3': (40.7821, -73.9732),
        'intersection_4': (40.7851, -73.9712),
        'intersection_5': (40.7811, -73.9712),
        'intersection_6': (40.7861, -73.9702)
    }

def save_campus_config():
    """Save current campus configuration to JSON file"""
    global BUILDINGS, INTERSECTIONS, CAMPUS_CONFIG, MAP_CENTER, MAP_BOUNDS_KM
    
    # Update config with current data
    config_data = {
        'map_settings': {
            'center_coordinates': list(MAP_CENTER),
            'map_bounds_km': MAP_BOUNDS_KM,
            'zoom_level': CAMPUS_CONFIG.get('map_settings', {}).get('zoom_level', 16)
        },
        'admin_settings': CAMPUS_CONFIG.get('admin_settings', {
            'admin_password': 'campus_admin_2024',
            'session_timeout_hours': 24
        }),
        'buildings': {},
        'intersections': {},
        'campus_paths': CAMPUS_CONFIG.get('campus_paths', [])
    }
    
    # Convert buildings to JSON format
    for building_id, building_data in BUILDINGS.items():
        config_data['buildings'][building_id] = {
            'name': building_data['name'],
            'coordinates': list(building_data['coordinates']),
            'description': building_data['description'],
            'type': building_data.get('type', 'general')
        }
    
    # Convert intersections to JSON format
    for intersection_id, coordinates in INTERSECTIONS.items():
        config_data['intersections'][intersection_id] = list(coordinates)
    
    try:
        with open('campus_config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_map_bounds() -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Calculate map bounds based on center coordinates and bounds distance"""
    center_lat, center_lon = MAP_CENTER
    
    # Convert km to degrees (approximate)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    lat_offset = MAP_BOUNDS_KM / 2 / 111.0
    lon_offset = MAP_BOUNDS_KM / 2 / (111.0 * math.cos(math.radians(center_lat)))
    
    # Calculate bounds
    north = center_lat + lat_offset
    south = center_lat - lat_offset
    east = center_lon + lon_offset
    west = center_lon - lon_offset
    
    return ((south, west), (north, east))

def is_within_bounds(lat: float, lon: float) -> bool:
    """Check if coordinates are within the campus bounds"""
    (south, west), (north, east) = get_map_bounds()
    return south <= lat <= north and west <= lon <= east

def calculate_distance(coord1, coord2):
    """
    Calculate the distance between two coordinates using Haversine formula
    Returns distance in meters
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in meters
    r = 6371000
    distance = r * c
    
    return distance

def create_campus_graph():
    """
    Create a NetworkX graph representing the campus with buildings and paths
    """
    G = nx.Graph()
    
    # Add all nodes (buildings and intersections)
    for building_id, building_data in BUILDINGS.items():
        G.add_node(building_id, 
                   name=building_data['name'],
                   coordinates=building_data['coordinates'],
                   type='building',
                   description=building_data['description'],
                   building_type=building_data.get('type', 'general'))
    
    for intersection_id, coordinates in INTERSECTIONS.items():
        G.add_node(intersection_id,
                   name=intersection_id,
                   coordinates=coordinates,
                   type='intersection')
    
    # Get campus paths from configuration
    campus_paths = CAMPUS_CONFIG.get('campus_paths', [])
    
    # Add edges with calculated or predefined weights (distances in meters)
    for path in campus_paths:
        if len(path) == 3:
            # Predefined distance
            node1, node2, distance = path
            if node1 in G.nodes and node2 in G.nodes:
                G.add_edge(node1, node2, weight=distance, distance=distance)
        else:
            # Calculate distance based on coordinates
            node1, node2 = path
            if node1 in G.nodes and node2 in G.nodes:
                coord1 = G.nodes[node1]['coordinates']
                coord2 = G.nodes[node2]['coordinates']
                distance = calculate_distance(coord1, coord2)
                G.add_edge(node1, node2, weight=distance, distance=distance)
    
    return G

def get_building_list():
    """
    Return a list of buildings for the frontend
    """
    return [{
        'id': building_id,
        'name': building_data['name'],
        'coordinates': building_data['coordinates'],
        'description': building_data['description']
    } for building_id, building_data in BUILDINGS.items()]

# Initialize campus data when module is imported
load_campus_config()
campus_graph = create_campus_graph()
