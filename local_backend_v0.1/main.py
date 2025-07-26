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
import aiohttp
import logging
import re
import traceback
from midealocal.discover import discover
from models import (
    Schedule, Scenario, Chamber, SchedulePLC, PLCStep, LightSector, WateringSector, 
    Utils, ControlMode, DefineController, EnvironmentParameters, EnvironmentControlSettings, 
    EnvironmentSectorsSum, SectorIds, SensorReading, SwitchState, ESPHomeDevice, 
    DashboardState, SwitchToggleRequest, CurrentStep
)
from time import time
from esphomeAPI import (
    esphome_manager, initialize_esphome_devices, get_chamber_esphome_devices, 
    toggle_esphome_switch
)
from mideaAPI import (
    midea_manager, initialize_midea_devices, get_chamber_midea_devices
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
mongodb_client: MongoClient = None
database = None

# Dashboard state and SSE connections
dashboard_connections: Dict[str, List] = {}  # chamber_id -> list of connections
dashboard_states: Dict[str, DashboardState] = {}  # chamber_id -> dashboard state

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

async def initialize_all_devices():
    """Initialize ESPHome and Midea devices for all chambers"""
    try:
        logger.info("Initializing ESPHome and Midea devices for all chambers")
        chambers = list(database.chambers.find())
        
        all_controllers = []
        for chamber in chambers:
            controllers = chamber.get("controllers", [])
            all_controllers.extend(controllers)
        
        # Initialize ESPHome connections
        await initialize_esphome_devices(all_controllers)
        logger.info("ESPHome devices initialized successfully")
        
        # Initialize Midea connections
        discovered_devices = discover()
        ip_addresses = [i['ip_address'] for i in discovered_devices.values()]
        await initialize_midea_devices(ip_addresses)
        logger.info("Midea devices initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing devices: {e}")
        logger.error(traceback.format_exc())

# Schedule status monitor
schedule_monitor_task = None

async def check_schedule_status():
    """Check and update schedule statuses every minute"""
    while True:
        try:
            current_time = int(time())
            logger.info(f"Checking schedule statuses at {current_time}")
            
            # Find all schedules that might need status updates
            schedules = list(database.schedules.find({
                "status": {"$in": ["ready", "active"]}
            }))
            
            for schedule in schedules:
                schedule_id = str(schedule["_id"])
                
                # Check if schedule should be activated
                if (schedule["status"] == "ready" and 
                    schedule.get("time_start") and 
                    schedule.get("time_end") and
                    schedule["time_start"] <= current_time < schedule["time_end"]):
                    
                    # Activate schedule
                    database.schedules.update_one(
                        {"_id": schedule["_id"]}, 
                        {"$set": {"status": "active", "updated_at": current_time}}
                    )
                    
                    # Activate schedule PLC
                    database.schedule_plc.update_one(
                        {"schedule_id": schedule_id}, 
                        {"$set": {"status": "active", "updated_at": current_time}}
                    )
                    
                    logger.info(f"Activated schedule {schedule_id}: {schedule.get('name', 'Unknown')}")
                
                # Check if schedule should be completed
                elif (schedule["status"] == "active" and 
                      schedule.get("time_end") and
                      current_time >= schedule["time_end"]):
                    
                    # Complete schedule
                    database.schedules.update_one(
                        {"_id": schedule["_id"]}, 
                        {"$set": {"status": "completed", "updated_at": current_time}}
                    )
                    
                    # Complete schedule PLC
                    database.schedule_plc.update_one(
                        {"schedule_id": schedule_id}, 
                        {"$set": {"status": "completed", "updated_at": current_time}}
                    )
                    
                    logger.info(f"Completed schedule {schedule_id}: {schedule.get('name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error in schedule status check: {e}")
            logger.error(traceback.format_exc())
        
        # Wait for 60 seconds before next check
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client, database, schedule_monitor_task
    mongodb_client = MongoClient("mongodb://gen_user:5LenbD*.Om!oP\@217.199.253.70:27017/default_db?authSource=admin&directConnection=true")
    database = mongodb_client.get_database("default_db")
    print(f"Connected to MongoDB at {mongodb_client}")
    
    # Create default chamber if none exists
    await create_default_chambers()
    
    # Initialize ESPHome and Midea devices
    await initialize_all_devices()
    
    # Start schedule status monitoring task
    schedule_monitor_task = asyncio.create_task(check_schedule_status())
    logger.info("Schedule status monitor started")
    
    yield
    
    # Shutdown
    if schedule_monitor_task:
        schedule_monitor_task.cancel()
        logger.info("Schedule status monitor stopped")
        
    if esphome_manager:
        await esphome_manager.disconnect_all()
        
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
@app.get("/chambers", response_model=List[Chamber])
def get_chambers():
    """Get all chambers"""
    try:
        chambers = list(database.chambers.find())
        for chamber in chambers:
            chamber["_id"] = str(chamber["_id"])
        return chambers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chambers/{chamber_id}", response_model=Chamber)
def get_chamber(chamber_id: str):
    """Get specific chamber by ID"""
    try:
        if not ObjectId.is_valid(chamber_id):
            raise HTTPException(status_code=400, detail="Invalid chamber ID")
        
        chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
        if not chamber:
            raise HTTPException(status_code=404, detail="Chamber not found")
        chamber["_id"] = str(chamber["_id"])
        return chamber
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for backward compatibility
@app.get("/chamber", response_model=Chamber)
def get_first_chamber():
    """Get first chamber (legacy endpoint)"""
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
async def apply_controller(chamber_id: str, controller: DefineController):
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
    
    result = database.chambers.update_one({"_id": ObjectId(chamber_id)}, {"$set": {"is_active": True, "controllers": controllers_dict, "sum_sectors": new_sum_sectors.model_dump(), "updated_at": int(time())}})
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to apply controller")
    
    # Initialize ESPHome and Midea devices for new controllers
    try:
        await initialize_esphome_devices(controllers_dict)
        logger.info(f"ESPHome devices initialized for chamber {chamber_id}")
    except Exception as e:
        logger.error(f"Error initializing ESPHome devices: {e}")
    
    return Response(status_code=200, content="Controller applied successfully")

async def get_current_step(chamber_id: str) -> CurrentStep:
    """Get current active step for the chamber"""
    try:
        current_time = int(time())
        
        # Find active schedule for the chamber
        active_schedule_plc = database.schedule_plc.find_one({
            "chamber_id": chamber_id,
            "status": "active",
            "time_start": {"$lte": current_time},
            "time_end": {"$gte": current_time}
        })
        
        if not active_schedule_plc:
            return CurrentStep(is_active=False)
        
        # Get schedule details
        schedule = database.schedules.find_one({"_id": ObjectId(active_schedule_plc["schedule_id"])})
        if not schedule:
            logger.error(f"Schedule not found for ID: {active_schedule_plc['schedule_id']}")
            return CurrentStep(is_active=False)
        
        # Calculate elapsed time since schedule start
        elapsed_time = current_time - active_schedule_plc["time_start"]
        
        # Get scenario steps from the schedule PLC
        scenario_steps = active_schedule_plc.get("scenarios", {})
        schedule_scenarios = active_schedule_plc.get("schedule_scenarios", [])
        
        if not scenario_steps:
            logger.warning("No scenario steps found in schedule PLC")
            return CurrentStep(is_active=False)
        
        # Find current step based on elapsed time
        current_step = None
        current_scenario_name = None
        time_remaining = None
        
        # Calculate scenario durations based on schedule_scenarios
        total_elapsed = 0
        
        # Process schedule_scenarios to get proper durations
        # schedule_scenarios format: [[scenario_index, days_count], ...]
        for schedule_scenario in schedule_scenarios:
            if len(schedule_scenario) < 2:
                continue
                
            scenario_idx = schedule_scenario[0]
            days_count = schedule_scenario[1]
            scenario_duration = days_count * 86400  # days to seconds
            
            # Get scenario info from schedule
            scenario_name = f"Scenario {scenario_idx}"
            if scenario_idx < len(schedule.get("scenarios", [])):
                scenario_id = schedule["scenarios"][scenario_idx]
                scenario = database.scenarios.find_one({"_id": ObjectId(scenario_id)})
                if scenario:
                    scenario_name = scenario.get("name", scenario_name)
            
            # Check if elapsed time falls within this scenario
            if total_elapsed <= elapsed_time < total_elapsed + scenario_duration:
                
                # Get steps for this scenario
                scenario_key = str(scenario_idx)
                if scenario_key in scenario_steps:
                    steps = scenario_steps[scenario_key]
                    scenario_elapsed = elapsed_time - total_elapsed
                    
                    # Find current step within this scenario
                    for i, step in enumerate(steps):
                        step_start = step.get("relative_start_time", 0)
                        
                        # Calculate step end time
                        if i + 1 < len(steps):
                            next_step_start = steps[i + 1].get("relative_start_time", scenario_duration)
                        else:
                            next_step_start = scenario_duration
                        
                        if step_start <= scenario_elapsed < next_step_start:
                            current_step = step
                            current_scenario_name = scenario_name
                            time_remaining = next_step_start - scenario_elapsed
                            break
                    
                    if current_step:
                        break
                else:
                    logger.warning(f"No steps found for scenario key: {scenario_key}")
            
            total_elapsed += scenario_duration
        
        if not current_step:
            return CurrentStep(is_active=False)
        
        result = CurrentStep(
            step_id=f"{active_schedule_plc['schedule_id']}_{elapsed_time}",
            schedule_name=schedule.get("name", "Unknown Schedule"),
            scenario_name=current_scenario_name,
            temperature=current_step.get("temperature"),
            humidity=current_step.get("humidity"),
            co2=current_step.get("co2"),
            light_sectors=current_step.get("light_sectors"),
            relative_start_time=current_step.get("relative_start_time"),
            time_remaining=time_remaining,
            is_active=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting current step for chamber {chamber_id}: {e}")
        logger.error(traceback.format_exc())
        return CurrentStep(is_active=False)

async def get_chamber_dashboard_data(chamber_id: str) -> DashboardState:
    """Get dashboard data for a chamber from its ESPHome controllers"""
    try:
        # Get chamber data
        chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
        if not chamber:
            raise HTTPException(status_code=404, detail="Chamber not found")
        
        # Get controllers from chamber
        controllers = chamber.get("controllers", [])
        if not controllers:
            logger.warning(f"No controllers found for chamber {chamber_id}")
            return DashboardState(chamber_id=chamber_id, esp_devices=[], midea_devices=[])
        
        # Get ESPHome and Midea devices for this chamber
        esp_devices = await get_chamber_esphome_devices(controllers)
        midea_devices = await get_chamber_midea_devices(controllers)
        
        # Get current step information
        current_step = await get_current_step(chamber_id)

        return DashboardState(
            chamber_id=chamber_id,
            esp_devices=esp_devices,
            midea_devices=midea_devices,
            current_step=current_step,
            last_update=int(time()),
            auto_mode=True
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard data for chamber {chamber_id}: {e}")
        logger.error(traceback.format_exc())
        return DashboardState(
            chamber_id=chamber_id,
            esp_devices=[],
            midea_devices=[],
            current_step=CurrentStep(is_active=False),
            last_update=int(time()),
            auto_mode=True
        )

async def dashboard_event_generator(chamber_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for dashboard updates"""
    try:
        while True:
            # Get updated dashboard state from ESPHome controllers
            dashboard_state = await get_chamber_dashboard_data(chamber_id)
            # Update cached state
            dashboard_states[chamber_id] = dashboard_state
            
            # Format as SSE event
            data = json.dumps(dashboard_state.model_dump(), ensure_ascii=False)
            yield f"data: {data}\n\n"
            
            # Wait before next update
            await asyncio.sleep(3)  # Update every 3 seconds
            
    except Exception as e:
        logger.error(f"Error in dashboard event generator: {e}")
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
    
    # Get current dashboard state
    dashboard_state = await get_chamber_dashboard_data(chamber_id)
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
    
    # Get current dashboard state to find device
    dashboard_state = await get_chamber_dashboard_data(chamber_id)
    
    # Find the device and switch
    for device in dashboard_state.esp_devices:
        for switch in device.switches:
            if switch.switch_id == switch_id:
                # Extract switch key from switch_id (format: device_id_switch_key)
                switch_key = switch_id.split('_')[-1]  # Get the last part as switch key
                
                # Use ESPHome API to toggle switch
                success = await toggle_esphome_switch(device.device_id, switch_key, request.state)
                
                if success:
                    return {"success": True, "switch_id": switch_id, "state": request.state}
                else:
                    raise HTTPException(status_code=500, detail="Failed to send command to ESPHome controller")
    
    raise HTTPException(status_code=404, detail="Switch not found")

# ESPHome Management endpoints
@app.post("/chambers/{chamber_id}/reinitialize_esphome")
async def reinitialize_chamber_esphome(chamber_id: str):
    """Reinitialize ESPHome devices for a specific chamber"""
    if not ObjectId.is_valid(chamber_id):
        raise HTTPException(status_code=400, detail="Invalid chamber ID")
    
    try:
        chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
        if not chamber:
            raise HTTPException(status_code=404, detail="Chamber not found")
        
        controllers = chamber.get("controllers", [])
        await initialize_esphome_devices(controllers)
        
        return {"success": True, "message": "ESPHome devices reinitialized"}
        
    except Exception as e:
        logger.error(f"Error reinitializing ESPHome devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chambers/{chamber_id}/reinitialize_all")
async def reinitialize_chamber_all_devices(chamber_id: str):
    """Reinitialize all devices (ESPHome and Midea) for a specific chamber"""
    if not ObjectId.is_valid(chamber_id):
        raise HTTPException(status_code=400, detail="Invalid chamber ID")
    
    try:
        chamber = database.chambers.find_one({"_id": ObjectId(chamber_id)})
        if not chamber:
            raise HTTPException(status_code=404, detail="Chamber not found")
        
        controllers = chamber.get("controllers", [])
        await initialize_esphome_devices(controllers)
        discovered_devices = discover()
        ip_addresses = [i['ip_address'] for i in discovered_devices.values()]
        await initialize_midea_devices(ip_addresses)
        
        return {"success": True, "message": "All devices reinitialized"}
        
    except Exception as e:
        logger.error(f"Error reinitializing all devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/esphome/devices")
async def get_all_esphome_devices():
    """Get all ESPHome devices status"""
    try:
        devices = await esphome_manager.get_all_devices()
        return {"devices": [device.model_dump() for device in devices]}
    except Exception as e:
        logger.error(f"Error getting ESPHome devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/midea/devices")
async def get_all_midea_devices():
    """Get all Midea devices status"""
    try:
        devices = await midea_manager.get_all_devices()
        return {"devices": [device.model_dump() for device in devices]}
    except Exception as e:
        logger.error(f"Error getting Midea devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/esphome/devices/{device_name}/reconnect")
async def reconnect_esphome_device(device_name: str):
    """Force reconnect to a specific ESPHome device"""
    try:
        # Find device info from chambers first
        chambers = list(database.chambers.find())
        device_found = False
        target_controller = None
        
        for chamber in chambers:
            controllers = chamber.get("controllers", [])
            for controller in controllers:
                if (controller.get("controller_type") == "ESPHome" and 
                    controller.get("controller_name") == device_name):
                    target_controller = controller
                    device_found = True
                    break
            
            if device_found:
                break
        
        if not target_controller:
            raise HTTPException(status_code=404, detail="Device configuration not found")
        
        # Remove existing device first
        # Find the actual device_id from the device info
        device_to_remove = None
        devices = await esphome_manager.get_all_devices()
        for device in devices:
            if device.name == device_name:
                device_to_remove = device.device_id
                break
        
        if device_to_remove:
            success = await esphome_manager.remove_device(device_to_remove)
            logger.info(f"Removed device {device_to_remove}: {success}")
        
        # Re-add device with correct parameters
        ip_address = target_controller.get("controller_ip")
        if ip_address and device_name:
            await esphome_manager.add_device(ip_address, device_name)
            return {"success": True, "message": f"Device {device_name} reconnection initiated"}
        else:
            raise HTTPException(status_code=400, detail="Missing IP address or device name")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconnecting ESPHome device {device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/midea/devices/{device_id}/set_temperature")
async def set_midea_temperature(device_id: str, temperature: float):
    """Set target temperature for Midea device"""
    try:
        success = await midea_manager.set_target_temperature(device_id, temperature)
        if success:
            return {"success": True, "device_id": device_id, "temperature": temperature}
        else:
            raise HTTPException(status_code=500, detail="Failed to set temperature")
    except Exception as e:
        logger.error(f"Error setting temperature for Midea device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/midea/devices/{device_id}/set_fan_speed")
async def set_midea_fan_speed(device_id: str, fan_speed: int):
    """Set fan speed for Midea device"""
    try:
        success = await midea_manager.set_fan_speed(device_id, fan_speed)
        if success:
            return {"success": True, "device_id": device_id, "fan_speed": fan_speed}
        else:
            raise HTTPException(status_code=500, detail="Failed to set fan speed")
    except Exception as e:
        logger.error(f"Error setting fan speed for Midea device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/midea/devices/{device_id}/set_mode")
async def set_midea_mode(device_id: str, mode: int):
    """Set operating mode for Midea device"""
    try:
        success = await midea_manager.set_mode(device_id, mode)
        if success:
            return {"success": True, "device_id": device_id, "mode": mode}
        else:
            raise HTTPException(status_code=500, detail="Failed to set mode")
    except Exception as e:
        logger.error(f"Error setting mode for Midea device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/midea/devices/{device_id}/state")
async def get_midea_device_state(device_id: str):
    """Get current state of Midea device"""
    try:
        state = await midea_manager.get_device_state(device_id)
        if state:
            return {"device_id": device_id, "state": state}
        else:
            raise HTTPException(status_code=404, detail="Device not found")
    except Exception as e:
        logger.error(f"Error getting state for Midea device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
                            elif param_name == "watering":
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

@app.get("/schedules/status")
async def get_schedules_status():
    """Get status of all schedules with timing information"""
    try:
        current_time = int(time())
        schedules = list(database.schedules.find())
        
        schedule_statuses = []
        for schedule in schedules:
            schedule_status = {
                "id": str(schedule["_id"]),
                "name": schedule.get("name", "Unknown"),
                "status": schedule.get("status", "draft"),
                "chamber_id": schedule.get("chamber_id"),
                "time_start": schedule.get("time_start"),
                "time_end": schedule.get("time_end"),
                "current_time": current_time,
                "created_at": schedule.get("created_at"),
                "updated_at": schedule.get("updated_at")
            }
            
            # Add time-based info
            if schedule.get("time_start") and schedule.get("time_end"):
                if current_time < schedule["time_start"]:
                    schedule_status["time_until_start"] = schedule["time_start"] - current_time
                elif schedule["time_start"] <= current_time < schedule["time_end"]:
                    schedule_status["time_remaining"] = schedule["time_end"] - current_time
                    schedule_status["time_elapsed"] = current_time - schedule["time_start"]
                else:
                    schedule_status["time_since_end"] = current_time - schedule["time_end"]
            
            schedule_statuses.append(schedule_status)
        
        return {"schedules": schedule_statuses, "current_time": current_time}
        
    except Exception as e:
        logger.error(f"Error getting schedules status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedules/{schedule_id}/start")
async def start_schedule_now(schedule_id: str):
    """Start a schedule immediately for testing purposes"""
    if not ObjectId.is_valid(schedule_id):
        raise HTTPException(status_code=400, detail="Invalid schedule ID")
    
    try:
        current_time = int(time())
        
        # Get schedule to calculate duration
        schedule = database.schedules.find_one({"_id": ObjectId(schedule_id)})
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Calculate duration based on scenario schedules
        duration = 0
        if schedule.get("schedule_scenarios"):
            duration = sum(days[1] * 86400 for days in schedule["schedule_scenarios"])  # days * seconds per day
        else:
            duration = 86400  # Default 1 day
        
        time_end = current_time + duration
        
        # Update schedule status to active and set current time as start time
        result = database.schedules.update_one(
            {"_id": ObjectId(schedule_id)}, 
            {"$set": {
                "status": "active", 
                "time_start": current_time,
                "time_end": time_end,
                "updated_at": current_time
            }}
        )
        
        # Update schedule PLC status to active and timing
        plc_result = database.schedule_plc.update_one(
            {"schedule_id": schedule_id}, 
            {"$set": {
                "status": "active", 
                "time_start": current_time,
                "time_end": time_end,
                "updated_at": current_time
            }}
        )
        
        if result.modified_count > 0 or plc_result.modified_count > 0:
            return {
                "success": True, 
                "message": "Schedule started",
                "time_start": current_time,
                "time_end": time_end,
                "duration": duration
            }
        else:
            raise HTTPException(status_code=404, detail="Schedule not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


