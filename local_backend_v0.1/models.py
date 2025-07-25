from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Tuple
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
    sector_id: str = Field()
    light_intensity: int = Field()

class WateringSector(BaseModel):
    sector_id: str = Field()
    watering_duration: int = Field()

class Utils(BaseModel):
    controller_type: Literal["relay", "pwm"] = Field()
    pin_type: Literal["relay", "pwm"] = Field()
    pin_number: int = Field()
    pin_value: int = Field()

class Parameters(BaseModel):
    relative_start_time: int = Field()
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

class SectorIds(BaseModel):
    temperature: List[str] = Field(description="List of sector IDs for this parameter")
    humidity: List[str] = Field(description="List of sector IDs for this parameter")
    co2: List[str] = Field(description="List of sector IDs for this parameter")
    light: List[str] = Field(description="List of sector IDs for this parameter")
    watering: List[str] = Field(description="List of sector IDs for this parameter")

class Schedule(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(default="Новая расписание")
    description: Optional[str] = Field(default=None)
    status: Optional[Literal["draft", "ready", "active", "completed", "cancelled"]] = Field(default="draft")
    chamber_id: Optional[str] = Field()
    time_start: Optional[int] = Field()
    time_end: Optional[int] = Field(default=None)
    created_at: Optional[int] = Field(default=int(datetime.now().timestamp()))
    updated_at: Optional[int] = Field(default=int(datetime.now().timestamp()))
    scenarios: List[str] = Field(default=[], description="List of scenario IDs")
    schedule_scenarios: List[List[int]] = Field(default=[], description="List of schedule scenarios")
    sector_ids: Optional[SectorIds] = Field(default=None, description="Object containing sector IDs for each environment parameter")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class PLCStep(BaseModel):
    relative_start_time: int = Field()
    temperature: Optional[int] = Field(default=None)
    humidity: Optional[int] = Field(default=None)
    co2: Optional[int] = Field(default=None)
    light_sectors: Optional[List[int]] = Field(default=None)
    watering_sectors: Optional[List[int]] = Field(default=None)
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
    chamber_id: Optional[str] = Field(default=None)
    schedule_id: str = Field(default=None)
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))
    scenarios: dict[str, list[PLCStep]] = Field(default={})
    status: Optional[Literal["ready", "active", "completed", "cancelled"]] = Field(default=None)
    schedule_scenarios: List[List[int]] = Field(default=[], description="List of schedule scenarios")
    sector_ids: Optional[SectorIds] = Field(default=None, description="Object containing sector IDs for each environment parameter")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class EnvironmentControlSettings(BaseModel):
    sectors: int = Field()
    types: Optional[List[str]] = Field(default=None)

class EnvironmentParameters(BaseModel):
    temperature: Optional[EnvironmentControlSettings] = Field(default=None)
    humidity: Optional[EnvironmentControlSettings] = Field(default=None)
    co2: Optional[EnvironmentControlSettings] = Field(default=None)
    light: Optional[EnvironmentControlSettings] = Field(default=None)
    watering: Optional[EnvironmentControlSettings] = Field(default=None)

class EnvironmentSectorsSum(BaseModel):
    temperature: int = Field(default=0)
    humidity: int = Field(default=0)
    co2: int = Field(default=0)
    light: int = Field(default=0)
    watering: int = Field(default=0)

class DefineController(BaseModel):
    controller_name: str = Field()
    controller_ip: str = Field()
    controller_type: Literal["ESPHome", "Midea"] = Field()
    settings: EnvironmentParameters = Field()

    def __eq__(self, other):
        if isinstance(other, DefineController):
            return self.controller_name == other.controller_name and self.settings == other.settings
        return False

class Chamber(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(default="Новая камера")
    is_active: bool = Field(default=False)
    controllers: List[DefineController] = Field(default=None)
    sum_sectors: EnvironmentParameters = Field(default=None)
    created_at: int = Field(default=int(datetime.now().timestamp()))
    updated_at: int = Field(default=int(datetime.now().timestamp()))

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Dashboard Models
class SensorReading(BaseModel):
    sensor_id: str = Field()
    name: str = Field()
    sensor_type: Literal["temperature", "humidity", "co2", "light", "ph"] = Field()
    value: float = Field()
    unit: str = Field()
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    status: Literal["online", "offline", "error"] = Field(default="online")

class SwitchState(BaseModel):
    switch_id: str = Field()
    name: str = Field()
    state: bool = Field(default=False)
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

class Climate(BaseModel):
    indoor_temperature: float = Field()
    outdoor_temperature: float = Field()
    target_temperature: int = Field()
    fan_speed: int = Field()
    mode: Literal["off", "cool", "dry", "auto", "heat"] = Field()

class Device(BaseModel):
    device_id: str = Field()
    name: str = Field()
    ip_address: str = Field()
    status: Literal["online", "offline"] = Field(default="offline")
    last_seen: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

class ESPHomeDevice(Device):
    sensors: List[SensorReading] = Field(default=[])
    switches: List[SwitchState] = Field(default=[])

class MideaDevice(Device):
    climate: Climate = Field(default=None)

class CurrentStep(BaseModel):
    step_id: Optional[str] = Field(default=None)
    schedule_name: Optional[str] = Field(default=None)
    scenario_name: Optional[str] = Field(default=None)
    temperature: Optional[int] = Field(default=None)
    humidity: Optional[int] = Field(default=None)
    co2: Optional[int] = Field(default=None)
    light_sectors: Optional[List[int]] = Field(default=None)
    relative_start_time: Optional[int] = Field(default=None)
    time_remaining: Optional[int] = Field(default=None, description="Seconds until next step")
    is_active: bool = Field(default=False)

class DashboardState(BaseModel):
    chamber_id: str = Field()
    esp_devices: List[ESPHomeDevice] = Field(default=[])
    midea_devices: List[MideaDevice] = Field(default=[])
    current_step: Optional[CurrentStep] = Field(default=None)
    last_update: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    auto_mode: bool = Field(default=True)

class SwitchToggleRequest(BaseModel):
    switch_id: str = Field()
    state: bool = Field()
    auto_mode: Optional[bool] = Field(default=None)


