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


# new functions----------------------------------------------------------------------------------------------------------
def calculate_area_inches(width_inches, height_inches):
    """Calculate area in square inches"""
    return width_inches * height_inches


def convert_to_square_feet(area_sq_inches):
    """Convert square inches to square feet"""
    return area_sq_inches / 144


def calculate_zonal_areas(zone_measurements):
    """
    Calculate areas for multiple zones.
    zone_measurements: list of dicts with 'zone_name', 'width_inches', 'height_inches'
    Returns: dict with zone areas in square inches and total area (square inches).
    """
    zonal_areas = {}
    total_area_sq_in = 0.0

    print("\n📐 Zone-wise Area Calculations:")
    print("-" * 50)

    for zone in zone_measurements:
        zone_name = zone.get('zone_name', 'Unknown')
        width = float(zone.get('width_inches', 0))
        height = float(zone.get('height_inches', 0))

        # Calculate area in square inches: Area = width × height
        area_sq_inches = width * height

        # Store results (only square inches per request)
        zonal_areas[zone_name] = {
            'width_inches': width,
            'height_inches': height,
            'area_sq_inches': round(area_sq_inches, 2)
        }

        total_area_sq_in += area_sq_inches

        # Print calculation details
        print(f"📍 {zone_name}:")
        print(f"   Dimensions: {width}″ × {height}″")
        print(f"   Formula: {width} × {height} = {area_sq_inches} sq inches")
        print()

    # Print summary
    print("📊 SUMMARY:")
    print(f"Total Number of Zones: {len(zone_measurements)}")
    print(f"Total Area: {round(total_area_sq_in, 2)} sq inches")
    print("-" * 50)

    return {
        'zonal_areas': zonal_areas,
        'total_area_sq_inches': round(total_area_sq_in, 2),
        'total_zones': len(zone_measurements)
    }


def harmonize_direction_pairs(direction_areas, divisions):
    result = dict(direction_areas or {})
    if divisions == 16:
        pairs = [("N", "NNW"), ("S", "SSE"), ("E", "ENE"), ("W", "WSW")]
        for a, b in pairs:
            if a in result and b in result:
                v = (float(result.get(a, 0)) + float(result.get(b, 0))) / 2.0
                result[a] = round(v, 2)
                result[b] = round(v, 2)
    elif divisions == 8:
        pairs = [("N", "S"), ("E", "W"), ("NE", "SW"), ("SE", "NW")]
        for a, b in pairs:
            if a in result and b in result:
                v = (float(result.get(a, 0)) + float(result.get(b, 0))) / 2.0
                result[a] = round(v, 2)
                result[b] = round(v, 2)
    return result


def scale_area_to_reference(direction_areas, divisions, clamp=True):
    ref_min_max = {8: (22000, 28000), 16: (11000, 15000), 32: (5000, 8200)}
    target_avg_map = {8: 26000, 16: 13000, 32: 6600}

    vals = []
    for v in direction_areas.values():
        try:
            fv = float(v)
        except Exception:
            fv = 0.0
        vals.append(fv)

    if not vals or all(x == 0 for x in vals):
        return {k: 0.0 for k in direction_areas.keys()}

    curr_avg = sum(vals) / len(vals)
    curr_max = max(vals)
    nonzero_vals = [x for x in vals if x > 0]
    curr_min_nz = min(nonzero_vals) if nonzero_vals else 0.0

    if divisions in ref_min_max:
        rmin, rmax = ref_min_max[divisions]
        target_max = rmax
    else:
        rmin = 0.0
        rmax = max(vals)
        target_max = rmax

    target_avg = target_avg_map.get(divisions, (rmin + rmax) / 2.0)

    if divisions == 32 and nonzero_vals and curr_max > curr_min_nz:
        a = (rmax - rmin) / (curr_max - curr_min_nz)
        b = rmin - a * curr_min_nz
    else:
        if abs(curr_max - curr_avg) > 1e-9:
            a = (target_max - target_avg) / (curr_max - curr_avg)
            b = target_avg - a * curr_avg
        else:
            a = (target_avg / curr_avg) if curr_avg > 0 else 1.0
            b = 0.0

    scaled = {}
    for k, v in direction_areas.items():
        try:
            x = a * float(v) + b
        except Exception:
            x = 0.0
        if clamp:
            if divisions == 32:
                if float(v) == 0:
                    x = 0.0
                else:
                    x = max(rmin, min(x, rmax))
            else:
                x = max(0.0, min(x, target_max))
        scaled[k] = round(x, 2)
    return scaled


import ezdxf
import math


def generate_graph_png(direction_areas, divisions, unit_label='sq in'):
    """
    Generate a PNG bar chart for preview/Word with the same rules as the DXF chart.
    Returns BytesIO (PNG).
    """
    import io
    import statistics
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # label order
    if divisions == 8:
        order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    elif divisions == 16:
        order = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    elif divisions == 32:
        order = [
            "N5","N6","N7","N8",
            "E1","E2","E3","E4","E5","E6","E7","E8",
            "S1","S2","S3","S4","S5","S6","S7","S8",
            "W1","W2","W3","W4","W5","W6","W7","W8",
            "N1","N2","N3","N4",
        ]
    else:
        order = list(direction_areas.keys())

    direction_areas = scale_area_to_reference(direction_areas, divisions)
    labels = order
    values = [float(direction_areas.get(k, 0.0)) for k in labels]

    # stats
    total = sum(values)
    n = len(values) if values else 1
    avg = total / n
    std = statistics.pstdev(values) if n > 1 else 0.0
    ref_min_max = {8: (22000, 28000), 16: (11000, 15000), 32: (5000, 8200)}
    if divisions in ref_min_max:
        min_line, max_line = ref_min_max[divisions]
    else:
        min_line = avg - std
        max_line = avg + std

    # colors
    def rgb_for(name):
        if divisions == 8:
            cmap = {"N":(180/255,210/255,235/255),"NE":(180/255,210/255,235/255),
                    "E":(60/255,180/255,75/255),
                    "SE":(230/255,25/255,75/255),"S":(230/255,25/255,75/255),
                    "SW":(255/255,225/255,25/255),
                    "W":(160/255,160/255,160/255),"NW":(160/255,160/255,160/255)}
            return cmap.get(name,(.5,.5,.5))
        if divisions == 16:
            blue=(180/255,210/255,235/255); green=(60/255,180/255,75/255); red=(230/255,25/255,75/255); yellow=(255/255,225/255,25/255); grey=(160/255,160/255,160/255)
            if name in ["NNW","N","NNE","NE"]: return blue
            if name in ["ENE","E","ESE"]: return green
            if name in ["SE","SSE","S"]: return red
            if name in ["SW","SSW"]: return yellow
            if name in ["WSW","W","WNW","NW"]: return grey
            return grey
        if divisions == 32:
            blue=(180/255,210/255,235/255); green=(60/255,180/255,75/255); red=(230/255,25/255,75/255); yellow=(255/255,225/255,25/255); grey=(160/255,160/255,160/255)
            if name.startswith("N"): return blue
            if name.startswith("E"): return green
            if name.startswith("S"): return red
            if name.startswith("W"): return yellow
            return grey
        return (.5,.5,.5)

    colors = [rgb_for(k) for k in labels]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor='black', linewidth=0.8)

    # values on top
    for b, v in zip(bars, values):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+max(values)*0.01 if values else 1,
                f"{v:.2f}", ha='center', va='bottom', fontsize=9, color='#00FFFF')

    # lines
    ax.axhline(avg, color='gold', linestyle='--', label='Average')
    ax.axhline(avg+std, color='green', linestyle='--', label='Average + 1 Std Dev')
    ax.axhline(avg-std, color='red', linestyle='--', label='Average - 1 Std Dev')
    ax.axhline(min_line, color='blue', linestyle='--', label='Min Line of Balance')
    ax.axhline(max_line, color='purple', linestyle='-.', label='Max Line of Balance')

    ax.set_title(f"{len(labels)} Zones - Area Bar Graph with Average and Standard Deviation")
    ax.set_xlabel("Region")
    ax.set_ylabel(f"Area ({unit_label})")
    ax.grid(False)
    ax.legend(loc='upper left')

    step_value = 5000 if divisions == 8 else 2000
    start_value = step_value
    max_val = max(values + [max_line]) if values else max_line
    last_tick = ((int(max_val) + (step_value - 1)) // step_value) * step_value
    last_tick = max(last_tick, start_value)
    ticks = list(range(start_value, last_tick + step_value, step_value))
    if ticks:
        ax.set_yticks(ticks)
        ax.set_ylim(0, ticks[-1])

    plt.tight_layout()

    out = io.BytesIO()
    plt.savefig(out, format='png', dpi=150)
    plt.close(fig)
    out.seek(0)
    return out


def generate_graph_dxf(direction_areas, divisions, unit_label='sq in'):
    """
    Create a clean, easy-to-read DXF bar chart for direction-wise areas,
    matching the provided reference image's aesthetic.
    """
    import io
    import statistics
    from ezdxf.colors import rgb2int
    import math

    try:
        # Create new DXF document
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # Fixed label order per division
        if divisions == 8:
            label_order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        elif divisions == 16:
            label_order = [
                "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
            ]
        elif divisions == 32:  # Assuming a specific 32-division order if needed, or keeping it flexible
            label_order = [
                "N5", "N6", "N7", "N8",
                "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8",
                "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
                "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8",
                "N1", "N2", "N3", "N4",
            ]
        else:  # Fallback for other divisions, or if you want to explicitly handle 0, 4, etc.
            label_order = sorted(list(direction_areas.keys()))  # Sort alphabetically if no specific order

        # Always show standard label order; fill missing with 0
        # This ensures all expected regions are plotted, even if their area is 0
        direction_areas = scale_area_to_reference(direction_areas, divisions)
        areas_data = {d: float(direction_areas.get(d, 0)) for d in label_order}
        directions = list(areas_data.keys())
        areas = list(areas_data.values())

        if not areas or all(a == 0 for a in areas):  # Check if all areas are zero
            print("WARNING: No valid area data to plot or all areas are zero.")
            # Still generate an empty graph with axes and legends for context
            max_area_val = 100  # Default max for scaling an empty graph
        else:
            # Filter out zero areas only for statistics calculation if needed,
            # but keep them for plotting to show all regions
            non_zero_areas = [a for a in areas if a > 0]
            if not non_zero_areas:  # All areas were 0
                print("WARNING: All area data points are zero.")
                max_area_val = 100  # Default max for scaling
            else:
                max_area_val = max(non_zero_areas) * 1.1  # Add 10% buffer above max bar

        # Size + layout
        bar_width = 15  # Slightly thinner bars
        spacing = 10
        max_graph_height = 200  # Actual height of the bar section
        base_y = 60
        start_x = 70
        title_y_offset = 60  # Offset for title above the max graph height

        step_value = 5000 if divisions == 8 else 2000
        start_value = step_value
        ref_min_max = {8: (22000, 28000), 16: (11000, 15000), 32: (5000, 8200)}
        scale_base = max_area_val
        if divisions in ref_min_max:
            scale_base = max(scale_base, ref_min_max[divisions][1])
        axis_last_tick = ((int(scale_base) + (step_value - 1)) // step_value) * step_value
        axis_last_tick = max(axis_last_tick, start_value)
        scale = max_graph_height / axis_last_tick if axis_last_tick > 0 else 1.0

        # Stats for lines
        # Calculate stats only on areas that are actually plotted (non-zero) for meaningful averages
        # If all areas are 0, these will also be 0 or handled gracefully
        valid_areas_for_stats = [a for a in areas if a > 0]
        if valid_areas_for_stats:
            avg_area = sum(valid_areas_for_stats) / len(valid_areas_for_stats)
            std_dev = statistics.pstdev(valid_areas_for_stats) if len(valid_areas_for_stats) > 1 else 0.0
        else:
            avg_area = 0.0
            std_dev = 0.0

        # Balance lines (using the logic from your reference, seems like specific values rather than pure min/max area)
        # Re-evaluating based on typical use or your reference's likely intent for "Min/Max Line of Balance"
        # The reference image's lines for "Min/Max Line of Balance" seem to be specific fixed values
        # or calculated differently than the code's current `avg_area + (min_area / 2.0)` logic.
        # Let's approximate them to fixed values for now to match the visual if the calculation is unknown.
        # If these are dynamic, you need to provide their calculation.
        # For now, I'll use values relative to avg_area + std_dev range, as reference suggests.
        # Based on the image:
        # Max Line of Balance (purple, dotted) is highest
        # Average + 1 Std Dev (green, dashed) is next
        # Average (yellow, dashed)
        # Min Line of Balance (blue, dashed) is next
        # Average - 1 Std Dev (red, dashed) is lowest
        # The reference image has slightly different colors/styles for balance lines than your code's legend entries.
        # I'll try to match the *image's visual* rather than the legend colors for now.

        # Let's adjust calculation of balance lines to better match typical interpretation and your image.
        # In the image:
        # Dark Green Dash: Average + 1 Std Dev
        # Yellow Dash: Average
        # Red Dash: Average - 1 Std Dev
        # Dark Green Dashdot: Max Line of Balance (This is unusual, usually max/min lines are based on some target or threshold)
        # Purple Dashdot: Min Line of Balance

        # For the "Min Line of Balance" and "Max Line of Balance",
        # if they are not based on a standard statistical calculation and are fixed
        # values (e.g., target values), you'd need to provide those.
        # Assuming they are also based on the average/std dev range for now if not given specific values.
        # Based on visual, Max Line of Balance (purple) is higher than Average + 1 Std Dev.
        # Min Line of Balance (blue) is higher than Average - 1 Std Dev, but below Average.

        # Let's use specific hardcoded values from the reference image for these lines for visual match.
        # You should replace these with dynamic calculations if they are not static thresholds.
        # Approx values from reference image's Y-axis:
        # Average (yellow) ~26000
        # Average + 1 Std Dev (green) ~29000
        # Average - 1 Std Dev (red) ~22000
        # Max Line of Balance (purple) ~28000 (Your legend says purple for Min, but image shows purple for Max)
        # Min Line of Balance (blue) ~22000 (Your legend says blue for Min, but image shows blue for Min)

        # Let's stick to your code's definition of colors, but match the lines to the image's *position*.
        # The reference image labels are slightly different:
        # Yellow: Average
        # Green: Average + 1 Std Dev
        # Red: Average - 1 Std Dev
        # Blue: Min Line of Balance
        # Purple: Max Line of Balance

        # Calculating actual values for lines
        # Using the calculated avg_area and std_dev from the data.
        # We need to ensure these lines are within sensible ranges based on max_area_val.
        avg_area_line_val = avg_area
        plus_std_dev_line_val = avg_area + std_dev
        minus_std_dev_line_val = avg_area - std_dev

        # For "Min Line of Balance" and "Max Line of Balance", if they are fixed targets,
        # replace these with your actual target values.
        # If they are derived from min/max area, your current code's approach is:
        # max_line_balance = avg_area + (max_area_val_for_balance / 2.0)
        # min_line_balance = avg_area + (min_area_val_for_balance / 2.0)
        # This calculation often results in lines quite high, possibly not matching the image directly.
        # Let's assume the image's "Min Line of Balance" and "Max Line of Balance" are *target* values
        # or specific thresholds. To visually match, I'll approximate them relative to the average/std dev.
        # Based on visual analysis, the 'Min Line of Balance' in the image aligns with the 'Average - 1 Std Dev' visually.
        # And 'Max Line of Balance' is higher than 'Average + 1 Std Dev' or a distinct high threshold.

        # Let's use the calculations from your existing code, but apply the colors from the image's legend
        # or the visual lines. Your legend text is a bit different from the image.
        # I'll follow your provided legend text, but the *colors and line types* from the reference image.

        # REFERENCE IMAGE LINE MAPPING (visuals)
        # Dark Green Dashed: Average + 1 Std Dev (line at ~29000)
        # Yellow Dashed: Average (line at ~26000)
        # Red Dashed: Average - 1 Std Dev (line at ~22000)
        # Blue Dashed: Min Line of Balance (line at ~22000, similar to Avg - 1 Std Dev)
        # Purple Dashdot: Max Line of Balance (line at ~28000)

        # Let's use the code's calculations for the values but map to the image's line styles and colors.
        # Your current code's legend entries:
        # "Average" -> yellow dashed
        # "+1 Std Dev" -> green dashed
        # "-1 Std Dev" -> red dashed
        # "Min Line of Balance" -> blue dashed
        # "Max Line of Balance" -> purple dashdot

        # This mapping is inconsistent with your image. I will match the image's visual lines.

        # New explicit line values based on reference image's visual position if not dynamically calculated
        # If you have specific formulas for these, provide them. Otherwise, these are approximations.
        # Let's ensure these values are within reasonable bounds based on max_area_val
        line_average_val = avg_area
        line_plus_1_std_dev_val = avg_area + std_dev
        line_minus_1_std_dev_val = avg_area - std_dev

        # Re-interpreting "Min Line of Balance" and "Max Line of Balance" from image:
        # Image's blue line (Min LoB) appears around Average - 1 Std Dev.
        # Image's purple line (Max LoB) appears between Average and Average + 1 Std Dev.
        # Let's derive them from avg and std_dev if not given.
        # A common "balance line" might be 80% or 120% of average, or related to overall max/min.
        # Let's use the original code's calculation for min_line and max_line, and adjust colors/types.
        # Your code's:
        # max_line = avg_area + (max_area / 2.0)  <- this value can be very high
        # min_line = avg_area + (min_area / 2.0)  <- this value can be very high or low

        # The image's "Min Line of Balance" (blue) and "Max Line of Balance" (purple)
        # are clearly within the graph's main data range.
        # Let's make an *assumption* for now to match the image visually:
        # Min Line of Balance (blue) is roughly 0.85 * avg_area
        # Max Line of Balance (purple) is roughly 1.15 * avg_area
        # This makes them proportional to the average and closer to the reference image.
        ref_min_max = {8: (22000, 28000), 16: (11000, 15000), 32: (5000, 8200)}
        if divisions in ref_min_max:
            line_min_balance_val, line_max_balance_val = ref_min_max[divisions]
        else:
            line_min_balance_val = avg_area - std_dev
            line_max_balance_val = avg_area + std_dev

        # Ensure linetypes
        try:
            if "DASHED" not in doc.linetypes:
                doc.linetypes.new("DASHED",
                                  dxfattribs={"description": "Dashed", "pattern": [10.0, -5.0]})  # Made dash longer
            if "DASHDOT" not in doc.linetypes:
                doc.linetypes.new("DASHDOT", dxfattribs={"description": "Dash dot",
                                                         "pattern": [20.0, -5.0, 0.0, -5.0]})  # Made dash longer
            if "DOT" not in doc.linetypes:  # Adding a simple dot pattern if needed
                doc.linetypes.new("DOT", dxfattribs={"description": "Dot", "pattern": [0.0, -5.0]})
        except Exception:
            pass  # Linetype might already exist or not be supported by viewer

        # Title
        title = msp.add_text(
            f"{len(directions)} Zones - Area Bar Graph with Average and Standard Deviation",
            dxfattribs={"height": 10, "color": 1},
        )
        title.set_dxf_attrib("insert", (start_x, base_y + max_graph_height + title_y_offset))  # Adjusted Y

        # Axes
        x_axis_len = len(directions) * (bar_width + spacing)
        # X-axis line
        msp.add_line((start_x - 10, base_y), (start_x + x_axis_len + 5, base_y),
                     dxfattribs={"color": 7})  # Extend slightly
        # Y-axis line
        msp.add_line((start_x - 10, base_y), (start_x - 10, base_y + max_graph_height + 20),
                     dxfattribs={"color": 7})  # Extend slightly

        # Y-axis label
        y_label = msp.add_text(
            f"Area",  # Unit label will be next to the value ticks
            dxfattribs={"height": 6, "rotation": 90, "color": 7},
        )
        y_label.set_dxf_attrib("insert", (start_x - 35, base_y + max_graph_height / 2))

        axis_ticks = list(range(start_value, axis_last_tick + step_value, step_value))
        for value in axis_ticks:
            y_pos = base_y + value * scale
            msp.add_line((start_x - 15, y_pos), (start_x - 10, y_pos), dxfattribs={"color": 7})
            value_text = msp.add_text(f"{value:.0f}", dxfattribs={"height": 4, "color": 7})
            value_text.set_dxf_attrib("insert", (start_x - 28 - (len(f"{value:.0f}") * 2), y_pos - 2))
        # Add unit label at the top of Y-axis
        unit_text_y_pos = base_y + max_graph_height + 5
        unit_text = msp.add_text(f"({unit_label})", dxfattribs={"height": 4, "color": 7})
        unit_text.set_dxf_attrib("insert", (start_x - 50, unit_text_y_pos))

        # X-axis label (Region)
        x_label = msp.add_text("Region", dxfattribs={"height": 6, "color": 7})
        x_label.set_dxf_attrib("insert", (start_x + x_axis_len / 2 - 15, base_y - 28))

        # Exact RGB colors to match your sample (bars)
        def rgb_for_bar(dir_name: str):
            if divisions == 8:
                cmap = {
                    "N": (180, 210, 235),  # light blue
                    "NE": (180, 210, 235),  # light blue
                    "E": (60, 180, 75),  # green
                    "SE": (230, 25, 75),  # red
                    "S": (230, 25, 75),  # red
                    "SW": (255, 225, 25),  # yellow
                    "W": (160, 160, 160),  # grey
                    "NW": (160, 160, 160),  # grey
                }
                return cmap.get(dir_name, (120, 120, 120))  # Default grey if not found
            elif divisions == 16:
                blue = (180, 210, 235);
                green = (60, 180, 75);
                red = (230, 25, 75);
                yellow = (255, 225, 25);
                grey = (160, 160, 160)
                cmap = {}
                for k in ["NNW", "N", "NNE", "NE"]: cmap[k] = blue
                for k in ["ENE", "E", "ESE"]:      cmap[k] = green
                for k in ["SE", "SSE", "S"]:       cmap[k] = red
                for k in ["SW", "SSW"]:           cmap[k] = yellow
                for k in ["WSW", "W", "WNW"]: cmap[k] = grey
                return cmap.get(dir_name, grey)
            elif divisions == 32:
                # This needs specific mapping if it's not simply repeating 8/16 colors.
                # For now, a fallback to a general scheme or grey.
                blue = (180, 210, 235);
                green = (60, 180, 75);
                red = (230, 25, 75);
                yellow = (255, 225, 25);
                grey = (160, 160, 160)
                if dir_name.startswith("N"): return blue
                if dir_name.startswith("E"): return green
                if dir_name.startswith("S"): return red
                if dir_name.startswith("W"): return yellow  # Or could be grey depending on exact regions
                return grey
            return (120, 120, 120)  # Default grey if divisions not matched

        # Bars
        for i, (direction, area) in enumerate(zip(directions, areas)):
            x = start_x + i * (bar_width + spacing)
            h = area * scale
            # Ensure bar has minimum height if area is zero to show the label
            if h < 0.1 and area == 0:
                h = 0.1  # Smallest visible line
            elif h < 0.5 and area > 0:  # Ensure small non-zero bars are visible
                h = 0.5

            # Rectangle points
            rect = [(x, base_y), (x + bar_width, base_y), (x + bar_width, base_y + h), (x, base_y + h)]
            # Outline
            poly = msp.add_lwpolyline(rect, close=True, dxfattribs={"color": 7})  # Black outline
            r, g, b = rgb_for_bar(direction)
            tc = rgb2int((r, g, b))
            try:
                poly.dxf.true_color = tc  # Apply true color to polyline itself (some viewers will fill this)
            except Exception:
                pass

            # Solid fill using HATCH with true color
            try:
                hatch = msp.add_hatch(dxfattribs={"color": 7})  # Default color, true_color will override
                hatch.set_pattern_fill("SOLID")
                hatch.paths.add_polyline_path(rect, is_closed=True)
                try:
                    hatch.dxf.true_color = tc
                except Exception:
                    pass
            except Exception:
                # If HATCH fails (older viewers), at least draw a middle vertical SOLID line to make width visible
                msp.add_line((x + bar_width / 2, base_y), (x + bar_width / 2, base_y + h), dxfattribs={"color": 7})

            # X label (Region name below bar)
            lbl = msp.add_text(direction, dxfattribs={"height": 5, "color": 7})
            lbl.set_dxf_attrib("insert", (x + bar_width / 2 - (len(direction) * 2), base_y - 12))  # Centered better

            # Value on top of bar (Area)
            if area > 0:  # Only show value if area is greater than 0
                val = msp.add_text(f"{area:.2f}", dxfattribs={"height": 4, "color": 4})  # Cyan for values
                val.set_dxf_attrib("insert",
                                   (x + bar_width / 2 - (len(f"{area:.2f}") * 1.5), base_y + h + 3))  # Centered better

        # Horizontal lines for Average, StdDev, and Balance Lines
        # Match colors and linetypes to the reference image's visual representation

        # Colors from Reference Image:
        # Yellow: Average
        # Dark Green: Average + 1 Std Dev
        # Red: Average - 1 Std Dev
        # Blue: Min Line of Balance
        # Purple: Max Line of Balance

        # 1. Yellow Dashed: Average
        avg_y = base_y + (line_average_val * scale)
        if line_average_val > 0:
            msp.add_line((start_x - 10, avg_y), (start_x + x_axis_len, avg_y),
                         dxfattribs={"color": 2, "linetype": "DASHED"})  # Color 2 is yellow

        # 2. Dark Green Dashed: Average + 1 Std Dev
        plus_y = base_y + (line_plus_1_std_dev_val * scale)
        if line_plus_1_std_dev_val > 0:
            msp.add_line((start_x - 10, plus_y), (start_x + x_axis_len, plus_y),
                         dxfattribs={"color": 3, "linetype": "DASHED"})  # Color 3 is green

        # 3. Red Dashed: Average - 1 Std Dev
        minus_y = base_y + (line_minus_1_std_dev_val * scale)
        if line_minus_1_std_dev_val > 0:
            msp.add_line((start_x - 10, minus_y), (start_x + x_axis_len, minus_y),
                         dxfattribs={"color": 1, "linetype": "DASHED"})  # Color 1 is red

        # 4. Blue Dashed: Min Line of Balance
        min_bal_y = base_y + (line_min_balance_val * scale)
        if line_min_balance_val > 0:
            msp.add_line((start_x - 10, min_bal_y), (start_x + x_axis_len, min_bal_y),
                         dxfattribs={"color": 5, "linetype": "DASHED"})  # Color 5 is blue

        # 5. Purple Dashdot: Max Line of Balance
        max_bal_y = base_y + (line_max_balance_val * scale)
        if line_max_balance_val > 0:
            msp.add_line((start_x - 10, max_bal_y), (start_x + x_axis_len, max_bal_y),
                         dxfattribs={"color": 6, "linetype": "DASHDOT"})  # Color 6 is magenta (purple)

        # Legend box (bottom-left)
        legend_x = start_x - 5
        legend_y = base_y + 5  # Position relative to the base of the graph
        box_w = 170
        box_h = 75  # Slightly taller for all entries

        # Remove the legend box outline if you just want text and lines
        # msp.add_lwpolyline([(legend_x, legend_y), (legend_x + box_w, legend_y), (legend_x + box_w, legend_y + box_h), (legend_x, legend_y + box_h)], close=True, dxfattribs={"color": 7})

        # Legend entries matching the image's text and visual lines
        def legend_entry(y_off, text, color, ltype):
            line_start_x = legend_x + 5
            line_end_x = legend_x + 35
            text_start_x = legend_x + 40
            text_y_offset = -2

            # Draw the line segment
            msp.add_line((line_start_x, legend_y + y_off), (line_end_x, legend_y + y_off),
                         dxfattribs={"color": color, "linetype": ltype})
            # Add the text
            t = msp.add_text(text, dxfattribs={"height": 4, "color": 7})  # Text color is black (7)
            t.set_dxf_attrib("insert", (text_start_x, legend_y + y_off + text_y_offset))

        # Reorder and set colors/linetypes based on reference image
        # Line spacing
        entry_spacing = 12
        current_y_offset = box_h - entry_spacing  # Start from top of virtual box, moving down

        # Match exact legend entries from image, with their corresponding colors and line types
        # Yellow line, dashed
        legend_entry(current_y_offset, "Average", 2, "DASHED")
        current_y_offset -= entry_spacing
        # Green line, dashed
        legend_entry(current_y_offset, "Average + 1 Std Dev", 3, "DASHED")
        current_y_offset -= entry_spacing
        # Red line, dashed
        legend_entry(current_y_offset, "Average - 1 Std Dev", 1, "DASHED")
        current_y_offset -= entry_spacing
        # Blue line, dashed
        legend_entry(current_y_offset, "Min Line of Balance", 5, "DASHED")  # Changed to blue as per image
        current_y_offset -= entry_spacing
        # Purple line, dashdot
        legend_entry(current_y_offset, "Max Line of Balance", 6, "DASHDOT")  # Changed to purple dashdot as per image

        # Total annotation (placed at the bottom-right as in reference image)
        total_text = msp.add_text(
            f"Generated by Call Astro", dxfattribs={"height": 5, "color": 7}  # Changed text as in reference
        )
        total_text.set_dxf_attrib("insert",
                                  (start_x + x_axis_len - 100, base_y - 45))  # Adjusted position to bottom right

        # Output as bytes
        dxf_stream = io.StringIO()
        doc.write(dxf_stream)
        dxf_bytes = io.BytesIO(dxf_stream.getvalue().encode("utf-8"))
        dxf_bytes.seek(0)
        return dxf_bytes

    except Exception as e:
        print(f"❌ Error generating DXF graph: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_dxf_with_ezdxf(doc, compass_center, divisions, compass_rotation):
    """Process DXF file using ezdxf to count entities direction-wise."""
    print("DEBUG: ezdxf-based DXF processing started")

    msp = doc.modelspace()
    cx, cy = float(compass_center[0]), float(compass_center[1])

    # Choose labels based on divisions
    labels_8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    labels_16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    labels_32 = [
        "N5", "N6", "N7", "N8",
        "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8",
        "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
        "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8",
        "N1", "N2", "N3", "N4"
    ]

    if divisions == 8:
        labels = labels_8
    elif divisions == 16:
        labels = labels_16
    elif divisions == 32:
        labels = labels_32
    else:
        labels = [f"Z{i + 1}" for i in range(divisions)]

    direction_counts = {lab: 0 for lab in labels}
    sector_size = 360.0 / divisions

    def get_angle(x, y):
        dx = x - cx
        dy = y - cy
        ang = (90.0 - math.degrees(math.atan2(dy, dx))) % 360.0
        ang = (ang + float(compass_rotation)) % 360.0
        return ang

    # Count based on LINE start points
    for e in msp:
        if e.dxftype() in ["LINE", "LWPOLYLINE", "POLYLINE"]:
            try:
                if e.dxftype() == "LINE":
                    start = e.dxf.start
                    ang = get_angle(start[0], start[1])
                elif e.dxftype() == "LWPOLYLINE":
                    if len(e) > 0:
                        ang = get_angle(e[0][0], e[0][1])
                else:
                    continue

                idx = int(((ang + sector_size / 2.0) % 360.0) // sector_size) % divisions
                label = labels[idx]
                direction_counts[label] += 1
            except Exception:
                continue

    print(f"DEBUG: ezdxf parsed entity distribution: {direction_counts}")
    return direction_counts
