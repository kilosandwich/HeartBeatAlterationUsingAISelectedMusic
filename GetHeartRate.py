import threading
import time
import numpy as np
import queue
from HeartRateFeed import start_monitor

class HeartRateReader:
    def __init__(self):
        # Create the queue in the initialization function
        self.heart_rate_data = queue.Queue(maxsize=1)
        # This is the current heart rate as a list, it is not the queue!
        self.current_heart_rate = None
        # Create the thread for the monitor, pass the queue as an argument into the thread
        self.monitor_thread = threading.Thread(target=start_monitor, args=(self.heart_rate_data,))
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
                    while len(self.current_heart_rate) < 5:
                        self.current_heart_rate.append(0)
                    print(f"Heart Rate List As Read From Queue: {self.current_heart_rate}")
        except Exception as e:
            print(f"Error reading heart rate data: {e}")

    def get_heart_rate(self):
        self.read_heart_rate()
        return self.current_heart_rate

    def get_heart_rate_int(self):
        print("I am attempting to retrieve an integer of the current heart rate!")
        self.read_heart_rate()  # Read the heart rate once
        return self.current_heart_rate[0] if self.current_heart_rate else None

    def get_resting_heart_rate(self):
        TIMEOUT = 60
        start_time = time.time()
        resting_heart_rate = None

        while True:
            self.read_heart_rate()
            heart_rates = self.get_heart_rate()
            if heart_rates and len(heart_rates) > 1 and (max(heart_rates) - min(heart_rates)) <= 3:
                resting_heart_rate = int(np.mean(heart_rates))
                return resting_heart_rate

            if (time.time() - start_time) >= TIMEOUT:
                resting_heart_rate = -1
                return resting_heart_rate

if __name__ == "__main__":
    reader = HeartRateReader()
    reader.read_heart_rate()
