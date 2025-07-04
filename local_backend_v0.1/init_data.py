from models import Schedule, Scenario, Parameters, LightSector, WateringSector
from pymongo import MongoClient
from datetime import datetime, time
import math

# MongoDB connection
mongodb_client = MongoClient('mongodb://localhost:27017')
database = mongodb_client.get_database("default_db")

def generate_24_hour_scenarios():
    """Generate 24 scenarios with realistic hourly variations"""
    parameters = []
    
    for hour in range(24):
        # Simulate natural light cycle (higher during day, lower at night)
        if 6 <= hour <= 18:  # Day time
            base_light = 80
            base_temp = 24
            base_humidity = 65
            base_co2 = 400
        else:  # Night time
            base_light = 20
            base_temp = 20
            base_humidity = 70
            base_co2 = 350
        
        # Add some variation based on hour
        light_variation = int(20 * math.sin(math.pi * hour / 12))
        temp_variation = int(3 * math.sin(math.pi * hour / 12))
        humidity_variation = int(5 * math.cos(math.pi * hour / 12))
        co2_variation = int(50 * math.sin(math.pi * hour / 12))
        
        # Calculate final values
        light_intensity = max(10, min(100, base_light + light_variation))
        temperature = max(18, min(30, base_temp + temp_variation))
        humidity = max(50, min(80, base_humidity + humidity_variation))
        co2_level = max(300, min(500, base_co2 + co2_variation))
        
        # Create light sectors (3 sectors with varying intensities)
        light_sectors = [
            LightSector(sector_id=1, light_intensity=light_intensity),
            LightSector(sector_id=2, light_intensity=max(0, light_intensity - 10)),
            LightSector(sector_id=3, light_intensity=max(0, light_intensity - 20))
        ]
        
        # Create watering sectors (water every 4 hours during day, less at night)
        watering_duration = 30 if hour % 4 == 0 and 6 <= hour <= 18 else 0
        if hour in [22, 2]:  # Light watering at night
            watering_duration = 10
            
        watering_sectors = [
            WateringSector(sector_id=1, watering_duration=watering_duration),
            WateringSector(sector_id=2, watering_duration=watering_duration),
            WateringSector(sector_id=3, watering_duration=max(0, watering_duration - 10))
        ]
        
        # Create scenario parameters
        param = Parameters(
            temperature=temperature,
            humidity=humidity,
            light_sectors=light_sectors,
            co2_level=co2_level,
            watering_sectors=watering_sectors
        )

        parameters.append(param)
        
    # Create scenario with all 24 parameters
    scenario = Scenario(
        name="24-Hour Complete Cycle",
        description="Complete 24-hour growing cycle with all hourly variations",
        parameters=parameters
    )
    
    return scenario

def create_schedule_with_scenarios(scenario_ids):
    """Create a 24-hour schedule using the generated scenarios"""
    schedule = Schedule(
        name="24-Hour Growing Cycle",
        description="Complete 24-hour automated growing cycle with hourly variations",
        time_start=0,  # 00:00
        time_end=23,   # 23:00
        scenarios=scenario_ids
    )
    
    return schedule

def init_database():
    """Initialize database with 24-hour scenarios and schedule"""
    print("🌱 Generating 24-hour growing scenario...")
    
    # Generate scenario with all 24 steps
    scenario = generate_24_hour_scenarios()
    
    # Clear existing data
    database.scenarios.delete_many({})
    database.schedules.delete_many({})
    
    # Insert scenario
    scenario_dict = scenario.model_dump(exclude={"id"})
    result = database.scenarios.insert_one(scenario_dict)
    scenario_id = str(result.inserted_id)
    print(f"✅ Created scenario: {scenario.name} with {len(scenario.parameters)} parameters")
    
    # Create schedule
    schedule = create_schedule_with_scenarios([scenario_id])
    schedule_dict = schedule.model_dump(exclude={"id"})
    schedule_result = database.schedules.insert_one(schedule_dict)
    
    print(f"✅ Created schedule: {schedule.name}")
    print(f"📋 Schedule ID: {schedule_result.inserted_id}")
    print(f"🔗 Using scenario: {scenario_id}")
    
    # Print summary
    print("\n📊 Summary:")
    print(f"- Scenario created with {len(scenario.parameters)} hourly parameters")
    print(f"- Schedule spans: {schedule.time_start}:00 to {schedule.time_end}:00")
    print(f"- Database collections: scenarios, schedules")
    
    return schedule_result.inserted_id, [scenario_id]

if __name__ == "__main__":
    try:
        schedule_id, scenario_ids = init_database()
        print(f"\n🎉 Initialization complete!")
        print(f"🔗 Schedule ID: {schedule_id}")
        print(f"🌐 Test your API at: http://localhost:8000/schedules/{schedule_id}")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
    finally:
        mongodb_client.close()
        print("🔌 Database connection closed") 