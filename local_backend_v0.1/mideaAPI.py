from midealocal.discover import discover
from midea_beautiful import appliance_state
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from models import DefineController, MideaDevice, Climate
from time import time
import traceback



# Configure logging
logger = logging.getLogger(__name__)

class MideaController:
    """Manages connections and control for Midea air conditioner devices"""
    
    def __init__(self):
        self.devices: Dict[str, Any] = {}  # device_id -> appliance object
        self.device_states: Dict[str, Dict] = {}
        self.state_callbacks: List[Callable] = []
        self.device_info: Dict[str, MideaDevice] = {}
        self.token = "2ca510843ccf4c233e4ce8c177c8c9b4a79d967417bdb8307e47239bb4dd8918555a738d618431a15336d62abb79dc2472e0684c9779ca34b8e75978733975ab"
        self.key = "1d69090b797d41e8a7c029810933725f62f64be143764abaaa6badbbf602fe88"
        
    async def add_device(self, ip_address: str):
        """Add and connect to a Midea air conditioner device"""
        device_id = None
        try:
            logger.info(f"Adding Midea device: {ip_address}")
            
            # Create appliance connection
            appliance = appliance_state(
                address=ip_address,
                token=self.token,
                key=self.key,
            )
            
            # Use IP as device_id for simplicity (could be improved)
            device_id = ip_address.replace('.', '_')
            
            self.devices[device_id] = appliance
            
            # Initialize device state
            self.device_states[device_id] = {
                'target_temperature': None,
                'fan_speed': None,
                'mode': None,
                'indoor_temperature': None,
                'outdoor_temperature': None,
                'last_update': int(time()),
                'status': 'connecting'
            }
            
            # Store device info
            self.device_info[device_id] = MideaDevice(
                device_id=device_id,
                name=appliance.name,
                ip_address=ip_address,
                status='online',
                climate=Climate(
                    indoor_temperature=0.0,
                    outdoor_temperature=0.0,
                    target_temperature=20,
                    fan_speed=0,
                    mode='off'
                )
            )
            
            # Initial state refresh
            await self.refresh_device_state(device_id)
            
            logger.info(f"Successfully added Midea device: {appliance.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding device: {e}")
            return False
    
    async def refresh_device_state(self, device_id: str):
        """Refresh the current state of a device"""
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return False
            
            appliance = self.devices[device_id]
            
            # Refresh the appliance state
            appliance.refresh()
            
            # Update our state tracking and device info
            state = appliance.state
            self.device_states[device_id].update({
                'target_temperature': getattr(state, 'target_temperature', None),
                'fan_speed': getattr(state, 'fan_speed', None),
                'mode': getattr(state, 'mode', None),
                'indoor_temperature': getattr(state, 'indoor_temperature', None),
                'outdoor_temperature': getattr(state, 'outdoor_temperature', None),
                'last_update': int(time()),
                'status': 'online'
            })
            
            # Update MideaDevice climate info
            if device_id in self.device_info:
                device = self.device_info[device_id]
                device.status = 'online'
                device.last_seen = int(time())
                
                # Update climate data
                if device.climate:
                    device.climate.indoor_temperature = float(getattr(state, 'indoor_temperature', 0))
                    device.climate.outdoor_temperature = float(getattr(state, 'outdoor_temperature', 0))
                    device.climate.target_temperature = int(getattr(state, 'target_temperature', 20))
                    device.climate.fan_speed = int(getattr(state, 'fan_speed', 0))
                    
                    # Map mode to power mode
                    mode = getattr(state, 'mode', 0)
                    if mode == 1:
                        device.climate.mode = 'auto'
                    elif mode == 2:
                        device.climate.mode = 'cool'
                    elif mode == 4:
                        device.climate.mode = 'heat'
                    else:
                        device.climate.mode = 'cool'
            
            logger.debug(f"Refreshed state for device {device_id}: {self.device_states[device_id]}")
            
            # Notify callbacks
            await self._notify_state_callbacks(device_id, self.device_states[device_id])
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing device state for {device_id}: {e}")
            if device_id in self.device_states:
                self.device_states[device_id]['status'] = 'error'
            return False
    
    async def set_target_temperature(self, device_id: str, temperature: float) -> bool:
        """Set target temperature for the device"""
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return False
            
            appliance = self.devices[device_id]
            
            # Set the target temperature
            appliance.state.target_temperature = temperature
            
            # Apply the changes
            appliance.apply()
            
            # Update our state tracking
            self.device_states[device_id]['target_temperature'] = temperature
            self.device_states[device_id]['last_update'] = int(time())
            
            logger.info(f"Set target temperature to {temperature}°C for device {device_id}")
            
            # Notify callbacks
            await self._notify_state_callbacks(device_id, self.device_states[device_id])
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting target temperature for device {device_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def set_fan_speed(self, device_id: str, fan_speed: int) -> bool:
        """Set fan speed for the device"""
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return False
            
            appliance = self.devices[device_id]
            
            # Set the fan speed
            appliance.state.fan_speed = fan_speed
            
            # Apply the changes
            appliance.apply()
            
            # Update our state tracking
            self.device_states[device_id]['fan_speed'] = fan_speed
            self.device_states[device_id]['last_update'] = int(time())
            
            logger.info(f"Set fan speed to {fan_speed} for device {device_id}")
            
            # Notify callbacks
            await self._notify_state_callbacks(device_id, self.device_states[device_id])
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting fan speed for device {device_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def set_mode(self, device_id: str, mode: int) -> bool:
        """Set operating mode for the device"""
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return False
            
            appliance = self.devices[device_id]
            
            # Set the mode
            appliance.state.mode = mode
            
            # Apply the changes
            appliance.apply()
            
            # Update our state tracking
            self.device_states[device_id]['mode'] = mode
            self.device_states[device_id]['last_update'] = int(time())
            
            logger.info(f"Set mode to {mode} for device {device_id}")
            
            # Notify callbacks
            await self._notify_state_callbacks(device_id, self.device_states[device_id])
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting mode for device {device_id}: {e}")
            logger.error(traceback.format_exc())
            return False

    async def get_device_state(self, device_id: str) -> Optional[Dict]:
        """Get current state of a device"""
        if device_id in self.device_states:
            # Refresh state before returning
            await self.refresh_device_state(device_id)
            return self.device_states[device_id]
        return None
    
    async def get_all_devices(self) -> List[MideaDevice]:
        """Get state of all devices"""
        devices = []
        for device_id in self.device_info.keys():
            await self.refresh_device_state(device_id)  # Refresh before returning
            devices.append(self.device_info[device_id])
        return devices
    
    def add_state_callback(self, callback: Callable):
        """Add callback for state changes"""
        self.state_callbacks.append(callback)
    
    async def _notify_state_callbacks(self, device_id: str, state: Dict):
        """Notify registered callbacks about state changes"""
        for callback in self.state_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(device_id, state)
                else:
                    callback(device_id, state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

# Global instance similar to ESPHome pattern
midea_manager = MideaController()

async def initialize_midea_devices(ip_addresses: List[str]) -> None:
    """Initialize Midea devices from controller configuration"""
    for ip_address in ip_addresses:
            await midea_manager.add_device(
                ip_address=ip_address,
            )

async def get_chamber_midea_devices(chamber_controllers: List[Dict]) -> List[MideaDevice]:
    """Get Midea devices for a chamber"""
    midea_controllers = [c for c in chamber_controllers if c.get("controller_type") == "Midea"]

    devices = []
    for controller in midea_controllers:
        device_id = controller.get("controller_ip").replace('.', '_')
        if midea_manager.device_info[device_id]:
            await midea_manager.refresh_device_state(device_id)
            devices.append(midea_manager.device_info[device_id])
    
    return devices


# def main():
#     # Example usage for testing
#     discovered_devices = discover()
#     ip_addresses = [i['ip_address'] for i in discovered_devices.values()]

#     if ip_addresses:
#         appliance = appliance_state(
#             address=ip_addresses[0],  # APPLIANCE_IP_ADDRESS
#             token="2ca510843ccf4c233e4ce8c177c8c9b4a79d967417bdb8307e47239bb4dd8918555a738d618431a15336d62abb79dc2472e0684c9779ca34b8e75978733975ab",  # TOKEN obtained from Midea API
#             key="1d69090b797d41e8a7c029810933725f62f64be143764abaaa6badbbf602fe88",  # Token KEY obtained from Midea API
#         )
#         print("Current state:")
#         print(f"Target Temperature: {appliance.state.target_temperature}")
#         print(f"Fan Speed: {appliance.state.fanspeed}")
#         print(f"Mode: {appliance.state.mode}")
#         print(f"Power: {appliance.state.power}")
#         print(f"Indoor Temperature: {appliance.state.indoor_temperature}")

# if __name__ == "__main__":
#     main()
