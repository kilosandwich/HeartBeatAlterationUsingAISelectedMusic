#Implement a popup on the front-end to instruct the user to take a deep breath and try to relax before measuring
import time
import numpy as np
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
XX = 20
TIMEOUT = 60

def get_resting_HR():
    start_time = time.time()
    heart_rates = []

    while time.time() - start_time < TIMEOUT:
        current_rate = get_current_heart_rate()  # storees the current heart rate inside the variable
        heart_rates.append(current_rate) # adds the value of current_rate to the heart_rates list

        if len(heart_rates) > 1 and (max(heart_rates) - min(heart_rates)) <= 3: # Checks if there has been more than 1 heartrate recorded and if the range of the rates is 3 or less to determine heart rate stability
            return int(np.mean(heart_rates)) # calculates and returns the average estimated resting heart rate

        time.sleep(XX)

    # If heart rate never stabilizes, notify user on the front end about stabilization failure and suggest manual input or retry
    return -1

def get_current_heart_rate(device_id=0):
    while True:
        try:
            node = Node()
            node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
            #the device that is found is only a heartRate device
            device = HeartRate(node, device_id=device_id)
            break
        except Exception as e:
            print("Failed to initialize node, trying again!")

    def on_found():
        print(f"Device {device} found and receiving")

    def on_device_data(page: int, page_name: str, data):
        if isinstance(data, HeartRateData):
            print(f"Heart rate update {data.heart_rate} bpm")

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


if __name__ == "__main__":
    get_current_heart_rate()