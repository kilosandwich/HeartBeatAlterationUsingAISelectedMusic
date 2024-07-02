from GetHeartRate import HeartRateReader
import time

if __name__ == "__main__":
    reader = HeartRateReader()
    
    print("I am going to sleep night night")
    time.sleep(15)
    print("I AM AWOKEN FROM MY SLUMBER, FEAR MY WRATH ******************************************")
    heart_rate_int = reader.get_heart_rate_int()
    print("I HAVE READ THE VALUD OF HEART RATE INT AND IF YOU ARE NOT SEEING THIS THERE IS SOME OTHER HILARIOUS ERROR")
    print("The value of hear rate int is: ", heart_rate_int)
    print("Heart Rate Integer*************************************************************************************************8:", heart_rate_int)
