import asyncio
import socket
import struct
from bleak import BleakScanner, BleakClient

async def connect_to_ble(address):
    client = BleakClient(address)
    await client.connect()
    return client

def send_data_over_tcp(data):
    TCP_IP = '127.0.0.1'
    TCP_PORT = 8089
    message = data.encode('utf-8')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TCP_IP, TCP_PORT))
        s.sendall(message)

async def notification_handler(sender, data):
    flag = int.from_bytes(data[0:1], byteorder='little')
    heart_rate_value_format = (flag & 1)
    
    start_str = 'E;1;Heart;1;;;;HeartRate;'
    end_str = '\r\n'
    
    if heart_rate_value_format == 0:
        heart_rate = int.from_bytes(data[1:2], byteorder='little')
        if len(data) == 2:
            rr = 0
            to_imotions = f"{start_str}{heart_rate};{rr}{end_str}"
            send_data_over_tcp(to_imotions)
            print(f"Heart Rate: {heart_rate}, RR: {rr}")
        if len(data) > 2:
            rr = struct.unpack('<H', data[2:4])[0] / 1024 * 1000
            to_imotions = f"{start_str}{heart_rate};{rr}{end_str}"
            send_data_over_tcp(to_imotions)
            print(f"Heart Rate: {heart_rate}, RR: {rr}")
        if len(data) > 4:
            rr = struct.unpack('<H', data[4:6])[0] / 1024 * 1000
            to_imotions = f"{start_str}{heart_rate};{rr}{end_str}"
            send_data_over_tcp(to_imotions)
            print(f"Heart Rate: {heart_rate}, RR: {rr}")

async def handle_disconnect(address):
    print("Device disconnected, attempting to reconnect...")
    while True:
        try:
            client = await connect_to_ble(address)
            print("Reconnected to the device")
            await client.start_notify('00002a37-0000-1000-8000-00805f9b34fb', notification_handler)
            client.set_disconnected_callback(lambda _: asyncio.create_task(handle_disconnect(address)))
            return
        except Exception as e:
            print(f"Reconnection failed: {e}, retrying in 5 seconds...")
            await asyncio.sleep(5)

def on_disconnect(client):
    loop = asyncio.get_event_loop()
    loop.create_task(handle_disconnect(client.address))

async def main():
    connection = False
    n = 10
    timeout = 5
    devices = await BleakScanner.discover(timeout)
    if devices:
        print("Found the following devices:")
        polar_h10_counter = 0
        for device in devices:
            if device.name and device.name.startswith('Polar H10'):
                polar_h10_counter += 1
                print(f"{polar_h10_counter}. Name: {device.name}, MAC Address: {device.address}")     
        index = int(input("Select a device: ")) - 1
        polar_h10_devices = [device for device in devices if device.name and device.name.startswith('Polar H10')]
        address = polar_h10_devices[index].address
        client = await connect_to_ble(address)
        
        client.set_disconnected_callback(on_disconnect)

        await client.start_notify('00002a37-0000-1000-8000-00805f9b34fb', notification_handler)
        print(f"Connected to BLE device name:{polar_h10_devices[index].name}  MAC address: {polar_h10_devices[index].address}")
    
    h = input("Press any key to start data transmission...")
    while h:
        await asyncio.sleep(1)  # Keep the event loop running
    await client.stop_notify('00002a37-0000-1000-8000-00805f9b34fb')

if __name__ == "__main__":
    asyncio.run(main())


