import json
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
import numpy as np
from collections import deque

# Load the input JSON file
with open("./floor_plan_input.json") as f:
    data = json.load(f)


walls = []
rooms = []
interior_doors = []
exterior_doors = []


for item in data:
    if item['objectType'] == 'wall':
        walls.append(item)
    elif item['objectType'] == 'room':
        rooms.append(item)
    elif item['objectType'] == 'door':
        if item['isExit']:
            exterior_doors.append(item)
        else:
            interior_doors.append(item)


wall_polygons = [Polygon(wall['boundary']) for wall in walls]
room_polygons = [Polygon(room['boundary']) for room in rooms]
corridor_polygons = [Polygon(room['boundary']) for room in rooms if room.get("name") == "CORRIDOR"]


min_x = min(min(wall['boundary'], key=lambda p: p[0])[0] for wall in walls)
min_y = min(min(wall['boundary'], key=lambda p: p[1])[1] for wall in walls)
max_x = max(max(wall['boundary'], key=lambda p: p[0])[0] for wall in walls)
max_y = max(max(wall['boundary'], key=lambda p: p[1])[1] for wall in walls)

print(f"Bounds: min_x={min_x}, min_y={min_y}, max_x={max_x}, max_y={max_y}")

grid_size = 1.0
grid_width = int((max_x - min_x) / grid_size) + 1
grid_height = int((max_y - min_y) / grid_size) + 1

grid = np.ones((grid_width, grid_height), dtype=np.int8)


def mark_corridors(polygons):
    for polygon in polygons:
        min_x_poly, min_y_poly, max_x_poly, max_y_poly = polygon.bounds
        for x in np.arange(min_x_poly, max_x_poly, grid_size):
            for y in np.arange(min_y_poly, max_y_poly, grid_size):
                point = Point(x, y)
                if polygon.contains(point):
                    grid_x = int((x - min_x) / grid_size)
                    grid_y = int((y - min_y) / grid_size)
                    if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                        grid[grid_x, grid_y] = 0

mark_corridors(corridor_polygons)

def is_cell_valid(x, y):
    valid = (0 <= x < grid_width and 0 <= y < grid_height and grid[x, y] == 0)
    return valid


def find_nearest_exit(door, exterior_doors):
    min_distance = float('inf')
    nearest_exit = None
    
    for exit_door in exterior_doors:
        door_point = Point(door['centerLine'][0])
        exit_point = Point(exit_door['centerLine'][0])
        distance = door_point.distance(exit_point)
        
        if distance < min_distance:
            min_distance = distance
            nearest_exit = exit_door
    
    return nearest_exit

# BFS
def find_path(start, end, step_size=0.00005):
    directions = [(step_size, 0), (-step_size, 0), (0, step_size), (0, -step_size)]
    queue = deque([(start, [])])
    visited = set()

    
    while queue:
        current_point, path = queue.popleft()
        current_x, current_y = int((current_point[0] - min_x) / grid_size), int((current_point[1] - min_y) / grid_size)
    
        
        sorted_directions = sorted(directions, key=lambda d: abs(current_point[0] + d[0] - end[0]) + abs(current_point[1] + d[1] - end[1]))
        
        for direction in sorted_directions:
            next_point = (current_point[0] + direction[0], current_point[1] + direction[1])
            next_x, next_y = int((next_point[0] - min_x) / grid_size), int((next_point[1] - min_y) / grid_size)
            
            if is_cell_valid(next_x, next_y) and (next_x, next_y) not in visited:
                new_path = path + [next_point]
                
                if (direction[0] != 0 and (current_point[0] - end[0]) * (next_point[0] - end[0]) < 0) or (direction[1] != 0 and (current_point[1] - end[1]) * (next_point[1] - end[1]) < 0):
                    new_path.append(end)
                    print(f"Path found: {new_path}")
                    return new_path
                
                visited.add((next_x, next_y))
                queue.append((next_point, new_path))
    
    return path


def calculate_center_point(door):
    x1, y1 = door['centerLine'][0]
    x2, y2 = door['centerLine'][1]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


paths = []
for door in interior_doors:
    nearest_exit = find_nearest_exit(door, exterior_doors)
    
    if nearest_exit:
        start = calculate_center_point(door)
        end = calculate_center_point(nearest_exit)
        
        path = find_path(start, end, step_size=1)
        paths.append(path)


def plot_paths(walls, rooms, doors, paths):
    fig, ax = plt.subplots()

    for obj in data:
        if obj["objectType"] == "wall":
            # Draw the wall boundary
            boundary = obj["boundary"]
            ax.fill(*zip(*boundary), facecolor="black", alpha=0.5)
        elif obj["objectType"] == "room":
            # Draw the room boundary
            boundary = obj["boundary"]
            if obj.get("name") == "CORRIDOR":
                ax.fill(*zip(*boundary), facecolor="blue", alpha=0.1)
            else:
                ax.fill(*zip(*boundary), facecolor="lightgray")
        elif obj["objectType"] == "door":
            # Draw the door center line
            center_line = obj["centerLine"]
            # draw line here with extra thickness
            if obj.get("isExit"):
                ax.plot(*zip(*center_line), color="red", linewidth=2)
            else:
                ax.plot(*zip(*center_line), color="darkblue", linewidth=2)

    for path in paths:
        if path:
            x, y = zip(*path)
            ax.plot(x, y, color='green', linestyle='dashed')

    # Set the aspect ratio to be equal
    ax.set_aspect("equal", adjustable="box")
    
    plt.show()

plot_paths(walls, rooms, interior_doors + exterior_doors, paths)
