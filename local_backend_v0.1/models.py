from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum

class Status(Enum):
    DRAFT = "draft"
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class LightSector(BaseModel):
    sector_id: int = Field()
    light_intensity: int = Field()

class WateringSector(BaseModel):
    sector_id: int = Field()
    watering_duration: int = Field()

class Parameters(BaseModel):
    temperature: int = Field()
    humidity: int = Field()
    light_sectors: List[LightSector] = Field()
    co2_level: int = Field()
    watering_sectors: List[WateringSector] = Field()

class Scenario(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(default="Новый сценарий")
    description: str = Field(default=None)
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))
    parameters: List[Parameters]

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class Schedule(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(default="Новая расписание")
    description: Optional[str] = Field(default=None)
    status: Optional[Status] = Field(default=None)
    chamber_id: Optional[str] = Field(default=None)
    time_start: Optional[int] = Field(default=None)
    time_end: Optional[int] = Field(default=None)
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))
    scenarios: List[str] = Field(default=[], description="List of scenario IDs")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class SchedulePLC(BaseModel):
    id: str 
    time_start: int 
    time_end: int 
    parameters: Parameters 

class Chamber(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(default="Новая камера")
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


