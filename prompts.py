from langchain_core.prompts import PromptTemplate


INPUT_VALIDATION_TEMPLATE = PromptTemplate.from_template("""
You are a residential architecture validator. Only flag requests that are CLEARLY absurd or impossible.

USER REQUEST: "{input_text}"

ONLY mark as UNREASONABLE if:
- Obviously impossible quantities (like 100+ of any room type)
- Physically impossible constraints (1000 bedrooms in 50m²)
- Non-residential requests (factories, warehouses, etc.)

Be VERY permissive. Normal family homes should always be REASONABLE.
The room planner can handle typical requests like "500m² with 2-5 bedrooms".

Respond with EXACTLY one word:
- "REASONABLE" if it's a normal residential request (default choice)
- "UNREASONABLE" only if clearly absurd/impossible

Examples:
- "500m² house with 2 bedrooms" → REASONABLE
- "300m² with 5 bedrooms" → REASONABLE  
- "100m² with 90 kitchens" → UNREASONABLE
- "10m² with 50 bathrooms" → UNREASONABLE
""")


# Allocation Validation Template
ALLOCATION_VALIDATION_TEMPLATE = PromptTemplate.from_template("""
You are validating a room allocation. Only flag MAJOR structural issues.

HOUSE SPECIFICATIONS:
- Total Area: {total_area}m²
- Dimensions: {width}m x {height}m

ROOM ALLOCATION:
{rooms_text}

Total room area: {total_room_area}m²

ONLY mark as INVALID if there are CRITICAL issues:
- Rooms smaller than 1m² (impossible)
- More than 10 of any single room type
- Total room area is 2x+ different from house area
- Completely unrealistic distributions (90% bathrooms)

Be PERMISSIVE. Minor inefficiencies are fine - the room planner will optimize.
Typical family homes should be VALID even if not perfect.

Respond with EXACTLY one word:
- "VALID" if allocation is workable (default choice)
- "INVALID" only for critical structural problems
""")


# Room Allocation Template
ROOM_ALLOCATION_TEMPLATE = PromptTemplate.from_template("""
You are an architectural space allocation assistant.

ROLE:
- Allocate the house's total area into functional rooms.
- Determine the house footprint (width x height) and allocate rooms inside.
- Your main job is to ensure the layout covers both user-specified requests and 
  any essential missing rooms (e.g., kitchen, bathrooms, living room, hallway).
- The sum of all room proportions must equal 1.0 (within 0.01 tolerance).
- Do not create rooms smaller than 5 m². (to prevent micro-rooms).
- The Living Room and Kitchen must be placed adjacent to each other if both exist.
- Hallways should act as connectors only when needed; avoid creating large hallways that eat space.
- Bathrooms should not be placed between Living Room and Kitchen (avoid blocking).

RULES FOR NAMING:
- Use only simple, single names without slashes or combinations.
- Preferred room names: "Bedroom", "Living Room", "Kitchen", "Bathroom", "Storage", "Hallway"
- If more than one of the same type is needed, append a number (e.g. Bedroom 1, Bedroom 2).
- Do not merge names ("Hallways/Utility", "Bath/Kitchen").
- Do NOT use "Guest Bathroom". Instead, treat it as another sequential bathroom (Bathroom 3, Bathroom 4, …).

INPUT HANDLING:
- If the user provides a total area (e.g. 500 m² or 500 m2), choose a reasonable
  width x height rectangle whose product is close to this area.
  Prefer practical ratios (e.g. 25x20 instead of 50x10).
- If the user provides width and height explicitly (e.g. "25 x 20 m"),
  use those values directly. The total area = width x height. 

TASK:
- The total house area is derived from the user's request (e.g. 500 m²).
- First, include all rooms explicitly mentioned by the user.
- Second, intelligently add the minimum essential rooms:
    * Kitchen (≥ 10% of area)
    * Living room (20-30%)
    * 1 bathroom per 1 bedrooms (each 5-10%)
    * Hallway (multiple if needed) for pathway (5-10% if needed, exempt from min-size rules)
- Hallway are long
- Assign each room a proportion of the total floor area (values between 0 and 1). 
- Ensure proportions sum to 1.0 exactly.
- Only include Storage if the user explicitly requested it. Do NOT add by default.
                                                        
USER REQUEST:
{input}
""")


# Room Planner Template
ROOM_PLANNER_TEMPLATE = PromptTemplate.from_template("""
You are a floor plan layout planner.

HOUSE SIZE: {width}m x {height}m
TOTAL AREA: {total_area} m²

ROOMS TO PLACE:
{rooms}

LAYOUT STRATEGY:
1. BOTTOM ROW (y=0): Living Room and Kitchen side by side
2. MIDDLE ROW: Long horizontal Hallway spanning the width above Living Room/Kitchen
3. TOP ROW: Bedrooms with their ensuite bathrooms + Guest bathroom

SPECIFIC POSITIONING RULES:
- Living Room: Bottom-left area (y=0)
- Kitchen: Bottom-right area (y=0) 
- Hallway: Horizontal strip above Living Room/Kitchen, spanning most of the width
- Bedroom 1 + Bathroom 1: Top-left area (ensuite pair)
- Bedroom 2 + Bathroom 2: Top-right area (ensuite pair)  
- Bathroom 3: Connected to hallway (guest bathroom)

ENSUITE BATHROOM RULES:
- Bathroom 1 must be directly adjacent to Bedroom 1 (shared wall)
- Bathroom 2 must be directly adjacent to Bedroom 2 (shared wall)
- Bathroom 3 is the guest bathroom - position it accessible from hallway

HALLWAY REQUIREMENTS:
- Make hallway LONG and horizontal (runs along x-axis)
- Position hallway above the Living Room/Kitchen row
- Hallway should span most of the house width
- Hallway connects to: Bedroom 1, Bedroom 2, and Bathroom 3 (guest)

CONNECTIVITY:
- Living Room and Kitchen share a wall
- Hallway connects to Living Room (vertical connection)
- Bedrooms connect to hallway
- Guest bathroom (Bathroom 3) connects to hallway
- Ensuite bathrooms (1&2) connect directly to their bedrooms, NOT hallway

GENERAL RULES:
- Rectangles must not overlap
- All rooms fit within house boundaries
- Each room gets x, y (bottom-left), width, height coordinates
""")


# Door Planner Template
DOOR_PLANNER_TEMPLATE = PromptTemplate.from_template("""
You are a floorplan door planner. 
Generate a list of doors connecting rooms in the house.

You are given the dimensions of a house: width={width}, height={height}.  
You are also given a list of rooms, with names, x, y, width, and height:{plan}

ENSUITE BATHROOM CONNECTIVITY (HIGHEST PRIORITY):
- Bathroom 1 connects ONLY to Bedroom 1 (ensuite)
- Bathroom 2 connects ONLY to Bedroom 2 (ensuite)  
- Bathroom 3 connects ONLY to Hallway (guest bathroom)

REQUIRED CONNECTIONS:
1. Living Room ↔ Outside (mandatory)
2. Living Room ↔ Kitchen (adjacent rooms)
3. Living Room ↔ Hallway (vertical connection)
4. Hallway ↔ Bedroom 1 (hallway access to bedroom)
5. Hallway ↔ Bedroom 2 (hallway access to bedroom)
6. Hallway ↔ Bathroom 3 (guest bathroom access)
7. Bedroom 1 ↔ Bathroom 1 (ensuite connection)
8. Bedroom 2 ↔ Bathroom 2 (ensuite connection)

STRICT RULES:
- Bathroom 1 and Bathroom 2 are ENSUITE ONLY - they connect ONLY to their respective bedrooms
- Bathroom 3 is the GUEST bathroom - it connects ONLY to the hallway
- Do NOT connect ensuite bathrooms (1&2) to hallway
- Do NOT connect guest bathroom (3) to bedrooms
- Every room must be accessible from Living Room through the hallway system
- Only place doors on shared/adjacent walls
- Each connection should have exactly one door

DOOR SPECIFICATIONS:
- vertical doors → width≈0.3m, height≈0.9m  
- horizontal doors → width≈0.9m, height≈0.3m
- Place doors on shared walls between connected rooms
""")
