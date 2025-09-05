# Campus Navigation System - Admin Features

## 🚀 New Features Added

### 📍 **Bounded Map View (2km Square)**
- Map is now restricted to a configurable 2km × 2km area around your specified center coordinates
- No more scrolling around the entire world map
- Campus boundaries are clearly marked with an orange rectangle
- All new buildings must be placed within the campus boundaries

### 🔐 **Admin Authentication System**
- Secure admin panel with password protection
- Session-based authentication with configurable timeout (24 hours default)
- Protected coordinate editor that only admins can access

### 🏗️ **Interactive Coordinate Editor**
- **Click-to-place**: Click anywhere on the map to set building coordinates
- **Visual feedback**: Red marker shows exactly where you clicked
- **Boundary validation**: System prevents placing buildings outside campus bounds
- **Real-time updates**: Changes are immediately saved and reflected in the pathfinding system

### 📊 **Dynamic Configuration Management**
- All campus data is now stored in `campus_config.json`
- Buildings, intersections, and paths are dynamically loaded
- Changes are automatically saved and applied without server restart

## 🎯 **How to Use the Admin Features**

### **Step 1: Access Admin Panel**
1. Navigate to `http://localhost:5000`
2. Click the "Admin Panel" button in the top-right corner
3. **Default Password**: `campus_admin_2024`

### **Step 2: Configure Your Campus Center**
Edit the `campus_config.json` file to set your campus center:

```json
{
  "map_settings": {
    "center_coordinates": [YOUR_LATITUDE, YOUR_LONGITUDE],
    "map_bounds_km": 2.0,
    "zoom_level": 16
  }
}
```

### **Step 3: Add Buildings Using the Coordinate Editor**

#### **Method 1: Click on Map**
1. In the admin panel, simply click on the map where you want to place a building
2. The coordinates will automatically fill in the form
3. Add building name, type, and description
4. Click "Save Building"

#### **Method 2: Manual Entry**
1. Enter coordinates manually in the Latitude/Longitude fields
2. Complete the building information
3. Click "Save Building"

### **Step 4: Edit Existing Buildings**
1. In the "Existing Buildings" list, click the yellow edit button
2. The form will populate with the building's current information
3. Click on the map or modify fields as needed
4. Click "Save Building" to update

### **Step 5: Delete Buildings**
1. Click the red delete button next to any building
2. Confirm the deletion
3. The building will be removed from the pathfinding system

## 🗺️ **Map Configuration Options**

### **Center Coordinates**
Replace `[40.7831, -73.9712]` with your campus center coordinates:
- Get coordinates from Google Maps by right-clicking and selecting the coordinate
- Format: `[latitude, longitude]`

### **Boundary Size**
- Default: 2km × 2km square
- Modify `map_bounds_km` in the config file to change size
- Recommended: 1-5km depending on campus size

### **Example Configurations**

#### **Small Campus (1km)**
```json
"map_settings": {
  "center_coordinates": [40.7831, -73.9712],
  "map_bounds_km": 1.0,
  "zoom_level": 17
}
```

#### **Large Campus (4km)**
```json
"map_settings": {
  "center_coordinates": [40.7831, -73.9712],
  "map_bounds_km": 4.0,
  "zoom_level": 15
}
```

## 🛡️ **Security Features**

### **Password Protection**
- Admin panel is password-protected
- Sessions expire after 24 hours (configurable)
- No access to coordinate editing without authentication

### **Boundary Validation**
- All new buildings must be within the campus bounds
- System prevents accidental placement outside the campus area
- Clear error messages for invalid coordinates

### **Data Integrity**
- Automatic backup of configuration data
- Changes are validated before saving
- Graph is automatically rebuilt after changes

## 📋 **Building Types Available**
- **Academic**: Classrooms, libraries, labs
- **Residential**: Dormitories, student housing
- **Dining**: Cafeterias, food courts
- **Recreation**: Gyms, sports facilities
- **Student Services**: Student centers, health services
- **Administration**: Administrative offices
- **General**: Any other building type

## 🚨 **Important Notes**

### **Admin Password**
- **Default**: `campus_admin_2024`
- Change it in `campus_config.json`:
```json
"admin_settings": {
  "admin_password": "YOUR_SECURE_PASSWORD",
  "session_timeout_hours": 24
}
```

### **Coordinates Format**
- Use decimal degrees (e.g., 40.7831, -73.9712)
- Positive latitude = North, Negative = South
- Positive longitude = East, Negative = West

### **Campus Bounds**
- Buildings outside the 2km square will be rejected
- Adjust `map_bounds_km` if you need a larger area
- The orange rectangle on the admin map shows the boundaries

## 🔄 **System Updates**

The pathfinding system automatically updates when you:
- Add new buildings
- Edit building locations
- Delete buildings
- Modify the configuration file

No server restart required for most changes!

## 🎉 **Ready to Use!**

Your campus navigation system now has:
- ✅ Bounded 2km square map view
- ✅ Admin authentication system
- ✅ Interactive coordinate editor
- ✅ Click-to-place building functionality  
- ✅ Automatic boundary validation
- ✅ Dynamic configuration management
- ✅ Real-time pathfinding updates

**Start by setting your campus center coordinates and begin adding your buildings!**
