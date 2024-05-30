#############################
"""
Hello future me, and welcome to another exciting file
This is the getHeartRate.py file
This file has one function, return the current heart rate of the user

BUGS:
1.) Bad news, I have no clue how to get the data from a live heart rate feed,
my previous efforts have not been successful. For finishing the first prototype
we will instead return a simple value of the first heart rate value
"""
print("Starting up heartRateFeed.py")
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from datetime import datetime

#this is a blank list that is filled with files.

#This is the main function, it is run when the file is initialized
def main(device_id=0):
    HR = 0
    #estbalish the ANT nodes, feed it in the default ANT+ network key to make it operational
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
        nonlocal HR
        if isinstance(data, HeartRateData):
            print(data.heart_rate)
            HR = data.heart_rate
            #print("HR in the inner function is: ", HR)
            #unregister the callback function, call it a day. 
            device.on_device_data = None
    device.on_found = on_found
    device.on_device_data = on_device_data

    try:
        print(f"Starting {device}, press Ctrl-C to finish")
        node.start()
    except Exception as e:
        print("Closing ANT+ device...")
    finally:
        device.close_channel()
        node.stop()
    #print("HR is: ", HR)
    return HR

def getHeartRate():
    return main()
