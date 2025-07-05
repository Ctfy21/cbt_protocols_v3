from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pymongo import MongoClient
from bson import ObjectId
from typing import List
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from models import Schedule, Scenario, Chamber, SchedulePLC, PLCSteps, LightSector, WateringSector, Utils, ControlMode
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
                schedules=[]
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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
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
        chamber["_id"] = str(chamber["_id"])
        return chamber
    except Exception as e:
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
        schedule_plc = database.schedule_plc.find_one({"chamber_id": ObjectId(chamber_id)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schedules", response_model=Schedule)
def create_schedule(schedule: Schedule):
    """Create a new schedule"""
    try:
        chamber = database.chambers.find_one({"_id": ObjectId(schedule.chamber_id)})
        if chamber and schedule.time_start:
            schedule.time_end = schedule.time_start + 86400 * len(schedule.scenarios)
            schedule.status = "ready"
            schedule_dict = schedule.model_dump(exclude={"id"})

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
                        plc_steps.append(PLCSteps(
                            time_start=temp_time_start,
                            time_end=temp_time_start + 3600,
                            temperature=parameter.temperature,
                            humidity=parameter.humidity,
                            co2_level=parameter.co2_level,
                            light_sectors=[LightSector(sector_id=sector.sector_id, light_intensity=sector.light_intensity) for sector in parameter.light_sectors],
                            watering_sectors=[WateringSector(sector_id=sector.sector_id, watering_duration=sector.watering_duration) for sector in parameter.watering_sectors],
                            utils=parameter.utils
                        ))
                        temp_time_start += 3600
                else:
                    print(f"Warning: Scenario {schedule_scenario} has no parameters")
            if temp_time_start != schedule.time_end:
                raise HTTPException(status_code=500, detail="Time start and time end are not equal")
            
            result = database.schedules.insert_one(schedule_dict)
            schedule_dict["_id"] = str(result.inserted_id)
            print(str(result.inserted_id))
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
                schedule_id=str(result.inserted_id),
                status="ready",
                steps=plc_steps
            )
            schedule_plc_dict = schedule_plc.model_dump(exclude={"id"})
            result = database.schedule_plc.insert_one(schedule_plc_dict)


            return schedule_dict
        else:
            schedule.status = "draft"
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
                    plc_steps.append(PLCSteps(
                        time_start=temp_time_start,
                        time_end=temp_time_start + 3600,
                        temperature=parameter.temperature,
                        humidity=parameter.humidity,
                        co2_level=parameter.co2_level,
                        light_sectors=[LightSector(sector_id=sector.sector_id, light_intensity=sector.light_intensity) for sector in parameter.light_sectors],
                        watering_sectors=[WateringSector(sector_id=sector.sector_id, watering_duration=sector.watering_duration) for sector in parameter.watering_sectors],
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
            steps=plc_steps
        )
        result = database.schedules.update_one({"_id": ObjectId(schedule_id)}, {"$set": schedule.model_dump(exclude={"id"})})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Schedule PLC not found")
        schedule_plc_dict = schedule_plc.model_dump(exclude={"id"})
        result = database.schedule_plc.update_one({"schedule_id": ObjectId(schedule_id)}, {"$set": schedule_plc_dict})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Schedule PLC not found")

        return schedule_exists
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


