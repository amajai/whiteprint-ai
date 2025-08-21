from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from niceterminalui import (
    print_banner,
    print_step,
    print_success,
    print_warning,
    print_error,
    print_info,
    print_result_box,
    print_completion_message,
    create_progress_bar
)
from utils import draw_plan, generate_mermaid_diagram
from prompts import (
    INPUT_VALIDATION_TEMPLATE,
    ALLOCATION_VALIDATION_TEMPLATE,
    ROOM_ALLOCATION_TEMPLATE,
    ROOM_PLANNER_TEMPLATE,
    DOOR_PLANNER_TEMPLATE
)
from models import (
    FloorPlan,
    LayoutPlan,
    DoorPlan,
    FloorPlanState
)
import os
import time

load_dotenv()


def create_llm():
    provider = os.getenv("LLM_PROVIDER", "google_genai")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    return init_chat_model(
        model=model,
        model_provider=provider,
        temperature=temperature
    )

# Initialize 
llm = create_llm()


def verify_request(state: FloorPlanState) -> FloorPlanState:
    """Initial input validation before processing."""
    print_step("Input Validation", "🔍")
    print_info(f"Analyzing request: '{state.get('input', '')}'")
    return state

def should_continue_after_verification(state: FloorPlanState) -> str:
    """Use LLM to validate if initial request is reasonable."""
    try:
        input_text = state.get("input", "")
        
        prompt = INPUT_VALIDATION_TEMPLATE.format(input_text=input_text)
        response = llm.invoke(prompt).content.strip().upper()
        
        if "UNREASONABLE" in response:
            print_error("Request deemed unreasonable - contains clearly impossible requirements")
            return "END"
        elif "REASONABLE" in response:
            print_success("Input validation passed - proceeding to room allocation")
            return "CONTINUE"
        else:
            print_warning("Unclear validation response, assuming reasonable")
            return "CONTINUE"  # Default to continue for unclear responses
        
    except Exception as e:
        print_error(f"Input validation failed: {e}")
        return "END"

def validate_allocation(state: FloorPlanState) -> FloorPlanState:
    """Validate the room allocation results."""
    print_step("Allocation Validation", "🏗️")
    print_info("Checking room allocation integrity and feasibility...")
    state["_validation_passed"] = False
    return state

def should_continue_after_allocation(state: FloorPlanState) -> str:
    """Use LLM to validate room allocation output integrity and reasonableness."""
    try:
        # First check basic structure integrity (these are hard requirements)
        if not state.get("rooms"):
            print_error("Missing 'rooms' in allocation output")
            return "END"
            
        if not state.get("width") or not state.get("height"):
            print_error("Missing dimensions in allocation output") 
            return "END"
            
        if not state.get("total_area"):
            print_error("Missing 'total_area' in allocation output")
            return "END"

        # Check room data structure integrity
        for i, room in enumerate(state["rooms"]):
            if isinstance(room, dict):
                if not room.get("name") or not room.get("area"):
                    print_error(f"Room {i+1} missing required fields")
                    return "END"
            else:
                if not hasattr(room, 'name') or not hasattr(room, 'area'):
                    print_error(f"Room {i+1} missing required attributes")
                    return "END"

        # Now use LLM to validate reasonableness
        room_summary = []
        total_room_area = 0
        
        for room in state["rooms"]:
            name = room.get("name", "") if isinstance(room, dict) else room.name
            area = room.get("area", 0) if isinstance(room, dict) else room.area
            proportion = room.get("proportion", 0) if isinstance(room, dict) else room.proportion
            
            room_summary.append(f"- {name}: {area}m² ({proportion*100:.1f}%)")
            total_room_area += area

        rooms_text = "\n".join(room_summary)
        
        prompt = ALLOCATION_VALIDATION_TEMPLATE.format(
            total_area=state['total_area'],
            width=state['width'],
            height=state['height'],
            rooms_text=rooms_text,
            total_room_area=total_room_area
        )
        
        response = llm.invoke(prompt).content.strip().upper()
        
        if "INVALID" in response:
            print_error("Room allocation has critical structural issues")
            return "END"
        elif "VALID" in response:
            print_success("Allocation validation passed - proceeding to room planning")
            state["_validation_passed"] = True
            return "CONTINUE"
        else:
            print_warning("Unclear validation response, assuming valid")
            state["_validation_passed"] = True
            return "CONTINUE"  # Default to continue for unclear responses

    except Exception as e:
        print_error(f"❌ Allocation validation failed: {e}")
        return "END"

def room_allocator(state: FloorPlanState) -> FloorPlanState:
    print_step("Room Allocation", "🏠")
    
    with create_progress_bar() as progress:
        task = progress.add_task("[cyan]Analyzing space requirements...", total=100)
        
        # Step 1: Initialize structured LLM
        progress.update(task, advance=20, description="[cyan]Setting up AI room allocator...")
        time.sleep(0.3)
        structured_llm = llm.with_structured_output(FloorPlan)
        
        # Step 2: Prepare prompt
        progress.update(task, advance=20, description="[cyan]Preparing allocation prompt...")
        time.sleep(0.3)
        prompt = ROOM_ALLOCATION_TEMPLATE.format(input=state['input'])
        
        # Step 3: Invoke LLM (main processing)
        progress.update(task, advance=30, description="[cyan]AI analyzing room requirements...")
        plan: FloorPlan = structured_llm.invoke(prompt)
        
        # Step 4: Update state
        progress.update(task, advance=20, description="[cyan]Updating floor plan state...")
        time.sleep(0.3)
        state['height'] = plan.height
        state['width'] = plan.width
        state['total_area'] = plan.total_area
        state['rooms'] = plan.rooms
        
        # Step 5: Complete
        progress.update(task, advance=10, description="[cyan]Room allocation completed!")
        time.sleep(0.3)
    
    print_success(f"Room allocation complete: {len(plan.rooms)} rooms in {plan.total_area}m²")
    return state
    
def room_planner(state: FloorPlanState) -> FloorPlanState:
    print_step("Room Layout Planning", "📐")
    
    with create_progress_bar() as progress:
        task = progress.add_task("[yellow]Planning room positions...", total=100)
        
        # Step 1: Initialize layout planner
        progress.update(task, advance=25, description="[yellow]Setting up AI layout planner...")
        time.sleep(0.3)
        structured_planner = llm.with_structured_output(LayoutPlan)
        
        # Step 2: Prepare layout prompt
        progress.update(task, advance=25, description="[yellow]Analyzing room dimensions and constraints...")
        time.sleep(0.3)
        prompt = ROOM_PLANNER_TEMPLATE.format(
            width=state["width"],
            height=state["height"], 
            total_area=state['total_area'],
            rooms=state['rooms']
        )
        
        # Step 3: Generate layout (main processing)
        progress.update(task, advance=40, description="[yellow]AI optimizing room positioning...")
        state["plan"] = structured_planner.invoke(prompt)
        
        # Step 4: Complete
        progress.update(task, advance=10, description="[yellow]Room layout optimization completed!")
        time.sleep(0.3)
    
    print_success(f"Room layout complete: {len(state['plan'].rooms)} rooms positioned")
    return state

def door_planner(state: FloorPlanState) -> FloorPlanState:
    print_step("Door Planning", "🚪")
    
    with create_progress_bar() as progress:
        task = progress.add_task("[green]Planning door connections...", total=100)
        
        # Step 1: Initialize door planner
        progress.update(task, advance=25, description="[green]Setting up AI door planner...")
        time.sleep(0.3)
        structured_planner = llm.with_structured_output(DoorPlan)
        
        # Step 2: Analyze room adjacencies
        progress.update(task, advance=25, description="[green]Analyzing room adjacencies and accessibility...")
        time.sleep(0.3)
        prompt = DOOR_PLANNER_TEMPLATE.format(
            width=state['width'],
            height=state['height'],
            plan=state['plan']
        )
        
        # Step 3: Generate door plan (main processing)
        progress.update(task, advance=40, description="[green]AI designing door connections...")
        state["door_plan"] = structured_planner.invoke(prompt)
        
        # Step 4: Complete
        progress.update(task, advance=10, description="[green]Door connectivity planning completed!")
        time.sleep(0.3)
    
    print_success(f"Door planning complete: {len(state['door_plan'].doors)} doors designed")
    return state

def plan_renderer(state: FloorPlanState) -> FloorPlanState:
    print_step("Plan Rendering", "🎨")
    
    with create_progress_bar() as progress:
        task = progress.add_task("[magenta]Rendering floor plan...", total=100)
        
        # Step 1: Extract plan data
        progress.update(task, advance=30, description="[magenta]Extracting room and door data...")
        time.sleep(0.3)
        rooms = state["plan"].model_dump()
        doors = state["door_plan"].model_dump()["doors"]
        
        # Step 2: Generate visualization (main processing)
        progress.update(task, advance=60, description="[magenta]Creating visual floor plan...")
        fig = draw_plan(rooms, doors)
        
        # Step 3: Store rendered plan
        progress.update(task, advance=10, description="[magenta]Finalizing rendered floor plan...")
        time.sleep(0.3)
        state['rendered_plan'] = fig
    
    print_success("Floor plan rendered successfully")
    return state

def validate_plan(state: FloorPlanState) -> FloorPlanState:
    print_step("Plan Validation", "✅")
    print_info("Removing duplicate doors and validating connections...")
    
    doors = state["door_plan"].doors
    seen = set()
    filtered = []
    for d in doors:
        key = tuple(sorted([d.from_room, d.to_room]))
        if key not in seen:
            seen.add(key)
            filtered.append(d)
    
    removed_count = len(doors) - len(filtered)
    state["door_plan"].doors = filtered
    
    if removed_count > 0:
        print_warning(f"Removed {removed_count} duplicate door connections")
    print_success("Plan validation complete")
    return state

def plan_output(state: FloorPlanState) -> FloorPlanState:
    print_step("Final Output", "💾")
    print_info("Saving floor plan to file...")
    
    fig = state['rendered_plan']
    filename = 'floor_plan.png'
    fig.savefig(filename)
    
    print_success(f"Floor plan saved as '{filename}'")
    
    # Create a nice summary box
    room_summary = []
    for room in state["rooms"]:
        name = room.name if hasattr(room, 'name') else room['name']
        area = room.area if hasattr(room, 'area') else room['area']
        room_summary.append(f"• {name}: {area:.1f}m²")
    
    summary_content = f"""Floor Plan Generated Successfully!

House Specifications:
• Total Area: {state['total_area']}m²
• Dimensions: {state['width']}m × {state['height']}m
• Number of Rooms: {len(state['rooms'])}
• Number of Doors: {len(state['door_plan'].doors)}

Room Breakdown:
{chr(10).join(room_summary)}

Output File: {filename}"""
    
    print_result_box("FLOOR PLAN COMPLETE", summary_content)
    return state


workflow = StateGraph(FloorPlanState)

workflow.add_node("verify_request", verify_request)
workflow.add_node("room_allocator", room_allocator)
workflow.add_node("validate_allocation", validate_allocation)
workflow.add_node("room_planner", room_planner)
workflow.add_node("door_planner", door_planner)
workflow.add_node("validate_plan", validate_plan)
workflow.add_node("plan_renderer", plan_renderer)
workflow.add_node("plan_output", plan_output)

workflow.set_entry_point("verify_request")

# First validation checkpoint - check input
workflow.add_conditional_edges(
    "verify_request",
    should_continue_after_verification,
    {
        "CONTINUE": "room_allocator",
        "END": END
    }
)

# Second validation checkpoint - check allocation results
workflow.add_edge("room_allocator", "validate_allocation")
workflow.add_conditional_edges(
    "validate_allocation", 
    should_continue_after_allocation,
    {
        "CONTINUE": "room_planner",
        "END": END
    }
)

workflow.add_edge("room_planner", "door_planner")
workflow.add_edge("door_planner", "validate_plan")
workflow.add_edge("validate_plan", "plan_renderer")
workflow.add_edge("plan_renderer", "plan_output")

graph = workflow.compile()

def get_user_input():
    """Get floor plan request from user with examples and validation."""
    print_info("🏠 Describe your ideal floor plan using natural language")
    print()
    
    # Show examples
    print("💡 Example requests:")
    print("   • House 500m² with 3 bedrooms, 2 bathrooms, living room and kitchen")
    print("   • 600m² home with 2 bedrooms with ensuite bathrooms and guest bathroom")
    print("   • Large family house 800m² with 4 bedrooms, 3 bathrooms, and storage")
    print("   • Apartment 400m² with 2 bedrooms, living room, kitchen, and balcony")
    print()
    
    while True:
        user_input = input("🏗️  Enter your floor plan request: ").strip()
        
        if not user_input:
            print_warning("Please provide a floor plan description")
            continue
            
        if len(user_input) < 10:
            print_warning("Please provide more detail about your floor plan requirements")
            continue
            
        return user_input


def main():
    print_banner(
        title="WhitePrint AI", 
        subtitle="Intelligent Architectural Design Assistant", 
        description="Powered by LangGraph & AI Agents",
        subheader1="🏗️  Automated Room Allocation & Layout Planning",
        subheader2="🎨  Beautiful Visual Floor Plan Generation"
    )
    
    try:
        # Get user input
        user_request = get_user_input()
        print()
        print_info(f"🚀 Starting floor plan generation for: '{user_request}'")
        print()
        
        # Process the request
        result = graph.invoke({"input": user_request})
        print_completion_message("AI Floor Plan Generator", "Beautiful Architecture Made Simple")
        
    except KeyboardInterrupt:
        print()
        print_warning("Generation cancelled by user")
    except Exception as e:
        print_error(f"Floor plan generation failed: {e}")
        print_info("Please check your input and try again")


if __name__ == "__main__":
    main()

