#!/usr/bin/env python3
"""
Simple Bluetooth connection test for iPIXEL LED display
Tests direct connection without service discovery
"""
import asyncio
from bleak import BleakScanner, BleakClient

# iPIXEL UUIDs from protocol documentation
SERVICE_UUID = "0000fa01-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fa03-0000-1000-8000-00805f9b34fb"

async def scan_devices():
    """Scan for Bluetooth devices"""
    print("🔍 Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover(timeout=5.0)
    
    print(f"\n📱 Found {len(devices)} devices:")
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.name or 'Unknown'} - {device.address}")
    
    return devices

async def test_connection(address):
    """Test connection to specific device"""
    print(f"\n🔌 Attempting to connect to {address}...")
    
    try:
        async with BleakClient(address, timeout=10.0) as client:
            print(f"✅ Connected: {client.is_connected}")
            
            # Get services
            print("\n📋 Discovering services...")
            services = client.services
            
            print(f"\n🎯 Found {len(services)} services:")
            for service in services:
                print(f"\nService: {service.uuid}")
                print(f"  Description: {service.description}")
                
                for char in service.characteristics:
                    props = ', '.join(char.properties)
                    print(f"  └─ Characteristic: {char.uuid}")
                    print(f"     Properties: {props}")
            
            # Check for iPIXEL service
            if SERVICE_UUID in [s.uuid for s in services]:
                print(f"\n🎉 iPIXEL Service found: {SERVICE_UUID}")
                
                # Try to write a simple test command
                print("\n✏️ Testing write capability...")
                test_data = bytes([0x01, 0x00, 0x00])  # Simple test command
                await client.write_gatt_char(WRITE_UUID, test_data)
                print("✅ Write successful!")
            else:
                print(f"\n⚠️ iPIXEL Service NOT found")
                print(f"  Expected: {SERVICE_UUID}")
    
    except Exception as e:
        print(f"\n❌ Connection error: {type(e).__name__}")
        print(f"  Details: {str(e)}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("="*60)
    print("iPIXEL Bluetooth Connection Test")
    print("="*60)
    
    # Step 1: Scan for devices
    devices = await scan_devices()
    
    if not devices:
        print("\n❌ No devices found. Make sure your iPIXEL is powered on.")
        return
    
    # Step 2: Look for likely iPIXEL devices
    print("\n🔎 Looking for iPIXEL/iDotMatrix devices...")
    ipixel_devices = [d for d in devices if d.name and ('pixel' in d.name.lower() or 'dot' in d.name.lower() or 'matrix' in d.name.lower())]
    
    if ipixel_devices:
        print(f"\n🎯 Found potential iPIXEL device(s):")
        for device in ipixel_devices:
            print(f"  {device.name} - {device.address}")
            await test_connection(device.address)
    else:
        print("\n⚠️ No iPIXEL-like devices found by name.")
        print("  Trying first device anyway...")
        if devices:
            await test_connection(devices[0].address)

if __name__ == "__main__":
    asyncio.run(main())
