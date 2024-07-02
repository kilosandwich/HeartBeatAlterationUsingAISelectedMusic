

import tkinter as tk
import fnmatch 
import os 
from pygame import mixer

canvas =tk.Tk()
canvas.title ("Music player")
canvas .geometry("600x800")
canvas.config(bg = 'pink')
# this will include the dimensions of the pop up and the music player title as well as the background color

rootpath = "/Users/jeremyjohn/Desktop/music"
pattern = "* .mp3"
nameBox = tk.Listbox(canvas, fg = "cyan", bg ="black", width = 100, font=('poppins',14))
nameBox.pack(padx = 15, pady = 15)
#the rootpath function is the one that will access the folder with the mp3 files

label = tk.Label(canvas, text = '', bg = 'black', fg ='yellow', font =('poppins',18))
label.pack(pady=15)


                 


for root, dirs, files in os.walk(rootpath):
    for filename in fnmatch.filter(files, pattern):
        nameBox.insert('end', filename)



canvas.mainloop()