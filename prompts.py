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
    * Multiple hallways for optimal connectivity (8-18% total for wider circulation)
- Create multiple hallways (Hallway 1, Hallway 2, etc.) if needed for better access
- Hallways should be WIDER for comfortable circulation (allocate more area)
- Hallways can be horizontal, vertical, or both to create flexible room connections
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

CORE LAYOUT PRINCIPLES:
1. Living Room and Kitchen at bottom level (y=0), side by side
2. Multiple flexible hallways for optimal connectivity
3. Bedrooms with adjacent ensuite bathrooms (preserve bedroom-bathroom pairs)
4. Guest bathroom accessible via hallway system
5. Storage (if present) positioned to not disrupt ensuite pairs

ENSUITE BATHROOM REQUIREMENTS (CRITICAL):
- Bedroom 1 + Bathroom 1: Must be directly adjacent (shared wall)
- Bedroom 2 + Bathroom 2: Must be directly adjacent (shared wall)
- These pairs are SACRED - never separate them with other rooms

FLEXIBLE HALLWAY SYSTEM:
- Use multiple hallways (Hallway 1, Hallway 2, etc.) as needed
- Hallways can be horizontal (x-axis), vertical (y-axis), or both
- Create L-shaped, T-shaped, or linear hallway networks
- Main hallway connects Living Room to bedroom area
- Secondary hallways provide additional access and flexibility
- Make hallways WIDER for better circulation (minimum 2-3 meters width)
- Hallways should be spacious corridors, not narrow passages

SMART POSITIONING RULES:
- Living Room: Bottom area, connects to main hallway
- Kitchen: Bottom area, adjacent to Living Room
- Bedroom-Bathroom pairs: Keep together, position efficiently
- Guest bathroom (Bathroom 3): Accessible via hallway system
- Storage: Connect to hallway, do NOT break ensuite bedroom-bathroom adjacency

CONNECTIVITY STRATEGY:
- All rooms accessible via hallway network
- Preserve bedroom-bathroom ensuite connections
- Efficient traffic flow between public and private areas
- Storage accessible but not disruptive to main room relationships

LAYOUT FLEXIBILITY:
- Adapt hallway configuration to room count and storage needs
- Optimize for both access and space efficiency
- Maintain logical room groupings (bedrooms together, etc.)
- Use hallway system to solve layout challenges

GENERAL RULES:
- No overlapping rectangles
- All rooms within house boundaries
- Output x, y (bottom-left), width, height for each room
- Prioritize functionality over rigid grid patterns
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
- Bathroom 3 connects ONLY to hallway system (guest bathroom)

MULTIPLE HALLWAY CONNECTIVITY:
- Connect hallways to each other if multiple exist (Hallway 1 ↔ Hallway 2, etc.)
- Living Room connects to at least one hallway (main access)
- Bedrooms connect to hallway system (Hallway 1, Hallway 2, etc.)
- Guest bathroom (Bathroom 3) connects to any hallway
- Storage (if present) connects to hallway system

REQUIRED CONNECTION TYPES:
1. Living Room ↔ Outside (mandatory)
2. Living Room ↔ Kitchen (if adjacent)
3. Living Room ↔ Hallway system (main access)
4. Hallway interconnections (if multiple hallways exist)
5. Bedrooms ↔ Hallway system (access to private area)
6. Guest bathroom ↔ Hallway system
7. Storage ↔ Hallway system (if storage exists)
8. Bedroom 1 ↔ Bathroom 1 (ensuite connection)
9. Bedroom 2 ↔ Bathroom 2 (ensuite connection)

HALLWAY NETWORK RULES:
- If multiple hallways exist, connect them for continuous flow
- Each hallway should connect to relevant rooms in its area
- Create efficient circulation paths
- Avoid dead-end hallways unless necessary

STRICT ENSUITE RULES:
- Bathroom 1 and Bathroom 2 are ENSUITE ONLY - connect ONLY to their bedrooms
- Guest bathroom connects ONLY to hallway system, NOT to bedrooms
- Do NOT connect ensuite bathrooms to hallways
- Preserve bedroom-bathroom ensuite privacy

ACCESSIBILITY REQUIREMENTS:
- Every room accessible from Living Room via hallway system
- Storage accessible via hallway (not through bedrooms)
- Guest bathroom publicly accessible via hallway
- Efficient traffic flow between public and private areas

DOOR SPECIFICATIONS:
- vertical doors → width≈0.3m, height≈0.9m  
- horizontal doors → width≈0.9m, height≈0.3m
- Place doors only on shared/adjacent walls
- One door per connection
""")
