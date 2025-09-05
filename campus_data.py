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
BUILDING_INTERIORS = {}  # Store building interior configurations
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

def load_building_interior_config(building_id: str) -> Dict:
    """Load building interior configuration from JSON file"""
    config_file = f'buildings/{building_id}_interior.json'
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            return _create_default_building_interior(building_id)
    except Exception as e:
        print(f"Error loading building interior config for {building_id}: {e}")
        return _create_default_building_interior(building_id)

def _create_default_building_interior(building_id: str) -> Dict:
    """Create default building interior structure"""
    return {
        'building_id': building_id,
        'building_name': BUILDINGS.get(building_id, {}).get('name', building_id),
        'floors': {
            'ground': {
                'name': 'Ground Floor',
                'level': 0,
                'rooms': {},
                'connections': [],
                'entrances': ['main_entrance'],
                'floor_plan': {
                    'width': 100,
                    'height': 100,
                    'scale_meters_per_unit': 1.0
                }
            }
        },
        'vertical_connections': {
            'stairs': [],
            'elevators': []
        },
        'room_types': {
            'classroom': {'icon': 'chalkboard-teacher', 'color': 'blue'},
            'office': {'icon': 'briefcase', 'color': 'green'},
            'lab': {'icon': 'flask', 'color': 'purple'},
            'entrance': {'icon': 'door-open', 'color': 'orange'},
            'stairs': {'icon': 'stairs', 'color': 'gray'},
            'elevator': {'icon': 'elevator', 'color': 'gray'},
            'restroom': {'icon': 'restroom', 'color': 'lightblue'},
            'common': {'icon': 'users', 'color': 'yellow'}
        }
    }

def save_building_interior_config(building_id: str, config_data: Dict) -> bool:
    """Save building interior configuration to JSON file"""
    try:
        # Create buildings directory if it doesn't exist
        os.makedirs('buildings', exist_ok=True)
        
        config_file = f'buildings/{building_id}_interior.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Update in-memory storage
        BUILDING_INTERIORS[building_id] = config_data
        return True
    except Exception as e:
        print(f"Error saving building interior config for {building_id}: {e}")
        return False

def load_all_building_interiors():
    """Load all building interior configurations"""
    global BUILDING_INTERIORS
    BUILDING_INTERIORS = {}
    
    # Create buildings directory if it doesn't exist
    os.makedirs('buildings', exist_ok=True)
    
    for building_id in BUILDINGS.keys():
        BUILDING_INTERIORS[building_id] = load_building_interior_config(building_id)

def create_building_interior_graph(building_id: str) -> nx.Graph:
    """Create a NetworkX graph for building interior navigation"""
    if building_id not in BUILDING_INTERIORS:
        return nx.Graph()
    
    interior_config = BUILDING_INTERIORS[building_id]
    G = nx.Graph()
    
    # Add rooms as nodes
    for floor_id, floor_data in interior_config['floors'].items():
        floor_level = floor_data['level']
        
        for room_id, room_data in floor_data['rooms'].items():
            node_id = f"{building_id}_{floor_id}_{room_id}"
            G.add_node(node_id,
                      name=room_data.get('name', room_id),
                      room_type=room_data.get('type', 'common'),
                      floor=floor_id,
                      floor_level=floor_level,
                      coordinates=room_data.get('coordinates', [0, 0]),
                      building_id=building_id,
                      node_type='room')
        
        # Add connections within floor
        for connection in floor_data.get('connections', []):
            if len(connection) >= 2:
                room1_id = f"{building_id}_{floor_id}_{connection[0]}"
                room2_id = f"{building_id}_{floor_id}_{connection[1]}"
                distance = connection[2] if len(connection) > 2 else 10  # Default 10 meters
                
                if G.has_node(room1_id) and G.has_node(room2_id):
                    G.add_edge(room1_id, room2_id, weight=distance, connection_type='hallway')
        
        # Add vertical connection nodes to the floor
        for stair_data in interior_config['vertical_connections']['stairs']:
            if floor_id in stair_data.get('floors', []):
                stair_node_id = f"{building_id}_{floor_id}_stairs_{stair_data.get('id', '1')}"
                G.add_node(stair_node_id,
                          name=f"{stair_data.get('name', 'Stairs')} (Floor {floor_id})",
                          room_type='stairs',
                          floor=floor_id,
                          floor_level=floor_level,
                          coordinates=stair_data.get('location', [0, 0]),
                          building_id=building_id,
                          node_type='vertical_connection')
        
        for elevator_data in interior_config['vertical_connections']['elevators']:
            if floor_id in elevator_data.get('floors', []):
                elevator_node_id = f"{building_id}_{floor_id}_elevator_{elevator_data.get('id', '1')}"
                G.add_node(elevator_node_id,
                          name=f"{elevator_data.get('name', 'Elevator')} (Floor {floor_id})",
                          room_type='elevator',
                          floor=floor_id,
                          floor_level=floor_level,
                          coordinates=elevator_data.get('location', [0, 0]),
                          building_id=building_id,
                          node_type='vertical_connection')
    
    # Add vertical connections (stairs, elevators)
    for stair_data in interior_config['vertical_connections']['stairs']:
        _add_vertical_connection(G, building_id, stair_data, 'stairs')
    
    for elevator_data in interior_config['vertical_connections']['elevators']:
        _add_vertical_connection(G, building_id, elevator_data, 'elevator')
    
    return G

def _add_vertical_connection(graph: nx.Graph, building_id: str, connection_data: Dict, connection_type: str):
    """Add stairs or elevator connections between floors"""
    floors = connection_data.get('floors', [])
    location = connection_data.get('location', [0, 0])
    
    # Create vertical connection nodes for each floor
    vertical_nodes = []
    for floor_id in floors:
        node_id = f"{building_id}_{floor_id}_{connection_type}_{connection_data.get('id', '1')}"
        
        if not graph.has_node(node_id):
            graph.add_node(node_id,
                          name=f"{connection_type.title()} {connection_data.get('id', '1')}",
                          room_type=connection_type,
                          floor=floor_id,
                          coordinates=location,
                          building_id=building_id,
                          node_type='vertical_connection')
        
        vertical_nodes.append(node_id)
    
    # Connect vertical nodes
    for i in range(len(vertical_nodes) - 1):
        distance = 15 if connection_type == 'stairs' else 5  # Stairs take longer
        graph.add_edge(vertical_nodes[i], vertical_nodes[i + 1], 
                      weight=distance, connection_type=connection_type)

def get_building_entrance_rooms(building_id: str) -> List[str]:
    """Get list of entrance room IDs for a building"""
    if building_id not in BUILDING_INTERIORS:
        return []
    
    entrance_rooms = []
    interior_config = BUILDING_INTERIORS[building_id]
    
    for floor_id, floor_data in interior_config['floors'].items():
        for entrance_id in floor_data.get('entrances', []):
            entrance_room_id = f"{building_id}_{floor_id}_{entrance_id}"
            entrance_rooms.append(entrance_room_id)
    
    return entrance_rooms

def get_room_full_id(building_id: str, room_name: str) -> str:
    """Find full room ID from room name or partial ID"""
    if building_id not in BUILDING_INTERIORS:
        return None
    
    interior_config = BUILDING_INTERIORS[building_id]
    
    for floor_id, floor_data in interior_config['floors'].items():
        for room_id, room_data in floor_data['rooms'].items():
            # Check if room_name matches room_id or room name
            if (room_id.lower() == room_name.lower() or 
                room_data.get('name', '').lower() == room_name.lower()):
                return f"{building_id}_{floor_id}_{room_id}"
    
    return None

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

# Load building interior configurations
load_all_building_interiors()
