"""
Pathfinding algorithms for campus navigation
Implements Dijkstra's algorithm to find shortest paths between buildings
"""

import networkx as nx
from campus_data import campus_graph, BUILDINGS, BUILDING_INTERIORS, create_building_interior_graph, get_building_entrance_rooms, get_room_full_id
import heapq
from typing import List, Tuple, Dict, Optional

class CampusPathfinder:
    def __init__(self):
        self.graph = campus_graph
        self.building_graphs = {}  # Cache for building interior graphs
    
    def dijkstra_shortest_path(self, start: str, end: str) -> Tuple[Optional[List[str]], Optional[float]]:
        """
        Implement Dijkstra's algorithm to find the shortest path between two nodes
        
        Args:
            start (str): Starting node ID
            end (str): Ending node ID
            
        Returns:
            Tuple containing:
            - List of node IDs representing the path (None if no path exists)
            - Total distance of the path in meters (None if no path exists)
        """
        if start not in self.graph.nodes or end not in self.graph.nodes:
            return None, None
        
        # If start and end are the same
        if start == end:
            return [start], 0.0
        
        # Initialize distances and previous nodes
        distances = {node: float('inf') for node in self.graph.nodes}
        previous = {node: None for node in self.graph.nodes}
        distances[start] = 0
        
        # Priority queue: (distance, node)
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            # Skip if we've already processed this node
            if current_node in visited:
                continue
                
            visited.add(current_node)
            
            # If we've reached the destination
            if current_node == end:
                break
            
            # Check all neighbors
            for neighbor in self.graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                
                # Get edge weight (distance)
                edge_weight = self.graph.edges[current_node, neighbor]['weight']
                new_distance = current_distance + edge_weight
                
                # If we found a shorter path to the neighbor
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_distance, neighbor))
        
        # Reconstruct path
        if distances[end] == float('inf'):
            return None, None  # No path exists
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        return path, distances[end]
    
    def get_path_coordinates(self, path: List[str]) -> List[Tuple[float, float]]:
        """
        Convert a path of node IDs to a list of coordinates
        
        Args:
            path: List of node IDs
            
        Returns:
            List of (latitude, longitude) tuples
        """
        if not path:
            return []
        
        coordinates = []
        for node in path:
            if node in self.graph.nodes:
                coord = self.graph.nodes[node]['coordinates']
                coordinates.append(coord)
        
        return coordinates
    
    def get_path_details(self, path: List[str]) -> List[Dict]:
        """
        Get detailed information about each node in the path
        
        Args:
            path: List of node IDs
            
        Returns:
            List of dictionaries with node details
        """
        if not path:
            return []
        
        path_details = []
        for i, node in enumerate(path):
            if node in self.graph.nodes:
                node_data = self.graph.nodes[node]
                details = {
                    'node_id': node,
                    'name': node_data.get('name', node),
                    'coordinates': node_data['coordinates'],
                    'type': node_data.get('type', 'unknown'),
                    'step': i + 1
                }
                
                # Add distance to next node if not the last node
                if i < len(path) - 1:
                    next_node = path[i + 1]
                    if self.graph.has_edge(node, next_node):
                        distance = self.graph.edges[node, next_node]['weight']
                        details['distance_to_next'] = round(distance, 1)
                
                path_details.append(details)
        
        return path_details
    
    def find_route(self, start: str, end: str) -> Dict:
        """
        Find the complete route information between two buildings
        
        Args:
            start: Starting building ID
            end: Ending building ID
            
        Returns:
            Dictionary containing route information
        """
        path, total_distance = self.dijkstra_shortest_path(start, end)
        
        if path is None:
            return {
                'success': False,
                'error': f'No route found between {start} and {end}',
                'path': None,
                'coordinates': [],
                'total_distance': None,
                'path_details': []
            }
        
        coordinates = self.get_path_coordinates(path)
        path_details = self.get_path_details(path)
        
        return {
            'success': True,
            'path': path,
            'coordinates': coordinates,
            'total_distance': round(total_distance, 1),
            'path_details': path_details,
            'start_building': BUILDINGS.get(start, {}).get('name', start),
            'end_building': BUILDINGS.get(end, {}).get('name', end),
            'estimated_walk_time': self._calculate_walk_time(total_distance)
        }
    
    def _calculate_walk_time(self, distance_meters: float) -> int:
        """
        Calculate estimated walking time in minutes
        Assumes average walking speed of 5 km/h (1.39 m/s)
        
        Args:
            distance_meters: Distance in meters
            
        Returns:
            Estimated time in minutes
        """
        if distance_meters is None:
            return 0
        
        # Average walking speed: 5 km/h = 1.39 m/s
        walking_speed_ms = 1.39
        time_seconds = distance_meters / walking_speed_ms
        time_minutes = int(time_seconds / 60)
        
        return max(1, time_minutes)  # Minimum 1 minute
    
    def get_building_interior_graph(self, building_id: str) -> nx.Graph:
        """Get or create cached building interior graph"""
        if building_id not in self.building_graphs:
            self.building_graphs[building_id] = create_building_interior_graph(building_id)
        return self.building_graphs[building_id]
    
    def find_interior_route(self, building_id: str, start_room: str, end_room: str) -> Dict:
        """Find route within a building between two rooms"""
        interior_graph = self.get_building_interior_graph(building_id)
        
        if not interior_graph.nodes:
            return {
                'success': False,
                'error': f'No interior configuration found for building {building_id}',
                'path': None,
                'coordinates': [],
                'total_distance': None,
                'path_details': []
            }
        
        # Find full room IDs
        start_full_id = get_room_full_id(building_id, start_room) if '_' not in start_room else start_room
        end_full_id = get_room_full_id(building_id, end_room) if '_' not in end_room else end_room
        
        if not start_full_id or not end_full_id:
            return {
                'success': False,
                'error': f'Room not found in building {building_id}',
                'path': None,
                'coordinates': [],
                'total_distance': None,
                'path_details': []
            }
        
        # Use dijkstra on interior graph
        try:
            path, distance = nx.single_source_dijkstra(interior_graph, start_full_id, end_full_id)
            
            interior_coordinates = []
            path_details = []
            
            for i, node in enumerate(path):
                node_data = interior_graph.nodes[node]
                detail = {
                    'node_id': node,
                    'name': node_data.get('name', node),
                    'room_type': node_data.get('room_type', 'unknown'),
                    'floor': node_data.get('floor', 'unknown'),
                    'coordinates': node_data.get('coordinates', [0, 0]),
                    'step': i + 1,
                    'node_type': node_data.get('node_type', 'room')
                }
                
                if i < len(path) - 1:
                    next_node = path[i + 1]
                    if interior_graph.has_edge(node, next_node):
                        edge_distance = interior_graph.edges[node, next_node]['weight']
                        detail['distance_to_next'] = round(edge_distance, 1)
                        detail['connection_type'] = interior_graph.edges[node, next_node].get('connection_type', 'hallway')
                
                path_details.append(detail)
                interior_coordinates.append(node_data.get('coordinates', [0, 0]))
            
            return {
                'success': True,
                'path': path,
                'coordinates': interior_coordinates,
                'total_distance': round(distance, 1),
                'path_details': path_details,
                'start_room': interior_graph.nodes[start_full_id].get('name', start_room),
                'end_room': interior_graph.nodes[end_full_id].get('name', end_room),
                'estimated_walk_time': self._calculate_walk_time(distance),
                'building_id': building_id,
                'building_name': BUILDINGS.get(building_id, {}).get('name', building_id)
            }
            
        except nx.NetworkXNoPath:
            return {
                'success': False,
                'error': f'No path found between {start_room} and {end_room} in {building_id}',
                'path': None,
                'coordinates': [],
                'total_distance': None,
                'path_details': []
            }
    
    def find_campus_to_room_route(self, start_building: str, end_building: str, end_room: str) -> Dict:
        """Find route from one building to a specific room in another building"""
        # First, find route from start building to end building
        campus_route = self.find_route(start_building, end_building)
        
        if not campus_route['success']:
            return campus_route
        
        # Then, find route from building entrance to the specific room
        entrance_rooms = get_building_entrance_rooms(end_building)
        if not entrance_rooms:
            # If no entrance configured, use the building itself as entrance
            interior_route = self.find_interior_route(end_building, 'main_entrance', end_room)
        else:
            # Find best entrance (closest to the room)
            best_interior_route = None
            shortest_distance = float('inf')
            
            for entrance_room in entrance_rooms:
                interior_route = self.find_interior_route(end_building, entrance_room.split('_')[-1], end_room)
                if interior_route['success'] and interior_route['total_distance'] < shortest_distance:
                    shortest_distance = interior_route['total_distance']
                    best_interior_route = interior_route
            
            interior_route = best_interior_route if best_interior_route else {
                'success': False,
                'error': f'No path found to room {end_room} in {end_building}'
            }
        
        # Combine campus and interior routes
        return {
            'success': campus_route['success'] and interior_route['success'],
            'campus_route': campus_route,
            'interior_route': interior_route,
            'total_distance': campus_route['total_distance'] + (interior_route.get('total_distance', 0) if interior_route['success'] else 0),
            'total_walk_time': campus_route['estimated_walk_time'] + (interior_route.get('estimated_walk_time', 0) if interior_route['success'] else 0),
            'start_building': campus_route['start_building'],
            'end_building': campus_route['end_building'],
            'end_room': end_room,
            'route_type': 'campus_to_room'
        }
    
    def get_all_possible_destinations(self, start: str) -> List[Dict]:
        """
        Get all buildings reachable from a starting point with distances
        
        Args:
            start: Starting building ID
            
        Returns:
            List of dictionaries with destination information
        """
        destinations = []
        
        for building_id, building_data in BUILDINGS.items():
            if building_id != start:
                _, distance = self.dijkstra_shortest_path(start, building_id)
                if distance is not None:
                    destinations.append({
                        'id': building_id,
                        'name': building_data['name'],
                        'distance': round(distance, 1),
                        'walk_time': self._calculate_walk_time(distance),
                        'coordinates': building_data['coordinates'],
                        'description': building_data['description']
                    })
        
        # Sort by distance
        destinations.sort(key=lambda x: x['distance'])
        return destinations
    
    def get_building_rooms(self, building_id: str) -> List[Dict]:
        """Get all rooms in a building"""
        if building_id not in BUILDING_INTERIORS:
            return []
        
        rooms = []
        interior_config = BUILDING_INTERIORS[building_id]
        
        for floor_id, floor_data in interior_config['floors'].items():
            for room_id, room_data in floor_data['rooms'].items():
                rooms.append({
                    'id': room_id,
                    'full_id': f"{building_id}_{floor_id}_{room_id}",
                    'name': room_data.get('name', room_id),
                    'type': room_data.get('type', 'common'),
                    'floor': floor_id,
                    'floor_name': floor_data.get('name', floor_id),
                    'coordinates': room_data.get('coordinates', [0, 0])
                })
        
        return rooms
    
    def clear_building_graph_cache(self, building_id: str = None):
        """Clear cached building graphs"""
        if building_id:
            self.building_graphs.pop(building_id, None)
        else:
            self.building_graphs.clear()
    
    def update_campus_graph(self, new_graph):
        """Update the campus graph reference when it changes"""
        self.graph = new_graph
        # Clear building graphs cache as campus changes might affect building connections
        self.clear_building_graph_cache()

# Create global pathfinder instance
pathfinder = CampusPathfinder()
