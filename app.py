"""
Flask web application for campus pathfinding
Provides REST API endpoints and serves the web interface
"""

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import folium
import networkx as nx
from pathfinding import pathfinder
from campus_data import (get_building_list, BUILDINGS, INTERSECTIONS, campus_graph, save_campus_config, CAMPUS_CONFIG, 
                        get_map_bounds, is_within_bounds, MAP_CENTER, MAP_BOUNDS_KM, calculate_distance,
                        BUILDING_INTERIORS, save_building_interior_config, load_building_interior_config, 
                        load_all_building_interiors)
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

@app.route('/debug')
def debug():
    """Serve the debug page"""
    with open('debug.html', 'r') as f:
        return f.read()

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

@app.route('/admin/buildings')
def admin_buildings():
    """Serve the building configuration panel"""
    if not check_admin_auth():
        return render_template('admin_login.html')
    return render_template('admin_buildings.html')

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
            # Update pathfinder with new graph
            pathfinder.update_campus_graph(campus_graph)
            
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
            # Update pathfinder with new graph
            pathfinder.update_campus_graph(campus_graph)
            
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
            # Update pathfinder with new graph
            pathfinder.update_campus_graph(campus_graph)
            
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
            # Update pathfinder with new graph
            pathfinder.update_campus_graph(campus_graph)
            
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
            # Update pathfinder with new graph
            pathfinder.update_campus_graph(campus_graph)
            
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
            # Update pathfinder with new graph
            pathfinder.update_campus_graph(campus_graph)
            
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

# Building Interior API Endpoints

@app.route('/api/buildings/<building_id>/interior', methods=['GET'])
def get_building_interior(building_id):
    """Get building interior configuration"""
    try:
        if building_id not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': 'Building not found'
            }), 404
        
        interior_config = BUILDING_INTERIORS.get(building_id, {})
        
        return jsonify({
            'success': True,
            'building_id': building_id,
            'interior': interior_config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/buildings/<building_id>/interior', methods=['POST'])
def update_building_interior(building_id):
    """Update building interior configuration (admin only)"""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        if building_id not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': 'Building not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['floors', 'vertical_connections', 'room_types']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Ensure building_id and building_name are set correctly
        data['building_id'] = building_id
        data['building_name'] = BUILDINGS[building_id]['name']
        
        # Save configuration
        if save_building_interior_config(building_id, data):
            # Clear pathfinder cache for this building
            pathfinder.clear_building_graph_cache(building_id)
            
            return jsonify({
                'success': True,
                'message': f'Building interior updated for {BUILDINGS[building_id]["name"]}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save building configuration'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/buildings/<building_id>/rooms', methods=['GET'])
def get_building_rooms(building_id):
    """Get all rooms in a building"""
    try:
        if building_id not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': 'Building not found'
            }), 404
        
        rooms = pathfinder.get_building_rooms(building_id)
        
        return jsonify({
            'success': True,
            'building_id': building_id,
            'building_name': BUILDINGS[building_id]['name'],
            'rooms': rooms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/buildings/<building_id>/route', methods=['POST'])
def find_building_interior_route(building_id):
    """Find route within a building between two rooms"""
    try:
        if building_id not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': 'Building not found'
            }), 404
        
        data = request.get_json()
        if not data or 'start_room' not in data or 'end_room' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing start_room or end_room'
            }), 400
        
        start_room = data['start_room']
        end_room = data['end_room']
        
        route_info = pathfinder.find_interior_route(building_id, start_room, end_room)
        return jsonify(route_info)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/route/to-room', methods=['POST'])
def find_route_to_room():
    """Find route from building to specific room in another building"""
    try:
        data = request.get_json()
        
        if not data or 'start_building' not in data or 'end_building' not in data or 'end_room' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing start_building, end_building, or end_room'
            }), 400
        
        start_building = data['start_building']
        end_building = data['end_building']
        end_room = data['end_room']
        
        # Validate building IDs
        if start_building not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': f'Invalid start building: {start_building}'
            }), 400
            
        if end_building not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': f'Invalid end building: {end_building}'
            }), 400
        
        route_info = pathfinder.find_campus_to_room_route(start_building, end_building, end_room)
        return jsonify(route_info)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/buildings/<building_id>/floor-plan/<floor_id>', methods=['GET'])
def get_floor_plan_svg(building_id, floor_id):
    """Generate SVG floor plan for a specific floor"""
    try:
        if building_id not in BUILDINGS:
            return jsonify({
                'success': False,
                'error': 'Building not found'
            }), 404
        
        if building_id not in BUILDING_INTERIORS:
            return jsonify({
                'success': False,
                'error': 'Building interior configuration not found'
            }), 404
        
        interior_config = BUILDING_INTERIORS[building_id]
        
        if floor_id not in interior_config.get('floors', {}):
            return jsonify({
                'success': False,
                'error': f'Floor {floor_id} not found in building {building_id}'
            }), 404
        
        floor_data = interior_config['floors'][floor_id]
        floor_plan = floor_data.get('floor_plan', {'width': 100, 'height': 100})
        
        # Generate SVG
        svg_width = 600
        svg_height = 400
        
        svg_content = f'''
        <svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {floor_plan['width']} {floor_plan['height']}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{floor_plan['width']}" height="{floor_plan['height']}" fill="#f8f9fa" stroke="#ddd" stroke-width="1"/>
        '''
        
        # Add rooms
        room_types = interior_config.get('room_types', {})
        for room_id, room_data in floor_data.get('rooms', {}).items():
            x, y = room_data.get('coordinates', [0, 0])
            room_type = room_data.get('type', 'common')
            color = room_types.get(room_type, {}).get('color', '#667eea')
            
            # Draw room as circle
            svg_content += f'''
            <circle cx="{x}" cy="{y}" r="3" fill="{color}" stroke="#333" stroke-width="0.5"/>
            <text x="{x}" y="{y-5}" text-anchor="middle" font-size="8" fill="#333">{room_data.get('name', room_id)}</text>
            '''
        
        # Add connections
        for connection in floor_data.get('connections', []):
            if len(connection) >= 2:
                room1_id, room2_id = connection[0], connection[1]
                room1 = floor_data.get('rooms', {}).get(room1_id)
                room2 = floor_data.get('rooms', {}).get(room2_id)
                
                if room1 and room2:
                    x1, y1 = room1.get('coordinates', [0, 0])
                    x2, y2 = room2.get('coordinates', [0, 0])
                    
                    svg_content += f'''
                    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#6c757d" stroke-width="1" opacity="0.7"/>
                    '''
        
        # Add vertical connections (stairs, elevators) for this floor
        for stairs in interior_config.get('vertical_connections', {}).get('stairs', []):
            if floor_id in stairs.get('floors', []):
                x, y = stairs.get('location', [0, 0])
                svg_content += f'''
                <rect x="{x-2}" y="{y-2}" width="4" height="4" fill="#dc3545" stroke="#333" stroke-width="0.5"/>
                <text x="{x}" y="{y-5}" text-anchor="middle" font-size="6" fill="#333">Stairs</text>
                '''
        
        for elevator in interior_config.get('vertical_connections', {}).get('elevators', []):
            if floor_id in elevator.get('floors', []):
                x, y = elevator.get('location', [0, 0])
                svg_content += f'''
                <rect x="{x-2}" y="{y-2}" width="4" height="4" fill="#ffc107" stroke="#333" stroke-width="0.5"/>
                <text x="{x}" y="{y-5}" text-anchor="middle" font-size="6" fill="#333">Elevator</text>
                '''
        
        svg_content += '</svg>'
        
        return svg_content, 200, {'Content-Type': 'image/svg+xml'}
        
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
