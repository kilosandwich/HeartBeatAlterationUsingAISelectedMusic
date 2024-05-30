
import torch
import torch.nn as nn
import torch.optim as optim

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

