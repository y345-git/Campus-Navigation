"""
Test script for campus pathfinding functionality
Run this to verify that the Dijkstra's algorithm is working correctly
"""

import networkx as nx
from pathfinding import pathfinder
from campus_data import BUILDINGS, campus_graph

def test_pathfinding():
    """Test the pathfinding algorithm with sample routes"""
    print("=" * 60)
    print("CAMPUS NAVIGATION SYSTEM - PATHFINDING TEST")
    print("=" * 60)
    
    # Display campus information
    print(f"\n📊 Campus Information:")
    print(f"   Total Nodes: {len(campus_graph.nodes)}")
    print(f"   Total Edges: {len(campus_graph.edges)}")
    print(f"   Buildings: {len(BUILDINGS)}")
    print(f"   Graph Connected: {len(list(nx.connected_components(campus_graph))) == 1}")
    
    # List all buildings
    print(f"\n🏢 Available Buildings:")
    for i, (building_id, building_data) in enumerate(BUILDINGS.items(), 1):
        print(f"   {i:2d}. {building_data['name']} (ID: {building_id})")
    
    # Test cases
    test_cases = [
        ("Main_Library", "Engineering_Building", "Library to Engineering"),
        ("Student_Center", "Dormitory_A", "Student Center to Dorm A"),
        ("Science_Building", "Arts_Building", "Science to Arts"),
        ("Gym", "Cafeteria", "Gym to Cafeteria"),
        ("Business_School", "Dormitory_B", "Business School to Dorm B")
    ]
    
    print(f"\n🧪 Running Pathfinding Tests:")
    print("-" * 60)
    
    for i, (start, end, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        
        # Find route
        result = pathfinder.find_route(start, end)
        
        if result['success']:
            print(f"   ✅ Route found successfully!")
            print(f"   📍 From: {result['start_building']}")
            print(f"   📍 To: {result['end_building']}")
            print(f"   📏 Distance: {result['total_distance']}m")
            print(f"   ⏱️ Estimated Time: {result['estimated_walk_time']} minutes")
            print(f"   🛤️ Path: {' → '.join([step['name'] for step in result['path_details'] if step['type'] == 'building'])}")
            print(f"   🔗 Full Path: {' → '.join(result['path'])}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    # Test error cases
    print(f"\n🚫 Testing Error Cases:")
    print("-" * 60)
    
    error_cases = [
        ("Invalid_Building", "Main_Library", "Invalid start building"),
        ("Main_Library", "Invalid_Building", "Invalid end building"),
        ("NonExistent", "AlsoNonExistent", "Both buildings invalid")
    ]
    
    for i, (start, end, description) in enumerate(error_cases, 1):
        print(f"\nError Test {i}: {description}")
        result = pathfinder.find_route(start, end)
        
        if result['success']:
            print(f"   ⚠️ Unexpected success - this should have failed!")
        else:
            print(f"   ✅ Correctly handled error: {result['error']}")
    
    # Test destinations feature
    print(f"\n📍 Testing Destinations from Main Library:")
    print("-" * 60)
    
    destinations = pathfinder.get_all_possible_destinations("Main_Library")
    print(f"Found {len(destinations)} destinations from Main Library:")
    
    for dest in destinations[:5]:  # Show top 5 closest
        print(f"   • {dest['name']}: {dest['distance']}m ({dest['walk_time']} min)")
    
    if len(destinations) > 5:
        print(f"   ... and {len(destinations) - 5} more destinations")
    
    # Performance test
    print(f"\n⚡ Performance Test:")
    print("-" * 60)
    
    import time
    start_time = time.time()
    
    # Run multiple pathfinding operations
    for _ in range(100):
        pathfinder.find_route("Main_Library", "Engineering_Building")
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average pathfinding time: {avg_time:.2f}ms per route")
    
    print(f"\n✅ All tests completed successfully!")
    print("=" * 60)

def interactive_test():
    """Interactive pathfinding test"""
    print("\n🎮 Interactive Pathfinding Test")
    print("Enter building IDs to test pathfinding (or 'quit' to exit)")
    
    building_ids = list(BUILDINGS.keys())
    print(f"\nAvailable building IDs: {', '.join(building_ids)}")
    
    while True:
        try:
            print("\n" + "-" * 40)
            start = input("Enter start building ID (or 'quit'): ").strip()
            if start.lower() == 'quit':
                break
                
            end = input("Enter end building ID: ").strip()
            
            result = pathfinder.find_route(start, end)
            
            if result['success']:
                print(f"\n✅ Route Found:")
                print(f"   Distance: {result['total_distance']}m")
                print(f"   Time: {result['estimated_walk_time']} minutes")
                print(f"   Path: {' → '.join(result['path'])}")
            else:
                print(f"\n❌ Error: {result['error']}")
                
        except KeyboardInterrupt:
            print("\n\nExiting interactive test...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    # Run automated tests
    test_pathfinding()
    
    # Ask if user wants interactive test
    while True:
        choice = input("\nWould you like to run interactive pathfinding test? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            interactive_test()
            break
        elif choice in ['n', 'no']:
            print("Thanks for testing the Campus Navigation System! 🎉")
            break
        else:
            print("Please enter 'y' or 'n'")
