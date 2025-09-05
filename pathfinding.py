"""
Pathfinding algorithms for campus navigation
Implements Dijkstra's algorithm to find shortest paths between buildings
"""

import networkx as nx
from campus_data import campus_graph, BUILDINGS
import heapq
from typing import List, Tuple, Dict, Optional

class CampusPathfinder:
    def __init__(self):
        self.graph = campus_graph
    
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

# Create global pathfinder instance
pathfinder = CampusPathfinder()
