import time
import numpy as np
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData

def get_resting_HR(device_id=0):
    TIMEOUT = 60
    start_time = time.time()
    heart_rates = []
    resting_heart_rate = None  

    while True:
        try:
            node = Node()
            node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
            device = HeartRate(node, device_id=device_id)
            print("Initialized node and device successfully")
            break
        except Exception as e:
            print(f"Failed to initialize node, trying again! Error: {e}")

    def on_found():
        print(f"Device {device} found and receiving")

    def on_device_data(page: int, page_name: str, data):
        nonlocal TIMEOUT
        nonlocal start_time
        nonlocal heart_rates
        nonlocal resting_heart_rate  

        if isinstance(data, HeartRateData):
            current_rate = data.heart_rate
            print(f"Heart rate update: {current_rate} bpm")
            heart_rates.append(current_rate)
            print(f"Heart rates so far: {heart_rates}")
            if len(heart_rates) > 1 and (max(heart_rates) - min(heart_rates)) <= 3:
                resting_heart_rate = int(np.mean(heart_rates))  
                print(f"Resting heart rate determined: {resting_heart_rate} bpm")
                device.close_channel()
                node.stop()
            
            if (time.time() - start_time) >= TIMEOUT:
                resting_heart_rate = -1  
                print(f"Timeout reached: {TIMEOUT} seconds")
                device.close_channel()
                node.stop()

    device.on_found = on_found
    device.on_device_data = on_device_data

    try:
        print(f"Starting {device}, press Ctrl-C to finish")
        node.start()
    except KeyboardInterrupt:
        print("Closing ANT+ device...")
    finally:
        device.close_channel()
        node.stop()

    return resting_heart_rate  

if __name__ == "__main__":
    resting_hr = get_resting_HR()
    print(f"Resting Heart Rate: {resting_hr}")
