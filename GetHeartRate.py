import threading
import time
import numpy as np
import queue
from HeartRateFeed import start_monitor

class HeartRateReader:
    def __init__(self):
        # Create the queues in the initialization function
        self.heart_rate_data = queue.Queue(maxsize=1)
        self.resting_heart_rate_data = queue.Queue(maxsize=1)
        self.requiredLength = 10
        # This is the current heart rate as a list, it is not the queue!
        self.current_heart_rate = None
        # Create the thread for the monitor, pass both queues as arguments into the thread
        self.monitor_thread = threading.Thread(target=start_monitor, args=(self.heart_rate_data, self.resting_heart_rate_data))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def read_heart_rate(self):
        print("I am attempting to read the current heart rate!")
        try:
            # If the queue is not empty, remove the data from it!
            if not self.heart_rate_data.empty():
                heart_rate_list = self.heart_rate_data.get()
                # Based on the way the queue is defined, it appears that the queue is a list of tuples composed as follows
                # [(hr, timestamp)]
                if heart_rate_list:
                    # Update the internal value for HeartRateReader so that it can be used
                    # Clear the internal values for current heart rate
                    self.current_heart_rate = [i[0] for i in heart_rate_list if isinstance(i, tuple)]
                    # Ensure the list is always 5 elements long by appending zeros if necessary
                    # this can be adjusted under required length
                    while len(self.current_heart_rate) < self.requiredLength:
                        self.current_heart_rate.append(0)
                    print(f"Heart Rate List As Read From Queue: {self.current_heart_rate}")
        except Exception as e:
            print(f"Error reading heart rate data: {e}")

    # Reads the current heart rate list and returns it
    def get_heart_rate(self):
        print("I have been asked to read the current heart rate list")
        self.read_heart_rate()
        return self.current_heart_rate

    def get_heart_rate_int(self):
        print("I am attempting to retrieve an integer of the current heart rate!")
        self.read_heart_rate()  # Reads the heart rate once
        # Returns either the first element of the heart rate list or None if the list is empty
        return self.current_heart_rate[0] if self.current_heart_rate else None

    def get_resting_heart_rate(self):
        print("Attempting to retrieve resting heart rate...")

        while True:
            print("Help I am stuck in a loop")
            try:
                if not self.resting_heart_rate_data.empty():
                    resting_heart_rate = self.resting_heart_rate_data.get()
                    print(f"Resting Heart Rate Retrieved: {resting_heart_rate}")
                    return resting_heart_rate
                else:
                    print("Waiting for resting heart rate data...")
                    # Sleeps for 1 second before trying again
                    time.sleep(1)
            except Exception as e:
                print(f"Error retrieving resting heart rate: {e}")
                return None

if __name__ == "__main__":
    reader = HeartRateReader()
    while True:
        time.sleep(1)

    """
    # Example usage: Retrieve and print resting and current heart rates
    resting_hr = reader.get_resting_heart_rate()
    print(f"Resting Heart Rate: {resting_hr}")
    time.sleep(10)
    hr = reader.get_heart_rate_int()
    print(f"Current Heart Rate: {hr}")
    """
