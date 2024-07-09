print("Starting up HeartRateFeed.py")
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from datetime import datetime
import threading
import queue
import numpy as np  

def heart_rate_monitor(current_heart_rate_data: queue.Queue, resting_heart_rate_data: queue.Queue):  
    update_interval = 10
    fixed_list_size_current = 10
    fixed_list_size_resting = 20
    heart_rate_list_current = [0] * fixed_list_size_current
    heart_rate_list_resting = []
    last_update_time = datetime.now()
    device_id = 0
    resting_heart_rate = None

    # Try to connect infinitely, ideally there should be a timeout error here so the
    # thread isn't wasted. Please create a way to return an error here in the future
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
        nonlocal last_update_time, heart_rate_list_resting, resting_heart_rate
        if isinstance(data, HeartRateData):
            current_time = datetime.now()

            # Logic for current heart rate data
            if ((current_time - last_update_time).total_seconds() > update_interval):
                last_update_time = current_time
                #if the list is bigger than it should be, pop out items in the list
                while len(heart_rate_list_current) >= fixed_list_size_current:
                    heart_rate_list_current.pop()
                #geez no wonder queues are so confusing, we're passing the date time stamp FOR every item in the list
                #WHY? for testing purposes to make sure that the time between measurements is correct
                #insert the current heart rate and its time stamp into the list
                heart_rate_list_current.insert(0, (data.heart_rate, current_time))

                #empty out the queue, there should only be one value in it
                while not current_heart_rate_data.empty():
                    current_heart_rate_data.get() 
                #now that the queue is empty, put a value into the queue
                current_heart_rate_data.put(list(heart_rate_list_current))  
                #print("Current Heart Rate List:", heart_rate_list_current)

            # Logic for resting heart rate data
            heart_rate_list_resting.append(data.heart_rate)
            if len(heart_rate_list_resting) > fixed_list_size_resting:
                heart_rate_list_resting.pop(0)

            #print("Resting Heart Rate List Before Check:", heart_rate_list_resting)  # Debug statement
            if len(heart_rate_list_resting) == fixed_list_size_resting:
                hr_range = max(heart_rate_list_resting) - min(heart_rate_list_resting)
                #print(f"Resting Heart Rate Range: {hr_range}")  # Debug statement
                if hr_range < 3:
                    avg_hr = int(np.mean(heart_rate_list_resting))
                    #print(f"Calculated Resting Heart Rate: {avg_hr}")  # Debug statement
                    # Check and update the resting heart rate in the queue
                    if not resting_heart_rate_data.empty():
                        current_resting_hr = resting_heart_rate_data.queue[0]
                        if avg_hr < current_resting_hr:
                            while not resting_heart_rate_data.empty():
                                resting_heart_rate_data.get()
                            resting_heart_rate_data.put(avg_hr)
                            #print(f"Updated Resting Heart Rate in Queue: {avg_hr}")  # Debug statement
                        else:
                            #nonsense statement so we can access print statement later, remove this 
                            nonsense = 0
                            #print(f"Kept Resting Heart Rate in Queue: {current_resting_hr}")  # Debug statement
                    else:
                        resting_heart_rate_data.put(avg_hr)
                        #print(f"Initial Resting Heart Rate in Queue: {avg_hr}")  # Debug statement
                #print("Resting Heart Rate List After Check:", heart_rate_list_resting)  # Debug statement

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

# Modify the start_monitor function to accept both queues
def start_monitor(current_heart_rate_data: queue.Queue, resting_heart_rate_data: queue.Queue):
    heart_rate_monitor(current_heart_rate_data, resting_heart_rate_data)
