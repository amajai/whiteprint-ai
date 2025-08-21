from typing import List, Dict, TypedDict, Any, Annotated, Literal
from pydantic import BaseModel, Field
from matplotlib.figure import Figure
from langgraph.graph import add_messages


class Room(BaseModel):
    name: str = Field(description="Name of the room")
    proportion: float = Field(description="Allocation of the room between 0 and 1")
    area: float = Field(description="Area in m²")


class FloorPlan(BaseModel):
    total_area: float
    width: int = Field(description='Width in m')
    height: int = Field(description='Height in m')
    rooms: List[Room] = Field(description='List of rooms')


class RoomLayout(BaseModel):
    name: str
    area: float
    x: float
    y: float
    width: float
    height: float


class LayoutPlan(BaseModel):
    width: int = Field(description='Width in m')
    height: int = Field(description='Height in m')
    rooms: List[RoomLayout]


class DoorLayout(BaseModel):
    from_room: str
    to_room: str
    x: float
    y: float
    width: float
    height: float
    orientation: Literal["vertical", "horizontal"]


class DoorPlan(BaseModel):
    doors: List[DoorLayout]


class FloorPlanState(TypedDict):
    input: str
    total_area: float
    width: int
    height: int
    rooms: List[Dict[str, Any]]
    plan: LayoutPlan 
    door_plan: DoorPlan
    rendered_plan: Figure
    _validation_passed: bool
    messages: Annotated[list, add_messages]