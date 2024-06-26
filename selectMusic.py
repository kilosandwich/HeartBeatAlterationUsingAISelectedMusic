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

import random


#################CONSTANTS FOR CONFIGURATION###########################
SHALLOW = 1
LINEAR = 2
STEEP = 3


#######################################################################


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
    #if the approach path is 'rollercoaster' change the goal to a randomly
    #positive or negative version of itself
    #then change the approach path to fastest to achieve that goal
    if approachPath == "Rollercoaster":
        goalHRChange = random.choice([goalHRChange, -goalHRChange])
    elif approachPath == "Parabola":
        #if the goal is positive, occasionally randomly overshoot in target heart
        #rate goal
        if goalHRChange > 0:
            goalHRChange = random.choice([goalHRChange, goalHRChange+5])
        else:
            goalHRChange = random.choice([goalHRChange, goalHRChange-5])
    
    #ITERATE THROUGH THE CSV FILE
    #PUT ALL THE ROWS INTO A LIST
    with open(csvLocation, 'r') as file:
        reader = csv.reader(file)
        #get each row of the csv file
        rows = list(reader)
    #ASSUME THE FIRST ROW CONTAINS INFORMATION THAT IS NOT USEFUL
    del rows[0]
    
    #CREATE THE DEFAULT SONG CHOICE
    #the order is [filepath, changeinHR, songLength]
    #an improbably small song length is given for the purpose of creating comically
    #inaccurate change in HRs so they are replaced rapidly.
    currentSong = [ rows[0][0], 0,0.0001]
    
    #This is a nested function for calculating the gap between two points
    def calculateGap(goal, input):
        return abs(goal-input)
    
    for musicRow in rows:
        #convert every item in the row EXCEPT FOR THE FILEPATH IN THE FIRST ROW into floats
        tempList = []
        for i in range(1,len(musicRow)):
            #fill the list with the numerical values of each row
            tempList.append(float(musicRow[i]))
        tempSongLength = tempList[4]
        tempList.append(heartRate)
        tempList.append(restingHR)
        #convert the templist into a tensor so it can be fed into the machine learning model
        tempTensor = torch.tensor(tempList,dtype=torch.float32)
        #feed the tensor into the model to get the predicted change in heart rate
        tempprediction = model(tempTensor)
        #The output of the model is a tensor, which must be converted to a list
        tempprediction = tempprediction.tolist()
        tempprediction = tempprediction[0]
        #create a temporary tuple like thing
        tempprediction = [ musicRow[0], tempprediction, tempSongLength]
        #great, we have our temporary prediction, AT THIS POINT WE WOULD CHOOSE WHAT APPROACH PATH TO USE
        #FUTURE FEATURE GOES HERE, APPROACH PATH
        
        #repeated calls to a list are slow, assign them to temporary variables here
        currentSongHRChange = currentSong[1]
        currentSongLength = currentSong[2]
        tempSongHRChange = tempprediction[1]
        tempSongLength = tempSongLength
        
        #Calculate the rate of change of the song.
        tempChangeRate = tempSongHRChange/tempSongLength
        currentChangeRate = currentSongHRChange/currentSongLength
        
        if approachPath == "Shallow":
            #CurrentSongGap between SHALLOW
            tempGap = calculateGap(SHALLOW, tempChangeRate)
            currentGap = calculateGap(SHALLOW,currentChangeRate)
            #if the the temporary song is closer to the goal, it is a beter choice
            betterChoice = (tempGap < currentGap)
            
            #user wants to increase their heart rate
            if goalHRChange > 0:
                #tempchangeRate should only be considered if it is positive
                if (tempChangeRate > 0) and betterChoice:
                    currentSong = tempprediction.copy()            
            #user wants to decrease their heart rate/
            else:    
                #if the tempChangeRate should only be considered if it is negative
                if (tempChangeRate < 0) and (betterChoice):
                    currentSong = tempprediction.copy()
        elif approachPath == "Linear":
            #CurrentSongGap between SHALLOW
            tempGap = calculateGap(LINEAR, tempChangeRate)
            currentGap = calculateGap(LINEAR,currentChangeRate)
            #if the the temporary song is closer to the goal, it is a beter choice
            betterChoice = (tempGap < currentGap)
            
            #user wants to increase their heart rate
            if goalHRChange > 0:
                #tempchangeRate should only be considered if it is positive
                if (tempChangeRate > 0) and betterChoice:
                    currentSong = tempprediction.copy()            
            #user wants to decrease their heart rate/
            else:    
                #if the tempChangeRate should only be considered if it is negative
                if (tempChangeRate < 0) and (betterChoice):
                    currentSong = tempprediction.copy()
        elif approachPath == "Steep":
            #CurrentSongGap between SHALLOW
            tempGap = calculateGap(STEEP, tempChangeRate)
            currentGap = calculateGap(STEEP,currentChangeRate)
            #if the the temporary song is closer to the goal, it is a beter choice
            betterChoice = (tempGap < currentGap)
            
            #user wants to increase their heart rate
            if goalHRChange > 0:
                #tempchangeRate should only be considered if it is positive
                if (tempChangeRate > 0) and betterChoice:
                    currentSong = tempprediction.copy()            
            #user wants to decrease their heart rate/
            else:    
                #if the tempChangeRate should only be considered if it is negative
                if (tempChangeRate < 0) and (betterChoice):
                    currentSong = tempprediction.copy()
        elif (approachPath == "Fastest") or (approachPath == "Rollercoaster"):
            #case where user wants to increase their heart rate
            if goalHRChange > 0:
                if tempChangeRate > currentChangeRate:
                    currentSong = tempprediction.copy()
            #case where user wants to decrease their heart rate
            else:
                if tempChangeRate < currentChangeRate:
                    currentSong = tempprediction.copy()
        elif (approachPath == "Parabola"):
            #CurrentSongGap between Parabola
            #EXPLANATION
            #Parabola picks the better choice from whichever song gets
            #closest to the goalHRChange, however the goalHRchange is randomly
            #sometimes an 'overshoot' of the actual goal.
            
            tempGap = calculateGap(goalHRChange, tempSongHRChange)
            currentGap = calculateGap(goalHRChange,currentSongHRChange)
            #if the the temporary song is closer to the goal, it is a beter choice
            betterChoice = (tempGap < currentGap)
            
            #user wants to increase their heart rate
            if goalHRChange > 0:
                #tempchangeRate should only be considered if it is positive
                if (tempChangeRate > 0) and betterChoice:
                    currentSong = tempprediction.copy()            
            #user wants to decrease their heart rate/
            else:    
                #if the tempChangeRate should only be considered if it is negative
                if (tempChangeRate < 0) and (betterChoice):
                    currentSong = tempprediction.copy()
            
                    
        #this is the catch all else statement, this means that an approach path will ALWAYS be selected.
        else:
            #if the goal is simply to increase heart rate, choose whatever increases heart rate the most
            if goalHRChange > 0:
                #if the predicted heart rate change is greater than the current, replace the song
                if tempSongHRChange > currentSongHRChange:
                    currentSong = tempprediction.copy()
            #goal where solution is to decrease the heart rate
            else: 
                #if the predicted heart rate change is less than the current, replace the current song
                if tempSongHRChange < currentSongHRChange:
                    currentSong = tempprediction.copy()
    return currentSong[0]

