import math

def get_angle(cx, cy, px, py):
    angle = math.degrees(math.atan2(py - cy, px - cx))
    angle = (angle + 360) % 360
    return angle

def get_direction(angle, divisions, compass_rotation=0):
    step = 360 / divisions
    adjusted_angle = (angle - compass_rotation + 360) % 360

    if divisions == 8:
        labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    elif divisions == 16:
        labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    elif divisions == 32:
        labels = [
            "N4", "N5", "N6", "N7", "N8", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8",
            "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
            "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8",
            "N1", "N2", "N3"
        ]
    else:
        labels = [f"D{i}" for i in range(divisions)]

    index = int(adjusted_angle // step)
    return labels[index % len(labels)]

def calculate_directional_areas(points, center, divisions, compass_rotation=0): 
    cx, cy = center
    counts = {}

    for px, py in points:
        angle = get_angle(cx, cy, px, py)
        dir_name = get_direction(angle, divisions, compass_rotation)
        counts[dir_name] = counts.get(dir_name, 0) + 1

    # ⬇️ Extra Calculations
    values = list(counts.values())
    total_area = sum(values)
    num_zones = len(values)
    avg_area = total_area / num_zones if num_zones else 0
    max_area = max(values) if values else 0
    min_area = min(values) if values else 0

    max_line = (avg_area + max_area) / 2
    min_line = (avg_area + min_area) / 2

    # ✅ Print everything in backend console
    print("\n📦 Direction-wise Area Count:")
    for direction, count in counts.items():
        print(f"{direction}: {count}")

    print(f"\n📊 Summary:")
    print(f"TOTAL AREA: {total_area}")
    print(f"NO. OF ZONES: {num_zones}")
    print(f"AVG AREA: {avg_area:.2f}")
    print(f"MAX LINE OF BALANCE: {max_line:.2f}")
    print(f"MIN LINE OF BALANCE: {min_line:.2f}")

    return counts
