import asyncio
import socket
import struct
import time
from bleak import BleakScanner, BleakClient
from openpyxl import Workbook

# Global variables for Excel writing
workbook = None
worksheet = None
save_interval = 10  # Save every 10 seconds
last_save_time = time.time()
excel_filename = None
tcp_enabled = False
excel_enabled = False

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
    global last_save_time
    flag = int.from_bytes(data[0:1], byteorder='little')
    heart_rate_value_format = (flag & 1)
    heart_rate = int.from_bytes(data[1:2], byteorder='little')
    rr_intervals = []
    if len(data) > 2:
        rr_intervals = [struct.unpack('<H', data[i:i+2])[0] / 1024 * 1000 for i in range(2, len(data), 2)]
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    start_str = 'E;1;Heart;1;;;;HeartRate;'
    end_str = '\r\n'
    for rr in rr_intervals or [0]:  # Use [0] if no RR interval is found
        if tcp_enabled:
            try:
                to_imotions = f"{start_str}{heart_rate};{rr}{end_str}"
                send_data_over_tcp(to_imotions)
            except Exception as e:
                print(f"TCP Error: {e}")

        if excel_enabled:
            worksheet.append([timestamp, heart_rate, rr])

        print(f"Heart Rate: {heart_rate}, RR: {rr}, Timestamp: {timestamp}")
    if excel_enabled and time.time() - last_save_time > save_interval:
        workbook.save(excel_filename)
        last_save_time = time.time()

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
    global workbook, worksheet, excel_filename, tcp_enabled, excel_enabled
    # Discover BLE devices
    connection = False
    timeout = 5
    devices = await BleakScanner.discover(timeout)
    if devices:
        print("Found the following devices:")
        polar_h10_counter = 0
        for device in devices:
            if device.name and device.name.startswith('Polar H10'):#Polar H10
                polar_h10_counter += 1
                print(f"{polar_h10_counter}. Name: {device.name}, MAC Address: {device.address}")     
        index = int(input("Select a device: ")) - 1
        polar_h10_devices = [device for device in devices if device.name and device.name.startswith('Polar H10')]#Polar H10
        address = polar_h10_devices[index].address
        client = await connect_to_ble(address)
        
        client.set_disconnected_callback(on_disconnect)

        await client.start_notify('00002a37-0000-1000-8000-00805f9b34fb', notification_handler)
        print(f"Connected to BLE device name:{polar_h10_devices[index].name}  MAC address: {polar_h10_devices[index].address}")   
   
    # Ask user which functionalities to enable
    print("Choose an option:")
    print("1. Only TCP")
    print("2. TCP and Excel Storage")
    print("3. Only Excel Storage")
    choice = int(input("Enter your choice (1/2/3): "))

    if choice == 1:
        tcp_enabled = True
        print("TCP mode selected.")
    elif choice == 2:
        tcp_enabled = True
        excel_enabled = True
        excel_filename = input("Enter the name for the Excel file (e.g., 'heart_data.xlsx'): ")
        # Check and append .xlsx if not present
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        print(f"TCP and Excel Storage mode selected. Excel file: {excel_filename}")
    elif choice == 3:
        excel_enabled = True
        excel_filename = input("Enter the name for the Excel file (e.g., 'heart_data.xlsx'): ")
        # Check and append .xlsx if not present
        if not excel_filename.endswith('.xlsx'):
            excel_filename += '.xlsx'
        print(f"Excel Storage mode selected. Excel file: {excel_filename}")

    # Initialize Excel workbook and worksheet if Excel storage is enabled
    if excel_enabled:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Heart Rate Data"
        worksheet.append(["Timestamp", "Heart Rate", "RR Interval"])
    

    
    h = input("Press any key and hit enter to start data transmission...")
    while h:
        await asyncio.sleep(1)  # Keep the event loop running
    await client.stop_notify('00002a37-0000-1000-8000-00805f9b34fb')

if __name__ == "__main__":
    asyncio.run(main())
