# Campus Navigation System

A web-based pathfinding application that helps users navigate a college campus by finding the shortest routes between buildings using Dijkstra's algorithm.

## Features

### 🗺️ Interactive Map
- Interactive campus map using Leaflet.js
- Visual representation of all campus buildings
- Real-time route visualization with highlighted paths
- Clickable building markers with detailed information

### 🚀 Pathfinding Algorithm
- **Dijkstra's Algorithm** implementation for finding shortest paths
- Optimized route calculation considering real distances
- Support for multiple waypoints and intersections
- Walking time estimation based on average walking speed

### 🏢 Building Management
- **10 Sample Buildings** with realistic campus layout:
  - Main Library
  - Engineering Building
  - Student Center
  - Science Building
  - Business School
  - Arts Building
  - Dormitory A & B
  - Main Cafeteria
  - Recreation Center

### 🎨 Modern User Interface
- Responsive design that works on desktop and mobile
- Gradient backgrounds and modern styling
- Real-time loading indicators
- Error handling with user-friendly messages
- Interactive building selection from map popups

### 📊 Route Information
- Total distance in meters
- Estimated walking time
- Step-by-step directions
- Visual route highlighting on map

## Technology Stack

### Backend
- **Python 3.x**
- **Flask** - Web framework
- **NetworkX** - Graph data structures and algorithms
- **Folium** - Map generation library
- **Flask-CORS** - Cross-origin resource sharing

### Frontend
- **HTML5/CSS3** - Structure and styling
- **JavaScript (ES6+)** - Interactive functionality
- **Leaflet.js** - Interactive maps
- **Font Awesome** - Icons

### Algorithms
- **Dijkstra's Algorithm** - Shortest path calculation
- **Haversine Formula** - Distance calculation between coordinates

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Clone/Download the Project
```bash
# Navigate to your project directory
cd "C:\Users\HP\Desktop\Programming\Python\Under Work\Campus Mapping"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

### GET `/api/buildings`
Returns list of all campus buildings with coordinates and descriptions.

**Response:**
```json
{
  "success": true,
  "buildings": [
    {
      "id": "Main_Library",
      "name": "Main Library",
      "coordinates": [40.7831, -73.9712],
      "description": "Central library with study spaces and resources"
    }
  ]
}
```

### POST `/api/route`
Calculate shortest route between two buildings.

**Request Body:**
```json
{
  "start": "Main_Library",
  "end": "Engineering_Building"
}
```

**Response:**
```json
{
  "success": true,
  "path": ["Main_Library", "intersection_2", "intersection_4", "Engineering_Building"],
  "coordinates": [[40.7831, -73.9712], [40.7841, -73.9712], ...],
  "total_distance": 350.0,
  "estimated_walk_time": 4,
  "start_building": "Main Library",
  "end_building": "Engineering Building",
  "path_details": [...]
}
```

### GET `/api/map`
Returns HTML for campus overview map with all buildings and paths.

### POST `/api/map/route`
Returns HTML for route-specific map showing the calculated path.

### GET `/api/destinations/<building_id>`
Get all possible destinations from a given building with distances.

### GET `/api/graph-info`
Returns information about the campus graph structure.

## Project Structure

```
Campus Mapping/
├── app.py                 # Flask application and API endpoints
├── campus_data.py         # Campus buildings and graph data structure
├── pathfinding.py         # Dijkstra's algorithm implementation
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main web interface
└── README.md             # This file
```

## Usage Guide

### Finding a Route
1. Open the application in your web browser
2. Select a starting building from the "From" dropdown
3. Select a destination building from the "To" dropdown
4. Click "Find Route" button
5. View the calculated route on the map and route details in the sidebar

### Interactive Map Features
- Click on building markers to see information
- Use "Set as Start" or "Set as End" buttons in popups to quickly select buildings
- Click "Show Campus Overview" to see all buildings and paths

## Customization

### Adding New Buildings
1. Edit `campus_data.py`
2. Add new building entries to the `BUILDINGS` dictionary
3. Update the `campus_paths` list to connect new buildings to the graph
4. Restart the application

### Modifying Campus Layout
1. Update coordinates in `BUILDINGS` dictionary
2. Adjust paths in the `create_campus_graph()` function
3. Add or remove intersections as needed

### UI Customization
1. Modify CSS styles in `templates/index.html`
2. Update colors, fonts, and layout as desired
3. Add new interactive features in the JavaScript section

## Algorithm Details

### Dijkstra's Algorithm Implementation
- **Time Complexity:** O((V + E) log V) where V is vertices and E is edges
- **Space Complexity:** O(V) for storing distances and previous nodes
- **Optimized:** Uses priority queue (heapq) for efficient node selection

### Distance Calculation
- Uses Haversine formula for accurate GPS coordinate distance calculation
- Accounts for Earth's curvature
- Returns distances in meters for precise navigation

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Kill process using port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

**Module Import Errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Map Not Loading:**
- Check internet connection (required for map tiles)
- Verify JavaScript console for errors
- Ensure Flask server is running

## Performance Notes

- Application supports up to 1000+ buildings with proper optimization
- Graph algorithms scale well with campus size
- Frontend caches building data for improved performance
- Map rendering is optimized for smooth user experience

## Future Enhancements

- [ ] Real-time traffic/crowding data integration
- [ ] Multiple route options (shortest vs fastest)
- [ ] Indoor navigation for large buildings
- [ ] Mobile app version
- [ ] User preferences and saved routes
- [ ] Accessibility features for disabled users
- [ ] Integration with campus events and schedules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Contact

For questions or support, please contact the development team.

---

**Developed with ❤️ for campus navigation**
