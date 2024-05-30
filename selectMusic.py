################################################################
"""
Hello again future self and welcome to another exciting file

This is the selectMusic.py file. This file is supposed to take the user's heartbeat
the user's current resting heart rate, and the location of the CSV containing the scans
of the songs characteristics to determine the best song for the user to use.


"""

import os
#get the directory we are currently in 
script_dir = os.path.dirname(os.path.abspath(__file__))


#########################################################################
#########################################################################
#LOAD A LOCAL VERSION OF THE MACHINE LEARNING MODEL #####################
import torch
from ModelDefinition import SimpleNN  # Import your model class

# Define the model
input_size = 9  # Number of input values is equal to that number
#was determined earlier.
#10 is a working number, I don't know why
hidden_size = 10 # Number of neurons in the hidden layer (you can change this, but don't. It's working)
#remember, our good little model only return one output. 
output_size = 1  # Number of output values (I don't think heartbeat will exceed 200)
#0.01 is a good learning rate, DO NOT MESS WITH IT. I KNOW YOU ARE TEMPTED TO.
learning_rate = 0.01 
#10% probability of dropping any given connection for the purposes of reducing
#overiffing
dropout_prob = 0.1

print("Load the saved model definition")
# Define the file path to the saved model

script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "HBModel.pth")


# Instantiate the model
model = SimpleNN(input_size, hidden_size, output_size, dropout_prob) # Ensure to provide the required arguments


# Load the model state dict
model.load_state_dict(torch.load(model_path))

# Set the model to evaluation mode
model.eval()
###############################################################################
###############################################################################


import csv
def selectMusic(targetHR, heartRate, restingHR, csvLocation, approachPath = "default"):
    
    goalHRChange = targetHR - heartRate
    #ITERATE THROUGH THE CSV FILE
    #PUT ALL THE ROWS INTO A LIST
    with open(csvLocation, 'r') as file:
        reader = csv.reader(file)
        #get each row of the csv file
        rows = list(reader)
    #ASSUME THE FIRST ROW CONTAINS INFORMATION THAT IS NOT USEFUL
    del rows[0]
    
    #CREATE THE DEFAULT SONG CHOICE
    #the order is [filepath, changeinHR]
    currentSong = [ rows[0][0], 0]
    
    for musicRow in rows:
        #convert every item in the row EXCEPT FOR THE FILEPATH IN THE FIRST ROW into floats
        tempList = []
        for i in range(1,len(musicRow)):
            #fill the list with the numerical values of each row
            tempList.append(float(musicRow[i]))
        tempList.append(heartRate)
        tempList.append(restingHR)
        #convert the templist into a tensor so it can be fed into the machine learning model
        tempTensor = torch.tensor(tempList,dtype=torch.float32)
        #feed the tensor into the model to get the predicted change in heart rate
        tempprediction = model(tempTensor)
        tempprediction = tempprediction.tolist()
        tempprediction = tempprediction[0]
        #create a temporary tuple like thing
        tempprediction = [ musicRow[0], tempprediction]
        #great, we have our temporary prediction, AT THIS POINT WE WOULD CHOOSE WHAT APPROACH PATH TO USE
        #FUTURE FEATURE GOES HERE, APPROACH PATH
        
        #if the goal is simply to increase heart rate, choose whatever increases heart rate the most
        if goalHRChange > 0:
            #if the predicted heart rate change is greater than the current, replace the song
            if tempprediction[0] > currentSong[0]:
                currentSong = tempprediction.copy()
        #goal where solution is to decrease the heart rate
        else: 
            #if the predicted heart rate change is less than the current, replace the current song
             if tempprediction[0] < currentSong[0]:
                currentSong = tempprediction.copy()
    return currentSong[0]

