import threading
import time
import numpy as np
from HeartRateFeed import start_monitor, heart_rate_data

class HeartRateReader:
    def __init__(self):
        self.current_heart_rate = None
        self.monitor_thread = threading.Thread(target=start_monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def read_heart_rate(self):
        while True:
            try:
                if not heart_rate_data.empty():
                    heart_rate_list = heart_rate_data.get()
                    if heart_rate_list:
                        self.current_heart_rate = heart_rate_list[0][0]  
                        print(f"Heart Rate: {self.current_heart_rate}")
            except Exception as e:
                print(f"Error reading heart rate data: {e}")
            time.sleep(1)

    def get_heart_rate(self):
        return self.read_heart_rate()
    def get_heart_rate_int(self):
        return self.read_heart_rate()[0]
    def get_resting_heart_rate(self):
                
        TIMEOUT = 60
        start_time = time.time()
  
        resting_heart_rate = None  
     
        while(True):
            heart_rates = self.read_heart_rate()
            if len(heart_rates) > 1 and (max(heart_rates) - min(heart_rates)) <= 3:
                resting_heart_rate = int(np.mean(heart_rates))  
                return resting_heart_rate
                
            if (time.time() - start_time) >= TIMEOUT:
                resting_heart_rate = -1  
                return resting_heart_rate


if __name__ == "__main__":
    reader = HeartRateReader()
    reader.read_heart_rate()
