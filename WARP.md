# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Campus Navigation System** - a Flask-based web application that helps users navigate a college campus by finding the shortest routes between buildings using Dijkstra's algorithm. The system features an interactive map interface, real-time pathfinding, and an admin panel for campus management.

## Core Architecture

### Backend Structure
- **Flask Application (`app.py`)**: Main web server with REST API endpoints
- **Pathfinding Engine (`pathfinding.py`)**: Custom implementation of Dijkstra's algorithm for shortest path calculation
- **Campus Data Management (`campus_data.py`)**: Handles building/intersection data, graph creation, and configuration persistence
- **Configuration System (`campus_config.json`)**: JSON-based dynamic configuration for buildings, intersections, and paths

### Key Components
1. **Graph-Based Navigation**: Uses NetworkX to create a campus graph where buildings and intersections are nodes, connected by weighted edges (distances in meters)
2. **Dynamic Configuration**: Campus layout is stored in JSON and can be modified via admin interface without code changes
3. **Interactive Maps**: Uses Folium for server-side map generation and Leaflet.js for client-side interactivity
4. **Admin Panel**: Web-based interface for adding/editing buildings, intersections, and paths

## Essential Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application  
python app.py

# Alternative: Use the provided batch script (Windows)
start_app.bat

# Run pathfinding tests
python test_pathfinding.py
```

### Testing & Validation
```bash
# Test pathfinding algorithms with sample data
python test_pathfinding.py

# Interactive pathfinding test (run within test script)
# Provides manual testing interface for route calculations

# Test building interior APIs
curl http://localhost:5000/api/buildings/Library/rooms
curl -X POST http://localhost:5000/api/buildings/Library/route -H "Content-Type: application/json" -d '{"start_room":"main_entrance","end_room":"study_room_1"}'
```

### Application Access
- **Main Application**: http://localhost:5000
- **Campus Admin Panel**: http://localhost:5000/admin
- **Building Admin Panel**: http://localhost:5000/admin/buildings
- **Admin Debug Panel**: http://localhost:5000/admin/debug
- **Default Admin Password**: `campus_admin_2024`

## API Endpoints Structure

### Public Endpoints
- `GET /api/buildings` - List all campus buildings
- `POST /api/route` - Calculate shortest route between buildings
- `POST /api/route/to-room` - Calculate route from building to specific room
- `GET /api/map` - Generate campus overview map
- `POST /api/map/route` - Generate route-specific map
- `GET /api/destinations/<building_id>` - Get possible destinations from building

### Building Interior Endpoints
- `GET /api/buildings/<building_id>/interior` - Get building interior configuration
- `GET /api/buildings/<building_id>/rooms` - List all rooms in a building
- `POST /api/buildings/<building_id>/route` - Find route within building between rooms
- `GET /api/buildings/<building_id>/floor-plan/<floor_id>` - Get SVG floor plan for specific floor

### Admin Endpoints (Authentication Required)
- `POST /admin/login` - Admin authentication
- `POST /api/admin/buildings` - Add/update buildings (campus level)
- `DELETE /api/admin/buildings/<id>` - Delete buildings
- `GET /api/admin/intersections` - Manage intersections
- `GET /api/admin/paths` - Manage campus paths
- `POST /api/buildings/<building_id>/interior` - Update building interior configuration (admin)

## Configuration Management

### Campus Configuration (`campus_config.json`)
The system uses a centralized JSON configuration file with these sections:
- **buildings**: Campus buildings with coordinates, names, descriptions, and types
- **intersections**: Path intersection points for complex routing
- **campus_paths**: Connections between nodes with distances
- **map_settings**: Map center coordinates, bounds, and zoom levels
- **admin_settings**: Admin authentication and session settings

### Building Interior Configuration (`buildings/{building_id}_interior.json`)
Each building can have its own interior configuration file with:
- **floors**: Floor definitions with rooms, connections, and entrances
- **vertical_connections**: Stairs and elevators connecting floors
- **room_types**: Icon and color definitions for different room types

#### Sample Building Interior Structure:
```json
{
  "building_id": "Library",
  "building_name": "Central Library",
  "floors": {
    "ground": {
      "name": "Ground Floor",
      "level": 0,
      "rooms": {
        "main_entrance": {
          "name": "Main Entrance",
          "type": "entrance",
          "coordinates": [10, 50],
          "description": "Main building entrance"
        }
      },
      "connections": [["main_entrance", "reception", 8]],
      "entrances": ["main_entrance"]
    }
  },
  "vertical_connections": {
    "stairs": [{
      "id": "1",
      "floors": ["ground", "first"],
      "location": [25, 35]
    }]
  }
}
```

### Adding New Buildings
1. **Campus Level**: Use admin panel at `/admin` (preferred method)
2. **Building Interiors**: Use admin panel at `/admin/buildings`
3. Or manually edit configuration files and restart application
4. Buildings must be within the configured map bounds (default: 2km square)

## Development Guidelines

### Working with Pathfinding
- The `CampusPathfinder` class in `pathfinding.py` implements Dijkstra's algorithm from scratch
- **Campus Level**: Graph uses real GPS coordinates and Haversine formula for accurate distance calculations
- **Building Level**: Interior graphs use local coordinate systems with configurable scale
- All distances are in meters, walking times assume 5 km/h average speed
- **Multi-level Routing**: System automatically combines campus + interior routes when destination is a room
- Test modifications using `test_pathfinding.py` before deployment

### Campus Data Structure
- **Campus Graph**: Buildings and intersections are nodes, edges represent walkable paths
- **Interior Graphs**: Per-building graphs with rooms, halls, stairs, and elevators as nodes
- **Vertical Connections**: Stairs and elevators create weighted edges between floors (stairs = 15m, elevators = 5m)
- Graph is rebuilt automatically when configuration changes via admin panel
- Campus bounds are configurable to prevent invalid coordinate entries

### Building Interior System
- **Data Storage**: Each building has separate JSON file in `buildings/` directory
- **Graph Caching**: Building interior graphs are cached in memory and rebuilt when configuration changes
- **Room Identification**: Rooms use hierarchical IDs: `{building_id}_{floor_id}_{room_id}`
- **Entrance Detection**: System finds best building entrance for room-based navigation
- **Floor Plan Visualization**: SVG floor plans generated dynamically from room coordinates

### Frontend Integration
- **Main Interface**: `templates/index.html` supports both building-to-building and building-to-room routing
- **Campus Maps**: Generated server-side with Folium, displayed with Leaflet.js
- **Interior Maps**: SVG floor plans with room highlighting and connection visualization
- **Admin Panels**: Separate interfaces for Campus Configuration (`/admin`) and Building Configuration (`/admin/buildings`)
- **Responsive Design**: Works on both desktop and mobile devices

### Security Considerations
- Admin panel requires password authentication with session management
- CORS is enabled for cross-origin requests
- Session timeouts are configurable (default: 24 hours)
- Admin password should be changed from default in production
- Building interior configurations are admin-protected

## Performance Notes

- Pathfinding algorithm complexity: O((V + E) log V) where V = vertices, E = edges
- Graph supports 1000+ buildings with proper optimization
- Frontend caches building data to reduce API calls
- Map rendering is optimized for smooth user experience

## Troubleshooting Common Issues

### Port Already in Use (Windows)
```bash
# Find process using port 5000
netstat -ano | findstr :5000
# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F
```

### Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Graph Connectivity Issues
- Use admin debug panel to verify all nodes are connected
- Check that campus paths properly link buildings to intersections
- Run `test_pathfinding.py` to validate graph integrity

### Map Not Loading
- Verify internet connection (required for map tiles)
- Check browser console for JavaScript errors
- Ensure Flask server is running and accessible

## File Structure Importance

- `app.py`: Main Flask application with campus and building interior API endpoints
- `pathfinding.py`: Core algorithm with both campus and building interior pathfinding
- `campus_data.py`: Data layer for both campus and building interior configuration
- `templates/index.html`: Main frontend with room-based navigation support
- `templates/admin_buildings.html`: Building interior configuration admin interface
- `campus_config.json`: Campus-level configuration (buildings, intersections, paths)
- `buildings/{building_id}_interior.json`: Per-building interior configurations
- `utils/`: Contains legacy drawing utilities (not used in main app)

## Technology Stack

- **Backend**: Python 3.7+, Flask, NetworkX, Folium, Flask-CORS
- **Frontend**: HTML5/CSS3, JavaScript ES6+, Leaflet.js, Font Awesome
- **Data**: JSON-based configuration, NetworkX graphs
- **Maps**: OpenStreetMap tiles, Folium server-side generation, Leaflet.js client-side
