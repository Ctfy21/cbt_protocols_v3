from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from typing import Dict, Any, List
import logging
from contextlib import asynccontextmanager
import httpx
import socket
import asyncio
import json
from datetime import datetime
from midea_beautiful import appliance_state
from midealocal.discover import discover

backend_ip = "192.168.53.230"
define_cond_ips = ["192.168.53.248"]
key="1d69090b797d41e8a7c029810933725f62f64be143764abaaa6badbbf602fe88"
token="2ca510843ccf4c233e4ce8c177c8c9b4a79d967417bdb8307e47239bb4dd8918555a738d618431a15336d62abb79dc2472e0684c9779ca34b8e75978733975ab"





# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class CurrentStep(BaseModel):
    index: int = 0
    time_start: int = 0
    time_end: int = 0
    temperature: int = 21
    humidity: int = 60
    co2_level: int = 400
    light_sectors: List[float] = Field(default_factory=lambda: [0.0] * 50)
    light_sectors_count: int = 0
    watering_sectors: List[float] = Field(default_factory=lambda: [0.0] * 50)
    watering_sectors_count: int = 0

class SectorIds(BaseModel):
    temperature: List[str] = Field(default_factory=list)
    humidity: List[str] = Field(default_factory=list)
    co2: List[str] = Field(default_factory=list)
    light: List[str] = Field(default_factory=list)
    watering: List[str] = Field(default_factory=list)

class ScheduleData(BaseModel):
    schedule_id: str = ""
    auto_mode: bool = False
    time_start: int = 0
    time_end: int = 0
    chamber_id: str = ""
    schedule_reference: str = ""
    created_at: int = 0
    updated_at: int = 0
    status: str = ""
    steps_count: int = 0
    scenarios_json: str = ""
    schedule_scenarios_json: str = ""
    control_modes_json: str = ""
    sector_ids: SectorIds = Field(default_factory=SectorIds)
    current_step: CurrentStep = Field(default_factory=CurrentStep)

# Global instance of schedule data
schedule_data = ScheduleData()

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket connection to determine the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to a remote address (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception as e:
        logger.error(f"Failed to get local IP: {str(e)}")
        return "localhost"

async def fetch_schedule_data():
    """Fetch schedule data from the server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{backend_ip}:8000/schedules/plc/6881f2dd82037cf38b8d27fa",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched schedule data. Size: {len(response.content)} bytes")
                return data
            else:
                logger.error(f"Failed to fetch schedule data. Status code: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error fetching schedule data: {str(e)}")
        return None

def parse_schedule_data(data):
    """Parse and store schedule data in global variables"""
    if not data:
        return
    
    try:
        # Store basic values
        schedule_data.schedule_id = data.get("_id", "")
        schedule_data.auto_mode = data.get("auto", False)
        schedule_data.time_start = data.get("time_start", 0)
        schedule_data.time_end = data.get("time_end", 0)
        schedule_data.chamber_id = data.get("chamber_id", "")
        schedule_data.schedule_reference = data.get("schedule_id", "")
        schedule_data.created_at = data.get("created_at", 0)
        schedule_data.updated_at = data.get("updated_at", 0)
        schedule_data.status = data.get("status", "")
        
        # Store scenarios and schedule_scenarios as JSON strings
        if "scenarios" in data and "schedule_scenarios" in data:
            schedule_data.scenarios_json = json.dumps(data["scenarios"])
            schedule_data.schedule_scenarios_json = json.dumps(data["schedule_scenarios"])
            schedule_data.steps_count = len(data["schedule_scenarios"])
        
        # Store control_modes
        if "control_modes" in data:
            schedule_data.control_modes_json = json.dumps(data["control_modes"])
        
        # Store sector_ids
        if "sector_ids" in data:
            sector_ids = data["sector_ids"]
            schedule_data.sector_ids.temperature = sector_ids.get("temperature", [])
            schedule_data.sector_ids.humidity = sector_ids.get("humidity", [])
            schedule_data.sector_ids.co2 = sector_ids.get("co2", [])
            schedule_data.sector_ids.light = sector_ids.get("light", [])
            schedule_data.sector_ids.watering = sector_ids.get("watering", [])
        
        logger.info(f"Parsed schedule data: ID={schedule_data.schedule_id}, auto={schedule_data.auto_mode}")
        
    except Exception as e:
        logger.error(f"Error parsing schedule data: {str(e)}")

def find_current_step():
    """Find and load current step based on current time"""
    try:
        if not schedule_data.scenarios_json or not schedule_data.schedule_scenarios_json:
            logger.warning("No scenario data available")
            return
        
        scenarios = json.loads(schedule_data.scenarios_json)
        schedule_scenarios = json.loads(schedule_data.schedule_scenarios_json)
        
        current_timestamp = int(datetime.now().timestamp())
        schedule_start = schedule_data.time_start
        elapsed_time = current_timestamp - schedule_start
        
        # Find current scenario and step
        time_offset = 0
        found_scenario = -1
        found_step = -1
        found_day = -1
        
        for i, scenario_info in enumerate(schedule_scenarios):
            if len(scenario_info) >= 2:
                scenario_index = scenario_info[0]
                days_count = scenario_info[1]
                
                scenario_key = str(scenario_index)
                
                if scenario_key in scenarios:
                    scenario_steps = scenarios[scenario_key]
                    
                    # Check each day in this scenario
                    for day in range(days_count):
                        day_start = time_offset + (day * 86400)  # 86400 seconds in a day
                        day_end = day_start + 86400
                        
                        if elapsed_time >= day_start and elapsed_time < day_end:
                            # Found the day, now find the step
                            day_elapsed = elapsed_time - day_start
                            
                            for step_idx, scenario_step in enumerate(scenario_steps):
                                step_start = scenario_step["relative_start_time"]
                                step_end = scenario_steps[step_idx + 1]["relative_start_time"] if step_idx + 1 < len(scenario_steps) else 86400
                                
                                if day_elapsed >= step_start and day_elapsed < step_end:
                                    found_scenario = i
                                    found_step = step_idx
                                    found_day = day
                                    break
                            
                            if found_scenario != -1:
                                break
                    
                    if found_scenario != -1:
                        break
                    time_offset += days_count * 86400
        
        # Load the found step or use defaults
        if found_scenario != -1 and found_step != -1:
            scenario_info = schedule_scenarios[found_scenario]
            scenario_index = scenario_info[0]
            scenario_key = str(scenario_index)
            scenario_steps = scenarios[scenario_key]
            step = scenario_steps[found_step]
            
            # Store step information
            schedule_data.current_step.index = found_step
            schedule_data.current_step.time_start = schedule_start + time_offset + (found_day * 86400) + step["relative_start_time"]
            
            step_end_relative = scenario_steps[found_step + 1]["relative_start_time"] if found_step + 1 < len(scenario_steps) else 86400
            schedule_data.current_step.time_end = schedule_start + time_offset + (found_day * 86400) + step_end_relative
            
            schedule_data.current_step.temperature = step.get("temperature", 21)

            
            logger.info(f"Found step: scenario={found_scenario}, day={found_day}, step={found_step}")
            logger.info(f"Step values - temp: {schedule_data.current_step.temperature}")
            
        
        else:
            logger.info("No current step found, using defaults")
            schedule_data.current_step.index = 0
            schedule_data.current_step.temperature = 20
            schedule_data.current_step.humidity = 50
            schedule_data.current_step.co2_level = 400
            schedule_data.current_step.light_sectors = [0.0] * 50
            schedule_data.current_step.watering_sectors = [0.0] * 50
            schedule_data.current_step.light_sectors_count = 0
            schedule_data.current_step.watering_sectors_count = 0
    
    except Exception as e:
        logger.error(f"Error finding current step: {str(e)}")

async def execute_current_step():
    """Execute the current step - implement device control logic here"""
    try:
        current_step = schedule_data.current_step
        
        # TODO: Implement actual device control logic here
        # For example:
        # - Set temperature to current_step["temperature"]
        
        logger.info(f"Executing step {current_step.index}: "
                   f"temp={current_step.temperature}")

        for ip in define_cond_ips:
            appliance = appliance_state(
                address=ip,
                token=token,
                key=key,
            )
            appliance.state.target_temperature = current_step.temperature
            appliance.apply()
            appliance.refresh()
            logger.info(f"Midea device {ip} set to {current_step.temperature}")
        

        
    except Exception as e:
        logger.error(f"Error executing current step: {str(e)}")

async def schedule_timer():
    """Timer function that runs every 60 seconds"""
    while True:
        try:
            logger.info("Fetching schedule data...")
            
            # Fetch schedule data
            data = await fetch_schedule_data()
            if data:
                # Parse the data
                parse_schedule_data(data)
                
                # Find and load current step
                find_current_step()
                
                # Execute current step
                await execute_current_step()
            
        except Exception as e:
            logger.error(f"Error in schedule timer: {str(e)}")
        
        # Wait for 60 seconds
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    local_ip = get_local_ip()
    logger.info(f"Local IP address: {local_ip}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{backend_ip}:8000/chambers/6881f2dd82037cf38b8d27fa/apply_controller",  # Replace with your desired URL
                json={
                    "controller_name": "midea_controller",
                    "controller_ip": "192.168.53.248",  # Use dynamic local IP
                    "controller_type": "Midea",
                    "settings": {
                        "temperature": {
                            "sectors": 1,
                        }
                    }
                },
                timeout=10.0
            )
            logger.info(f"Startup POST request sent. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send startup POST request: {str(e)}")
    
    # Start the schedule timer task
    timer_task = asyncio.create_task(schedule_timer())
    
    yield
    
    # Shutdown - cancel the timer task
    timer_task.cancel()
    try:
        await timer_task
    except asyncio.CancelledError:
        logger.info("Schedule timer task cancelled")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/devices")
async def list_devices():
    """List available Midea devices"""
    
    discovered_devices = discover()
    devices = [i for i in discovered_devices.values()]

    return {
        "devices": devices,
    }

@app.get("/schedule/status")
async def get_schedule_status():
    """Get current schedule status and step information"""
    try:
        return {
            "status": "success",
            "schedule_data": {
                "schedule_id": schedule_data.schedule_id,
                "auto_mode": schedule_data.auto_mode,
                "time_start": schedule_data.time_start,
                "time_end": schedule_data.time_end,
                "chamber_id": schedule_data.chamber_id,
                "status": schedule_data.status,
                "steps_count": schedule_data.steps_count
            },
            "current_step": schedule_data.current_step.dict(),
            "sector_ids": schedule_data.sector_ids.dict()
        }
    except Exception as e:
        logger.error(f"Error getting schedule status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedule status: {str(e)}")

@app.post("/schedule/refresh")
async def refresh_schedule():
    """Manually refresh schedule data"""
    try:
        logger.info("Manual schedule refresh requested")
        
        # Fetch schedule data
        data = await fetch_schedule_data()
        if data:
            # Parse the data
            parse_schedule_data(data)
            
            # Find and load current step
            find_current_step()
            
            # Execute current step
            await execute_current_step()
            
            return {
                "status": "success",
                "message": "Schedule refreshed successfully",
                "current_step": schedule_data.current_step.dict()
            }
        else:
            return {
                "status": "error",
                "message": "Failed to fetch schedule data"
            }
    except Exception as e:
        logger.error(f"Error refreshing schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh schedule: {str(e)}")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
