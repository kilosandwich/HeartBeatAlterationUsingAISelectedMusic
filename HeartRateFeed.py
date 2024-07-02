print("Starting up heartRateFeed.py")
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from datetime import datetime
import threading
import queue

def heart_rate_monitor(heart_rate_data: queue):  
    update_interval = 10
    fixed_list_size = 10
    last_update_time = datetime.now()
    #make sure that the list is initially only 10 long, 0 represents the default
    heart_rate_list = [0]*fixed_list_size
    device_id=0
    #try to connect infinitely, ideally there should be a timeout error here so the
    #thread isn't wasted. Please create a way to return an error here in the future
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
                #if the list is bigger than it should be, pop out items in the list
                while(len(heart_rate_list) >= fixed_list_size):
                    heart_rate_list.pop()
                #geez no wonder queues are so confusing, we're passing the date time stamp FOR every item in the list
                #WHY? for testing purposes to make sure that the time between measurements is correct
                #insert the current heart rate and its time stamp into the list
                heart_rate_list.insert(0, (data.heart_rate, datetime.now()))

                #empty out the queue, there should only be one value in it
                while not heart_rate_data.empty():
                    heart_rate_data.get() 
                #now that the queue is empty, put a value into the queue
                heart_rate_data.put(list(heart_rate_list))  
                print(heart_rate_list)

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

#I have defined the default parameter as queue so that you know to pass a queue to it
def start_monitor(heart_rate_data: queue):
    #run the heart rate monitor, pass the queue from the initialization
    heart_rate_monitor(heart_rate_data)
    
