"""
Flask web application for campus pathfinding
Provides REST API endpoints and serves the web interface
"""

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import folium
import networkx as nx
from pathfinding import pathfinder
from campus_data import get_building_list, BUILDINGS, INTERSECTIONS, campus_graph, save_campus_config, CAMPUS_CONFIG, get_map_bounds, is_within_bounds, MAP_CENTER, MAP_BOUNDS_KM, calculate_distance
import json
import hashlib
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate secure session key
CORS(app)  # Enable CORS for cross-origin requests

# Admin authentication functions
def check_admin_auth():
    """Check if user is authenticated as admin"""
    if 'admin_logged_in' not in session:
        return False
    
    # Check if session has expired
    if 'admin_login_time' in session:
        login_time = datetime.fromisoformat(session['admin_login_time'])
        timeout_hours = CAMPUS_CONFIG.get('admin_settings', {}).get('session_timeout_hours', 24)
        if datetime.now() - login_time > timedelta(hours=timeout_hours):
            session.clear()
            return False
    
    return session['admin_logged_in']

def hash_password(password: str) -> str:
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    """Serve the main web application"""
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    """Serve the admin panel"""
    if not check_admin_auth():
        return render_template('admin_login.html')
    return render_template('admin_panel.html')

@app.route('/admin/debug')
def admin_debug():
    """Serve the debug admin panel"""
    if not check_admin_auth():
        return render_template('admin_login.html')
    return render_template('admin_debug.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({'success': False, 'error': 'Password required'}), 400
        
        password = data['password']
        admin_password = CAMPUS_CONFIG.get('admin_settings', {}).get('admin_password', 'campus_admin_2024')
        
        if password == admin_password:
            session['admin_logged_in'] = True
            session['admin_login_time'] = datetime.now().isoformat()
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/admin/map-bounds', methods=['GET'])
def get_admin_map_bounds():
    """Get map bounds information for admin"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        bounds = get_map_bounds()
        return jsonify({
            'success': True,
            'center': list(MAP_CENTER),
            'bounds_km': MAP_BOUNDS_KM,
            'bounds_coordinates': {
                'south_west': list(bounds[0]),
                'north_east': list(bounds[1])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/buildings', methods=['POST'])
def add_or_update_building():
    """Add or update a building (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        required_fields = ['id', 'name', 'coordinates', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        building_id = data['id']
        name = data['name']
        coordinates = data['coordinates']
        description = data['description']
        building_type = data.get('type', 'general')
        
        # Validate coordinates
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return jsonify({'success': False, 'error': 'Coordinates must be [lat, lon] array'}), 400
        
        lat, lon = coordinates
        if not is_within_bounds(lat, lon):
            return jsonify({
                'success': False, 
                'error': f'Coordinates are outside the campus bounds ({MAP_BOUNDS_KM}km square)'
            }), 400
        
        # Update buildings data
        BUILDINGS[building_id] = {
            'name': name,
            'coordinates': tuple(coordinates),
            'description': description,
            'type': building_type
        }
        
        # Save to configuration file
        if save_campus_config():
            # Recreate the graph to include new building
            global campus_graph
            from campus_data import create_campus_graph
            campus_graph = create_campus_graph()
            
            return jsonify({
                'success': True,
                'message': f'Building {name} saved successfully',
                'building': {
                    'id': building_id,
                    'name': name,
                    'coordinates': coordinates,
                    'description': description,
                    'type': building_type
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/buildings/<building_id>', methods=['DELETE'])
def delete_building(building_id):
    """Delete a building (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        if building_id not in BUILDINGS:
            return jsonify({'success': False, 'error': 'Building not found'}), 404
        
        building_name = BUILDINGS[building_id]['name']
        del BUILDINGS[building_id]
        
        # Save to configuration file
        if save_campus_config():
            # Recreate the graph
            global campus_graph
            from campus_data import create_campus_graph
            campus_graph = create_campus_graph()
            
            return jsonify({
                'success': True,
                'message': f'Building {building_name} deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/intersections', methods=['GET'])
def get_intersections():
    """Get all intersections (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        intersections_list = [{
            'id': intersection_id,
            'name': intersection_id.replace('_', ' ').title(),
            'coordinates': list(coordinates)
        } for intersection_id, coordinates in INTERSECTIONS.items()]
        
        return jsonify({
            'success': True,
            'intersections': intersections_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/intersections', methods=['POST'])
def add_intersection():
    """Add a new intersection (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        required_fields = ['id', 'coordinates']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        intersection_id = data['id']
        coordinates = data['coordinates']
        
        # Validate coordinates
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return jsonify({'success': False, 'error': 'Coordinates must be [lat, lon] array'}), 400
        
        lat, lon = coordinates
        if not is_within_bounds(lat, lon):
            return jsonify({
                'success': False, 
                'error': f'Coordinates are outside the campus bounds ({MAP_BOUNDS_KM}km square)'
            }), 400
        
        # Add intersection
        INTERSECTIONS[intersection_id] = tuple(coordinates)
        
        # Save to configuration file
        if save_campus_config():
            # Recreate the graph
            global campus_graph
            from campus_data import create_campus_graph
            campus_graph = create_campus_graph()
            
            return jsonify({
                'success': True,
                'message': f'Intersection {intersection_id} added successfully',
                'intersection': {
                    'id': intersection_id,
                    'coordinates': coordinates
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/intersections/<intersection_id>', methods=['DELETE'])
def delete_intersection(intersection_id):
    """Delete an intersection (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        if intersection_id not in INTERSECTIONS:
            return jsonify({'success': False, 'error': 'Intersection not found'}), 404
        
        del INTERSECTIONS[intersection_id]
        
        # Also remove any paths that use this intersection
        campus_paths = CAMPUS_CONFIG.get('campus_paths', [])
        updated_paths = [path for path in campus_paths 
                        if intersection_id not in (path[0] if len(path) > 0 else '', 
                                                  path[1] if len(path) > 1 else '')]
        CAMPUS_CONFIG['campus_paths'] = updated_paths
        
        # Save to configuration file
        if save_campus_config():
            # Recreate the graph
            global campus_graph
            from campus_data import create_campus_graph
            campus_graph = create_campus_graph()
            
            return jsonify({
                'success': True,
                'message': f'Intersection {intersection_id} deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/paths', methods=['GET'])
def get_paths():
    """Get all campus paths (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        campus_paths = CAMPUS_CONFIG.get('campus_paths', [])
        paths_list = []
        
        for i, path in enumerate(campus_paths):
            if len(path) >= 2:
                node1, node2 = path[0], path[1]
                distance = path[2] if len(path) > 2 else None
                
                # Get node names
                node1_name = BUILDINGS.get(node1, {}).get('name', node1.replace('_', ' ').title())
                node2_name = BUILDINGS.get(node2, {}).get('name', node2.replace('_', ' ').title())
                
                # Calculate distance if not provided
                if distance is None and node1 in campus_graph.nodes and node2 in campus_graph.nodes:
                    coord1 = campus_graph.nodes[node1]['coordinates']
                    coord2 = campus_graph.nodes[node2]['coordinates']
                    distance = calculate_distance(coord1, coord2)
                
                paths_list.append({
                    'id': i,
                    'node1': node1,
                    'node2': node2,
                    'node1_name': node1_name,
                    'node2_name': node2_name,
                    'distance': round(distance, 1) if distance else None
                })
        
        return jsonify({
            'success': True,
            'paths': paths_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/paths', methods=['POST'])
def add_path():
    """Add a new path between two nodes (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        required_fields = ['node1', 'node2']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        node1 = data['node1']
        node2 = data['node2']
        distance = data.get('distance')
        
        # Validate nodes exist
        all_nodes = {**BUILDINGS, **INTERSECTIONS}
        if node1 not in all_nodes:
            return jsonify({'success': False, 'error': f'Node {node1} does not exist'}), 400
        if node2 not in all_nodes:
            return jsonify({'success': False, 'error': f'Node {node2} does not exist'}), 400
        
        if node1 == node2:
            return jsonify({'success': False, 'error': 'Cannot create path from node to itself'}), 400
        
        # Calculate distance if not provided
        if distance is None:
            coord1 = all_nodes[node1] if node1 in INTERSECTIONS else BUILDINGS[node1]['coordinates']
            coord2 = all_nodes[node2] if node2 in INTERSECTIONS else BUILDINGS[node2]['coordinates']
            distance = calculate_distance(coord1, coord2)
        
        # Check if path already exists
        campus_paths = CAMPUS_CONFIG.get('campus_paths', [])
        for existing_path in campus_paths:
            if len(existing_path) >= 2:
                if (existing_path[0] == node1 and existing_path[1] == node2) or \
                   (existing_path[0] == node2 and existing_path[1] == node1):
                    return jsonify({'success': False, 'error': 'Path between these nodes already exists'}), 400
        
        # Add new path
        new_path = [node1, node2, round(distance, 1)]
        campus_paths.append(new_path)
        CAMPUS_CONFIG['campus_paths'] = campus_paths
        
        # Save to configuration file
        if save_campus_config():
            # Recreate the graph
            global campus_graph
            from campus_data import create_campus_graph
            campus_graph = create_campus_graph()
            
            node1_name = BUILDINGS.get(node1, {}).get('name', node1.replace('_', ' ').title())
            node2_name = BUILDINGS.get(node2, {}).get('name', node2.replace('_', ' ').title())
            
            return jsonify({
                'success': True,
                'message': f'Path between {node1_name} and {node2_name} added successfully',
                'path': {
                    'node1': node1,
                    'node2': node2,
                    'node1_name': node1_name,
                    'node2_name': node2_name,
                    'distance': round(distance, 1)
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/paths/<int:path_id>', methods=['DELETE'])
def delete_path(path_id):
    """Delete a path (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        campus_paths = CAMPUS_CONFIG.get('campus_paths', [])
        
        if path_id < 0 or path_id >= len(campus_paths):
            return jsonify({'success': False, 'error': 'Path not found'}), 404
        
        deleted_path = campus_paths.pop(path_id)
        CAMPUS_CONFIG['campus_paths'] = campus_paths
        
        # Save to configuration file
        if save_campus_config():
            # Recreate the graph
            global campus_graph
            from campus_data import create_campus_graph
            campus_graph = create_campus_graph()
            
            return jsonify({
                'success': True,
                'message': f'Path deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/buildings', methods=['GET'])
def get_buildings():
    """Get list of all campus buildings"""
    try:
        buildings = get_building_list()
        return jsonify({
            'success': True,
            'buildings': buildings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/route', methods=['POST'])
def find_route():
    """Find the shortest route between two buildings"""
    try:
        data = request.get_json()
        
        if not data or 'start' not in data or 'end' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing start or end building'
            }), 400
        
        start = data['start']
        end = data['end']
        
        # Validate building IDs
        if start not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': f'Invalid start building: {start}'
            }), 400
            
        if end not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': f'Invalid end building: {end}'
            }), 400
        
        # Find the route
        route_info = pathfinder.find_route(start, end)
        return jsonify(route_info)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/destinations/<building_id>', methods=['GET'])
def get_destinations(building_id):
    """Get all possible destinations from a given building"""
    try:
        if building_id not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': f'Invalid building ID: {building_id}'
            }), 400
        
        destinations = pathfinder.get_all_possible_destinations(building_id)
        return jsonify({
            'success': True,
            'destinations': destinations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/map')
def get_campus_map():
    """Generate an interactive campus map with all buildings (bounded view)"""
    try:
        # Use configured map center and bounds
        center_lat, center_lon = MAP_CENTER
        bounds = get_map_bounds()
        
        # Create folium map with bounds
        campus_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=CAMPUS_CONFIG.get('map_settings', {}).get('zoom_level', 16),
            tiles='OpenStreetMap'
        )
        
        # Set map bounds to restrict view
        campus_map.fit_bounds(bounds)
        
        # Add building markers
        for building_id, building_data in BUILDINGS.items():
            lat, lon = building_data['coordinates']
            popup_content = f"""
            <div style='width: 200px;'>
                <h4>{building_data['name']}</h4>
                <p>{building_data['description']}</p>
                <p><strong>ID:</strong> {building_id}</p>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=250),
                tooltip=building_data['name'],
                icon=folium.Icon(color='red', icon='building', prefix='fa')
            ).add_to(campus_map)
        
        # Add intersection markers (optional, for debugging)
        for intersection_id, coordinates in campus_graph.nodes(data=True):
            if coordinates.get('type') == 'intersection':
                lat, lon = coordinates['coordinates']
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=3,
                    popup=intersection_id,
                    color='blue',
                    fillColor='blue',
                    fillOpacity=0.7
                ).add_to(campus_map)
        
        # Add paths between connected nodes
        for edge in campus_graph.edges():
            node1, node2 = edge
            coord1 = campus_graph.nodes[node1]['coordinates']
            coord2 = campus_graph.nodes[node2]['coordinates']
            
            folium.PolyLine(
                locations=[coord1, coord2],
                color='gray',
                weight=2,
                opacity=0.5
            ).add_to(campus_map)
        
        return campus_map._repr_html_()
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/map/route', methods=['POST'])
def get_route_map():
    """Generate a map showing the route between two buildings"""
    try:
        data = request.get_json()
        
        if not data or 'start' not in data or 'end' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing start or end building'
            }), 400
        
        start = data['start']
        end = data['end']
        
        # Get route information
        route_info = pathfinder.find_route(start, end)
        
        if not route_info['success']:
            return jsonify(route_info), 400
        
        # Calculate center for map
        all_coords = route_info['coordinates']
        center_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
        center_lon = sum(coord[1] for coord in all_coords) / len(all_coords)
        
        # Create map
        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=17,
            tiles='OpenStreetMap'
        )
        
        # Add all buildings as markers
        for building_id, building_data in BUILDINGS.items():
            lat, lon = building_data['coordinates']
            
            # Different colors for start, end, and other buildings
            if building_id == start:
                icon_color = 'green'
                icon_name = 'play'
            elif building_id == end:
                icon_color = 'red'
                icon_name = 'stop'
            else:
                icon_color = 'blue'
                icon_name = 'building'
            
            popup_content = f"""
            <div style='width: 200px;'>
                <h4>{building_data['name']}</h4>
                <p>{building_data['description']}</p>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=250),
                tooltip=building_data['name'],
                icon=folium.Icon(color=icon_color, icon=icon_name, prefix='fa')
            ).add_to(route_map)
        
        # Add the route path
        folium.PolyLine(
            locations=route_info['coordinates'],
            color='red',
            weight=5,
            opacity=0.8,
            popup=f"Route: {route_info['total_distance']}m, ~{route_info['estimated_walk_time']} min"
        ).add_to(route_map)
        
        # Add markers for intermediate points in the route
        for i, detail in enumerate(route_info['path_details']):
            if detail['type'] == 'intersection':
                lat, lon = detail['coordinates']
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    popup=f"Step {detail['step']}: {detail['name']}",
                    color='orange',
                    fillColor='orange',
                    fillOpacity=0.8
                ).add_to(route_map)
        
        return route_map._repr_html_()
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/graph-info')
def get_graph_info():
    """Get information about the campus graph"""
    try:
        info = {
            'total_nodes': len(campus_graph.nodes),
            'total_edges': len(campus_graph.edges),
            'buildings_count': len(BUILDINGS),
            'intersections_count': len([n for n, d in campus_graph.nodes(data=True) 
                                       if d.get('type') == 'intersection']),
            'is_connected': len(list(campus_graph.connected_components())) == 1
        }
        
        return jsonify({
            'success': True,
            'graph_info': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("Starting Campus Navigation Server...")
    print("Available buildings:")
    for building_id, building_data in BUILDINGS.items():
        print(f"  - {building_data['name']} (ID: {building_id})")
    
    print(f"\nGraph info:")
    print(f"  - Nodes: {len(campus_graph.nodes)}")
    print(f"  - Edges: {len(campus_graph.edges)}")
    print(f"  - Connected: {len(list(nx.connected_components(campus_graph))) == 1}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
