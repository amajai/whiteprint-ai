from langgraph.types import Command
from niceterminalui import create_interactive_prompt, print_warning, print_info
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import numpy as np

ROOM_COLORS = {
    "Living Room": "#F5F0E8",
    "Kitchen": "#FFD580",
    "Bedroom": "#AEC6CF",
    "Bathroom": "#FFB6C1",
    "Hallway": "#E6E6FA",
    "Storage": "#D3D3D3",
    "Dining Room": "#D3A760",
    "Utility": "#C2EABD",
    "Garage": "#D4C5B0",
    "Backyard": "#90C695",
}

def get_room_color(name: str):
    """
    Pick color based on the base room type.
    E.g., 'Bathroom 1' and 'Bathroom 2' -> 'Bathroom'.
    """
    base_name = "".join([c for c in name if not c.isdigit()]).strip()
    return ROOM_COLORS.get(base_name, "#FFFFFF")  # fallback = white

def draw_plan(plan: dict, door_plan: list):
    """Render floor plan visualization"""
    fig, ax = plt.subplots(figsize=(12, 10))
    house_w, house_h = plan["width"], plan["height"]

    # Draw bounding box
    ax.add_patch(Rectangle((0, 0), house_w, house_h, fill=False, edgecolor='black', lw=2))

    for room in plan["rooms"]:
        color = get_room_color(room["name"])
        if "polygon" in room:
            poly = Polygon(room["polygon"], facecolor=color, edgecolor='black')
            ax.add_patch(poly)
            cx = sum([p[0] for p in room["polygon"]]) / len(room["polygon"])
            cy = sum([p[1] for p in room["polygon"]]) / len(room["polygon"])
        else:
            rect = Rectangle((room["x"], room["y"]), room["width"], room["height"],
                             facecolor=color, edgecolor='black')
            ax.add_patch(rect)
            cx = room["x"] + room["width"]/2
            cy = room["y"] + room["height"]/2

        # Label with name, WxH, and Area
        ax.text(
            cx,
            cy,
            f"{room['name']}\n{room['width']:.1f} x {room['height']:.1f} m\n{room['area']:.1f} m²",
            ha="center", va="center", fontweight="bold", fontsize=8
        )
    for door in door_plan:
            rect = Rectangle((door['x'], door['y']), door['width'], door['height'],
                            facecolor='brown', edgecolor='black', linewidth=1.5)
            ax.add_patch(rect)
    ax.set_xlim(-1, house_w + 1)
    ax.set_ylim(-1, house_h + 1)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xticks(np.arange(0, house_w + 1, 1), minor=True)
    ax.set_yticks(np.arange(0, house_h + 1, 1), minor=True)
    ax.grid(True, which='minor', linestyle=':', alpha=0.7)
    ax.set_title(f'Floor Plan {house_w}x{house_h} ({plan["width"]*plan["height"]} m²)', fontsize=14)

    fig.tight_layout()
    return fig

def generate_mermaid_diagram(graph):
    """Generate horizontal Mermaid diagram for the workflow"""
    print(graph.get_graph().draw_mermaid())