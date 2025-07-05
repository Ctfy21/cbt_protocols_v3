from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
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

class Utils(BaseModel):
    controller_type: Literal["relay", "pwm"] = Field()
    pin_type: Literal["relay", "pwm"] = Field()
    pin_number: int = Field()
    pin_value: int = Field()

class Parameters(BaseModel):
    temperature: int = Field()
    humidity: int = Field()
    light_sectors: List[LightSector] = Field()
    co2_level: int = Field()
    watering_sectors: List[WateringSector] = Field()
    utils: Optional[List[Utils]] = Field(default=None)

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
    status: Optional[Literal["draft", "ready", "active", "completed", "cancelled"]] = Field(default=None)
    chamber_id: Optional[str] = Field(default=None)
    time_start: Optional[int] = Field(default=None)
    time_end: Optional[int] = Field(default=None)
    created_at: Optional[int] = Field(default=int(datetime.now().timestamp()))
    updated_at: Optional[int] = Field(default=int(datetime.now().timestamp()))
    scenarios: List[str] = Field(default=[], description="List of scenario IDs")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class PLCSteps(BaseModel):
    time_start: int = Field()
    time_end: int = Field()
    temperature: Optional[int] = Field(default=None)
    humidity: Optional[int] = Field(default=None)
    co2_level: Optional[int] = Field(default=None)
    light_sectors: Optional[List[LightSector]] = Field(default=None)
    watering_sectors: Optional[List[WateringSector]] = Field(default=None)
    utils: Optional[List[Utils]] = Field(default=None)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ControlMode(BaseModel):
    temperature_control: str = Field(default=None)
    humidity_control: str = Field(default=None)
    co2_control: str = Field(default=None)
    light_control: str = Field(default=None)
    watering_control: str = Field(default=None)

class SchedulePLC(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    auto: bool = Field(default=False)
    control_modes: ControlMode = Field(default=None)
    time_start: int = Field(default=None)
    time_end: int = Field(default=None)
    chamber_id: str = Field(default=None)
    schedule_id: str = Field(default=None)
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))
    steps: List[PLCSteps]
    status: Optional[Literal["ready", "active", "completed", "cancelled"]] = Field(default=None)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}




class ChamberSettings(BaseModel):
    light_sectors: int = Field(default=1)
    watering_sectors: int = Field(default=1)

class Chamber(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(default="Новая камера")
    settings: ChamberSettings = Field(default=ChamberSettings())
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


