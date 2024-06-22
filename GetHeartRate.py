import threading
import time
from heartRateFeed import start_monitor, heart_rate_data

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
        return self.current_heart_rate

if __name__ == "__main__":
    reader = HeartRateReader()
    reader.read_heart_rate()