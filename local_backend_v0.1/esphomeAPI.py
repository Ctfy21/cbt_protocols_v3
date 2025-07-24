import aioesphomeapi
import asyncio
import logging
import math
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from models import SensorReading, SwitchState, ESPHomeDevice
from time import time
import traceback
# Configure logging
logger = logging.getLogger(__name__)

class ESPHomeManager:
    """Manages connections and state for ESPHome devices"""
    
    def __init__(self):
        self.devices: Dict[str, aioesphomeapi.APIClient] = {}
        self.device_states: Dict[str, Dict] = {}
        self.state_callbacks: List[Callable] = []
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.reconnect_tasks: Dict[str, asyncio.Task] = {}
        self.device_info: Dict[str, ESPHomeDevice] = {}
        self.api_to_device_id: Dict[aioesphomeapi.APIClient, str] = {}  # Mapping API client to device ID
        
    async def add_device(self, ip_address: str, device_name: str, port: int = 6053, password: str = ""):
        """Add and connect to an ESPHome device"""
        device_id = None
        try:
            logger.info(f"Adding ESPHome device: {device_name} ({ip_address})")
            
            # Create API client
            api = aioesphomeapi.APIClient(ip_address, port, password)
            
            # Connect temporarily to get device information
            await api.connect(login=True)
            
            # Get device information to extract device_id
            device_info = await api.device_info()
            entities = await api.list_entities_services()
            device_id = str(entities[0][0].device_id)
            
            # Disconnect temporarily - _connect_device will handle the persistent connection
            await api.disconnect()
            
            self.devices[device_id] = api
            self.api_to_device_id[api] = device_id  # Store mapping
            
            # Initialize device state
            self.device_states[device_id] = {
                'sensors': {},
                'switches': {},
                'last_update': int(time()),
                'status': 'connecting'
            }
            
            # Start connection task
            task = asyncio.create_task(self._connect_device(device_id, device_name, ip_address))
            self.connection_tasks[device_id] = task
            
            return True
            
        except Exception as e:
            error_msg = f"Error adding device {device_name}"
            if device_id:
                error_msg = f"Error adding device {device_name} (ID: {device_id})"
            logger.error(f"{error_msg}: {e}")
            return False
    
    async def _connect_device(self, device_id: str, device_name: str, ip_address: str):
        """Connect to device and start state subscription"""
        api = self.devices[device_id]
        
        try:
            logger.info(f"Connecting to ESPHome device: {device_id}")
            
            # Connect to device
            await api.connect(login=True)
            
            # Get device information
            device_info = await api.device_info()
            logger.info(f"Connected to {device_info.name} (ESPHome {device_info.esphome_version})")
            
            # List all entities
            entities = await api.list_entities_services()
            

            # Create ESPHomeDevice object
            esphome_device = ESPHomeDevice(
                device_id=device_id,
                name=device_name,
                ip_address=ip_address,
                status="online",
                sensors=[],
                switches=[]
            )
            logger.info(f"ESPHome device {device_name} with device_id {device_id} has {len(entities)} entities")
            # Process entities and create initial state
            for entity in entities[0]:
                if isinstance(entity, aioesphomeapi.SensorInfo):
                    sensor_type = self._map_sensor_type(entity.name, entity.unit_of_measurement)
                    if sensor_type:
                        sensor = SensorReading(
                            sensor_id=f"{device_id}_{entity.key}",
                            name=entity.name,
                            sensor_type=sensor_type,
                            value=0.0,  # Will be updated from state
                            unit=entity.unit_of_measurement or "",
                            timestamp=int(time()),
                            status="online"
                        )
                        esphome_device.sensors.append(sensor)
                        
                elif isinstance(entity, aioesphomeapi.SwitchInfo):
                    switch = SwitchState(
                        switch_id=f"{device_id}_{entity.key}",
                        name=entity.name,
                        state=False,  # Will be updated from state
                        timestamp=int(time())
                    )
                    esphome_device.switches.append(switch)
            
            self.device_info[device_id] = esphome_device
            self.device_states[device_id]['status'] = 'online'
            
            # Subscribe to state changes
            api.subscribe_states(self._on_state_change)
            
            logger.info(f"Successfully connected and subscribed to {device_id}")
            logger.info(f"Device {device_id} has {len(esphome_device.sensors)} sensors and {len(esphome_device.switches)} switches")
        
        except aioesphomeapi.APIConnectionError as e:
            logger.error(f"Connection error to device {device_id}: {e}")
            if device_id in self.device_states:
                self.device_states[device_id]['status'] = 'offline'
            # Schedule reconnection
            await self._schedule_reconnect(device_id, device_name, ip_address)
            
        except aioesphomeapi.InvalidAuthAPIError as e:
            logger.error(f"Authentication error to device {device_id}: {e}")
            if device_id in self.device_states:
                self.device_states[device_id]['status'] = 'auth_error'
            
        except Exception as e:
            logger.error(f"Unexpected error connecting to device {device_name}: {type(e)}: {e}")
            logger.error(traceback.format_exc())
            if device_id in self.device_states:
                self.device_states[device_id]['status'] = 'error'
            # Schedule reconnection for unexpected errors
            await self._schedule_reconnect(device_id, device_name, ip_address)
        
    async def _schedule_reconnect(self, device_id: str, device_name: str, ip_address: str, delay: int = 30):
        """Schedule device reconnection"""
        logger.info(f"Scheduling reconnection for {device_id} in {delay} seconds")
        
        await asyncio.sleep(delay)
        
        # Try to reconnect
        try:
            # Ensure the API mapping is still valid
            if device_id in self.devices:
                api = self.devices[device_id]
                self.api_to_device_id[api] = device_id
                
            task = asyncio.create_task(self._connect_device(device_id, device_name, ip_address))
            self.connection_tasks[device_id] = task
        except Exception as e:
            logger.error(f"Error scheduling reconnection for {device_id}: {e}")
    
    def _on_state_change(self, state: aioesphomeapi.EntityState):
        """Handle state changes from ESPHome devices"""
        try:
            # Find device using state's device_id or key
            device_id = None
            
            # Try to get device_id from state object
            if hasattr(state, 'device_id') and state.device_id:
                device_id = state.device_id
            else:
                # Fallback: search for device by entity key
                logger.debug(f"No device_id in state, searching by key: {state.key}")
                for dev_id, device_info in self.device_info.items():
                    # Check sensors
                    for sensor in device_info.sensors:
                        if sensor.sensor_id.endswith(str(state.key)):
                            device_id = dev_id
                            break
                    
                    # Check switches if not found in sensors
                    if not device_id:
                        for switch in device_info.switches:
                            if switch.switch_id.endswith(str(state.key)):
                                device_id = dev_id
                                break
                    
                    if device_id:
                        break
            
            if not device_id:
                logger.debug(f"Could not find device for state change (key: {state.key}, type: {type(state).__name__})")
                return
            
            logger.debug(f"Processing state change for device {device_id}, key: {state.key}, type: {type(state).__name__}")
            
            # Update state based on entity type
            if isinstance(state, aioesphomeapi.SensorState):
                if device_id in self.device_states:
                    self.device_states[device_id]['sensors'][state.key] = {
                        'value': state.state,
                        'timestamp': int(time())
                    }
                
                # Update ESPHomeDevice sensor
                if device_id in self.device_info:
                    for sensor in self.device_info[device_id].sensors:
                        if sensor.sensor_id.endswith(str(state.key)):
                            try:
                                # Handle different state types
                                if state.state is not None:
                                    sensor.value = round(self._safe_float_value(state.state), 1)
                                    sensor.timestamp = int(time())
                                    sensor.status = "online"
                                else:
                                    sensor.status = "error"
                            except Exception as e:
                                logger.warning(f"Error updating sensor {sensor.sensor_id}: {e}")
                                sensor.status = "error"
                            
            elif isinstance(state, aioesphomeapi.SwitchState):
                if device_id in self.device_states:
                    self.device_states[device_id]['switches'][state.key] = {
                        'state': state.state,
                        'timestamp': int(time())
                    }
                
                # Update ESPHomeDevice switch
                if device_id in self.device_info:
                    for switch in self.device_info[device_id].switches:
                        if switch.switch_id.endswith(str(state.key)):
                            switch.state = bool(state.state)
                            switch.timestamp = int(time())
            
            if device_id in self.device_states:
                self.device_states[device_id]['last_update'] = int(time())
            
            # Notify callbacks
            self._notify_state_callbacks(device_id, state)
            
        except Exception as e:
            logger.error(f"Error handling state change: {e}", exc_info=True)
    
    def _notify_state_callbacks(self, device_id: str, state: aioesphomeapi.EntityState):
        """Notify registered callbacks about state changes"""
        for callback in self.state_callbacks:
            try:
                asyncio.create_task(callback(device_id, state))
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def _safe_float_value(self, value) -> float:
        """Safely convert value to float, handling NaN and infinite values"""
        try:
            if value is None:
                return 0.0
            
            float_val = float(value)
            
            # Check for NaN and infinite values using math functions
            if math.isnan(float_val) or math.isinf(float_val):
                logger.warning(f"Invalid float value detected: {value}, returning 0.0")
                return 0.0
            
            return float_val
            
        except (ValueError, TypeError, OverflowError):
            logger.warning(f"Could not convert value to float: {value}, returning 0.0")
            return 0.0
    
    
    async def get_device_state(self, device_name: str) -> Optional[ESPHomeDevice]:
        """Get current state of a device"""
        for device_id, device in self.device_info.items():
            if device.name == device_name:
                return device
        return None
    
    async def get_all_devices(self) -> List[ESPHomeDevice]:
        """Get state of all devices"""
        devices = []
        for device in self.device_info.values():
            # Create a copy and ensure all sensor values are safe
            device_copy = device.model_copy()
            for sensor in device_copy.sensors:
                sensor.value = self._safe_float_value(sensor.value)
            devices.append(device_copy)
        return devices
    
    def add_state_callback(self, callback: Callable):
        """Add callback for state changes"""
        self.state_callbacks.append(callback)

    def get_connection_info(self) -> Dict[str, Dict[str, Any]]:
        """Get connection information for all devices"""
        info = {}
        for device_id in self.devices:
            info[device_id] = {
                'status': self.device_states.get(device_id, {}).get('status', 'unknown'),
                'last_update': self.device_states.get(device_id, {}).get('last_update', 0),
                'has_connection_task': device_id in self.connection_tasks,
                'has_reconnect_task': device_id in self.reconnect_tasks,
                'sensors_count': len(self.device_info.get(device_id, ESPHomeDevice(device_id="", name="", ip_address="")).sensors),
                'switches_count': len(self.device_info.get(device_id, ESPHomeDevice(device_id="", name="", ip_address="")).switches)
            }
        return info
    
    async def remove_device(self, device_id: str) -> bool:
        """Remove and disconnect from an ESPHome device"""
        try:
            if device_id not in self.devices:
                logger.warning(f"Device {device_id} not found for removal")
                return False
            
            logger.info(f"Removing ESPHome device: {device_id}")
            
            # Cancel connection task if running
            if device_id in self.connection_tasks:
                self.connection_tasks[device_id].cancel()
                del self.connection_tasks[device_id]
            
            # Cancel reconnection task if running
            if device_id in self.reconnect_tasks:
                self.reconnect_tasks[device_id].cancel()
                del self.reconnect_tasks[device_id]
            
            # Disconnect API client
            api = self.devices[device_id]
            try:
                await api.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting from device {device_id}: {e}")
            
            # Clean up mappings
            if api in self.api_to_device_id:
                del self.api_to_device_id[api]
            
            # Remove from collections
            del self.devices[device_id]
            
            if device_id in self.device_states:
                del self.device_states[device_id]
            
            if device_id in self.device_info:
                del self.device_info[device_id]
            
            logger.info(f"Successfully removed device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing device {device_id}: {e}")
            return False
    
    async def set_switch_state(self, device_id: str, switch_key: str, state: bool) -> bool:
        """Set switch state on ESPHome device"""
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return False
            
            api = self.devices[device_id]
            
            # Get entities to find switch info
            entities = await api.list_entities_services()
            switch_info = None
            
            for entity in entities[0]:
                if isinstance(entity, aioesphomeapi.SwitchInfo) and entity.key == int(switch_key):
                    switch_info = entity
                    break
            
            if not switch_info:
                logger.error(f"Switch {switch_key} not found on device {device_id}")
                return False
            
            # Send switch command
            api.switch_command(switch_info.key, state)
            logger.info(f"Switch {switch_info.name} set to {state} on device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting switch state: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _map_sensor_type(self, sensor_name: str, unit: str) -> Optional[str]:
        """Map ESPHome sensor to our sensor types"""
        sensor_name_lower = sensor_name.lower()
        unit_lower = (unit or "").lower()
        
        if "temp" in sensor_name_lower or "°c" in unit_lower or "celsius" in unit_lower:
            return "temperature"
        elif "hum" in sensor_name_lower or "%" in unit_lower:
            return "humidity"
        elif "co2" in sensor_name_lower or "ppm" in unit_lower:
            return "co2"
        elif "light" in sensor_name_lower or "lux" in unit_lower or "ppfd" in sensor_name_lower:
            return "light"
        elif "ph" in sensor_name_lower:
            return "ph"
        elif "water" in sensor_name_lower and "level" in sensor_name_lower:
            return "water_level"
        
        return None
    
    def _map_switch_type(self, switch_name: str) -> str:
        """Map ESPHome switch to our switch types"""
        switch_name_lower = switch_name.lower()
        
        if "light" in switch_name_lower or "led" in switch_name_lower:
            return "light"
        elif "pump" in switch_name_lower:
            return "pump"
        elif "fan" in switch_name_lower or "ventilator" in switch_name_lower:
            return "fan"
        elif "heat" in switch_name_lower:
            return "heater"
        elif "cool" in switch_name_lower:
            return "cooler"
        elif "valve" in switch_name_lower:
            return "valve"
        
        return "fan"  # Default type
    
    def _determine_sector_id(self, entity_name: str, device_type: str) -> str:
        """Determine sector ID based on device name and type"""
        import re
        
        # Look for patterns like "sector_1", "zone_a", "area_2", etc.
        patterns = [
            r"sector[_\-]?(\w+)",
            r"zone[_\-]?(\w+)",
            r"area[_\-]?(\w+)",
            r"([a-zA-Z])$",  # Single letter at the end
            r"(\d+)$"       # Number at the end
        ]
        
        for pattern in patterns:
            match = re.search(pattern, entity_name.lower())
            if match:
                return match.group(1).upper()
        
        # Default sector ID based on device type
        if device_type in ["light"]:
            return "A"
        else:
            return "1"
    
    async def disconnect_all(self):
        """Disconnect from all devices"""
        logger.info("Disconnecting from all ESPHome devices")
        
        # Cancel all tasks
        for task in self.connection_tasks.values():
            task.cancel()
        
        for task in self.reconnect_tasks.values():
            task.cancel()
        
        # Disconnect all devices
        for device_id, api in self.devices.items():
            try:
                await api.disconnect()
                logger.info(f"Disconnected from device {device_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from device {device_id}: {e}")
        
        # Clear all data
        self.devices.clear()
        self.device_states.clear()
        self.device_info.clear()
        self.connection_tasks.clear()
        self.reconnect_tasks.clear()
        self.api_to_device_id.clear()

# Global ESPHome manager instance
esphome_manager = ESPHomeManager()

async def initialize_esphome_devices(controllers: List[Dict]) -> None:
    """Initialize ESPHome devices from controller configuration"""
    logger.info("Initializing ESPHome devices")
    
    for controller in controllers:
        if controller.get("controller_type") == "ESPHome":
            ip_address = controller.get("controller_ip")
            device_name = controller.get("controller_name")
            
            if ip_address and device_name:
                await esphome_manager.add_device(ip_address, device_name)
            else:
                logger.warning(f"Missing IP or name for controller: {controller}")

async def get_chamber_esphome_devices(chamber_controllers: List[Dict]) -> List[ESPHomeDevice]:
    """Get ESPHome devices for a specific chamber"""
    devices = []
    
    for controller in chamber_controllers:
        if controller.get("controller_type") == "ESPHome":
            device_name = controller.get("controller_name")
            device = await esphome_manager.get_device_state(device_name)
            if device:
                devices.append(device)
    
    return devices

async def toggle_esphome_switch(device_id: str, switch_key: str, state: bool) -> bool:
    """Toggle switch on ESPHome device"""
    # Extract switch key from switch_id
    return await esphome_manager.set_switch_state(device_id, switch_key, state)

# Testing function
async def test_connection(ip_address: str = "test.local"):
    """Test connection to ESPHome device"""
    try:
        await esphome_manager.add_device("test_device", ip_address, "Test Device")
        await asyncio.sleep(5)  # Wait for connection
        
        device = await esphome_manager.get_device_state("test_device")
        if device:
            print(f"Connected to: {device.name}")
            print(f"Sensors: {len(device.sensors)}")
            print(f"Switches: {len(device.switches)}")
        else:
            print("Failed to connect")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())