from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pymongo import MongoClient
from bson import ObjectId
from typing import List
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from models import Schedule, Scenario, Chamber, Status

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
# @app.get("/schedules/plc/{chamber_id}", response_model=List[SchedulePLC])
# def get_schedules_plc(chamber_id: str, duration_months: int = 3):
#     """Get all schedules for PLC"""
#     try:
#         schedules = list(database.chambers.find_one({"id": chamber_id})["schedules"])
#         for schedule in schedules:
#             schedule["_id"] = str(schedule["_id"])

#         return schedules
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/schedules", response_model=Schedule)
def create_schedule(schedule: Schedule, chamber_id: str | None = None):
    """Create a new schedule"""
    try:
        if chamber_id and schedule.time_start:
            schedule.time_end = schedule.time_start + 86400 * len(schedule.scenarios)
            schedule.status = Status.READY
            schedule.chamber_id = chamber_id
            schedule_dict = schedule.model_dump(exclude={"id"})
            result = database.schedules.insert_one(schedule_dict)
            schedule_dict["_id"] = str(result.inserted_id)
            return schedule_dict
        else:
            schedule.status = Status.DRAFT
            schedule_dict = schedule.model_dump(exclude={"id"})
            result = database.schedules.insert_one(schedule_dict)
            schedule_dict["_id"] = str(result.inserted_id)
            return schedule_dict
    except Exception as e:
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


