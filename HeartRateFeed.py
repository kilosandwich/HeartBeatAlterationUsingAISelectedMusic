print("Starting up heartRateFeed.py")
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from datetime import datetime
import threading
import queue

heart_rate_data = queue.Queue(maxsize=1)
update_interval = 10
fixed_list_size = 10

def heart_rate_monitor(device_id=0):
    last_update_time = datetime.now()
    heart_rate_list = []

    while True:
        try:
            node = Node()
            node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
            device = HeartRate(node, device_id=device_id)
            break
        except Exception as e:
            print("Failed to initialize node, trying again!")

    def device_found():
        print(f"Device {device} found and receiving")

    def handle_device_data(page: int, page_name: str, data):
        nonlocal last_update_time
        if isinstance(data, HeartRateData):
            if ((datetime.now() - last_update_time).total_seconds() > update_interval):
                last_update_time = datetime.now()
                if len(heart_rate_list) >= fixed_list_size:
                    heart_rate_list.pop()
                heart_rate_list.insert(0, (data.heart_rate, datetime.now()))
                
                while not heart_rate_data.empty():
                    heart_rate_data.get()
                heart_rate_data.put(list(heart_rate_list))
                print([hr for hr, _ in heart_rate_list])

    device.on_found = device_found
    device.on_device_data = handle_device_data

    try:
        print(f"Starting {device}, press Ctrl-C to finish")
        node.start()
    except KeyboardInterrupt:
        print("Closing ANT+ device...")
    finally:
        device.close_channel()
        node.stop()

def start_monitor():
    threading.Thread(target=heart_rate_monitor).start()