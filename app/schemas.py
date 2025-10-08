from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")

class Action(BaseModel):
    tool: str
    args: Dict[str, Any]

class LLMResponse(BaseModel):
    intent: str
    actions: List[Action] = []
    answer_md: str

class CustomerFeatures(BaseModel):
    Age: int
    Gender: str
    TravelCategory: str
    TravelClass: str
    Distance: float
    DepDelay: float
    ArrDelay: float
    SeatComfort: int
    Food: int
    Entertainment: int
    LegRoom: int
    Cleanliness: int
    Luggage: int
    BoardingPoint: str

    @field_validator('Gender')
    def gender_ok(cls, v):
        if v not in {"Male","Female"}:
            raise ValueError("Gender must be Male or Female")
        return v
