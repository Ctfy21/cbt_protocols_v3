from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Dict, AsyncGenerator
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import json
import asyncio
import random
from models import (
    Schedule, Scenario, Chamber, SchedulePLC, PLCStep, LightSector, WateringSector, 
    Utils, ControlMode, DefineController, EnvironmentParameters, EnvironmentControlSettings, 
    EnvironmentSectorsSum, SectorIds, SensorReading, SwitchState, ESPHomeDevice, 
    DashboardState, SwitchToggleRequest
)
from time import time
# MongoDB connection
mongodb_client: MongoClient = None
database = None

async def create_default_chambers():
    """Create a default chamber if none exists"""
    try:

        load_dotenv()

        chamber_names = os.getenv("CHAMBER_NAMES").split(",")

        for chamber_name in chamber_names:

            # Check if chamber already exists
            existing_chamber = database.chambers.find_one({"name": chamber_name})
            if existing_chamber:
                continue

            default_chamber = Chamber(
                name=chamber_name,
                is_active=False,
                controllers=[],
                sum_sectors=EnvironmentParameters(
                    temperature=EnvironmentControlSettings(sectors=0),
                    humidity=EnvironmentControlSettings(sectors=0),
                    co2=EnvironmentControlSettings(sectors=0),
                    light=EnvironmentControlSettings(sectors=0),
                    watering=EnvironmentControlSettings(sectors=0)
                )
            )
            chamber_dict = default_chamber.model_dump(exclude={"id"})
            result = database.chambers.insert_one(chamber_dict)
            chamber_id = str(result.inserted_id)

        
    except Exception as e:
        print(f"❌ Error creating default chambers: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client, database
    mongodb_client = MongoClient("mongodb://gen_user:5LenbD*.Om!oP\@217.199.253.70:27017/default_db?authSource=admin&directConnection=true")
    database = mongodb_client.get_database("default_db")
    print(f"Connected to MongoDB at {mongodb_client}")
    
    # Create default chamber if none exists
    await create_default_chambers()
    
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()
        print("Disconnected from MongoDB")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# Chamber endpoints
@app.get("/chamber", response_model=Chamber)
def get_chamber():
    """Get chamber"""
    try:
        chamber = database.chambers.find_one()
        if not chamber:
            raise HTTPException(status_code=404, detail="Chamber not found")
        chamber["_id"] = str(chamber["_id"])
        return chamber
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chamber endpoints
@app.post("/chambers/{chamber_id}/apply_controller")
def apply_controller(chamber_id: str, controller: DefineController):
    """Apply controller"""

    chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
    if not chamber:
        raise HTTPException(status_code=404, detail="Chamber not found")
    
    controllers_field = chamber.get("controllers")
    controllers_dict = controllers_field if controllers_field is not None else []

    new_controller_dict = controller.model_dump()
    
    exist_controller = next((c for c in controllers_dict if c["controller_name"] == controller.controller_name), None)
    if exist_controller == new_controller_dict:
        return Response(status_code=200, content="Nothing to change")
        
    if exist_controller:
        controllers_dict[controllers_dict.index(exist_controller)] = new_controller_dict
    else:
        controllers_dict.append(new_controller_dict)

    # Helper function to get unique types
    def get_unique_types(setting_name):
        all_types = []
        for controller in controllers_dict:
            if controller["settings"][setting_name] and controller["settings"][setting_name]["types"]:
                all_types.extend(controller["settings"][setting_name]["types"])
        return list(set(all_types)) if all_types else None

    new_sum_sectors = EnvironmentParameters(
        temperature=EnvironmentControlSettings(
            sectors=sum((controller["settings"]["temperature"]["sectors"] if controller["settings"]["temperature"] else 0 for controller in controllers_dict)), 
            types=get_unique_types("temperature")
        ),
        humidity=EnvironmentControlSettings(
            sectors=sum((controller["settings"]["humidity"]["sectors"] if controller["settings"]["humidity"] else 0 for controller in controllers_dict)), 
            types=get_unique_types("humidity")
        ),
        co2=EnvironmentControlSettings(
            sectors=sum((controller["settings"]["co2"]["sectors"] if controller["settings"]["co2"] else 0 for controller in controllers_dict)), 
            types=get_unique_types("co2")
        ),
        light=EnvironmentControlSettings(
            sectors=sum((controller["settings"]["light"]["sectors"] if controller["settings"]["light"] else 0 for controller in controllers_dict)), 
            types=get_unique_types("light")
        ),
        watering=EnvironmentControlSettings(
            sectors=sum((controller["settings"]["watering"]["sectors"] if controller["settings"]["watering"] else 0 for controller in controllers_dict)), 
            types=get_unique_types("watering")
        )
    )
    
    result = database.chambers.update_one({"_id": ObjectId(chamber_id)}, {"$set": {"is_active": True, "controllers": controllers_dict, "sum_sectors": new_sum_sectors.model_dump()}})
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to apply controller")
    return Response(status_code=200, content="Controller applied successfully")

# Dashboard state and SSE connections
dashboard_connections: Dict[str, List] = {}  # chamber_id -> list of connections
dashboard_states: Dict[str, DashboardState] = {}  # chamber_id -> dashboard state

# Mock sensor data generation
async def generate_mock_sensor_data(chamber_id: str) -> DashboardState:
    """Generate mock sensor data for demonstration purposes"""
    
    # Create mock devices if not exists
    if chamber_id not in dashboard_states:
        devices = []
        
        # Device 1: Environmental sensors
        env_sensors = [
            SensorReading(sensor_id="temp_1", sensor_type="temperature", value=round(22.5 + random.uniform(-2, 2), 1), unit="°C", sector_id="1"),
            SensorReading(sensor_id="hum_1", sensor_type="humidity", value=round(65 + random.uniform(-5, 5), 1), unit="%", sector_id="1"),
            SensorReading(sensor_id="co2_1", sensor_type="co2", value=round(400 + random.uniform(-50, 100), 0), unit="ppm", sector_id="1"),
        ]
        
        env_switches = [
            SwitchState(switch_id="fan_1", switch_type="fan", name="Вентилятор 1", state=random.choice([True, False]), sector_id="1"),
            SwitchState(switch_id="heater_1", switch_type="heater", name="Нагреватель 1", state=random.choice([True, False]), sector_id="1"),
        ]
        
        devices.append(ESPHomeDevice(
            device_id="env_controller_1", 
            name="Контроллер среды 1",
            ip_address="192.168.1.100",
            status="online",
            sensors=env_sensors,
            switches=env_switches
        ))
        
        # Device 2: Light controller
        light_sensors = [
            SensorReading(sensor_id="light_1", sensor_type="light", value=round(250 + random.uniform(-50, 100), 0), unit="µmol/m²/s", sector_id="A"),
            SensorReading(sensor_id="light_2", sensor_type="light", value=round(280 + random.uniform(-50, 100), 0), unit="µmol/m²/s", sector_id="B"),
        ]
        
        light_switches = [
            SwitchState(switch_id="light_a", switch_type="light", name="LED сектор A", state=random.choice([True, False]), sector_id="A"),
            SwitchState(switch_id="light_b", switch_type="light", name="LED сектор B", state=random.choice([True, False]), sector_id="B"),
        ]
        
        devices.append(ESPHomeDevice(
            device_id="light_controller_1",
            name="Контроллер освещения 1", 
            ip_address="192.168.1.101",
            status="online",
            sensors=light_sensors,
            switches=light_switches
        ))
        
        # Device 3: Water system
        water_sensors = [
            SensorReading(sensor_id="ph_1", sensor_type="ph", value=round(6.5 + random.uniform(-0.5, 0.5), 2), unit="pH", sector_id="1"),
            SensorReading(sensor_id="water_level_1", sensor_type="water_level", value=round(75 + random.uniform(-10, 10), 1), unit="%", sector_id="1"),
        ]
        
        water_switches = [
            SwitchState(switch_id="pump_1", switch_type="pump", name="Насос подачи", state=random.choice([True, False]), sector_id="1"),
            SwitchState(switch_id="valve_1", switch_type="valve", name="Клапан 1", state=random.choice([True, False]), sector_id="1"),
        ]
        
        devices.append(ESPHomeDevice(
            device_id="water_controller_1",
            name="Контроллер поливки 1",
            ip_address="192.168.1.102", 
            status="online",
            sensors=water_sensors,
            switches=water_switches
        ))
        
        dashboard_states[chamber_id] = DashboardState(chamber_id=chamber_id, devices=devices)
    
    # Update sensor values with some variation
    for device in dashboard_states[chamber_id].devices:
        for sensor in device.sensors:
            if sensor.sensor_type == "temperature":
                sensor.value = round(sensor.value + random.uniform(-0.2, 0.2), 1)
                sensor.value = max(18, min(30, sensor.value))  # Keep in realistic range
            elif sensor.sensor_type == "humidity":
                sensor.value = round(sensor.value + random.uniform(-1, 1), 1)
                sensor.value = max(30, min(90, sensor.value))
            elif sensor.sensor_type == "co2":
                sensor.value = round(sensor.value + random.uniform(-10, 10), 0)
                sensor.value = max(300, min(800, sensor.value))
            elif sensor.sensor_type == "light":
                sensor.value = round(sensor.value + random.uniform(-5, 5), 0)
                sensor.value = max(0, min(500, sensor.value))
            elif sensor.sensor_type == "ph":
                sensor.value = round(sensor.value + random.uniform(-0.1, 0.1), 2)
                sensor.value = max(5.5, min(7.5, sensor.value))
            elif sensor.sensor_type == "water_level":
                sensor.value = round(sensor.value + random.uniform(-1, 1), 1)
                sensor.value = max(0, min(100, sensor.value))
            
            sensor.timestamp = int(time())
    
    dashboard_states[chamber_id].last_update = int(time())
    return dashboard_states[chamber_id]

async def dashboard_event_generator(chamber_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for dashboard updates"""
    try:
        while True:
            # Generate updated dashboard state
            dashboard_state = await generate_mock_sensor_data(chamber_id)
            
            # Format as SSE event
            data = json.dumps(dashboard_state.model_dump(), ensure_ascii=False)
            yield f"data: {data}\n\n"
            
            # Wait before next update
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except Exception as e:
        print(f"Error in dashboard event generator: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# Dashboard endpoints
@app.get("/dashboard/{chamber_id}/stream")
async def dashboard_stream(chamber_id: str):
    """Server-Sent Events stream for real-time dashboard updates"""
    if not ObjectId.is_valid(chamber_id):
        raise HTTPException(status_code=400, detail="Invalid chamber ID")
    
    # Check if chamber exists
    chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
    if not chamber:
        raise HTTPException(status_code=404, detail="Chamber not found")
    
    return StreamingResponse(
        dashboard_event_generator(chamber_id),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/dashboard/{chamber_id}", response_model=DashboardState)
async def get_dashboard_state(chamber_id: str):
    """Get current dashboard state"""
    if not ObjectId.is_valid(chamber_id):
        raise HTTPException(status_code=400, detail="Invalid chamber ID")
    
    # Check if chamber exists
    chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
    if not chamber:
        raise HTTPException(status_code=404, detail="Chamber not found")
    
    # Generate or get current state
    dashboard_state = await generate_mock_sensor_data(chamber_id)
    return dashboard_state

@app.post("/dashboard/{chamber_id}/switches/{switch_id}/toggle")
async def toggle_switch(chamber_id: str, switch_id: str, request: SwitchToggleRequest):
    """Toggle switch state"""
    if not ObjectId.is_valid(chamber_id):
        raise HTTPException(status_code=400, detail="Invalid chamber ID")
    
    # Check if chamber exists
    chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
    if not chamber:
        raise HTTPException(status_code=404, detail="Chamber not found")
    
    # Find and update switch
    if chamber_id in dashboard_states:
        for device in dashboard_states[chamber_id].devices:
            for switch in device.switches:
                if switch.switch_id == switch_id:
                    switch.state = request.state
                    if request.auto_mode is not None:
                        switch.auto_mode = request.auto_mode
                    switch.timestamp = int(time())
                    
                    # Here you would typically send command to ESPHome device
                    # await send_esphome_command(device.ip_address, switch_id, request.state)
                    
                    return {"success": True, "switch_id": switch_id, "state": request.state}
    
    raise HTTPException(status_code=404, detail="Switch not found")


# Schedule endpoints
@app.get("/schedules", response_model=List[Schedule])
def get_schedules():
    """Get all schedules"""
    try:
        schedules = list(database.schedules.find())
        for schedule in schedules:
            schedule["_id"] = str(schedule["_id"])
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Schedule PLC endpoints
@app.get("/schedules/plc/{chamber_id}", response_model=SchedulePLC)
def get_schedules_plc(chamber_id: str):
    """Get all schedules for PLC"""
    try:
        if not ObjectId.is_valid(chamber_id):
            raise HTTPException(status_code=400, detail="Invalid chamber ID")
            
        schedule_plc = database.schedule_plc.find_one({"chamber_id": chamber_id})
        if not schedule_plc:
            raise HTTPException(status_code=404, detail="Schedule PLC not found")
            
        schedule_plc["_id"] = str(schedule_plc["_id"])
        return schedule_plc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schedules", response_model=Schedule)
def create_schedule(schedule: Schedule):
    """Create a new schedule"""
    try:
        chamber = database.chambers.find_one({"_id": ObjectId(schedule.chamber_id)})
        if chamber and schedule.time_start and schedule.schedule_scenarios:
            schedule.time_end = schedule.time_start + 86400 * sum(days[1] for days in schedule.schedule_scenarios)
            schedule.status = "ready"
            
            # Create sector_ids from chamber's sum_sectors
            if chamber.get("sum_sectors"):
                sum_sectors = chamber["sum_sectors"]
                
                # Initialize sector lists for each parameter
                temperature_sectors = []
                humidity_sectors = []
                co2_sectors = []
                light_sectors = []
                watering_sectors = []
                
                for param_name in ["temperature", "humidity", "co2", "light", "watering"]:
                    if sum_sectors.get(param_name) and sum_sectors[param_name].get("sectors", 0) > 0:
                        # Get sector IDs based on types or generate numbered IDs
                        param_types = sum_sectors[param_name].get("types", [])
                        sectors_count = sum_sectors[param_name].get("sectors", 0)
                        
                        if param_types and len(param_types) > 0:
                            # Use types as sector IDs for light, numbered IDs for others
                            if param_name == "light":
                                sector_list = param_types
                            else:
                                sector_list = [str(i) for i in range(1, sectors_count + 1)]
                        else:
                            # Generate numbered sector IDs
                            sector_list = [str(i) for i in range(1, sectors_count + 1)]
                        
                        # Assign to appropriate parameter list
                        if param_name == "temperature":
                            temperature_sectors = sector_list
                        elif param_name == "humidity":
                            humidity_sectors = sector_list
                        elif param_name == "co2":
                            co2_sectors = sector_list
                        elif param_name == "light":
                            light_sectors = sector_list
                        elif param_name == "watering":
                            watering_sectors = sector_list
                
                schedule.sector_ids = SectorIds(
                    temperature=temperature_sectors,
                    humidity=humidity_sectors,
                    co2=co2_sectors,
                    light=light_sectors,
                    watering=watering_sectors
                )
            schedule_dict = schedule.model_dump(exclude={"id"})

            # Create PLC steps
            scenarios = list(database.scenarios.find({"_id": {"$in": [ObjectId(scenario_id) for scenario_id in schedule.scenarios]}}))
            scenarios_models = [Scenario(id=str(scenario["_id"]), name=scenario["name"], description=scenario["description"], created_at=scenario["created_at"], updated_at=scenario["updated_at"], parameters=scenario["parameters"]) for scenario in scenarios]
            scenarios_plc: dict[str, list[PLCStep]] = {}
            
            # Обрабатываем каждый элемент schedule_scenarios: [индекс_сценария, количество_дней]
            for schedule_scenario in schedule.schedule_scenarios:
                scenario_index = schedule_scenario[0]  # Индекс сценария в массиве schedule.scenarios
                # days_count = schedule_scenario[1]    Количество дней для этого сценария
                
                # Получаем ID сценария по индексу
                scenario_id = schedule.scenarios[scenario_index]
                
                # Находим модель сценария
                current_scenario = next(scenarios_model for scenarios_model in scenarios_models if scenarios_model.id == scenario_id)
                
                if current_scenario.parameters and len(current_scenario.parameters) > 0:
                    parameters = current_scenario.parameters
                    plc_steps: list[PLCStep] = []
                    
                    for parameter in parameters:
                        plc_steps.append(PLCStep(
                            relative_start_time=parameter.relative_start_time,
                            temperature=parameter.temperature,
                            humidity=parameter.humidity,
                            co2=parameter.co2_level,
                            light_sectors=[sector.light_intensity for sector in parameter.light_sectors],
                            watering_sectors=[sector.watering_duration for sector in parameter.watering_sectors],
                            utils=parameter.utils
                        ))
                    
                    scenarios_plc[str(scenario_index)] = plc_steps
                else:
                    print(f"Warning: Scenario {scenario_id} (index {scenario_index}) has no parameters")
            
            result = database.schedules.insert_one(schedule_dict)
            schedule_dict["_id"] = str(result.inserted_id)
            print(str(result.inserted_id))
            # Create schedule PLC
            schedule_plc = SchedulePLC(
                auto=True,
                schedule_scenarios=schedule.schedule_scenarios,
                control_modes=ControlMode(
                    temperature_control="Midea",
                    humidity_control="ESPHome",
                    co2_control="ESPHome",
                    light_control="ESPHome",
                    watering_control="ESPHome"
                ),
                time_start=schedule.time_start,
                time_end=schedule.time_end,
                chamber_id=schedule.chamber_id,
                schedule_id=str(result.inserted_id),
                status="ready",
                scenarios=scenarios_plc,
                sector_ids=schedule.sector_ids
            )
            schedule_plc_dict = schedule_plc.model_dump(exclude={"id"})
            result = database.schedule_plc.insert_one(schedule_plc_dict)


            return schedule_dict
        else:
            schedule.status = "draft"
            
            # Create sector_ids from chamber's sum_sectors even for draft schedules
            if chamber:
                if chamber.get("sum_sectors"):
                    sum_sectors = chamber["sum_sectors"]
                    
                    # Initialize sector lists for each parameter
                    temperature_sectors = []
                    humidity_sectors = []
                    co2_sectors = []
                    light_sectors = []
                    watering_sectors = []
                    
                    for param_name in ["temperature", "humidity", "co2", "light", "watering"]:
                        if sum_sectors.get(param_name) and sum_sectors[param_name].get("sectors", 0) > 0:
                            # Get sector IDs based on types or generate numbered IDs
                            param_types = sum_sectors[param_name].get("types", [])
                            sectors_count = sum_sectors[param_name].get("sectors", 0)
                            
                            if param_types and len(param_types) > 0:
                                # Use types as sector IDs for light, numbered IDs for others
                                if param_name == "light":
                                    sector_list = param_types
                                else:
                                    sector_list = [str(i) for i in range(1, sectors_count + 1)]
                            else:
                                # Generate numbered sector IDs
                                sector_list = [str(i) for i in range(1, sectors_count + 1)]
                            
                            # Assign to appropriate parameter list
                            if param_name == "temperature":
                                temperature_sectors = sector_list
                            elif param_name == "humidity":
                                humidity_sectors = sector_list
                            elif param_name == "co2":
                                co2_sectors = sector_list
                            elif param_name == "light":
                                light_sectors = sector_list
                            elif param_name == "watering":
                                watering_sectors = sector_list
                    
                    schedule.sector_ids = SectorIds(
                        temperature=temperature_sectors,
                        humidity=humidity_sectors,
                        co2=co2_sectors,
                        light=light_sectors,
                        watering=watering_sectors
                    )
            
            schedule_dict = schedule.model_dump()
            result = database.schedules.insert_one(schedule_dict)
            schedule_dict["_id"] = str(result.inserted_id)
            return schedule_dict
    except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedules/{schedule_id}", response_model=Schedule)
def get_schedule(schedule_id: str):
    """Get a specific schedule by ID"""
    try:
        if not ObjectId.is_valid(schedule_id):
            raise HTTPException(status_code=400, detail="Invalid schedule ID")
        
        schedule = database.schedules.find_one({"_id": ObjectId(schedule_id)})
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule["_id"] = str(schedule["_id"])
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: str):
    """Delete a specific schedule by ID"""
    try:
        if not ObjectId.is_valid(schedule_id):
            raise HTTPException(status_code=400, detail="Invalid schedule ID")
        
        # Check if schedule exists
        schedule = database.schedules.find_one({"_id": ObjectId(schedule_id)})
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Delete the schedule PLC
        result = database.schedule_plc.delete_one({"schedule_id": schedule_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Schedule PLC not found")

        # Delete the schedule
        result = database.schedules.delete_one({"_id": ObjectId(schedule_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {"message": "Schedule deleted successfully", "deleted_id": schedule_id}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/schedules/{schedule_id}", response_model=Schedule)
def update_schedule(schedule_id: str, schedule: Schedule):
    """Update a specific schedule by ID"""
    try:
        if not ObjectId.is_valid(schedule_id):
            raise HTTPException(status_code=400, detail="Invalid schedule ID")
        # Check if schedule exists
        schedule_exists = database.schedules.find_one({"_id": ObjectId(schedule_id)})
        if not schedule_exists:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Get chamber information for sector_ids
        chamber = database.chambers.find_one({"_id": ObjectId(schedule.chamber_id)}) if schedule.chamber_id else None
        
        # Create sector_ids from chamber's sum_sectors
        if chamber:
            if chamber.get("sum_sectors"):
                sum_sectors = chamber["sum_sectors"]
                
                # Initialize sector lists for each parameter
                temperature_sectors = []
                humidity_sectors = []
                co2_sectors = []
                light_sectors = []
                watering_sectors = []
                
                for param_name in ["temperature", "humidity", "co2", "light", "watering"]:
                    if sum_sectors.get(param_name) and sum_sectors[param_name].get("sectors", 0) > 0:
                        # Get sector IDs based on types or generate numbered IDs
                        param_types = sum_sectors[param_name].get("types", [])
                        sectors_count = sum_sectors[param_name].get("sectors", 0)
                        
                        if param_types and len(param_types) > 0:
                            # Use types as sector IDs for light, numbered IDs for others
                            if param_name == "light":
                                sector_list = param_types
                            else:
                                sector_list = [str(i) for i in range(1, sectors_count + 1)]
                        else:
                            # Generate numbered sector IDs
                            sector_list = [str(i) for i in range(1, sectors_count + 1)]
                        
                        # Assign to appropriate parameter list
                        if param_name == "temperature":
                            temperature_sectors = sector_list
                        elif param_name == "humidity":
                            humidity_sectors = sector_list
                        elif param_name == "co2":
                            co2_sectors = sector_list
                        elif param_name == "light":
                            light_sectors = sector_list
                        elif param_name == "watering":
                            watering_sectors = sector_list
                
                schedule.sector_ids = SectorIds(
                    temperature=temperature_sectors,
                    humidity=humidity_sectors,
                    co2=co2_sectors,
                    light=light_sectors,
                    watering=watering_sectors
                )

        # Create PLC steps
        plc_steps = []
        scenarios = list(database.scenarios.find({"_id": {"$in": [ObjectId(scenario_id) for scenario_id in schedule.scenarios]}}))
        scenarios_models = [Scenario(id=str(scenario["_id"]), name=scenario["name"], description=scenario["description"], created_at=scenario["created_at"], updated_at=scenario["updated_at"], parameters=scenario["parameters"]) for scenario in scenarios]
        temp_time_start = schedule.time_start
        for schedule_scenario in schedule.scenarios:
            current_scenario = next(scenarios_model for scenarios_model in scenarios_models if scenarios_model.id == schedule_scenario)
            # parameters is a list, so we use the first parameter set
            if current_scenario.parameters and len(current_scenario.parameters) > 0:
                parameters = current_scenario.parameters
                for parameter in parameters:
                    plc_steps.append(PLCStep(
                        relative_start_time=parameter.relative_start_time,
                        temperature=parameter.temperature,
                        humidity=parameter.humidity,
                        co2=parameter.co2_level,
                        light_sectors=[sector.light_intensity for sector in parameter.light_sectors],
                        watering_sectors=[sector.watering_duration for sector in parameter.watering_sectors],
                        utils=parameter.utils
                    ))
                    temp_time_start += 3600
            else:
                print(f"Warning: Scenario {schedule_scenario} has no parameters")
        if temp_time_start != schedule.time_end:
            raise HTTPException(status_code=500, detail="Time start and time end are not equal")
        
        # Create schedule PLC
        schedule_plc = SchedulePLC(
            auto=True,
            control_modes=ControlMode(
                temperature_control="Midea",
                humidity_control="ESPHome",
                co2_control="ESPHome",
                light_control="ESPHome",
                watering_control="ESPHome"
            ),
            time_start=schedule.time_start,
            time_end=schedule.time_end,
            chamber_id=schedule.chamber_id,
            schedule_id=schedule_id,
            updated_at=int(time()),
            status="ready",
            steps=plc_steps,
            sector_ids=schedule.sector_ids
        )
        
        # Update the schedule
        result = database.schedules.update_one({"_id": ObjectId(schedule_id)}, {"$set": schedule.model_dump(exclude={"id"})})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Failed to update schedule")
            
        # Update schedule PLC
        schedule_plc_dict = schedule_plc.model_dump(exclude={"id"})
        result = database.schedule_plc.update_one({"schedule_id": schedule_id}, {"$set": schedule_plc_dict})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Schedule PLC not found")

        # Return the updated schedule
        updated_schedule = database.schedules.find_one({"_id": ObjectId(schedule_id)})
        updated_schedule["_id"] = str(updated_schedule["_id"])
        return updated_schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scenario endpoints
@app.get("/scenarios", response_model=List[Scenario])
def get_scenarios():
    """Get all scenarios"""
    try:
        scenarios = list(database.scenarios.find())
        for scenario in scenarios:
            scenario["_id"] = str(scenario["_id"])
        return scenarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scenarios", response_model=Scenario)
def create_scenario(scenario: Scenario):
    """Create a new scenario"""
    try:
        scenario_dict = scenario.model_dump(exclude={"id"})
        result = database.scenarios.insert_one(scenario_dict)
        scenario_dict["_id"] = str(result.inserted_id)
        return scenario_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios/{scenario_id}", response_model=Scenario)
def get_scenario(scenario_id: str):
    """Get a specific scenario by ID"""
    try:
        if not ObjectId.is_valid(scenario_id):
            raise HTTPException(status_code=400, detail="Invalid scenario ID")
        
        scenario = database.scenarios.find_one({"_id": ObjectId(scenario_id)})
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        scenario["_id"] = str(scenario["_id"])
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: str):
    """Delete a specific scenario by ID"""
    try:
        if not ObjectId.is_valid(scenario_id):
            raise HTTPException(status_code=400, detail="Invalid scenario ID")
        
        # Check if scenario exists
        scenario = database.scenarios.find_one({"_id": ObjectId(scenario_id)})
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        # Delete the scenario
        result = database.scenarios.delete_one({"_id": ObjectId(scenario_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return {"message": "Scenario deleted successfully", "deleted_id": scenario_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


