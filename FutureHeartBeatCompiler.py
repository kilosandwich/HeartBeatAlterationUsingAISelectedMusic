"""
To Do:
Create ModelDefinition.py
Rename this file to "ModelCompiler.py"

Hello future self, this is the FutureHeartBeatCompiler function
The original purpose of this file was to define the model externally in a different file called
'ModelDefinition.py', load an instance of that model, and save the model's weights so they could be 
loaded externally by another function.

I did this successfully, HOWEVER in doing so I noticed that it became frustrating to go BACK AND FORTH
between the model definition and the futureheartbeatcompiler.py file. For the time being, the model will
be compiled and defined here, then loaded externally using a model definition possessing identical inputs.

For some reason that's just easier.

HOW IT WORKS:
This file loads data from HR.csv, the format of this data is irrelevant - all that matters is that the
'targets' are located in the last column of the csv file. This was done so that if we wish to expand the 
number of inputs, no restructuring has to occur in the rest of the model. HOWEVER THIS DOES IMPACT THE
MODELDEFINITION.PY FUNCTION AS YOU NEED TO CHANGE THE NUMBER OF INPUTS MANUALLY
"""

import os


import torch
import torch.nn as nn
print("attempting to load Pandas")
import pandas as pd
print("Attempting to load everything else")
import numpy as np
import os

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd



#Get the data from our custom dataset trained on data for CALMING THE HEAT
datafilename = "HR.csv"
script_directory = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_directory, datafilename)

data = pd.read_csv(file_path, skiprows=0, na_values=['NA', 'nan', "NAN", "NaN", '']) 
data = data.dropna()

#in my world, the last number of the column is ALWAYS the target
input_data = data.iloc[:, :-1].values.tolist()
target_data = [[item] for item in data.iloc[:, -1].values.tolist()] 


#check to make sure your data is formatted correctly
print("First row of input_data:")
print(input_data[0])
print(input_data)

print("First row of target_data:")
print(target_data[0])
print(target_data)

#make sure the number of input variables in scalable if we wish to increase the size of the data set
num_input_variables = len(input_data[0])
print("This is the number of input variables")
print(num_input_variables)

# Prepare input and target tensors
x_train = torch.tensor(input_data, dtype=torch.float32)
y_train = torch.tensor(data.iloc[:, -1].values.reshape(-1, 1), dtype=torch.float32)


#I need to move batch size to hyper parameters
batch_size = 10
dataset = TensorDataset(x_train,y_train)

#make sure the xtrain and ytrain are properly formatted
#print("Here is the xtrain")
#print(x_train)
#print("Here is the y train")
print(y_train)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

class SimpleNN(nn.Module):
    #FOR SOME REASON THE LSTM LAYER IS NOT WORKING WHY GOD ISN'T IT WORKING????
    #when in doubt, fc is your friend. 
    #is two layers enough??? should I add more...I mean,,,,it shouldn't be an issue if I do right?
    def __init__(self, input_size, hidden_size, output_size, dropout_prob):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU() 
        self.fc4 = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout_prob)
        self.fc2 = nn.Linear(hidden_size,hidden_size)
        self.fc3 = nn.Linear(hidden_size,hidden_size)
        
    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)
        x = self.relu(x)
        x = self.fc3(x)
        #these seemed like they were increasing loss, I am happy with the current loss
        #as it consistently hovers around 18 as compared to 30 with only two fully connected layers
        #x = self.dropout(x)
        #x = self.relu(x)
        x = self.fc4(x)
        return x


# Define the model
input_size = num_input_variables  # Number of input values is equal to that number
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

model = SimpleNN(input_size, hidden_size, output_size, dropout_prob)

# Define loss function and optimizer
criterion = nn.MSELoss()  # Mean Squared Error loss
#SGD was causing failure, switching to ADAM has resulted in stability and ACTUAL OUTPUT FOR ONCE
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

# Training loop
num_epochs = 100
#run through all data for the number of epochs
for epoch in range(num_epochs):
    #for each datapoint within the dataloader object
    for data_point, target in dataloader:
        # Forward pass
        #print("Here is an example data point")
        #print(data_point)
        #Generate the predictions based on the given datapoint
        predictions = model(data_point)

        #based on our data point, see how much was missed using
        #our loss function
        loss = criterion(predictions, target)
        
        
        # Backward pass and optimization
        #knowing how much loss was had, run the optimizer to make it work
        optimizer.zero_grad() #reset the gradients so you can use your gosh darn optimizer
        loss.backward()
        optimizer.step()
        
        # Print progress
        #How the model doin
    if (epoch+1) % 10 == 0:
        #These print sections are for if the data you are getting is
        #overfitting, you can figure out WHICH pass the overfitting occurs
        #at.
        #print("Here are the predicted outputs using the model:")
        #print("This was the data point: ", data_point)
        #print("This was the target:", target)
        #print("This was the prediction: ",predictions)
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-
    
#In the future I should probably move the model into a separate file, and probably
#the datagetter too. I just don't like separate files. It makes me confused
#EVERYTHING SHOULD BE IN FRONT OF ME AT ALL TIMES
#....I should get a second monitor

print("Save the model")
script_directory = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(script_directory, "HBModel.pth")
torch.save(model.state_dict(), filepath)
