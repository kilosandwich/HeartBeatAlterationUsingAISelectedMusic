######################################################
#Hello future self, welcome to another exciting file!
"""
This is the heartRateFeed.py file. This file is meant to be in constant operation
as it connects to the heart rate monitor, and passes its information in the form of lists
to a queue that is then read by the getHeartRate.py file.

This is a direct adapation of the heart_rate.py file from the examples found on
openant:
https://github.com/Tigge/openant/blob/master/examples/heart_rate.py

There are notable differences:
1.) The information is stored within a list
2.) The list is passed to a queue that is passed between files
3.) This code is actually commented to explain how it works

CURRENT BUGS:

FIXED BUGS:
1.) For some reason it doesn't connect successfully on the first time. Maybe we create some sort of
try loop that constantly launches the file until it finally catches?
SOLUTION: Placed the node initialization into an infinite try catch loop that
tries to constantly start the node despite the futility. SURPRISINGLY THIS WORKS
"""

print("Starting up heartRateFeed.py")
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from datetime import datetime
import queue
import threading

#this is a blank list that is filled with files.
HRList = [70]*10
TimeSince = datetime.now()
global_q = queue.Queue()
##########################################################
#CRITICAL VALUE!!!! ALL ARE TESTING DATA WILL DESCEND FROM
#THIS NUMBER. THIS NUMBER REPRESENTS THE TIME BETWEEN TIME READINGS
#IF THIS NUMBER IS CHANGED ALL CRITICAL TESTING DATA WILL CHANGE. 
#THEREFORE TO MAKE IT EASY, THIS NUMBER WILL BE  
SECONDSBETWEENMEASUREMENTS = 10
##########################################################
#This is the main function, it is run when the file is initialized
def main(device_id=0):
    global HRList
    global TimeSince
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
        #REMEMBER, YOU HAVE TO DECLARE WITHIN EVERY FUNCTION ALL THE TIME ALWAYS
        global TimeSince
        global global_q
        if isinstance(data, HeartRateData):
            #only update the heart rate queue every 10 seconds, or else
            #our readings are too constant
            #we can adjust the time up top
            if ((datetime.now() - TimeSince).total_seconds() > SECONDSBETWEENMEASUREMENTS):
                TimeSince = datetime.now()
                HRList.pop(-1)#remove the last item in the list
                HRList.insert(0,data.heart_rate) #insert a new item to the front of the list 
                #print(f"Heart rate update {data.heart_rate} bpm")
                print(HRList)
                global_q.put(data) #place the data into the queue
                
                
                

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

def getHeartRate():
    global global_q 
    print("This is the current queue")
    #throw away EVERY item in the queue except for the last one
    while global_q.qsize() > 2:
        discardThis = global_q.get()
        print("Throwing away item in queue")
        print(discardThis)
    #return the last item in the list
    if global_q.queue[0]:
        return global_q.queue[0]
    else:
        return



if __name__ == "__main__":
    main()