# Toms Tkinter GUI
import time
from tkinter import *
import tkinter as tk
from tkinter import ttk

import tkinter.font as font

import threading
import fitz
from PIL import ImageTk, Image

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import style
import matplotlib.animation as animation
#from EntropyCoefficient import *

'''
import urllib
import json

import pandas as pd
import numpy as np
'''

# Changing the state of a button ( used for the start button
def buttonState(button):
    
    if (button['state'] == NORMAL or button['state'] == ACTIVE):
        button['state'] = DISABLED
    elif (button['state'] == DISABLED):
        button['state'] = NORMAL

def ImageHolder(image, frame):
    image1 = Image.open(image)
    image1 = image1.resize((120, 120), Image.ANTIALIAS)
    test = ImageTk.PhotoImage(image1)
    text_label = Label(frame, image=test, bg="#AE1C2B")
    text_label.place(relx=0.95, rely=0.70, anchor=SE)
    text_label.image = test

# ----------------------- PULLING DATA and PLOTTING ---------------------#
# plotting function
def animateTemp(i):
    pulledData = open("MovingData.txt", "r").read()
    dataList = pulledData.split('\n')
    xList = []
    yList0 = []
    yList1 = []
    yList2 = []
    yList3 = []
    for eachLine in dataList:
        if len(eachLine) > 1:  # stops blank lines from being .split()

            [time, t0, t1, t2, t3, volt] = eachLine.split(',')  # " csv" splitting
            xList.append(float(time))  # Because it's going to be read as a sting ??
            yList0.append(float(t0))
            yList1.append(float(t1))
            yList2.append(float(t2))
            yList3.append(float(t3))

    a.clear()  # This gets rid of the old graph
    a.plot(xList, yList0, label="Top Peltier Temp")
    a.plot(xList, yList1, label="Top Battery Temp")
    a.plot(xList, yList2, label="Bottom Peltier Temp")
    a.plot(xList, yList3, label="Bottom Battery Temp")
    a.legend()

# plotting function
def animateRawTemp(i):
    pulledData = open("Data.txt", "r").read()
    dataList = pulledData.split('\n')
    xList = []
    yList0 = []
    yList1 = []
    yList2 = []
    yList3 = []
    for eachLine in dataList:
        if len(eachLine) > 1:  # stops blank lines from being .split()

            [time, t0, t1, t2, t3, volt] = eachLine.split(',')  # " csv" splitting
            xList.append(float(time))  # Because it's going to be read as a sting ??
            yList0.append(float(t0))
            yList1.append(float(t1))
            yList2.append(float(t2))
            yList3.append(float(t3))

    b.clear()  # This gets rid of the old graph
    b.plot(xList, yList0, label="Top Peltier Temp")
    b.plot(xList, yList1, label="Top Battery Temp")
    b.plot(xList, yList2, label="Bottom Peltier Temp")
    b.plot(xList, yList3, label="Bottom Battery Temp")
    b.legend()

def animateVoltage(i):
    pulledData = open("MovingData.txt", "r").read()
    dataList = pulledData.split('\n')
    xList = []
    yListv = []
    for eachLine in dataList:
        if len(eachLine) > 1:  # stops blank lines from being .split()

            [time, t0, t1, t2, t3, volt] = eachLine.split(',')  # " csv" splitting
            xList.append(float(time))  # Because it's going to be read as a sting ??
            yListv.append(float(volt))

    c.clear()  # This gets rid of the old graph
    c.plot(xList, yListv, label="Battery Voltage")
    c.legend()

def updateMessage():

    Live = app.books[liveFrame].Live
    names = ["state", "targetTemp", "topAvgTemp", "botAvgTemp", "avgVolt", "topPelt", "botPelt"]
    messages = ["System State: {}", "Target Temperature: {}", "Top Battery Temperature: {}",
               "Bottom Battery Temperature: {}", "Average n={} Voltage: {}",
               "Top Peltier: Duty= {} Dir= {}", "Bot Peltier: Duty= {} Dir= {}"]
    #numbers = [sys.state, sys.targetTemp, sys.temp1Avg[0], sys.temp3Avg[0], sys.vBuffAvg[0],
               #(control.top_duty, control.top_direction), (control.bot_duty, control.bot_direction)]
    numbers = ["new","new","new","new",("new","new"),("new","new"),("new","new")]
    for index, (name,msg,num) in enumerate(zip(names,messages, numbers)):
        if index < 4:
            txt = msg.format(num) #sys.message)
        else:
            txt = msg.format(num[0],num[1])

        Live.labels[name].config(text=txt)
        Live.labels[name].update_idletasks()

    root.after(1000, updateMessage)
    

def animateRawVoltage(i):
    pulledData = open("Data.txt", "r").read()

    dataList = pulledData.split('\n')
    xList = []
    yListv = []
    for eachLine in dataList:
        if len(eachLine) > 1:  # stops blank lines from being .split()

            [time, t0, t1, t2, t3, volt] = eachLine.split(',')  # " csv" splitting
            xList.append(float(time))  # Because it's going to be read as a sting ??
            yListv.append(float(volt))

    d.clear()  # This gets rid of the old graph
    d.plot(xList, yListv, label="Raw Battery Voltage")
    d.legend()


# this calls all of the GUI settings
def apply(startButton, startPressed):

    # Carrry out settings change
    [sys.commandPeltier, sys.predictionState] = app.books[settingsFrame].settingPage.boxState()  # runs a function in the settings page
    if startPressed == 0:
        buttonState(startButton) # enables the start button

    usrSteps = usr_steps.get()
    sys.usrStepChoice(usrSteps)

    sys.bufferLen = int(bufferLen.get())
    print("bufferLen",sys.bufferLen)
    sys.avgLength = int(avgLength.get())
    sys.avgLengthVolt = int(avgLengthVolt.get())
    sys.voltLevelRange = float(voltLevelRange.get())
    sys.voltLevelSD = voltLevelSD.get()  # this is taken as a string as it can be empty
    sys.voltMeasureLen = int(voltMeasureLen.get())
    sys.predictionPeriod = int(predictionPeriod.get())
    control.batteryKp = int(batteryKp.get())
    control.batteryKi = float(batteryKi.get())
    control.peltierKp = int(peltierKp.get())


    print("Peltier Command", sys.commandPeltier)


def start(controller):  # This function calls the GUI to run on it's own thread
    buttonState(startButton) # disables the start button again    
    app.books[settingsFrame].settingPage.startPressed = 1 # start button has now been pressed

    controller.show_book(settingsFrame)
    
    x = threading.Thread(target=begin,args=(0,))  # daemon=True # daemon threads don't have to finish before the process can quit
    x.start()


def QUIT():
    sys.off()
    raise SystemExit(0)  # quits the program


# ----------------------- GUI START -----------------------#
class EntropyGUI():
    def __init__(self, root):
        # ------ NOTE BOOKS  -------#
        self.books = {}  # This dictionary contains all the frames ??

        for N in (startFrame,checklistFrame, pdfFrame1,pdfFrame2, settingsFrame, liveFrame):
            notebook = N(root, self)  # Calls the notebook function in question, self is
            self.books[N] = notebook  # Adds notebook to notebook dictionary
            #notebook.pack(side=LEFT)
            notebook.grid(row=0, column=0, sticky="nsew")

        self.show_book(startFrame)  # first bring the Start Notebook to the front

    def show_book(self, cont):  # Brings notebooks to the front
        book = self.books[cont]
        book.tkraise()  # Brings this frame to the front

    def style(self):
        s = ttk.Style()

        # bristol colours RGB = 174,28,43 "#AE1C2B"

        # buttons salmon RGB = 248, 104,94 "#F8685E"

        # Create Notebook theme which selects font, font size, colours, and size of tabs   "#8b0000"
        s.theme_create("GuiStyle", parent="alt", settings={
            "TNotebook": {"configure": {"tabmargins": [5, 5, 0, 0], "background": "#AE1C2B"}},
            "TNotebook.Tab": {"configure": {"padding": [20, 10], "background": "pink1",
                                            "font": ('Helvetica', '16', 'bold')},
                              "map": {"background": [("selected", "#AE1C2B")],
                                      "foreground": [("selected", "white")],
                                      "expand": [("selected", [1, 1, 1, 0])],
                                      },

                              }})
        s.theme_use("GuiStyle")

# ---------------------------------------- NOTEBOOK CLASS ----------------------------------#
class nb(ttk.Notebook):
    def __init__(self, root):
        ttk.Notebook.__init__(self, root)

        self.butH = 3
        self.butW = 8
        self.butBG = "white"  # F8685E"
        self.butFG = "black"
        self.butFONT = buttonFont
        self.bakBG = "blue"
        self.tabBG = "#AE1C2B"
        self.tabH = 550
        self.tabW = 1023
        self.txtFont = txtFont
    
 


    def navButtons(self, tab, controller):
        rightButtons = tk.Frame(tab, bg=self.bakBG)
        tab.grid_columnconfigure(2, weight=1)
        rightButtons.grid(row=0, column=3, sticky="n")  # ns causes frame to expand vertically

        #rightButtons.pack(side=RIGHT)
        button3 = tk.Button(rightButtons, text="Start\nPage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(startFrame))
        button3.pack(side=TOP)
        # button3.grid(row=2, column=2, sticky="e")
        button1 = tk.Button(rightButtons, text="Settings\nPage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(settingsFrame))
        #button1.grid(row=0, column=2, sticky="e")
        button1.pack(side=TOP)
        button2 = tk.Button(rightButtons, text="Live\nPage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(liveFrame))
        button2.pack(side=TOP)

        #button2.grid(row=1, column=2, sticky="e")


        button4 = tk.Button(rightButtons, text="Quit", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: QUIT())
        button4.pack(side=TOP)
        button5 = tk.Button(rightButtons, text="Next\nStep", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: sys.forceStep())
        button5.pack(side=TOP)
        #button4.grid(row=2, column=2, sticky="e")

# ------------------------------------------- START PAGE ------------------------------------------#
class startFrame(tk.Frame):  # The notebook has to sit on a frame in order for the tkraise to work properly
    def __init__(self, root, controller):
        self.butH = 2
        self.butW = 8
        self.butBG = "white"
        self.butFG = "black"
        self.butFONT = buttonFont
        self.messageFONT = messageFONT
        self.bakBG = "blue"
        self.tabBG = "#AE1C2B"
        self.tabH = 550
        self.tabW = 1023

        tk.Frame.__init__(self, root, width=self.tabW, height=self.tabH, bg=self.tabBG)
        self.grid(row=0, column=0, sticky="nsew")

        text = Label(self, text="Cylindrical Battery\nEntropy Coefficient Experiment", fg="white", bg=self.tabBG,
                     font=("Helvetica", 32))
        text.place(relx=0.5, rely=0.1, anchor=N)
        text2 = Label(self, text="Please see checklist before first use", fg="white", bg=self.tabBG,
                      font=("Helvetica", 20))
        text2.place(relx=0.5, rely=0.25, anchor=N)

        self.button1 = tk.Button(self, text="Settings Page", height=self.butH, width=self.butW+6, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT,state=DISABLED, command=lambda: controller.show_book(settingsFrame))
        self.button1.place(relx=0.5, rely=0.6, anchor=N)
        button2 = tk.Button(self, text="Instructions", height=self.butH, width=self.butW+3, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(pdfFrame1))
        button2.place(relx=0.5, rely=0.5, anchor=N)
        button3 = tk.Button(self, text="Safety Checklist", height=self.butH, width=self.butW + 6, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(checklistFrame))
        button3.place(relx=0.5, rely=0.4, anchor=N)


        ImageHolder("University_of_Bristol_logo.png",self)

        self.grid(row=2, column=2, sticky="nsew")

# ------------------------------------------- CHECKLIST PAGE ------------------------------------------#
class checklistFrame(tk.Frame):  # The notebook has to sit on a frame in order for the tkraise to work properly
    def __init__(self, root, controller):
        self.butH = 2
        self.butW = 8
        self.butBG = "white"
        self.butFG = "black"
        self.butFONT = buttonFont
        self.messageFONT = messageFONT
        self.bakBG = "blue"
        self.tabBG = "#AE1C2B"
        self.tabH = 550
        self.tabW = 1023

        tk.Frame.__init__(self, root, width=self.tabW, height=self.tabH, bg=self.tabBG)
        self.grid(row=0, column=0, sticky="nsew")


        # ----------------- CHECK BOXES ---------------#

        self.var1 = IntVar()
        self.var2 = IntVar()
        self.var3 = IntVar()
        self.var4 = IntVar()
        self.var5 = IntVar()

        chkFrame = Frame(self, bg=self.tabBG)

        chk1 = Checkbutton(chkFrame, text="Coolant is flowing properly ", variable=self.var1, bg=self.tabBG,font=messageFONT,fg ="white")
        chk1.pack(side=tk.TOP)

        chk2 = Checkbutton(chkFrame, text="Ensure both thermal fuses\nare correctly installed", variable=self.var2,
                           bg=self.tabBG,fg ="white",font=messageFONT)
        chk2.pack(side=tk.TOP)

        chk2 = Checkbutton(chkFrame, text="Check raspberry PI GPIO\nconfiguration against documentation", variable=self.var3,
                           bg=self.tabBG,fg ="white",font=messageFONT)
        chk2.pack(side=tk.TOP)

        chk2 = Checkbutton(chkFrame, text="Kill switch has been tested",
                           variable=self.var4,
                           bg=self.tabBG,fg ="white",font=messageFONT)
        chk2.pack(side=tk.TOP)

        chk3 = Checkbutton(chkFrame, text="Read safety instructions", variable=self.var5,
                           bg=self.tabBG,fg ="white",font=messageFONT)
        chk3.pack(side=tk.TOP)

        chkFrame.place(relx=0.45, rely=0.5, anchor=CENTER)


        #------------------ BUTTONS -----------------#

        buttonFrame = Frame(self, bg=self.tabBG)
        button1 = tk.Button(buttonFrame, text="Start Page", height=self.butH, width=self.butW+2, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: self.toStart(controller))
        button1.pack()
        buttonFrame.place(relx=0.65, rely=0.5, anchor=CENTER)

    def toStart(self,controller):
        checkVar = self.var1.get()+self.var2.get()+self.var3.get()+self.var4.get()+self.var5.get()
        button = app.books[startFrame].button1
        if checkVar == 5:
            button['state'] = NORMAL

        controller.show_book(startFrame)

# ------------------------------------------- PDF PAGE 1------------------------------------------#
class pdfFrame1(tk.Frame):  # The notebook has to sit on a frame in order for the tkraise to work properly
    def __init__(self, root, controller):
        self.butH = 2
        self.butW = 8
        self.butBG = "white"
        self.butFG = "black"
        self.butFONT = buttonFont
        self.messageFONT = messageFONT
        self.bakBG = "blue"
        self.tabBG = "#AE1C2B"
        self.tabH = 550
        self.tabW = 1023

        tk.Frame.__init__(self, root, width=self.tabW, height=self.tabH, bg="white")
        self.grid(row=0, column=0, sticky="nsew")
        buttonFrame = Frame(self)
        button1 = tk.Button(buttonFrame, text="Start\npage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(startFrame))
        #button1.place(relx=0.5, rely=0.5, anchor=N)
        button1.pack()
        button2 = tk.Button(buttonFrame, text="Next\npage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(pdfFrame2))
        #button2.place(relx=0.5, rely=0.5, anchor=N)
        button2.pack()
        buttonFrame.grid(row=0, column=1, sticky="ew")

        image1 = Image.open("InstructionsPage1.png")
        image1 = image1.resize((705, 500), Image.ANTIALIAS)
        test = ImageTk.PhotoImage(image1)
        text_label = Label(self, image=test, bg="white")
        text_label.grid(row=0,column=0, sticky="ns")
        text_label.image = test


        # # MuPDF code
        # # -----------------------------------------------------------------
        # doc = fitz.open("Instructions.pdf")
        # pix = doc.getPagePixmap(1 - 1)  # create pixmap for a page
        #
        # # -----------------------------------------------------------------
        # # Tkinter code
        # # -----------------------------------------------------------------
        # self.img = Image.frombytes("RGB",
        #                            [pix.width, pix.height],
        #                            pix.samples)
        # self.photo = ImageTk.PhotoImage(self.img)
        # canvas = Canvas(self, width=self.img.size[0] + 20,
        #                 height=self.img.size[1] + 5)
        # canvas.create_image(10, 10, anchor=NW, image=self.photo)
        # #canvas.pack(fill=BOTH, expand=1)
        # canvas.grid(row=1, column=0, sticky="nsew")

# ------------------------------------------- PDF PAGE 2------------------------------------------#
class pdfFrame2(tk.Frame):  # The notebook has to sit on a frame in order for the tkraise to work properly
    def __init__(self, root, controller):
        self.butH = 2
        self.butW = 8
        self.butBG = "white"
        self.butFG = "black"
        self.butFONT = buttonFont
        self.messageFONT = messageFONT
        self.bakBG = "blue"
        self.tabBG = "#AE1C2B"
        self.tabH = 550
        self.tabW = 1023

        tk.Frame.__init__(self, root, width=self.tabW, height=self.tabH, bg="white")
        self.grid(row=0, column=0, sticky="nsew")
        buttonFrame = Frame(self)
        button1 = tk.Button(buttonFrame, text="Start\npage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(startFrame))
        button1.pack()
        button2 = tk.Button(buttonFrame, text="Next\npage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(pdfFrame2))
        button2.pack()
        button2 = tk.Button(buttonFrame, text="Previous\npage", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: controller.show_book(pdfFrame1))

        button2.pack()
        buttonFrame.grid(row=1, column=1, sticky="ew")


        # MuPDF code
        # -----------------------------------------------------------------
        doc = fitz.open("Instructions.pdf")
        pix = doc.getPagePixmap(2 - 1)  # create pixmap for a page

        # -----------------------------------------------------------------
        # Tkinter code
        # -----------------------------------------------------------------
        self.img = Image.frombytes("RGB",
                                   [pix.width, pix.height],
                                   pix.samples)
        self.photo = ImageTk.PhotoImage(self.img)
        canvas = Canvas(self, width=self.img.size[0] + 20,
                        height=self.img.size[1] + 5)
        canvas.create_image(10, 10, anchor=NW, image=self.photo)
        #canvas.pack(fill=BOTH, expand=1)
        canvas.grid(row=1, column=0, sticky="nsew")

# --------------------------------------- SETTINGS PAGE -----------------------------------------#
class settingsFrame(tk.Frame):
    def __init__(self, root, controller):
        tk.Frame.__init__(self, root)
        #self.pack()
        self.grid(row=0, column=0, sticky="nsew")
        self.settingPage = Settings(self, controller)

class Settings(nb):
    def __init__(self, root, controller):  # controller is EntropyGUI, which has the show_book function
        nb.__init__(self, root)
        self.startPressed = 0

        self.pack(fill="both") #,expand=1)
        #self.grid(row=0, column=0, sticky="nsew")

        # ------ TAB 1 ------- #
        tab1 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab1.pack(fill="both", expand=1)
        self.add(tab1, text="Experiment Settings")

        # ---- BUTTONS --- #
        self.navButtons(tab1, controller)  # Generate the navigation buttons
        
        settingMainFrame = Frame(tab1, bg=self.tabBG)
        buttonFrame = Frame(settingMainFrame, bg=self.tabBG)

        global startButton
        startButton = tk.Button(buttonFrame, text="Start\nExperiment", height=self.butH, width=self.butW+4, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT,state=DISABLED, command=lambda: start(controller))
        startButton.pack(side=LEFT)

        button2 = tk.Button(buttonFrame, text="Apply\nChanges", height=self.butH, width=self.butW, bg=self.butBG,
                            fg=self.butFG, font=self.butFONT, command=lambda: apply(startButton,self.startPressed))
        button2.pack(side=LEFT)
        buttonFrame.grid(row=1,column=0, sticky="ns",padx=40, pady=20)

        # ----------------- CHECK BOXES ---------------#
        chkLabelFrame = Frame(settingMainFrame, bg=self.tabBG)
        chkFrame = Frame(chkLabelFrame, bg=self.tabBG)

        self.var1 = IntVar()  # inits the command peltier
        chk1 = Checkbutton(chkFrame, text="Command Peltiers", variable=self.var1, bg=self.tabBG,fg="white")
        chk1.pack(side=tk.TOP)

        self.var2 = IntVar()  # inits the predictionState variable
        chk2 = Radiobutton(chkFrame, text="Det. voltage change by predictions", variable=self.var2, value=1,
                           bg=self.tabBG,fg="white")
        chk2.pack(side=tk.TOP)

        chk3 = Radiobutton(chkFrame, text="Det. voltage change by threshold ", variable=self.var2, value=0,
                           bg=self.tabBG,fg="white")
        chk3.pack(side=tk.TOP)

        chkFrame.grid(row=0, column=0, sticky="ew")

        # ---------------- ENTRY's ----------------#

        entryFont = ("Helvetica", 16)

        # label frame for all the entry labels
        entryLabelFrame = Frame(chkLabelFrame, bg=self.tabBG)
        labelEntry1 = tk.Label(entryLabelFrame, text="Temperature stepping profile (eg.25,30): ",fg="white",
                               bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry2 = tk.Label(entryLabelFrame, text="Buffer length(s): ",fg="white",bg=self.tabBG,
                               font=entryFont).pack(side=tk.TOP)
        labelEntry3 = tk.Label(entryLabelFrame, text="Temp. moving avg. length (points): ",fg="white",
                               bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry4 = tk.Label(entryLabelFrame, text="Volt. moving avg. length (points): ",fg="white",
                               bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry5 = tk.Label(entryLabelFrame, text="Volt. detection threshold (+/- V): ",fg="white",
                               bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry6 = tk.Label(entryLabelFrame, text="Volt. detection threshold (Std.Dev): ",fg="white",
                               bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry11 = tk.Label(entryLabelFrame, text="Volt. measurement avg. length (points): ",fg="white",
                                bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry7 = tk.Label(entryLabelFrame, text="Prediction Period (s): ",fg="white", bg=self.tabBG,
                               font=entryFont).pack(side=tk.TOP)
        labelEntry8 = tk.Label(entryLabelFrame, text="Battery control proportional gain Kp: ",fg="white",
                               bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
        labelEntry9 = tk.Label(entryLabelFrame, text="Battery control integral gain Ki: ",fg="white", bg=self.tabBG,
                               font=entryFont).pack(side=tk.TOP)
        labelEntry10 = tk.Label(entryLabelFrame, text="Peltier control proportional gain Kp: ",fg="white",
                                bg=self.tabBG, font=entryFont).pack(side=tk.TOP)
    
        entryLabelFrame.grid(row=0, column=1, sticky="ew")
        ##self.messageLabel = self.messageBox(tab1, controller)

        # entry frame for all the entry
        entryFrame = Frame(chkLabelFrame, bg=self.tabBG)
        variables = [usr_steps, bufferLen, avgLength, avgLengthVolt, voltLevelRange, voltLevelSD, voltMeasureLen,
                     predictionPeriod, batteryKp, batteryKi, peltierKp]  # all the entriy variables
        defaults = ["25,30,35", "1000", "20", "100", "0.0001", "", "400", "3", "25", "0.1",
                    "4"]  # default values for those entries
        for var, dflt in zip(variables, defaults):  # looping through both lists at the same time
            entry = tk.Entry(entryFrame, textvariable=var, font=self.txtFont)
            entry.insert(-1, dflt)
            entry.pack(side=tk.TOP)
        entryFrame.grid(row=0, column=2, sticky="ew",pady=10)
        chkLabelFrame.grid(row=0, column=0, sticky="ew",pady=10)
        settingMainFrame.grid(row=0, column=0, sticky="ew")
        
        # # ---------- TAB 2 ----------#
        # tab2 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        # tab2.pack(fill="both", expand=1)
        #
        # self.add(tab2, text="Other Settings")
        #
        # # --- buttons ---#
        # self.navButtons(tab2, controller)  # Generate the navigation buttons

    def boxState(self):
        return [self.var1.get(), self.var2.get()]

# ------------------------------------------- LIVE PAGE ------------------------------------------#
class liveFrame(tk.Frame):  # The notebook has to sit on a frame in order for the tkraise to work properly
    def __init__(self, root, controller):
        tk.Frame.__init__(self, root)#, width=200, height=200)

        #self.pack(side=LEFT)
        self.grid(row=0, column=0, sticky="nsew")
        self.Live = Live(self, controller)


class Live(nb):
    def __init__(self, root, controller):  # controller is EntropyGUI, which has the show_book function
        nb.__init__(self, root)
        #self.grid(row=0, column=0, sticky="nsew")
        self.pack(fill="both") #, expand=True)

        # ------------------------------- TAB 1 -----------------------------#
        tab1 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab1.pack(fill="both", expand=1)
        self.add(tab1, text="Temperature")

        # ---- BUTTONS -----#
        self.navButtons(tab1, controller)  # Generate the navigation buttons
        self.messageBox(tab1,controller)

        # ---- GRAPHING -----##
        canvasFrame = Frame(tab1)
        canvas = FigureCanvasTkAgg(f1, canvasFrame)
        canvas.draw()
        canvas.get_tk_widget().pack()
        canvasFrame.grid(row=0, column=0, sticky="nsew",padx=15)

        # ------------------------------ TAB 2 --------------------------------#
        tab2 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab2.pack(fill="both", expand=1)
        self.add(tab2, text="Raw Temperature")

        # ------ BUTTONS ------#

        self.navButtons(tab2, controller)  # Generate the navigation buttons
        self.messageBox(tab2, controller)
        # ---- GRAPHING -------#
        
        canvas = FigureCanvasTkAgg(f2, tab2)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew",padx=15)

        # ------------------------------- TAB 3 -----------------------------#
        tab3 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab3.pack(fill="both", expand=1)
        self.add(tab3, text="Voltage")

        self.navButtons(tab3, controller)  # Generate the navigation buttons
        self.messageBox(tab3, controller)

        # ---- GRAPHING -------#
        canvas = FigureCanvasTkAgg(f3, tab3)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew",padx=15)



        # ------------------------------- TAB 4 -----------------------------#
        tab4 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab4.pack(fill="both", expand=1)
        self.add(tab4, text="Raw Voltage")

        self.navButtons(tab4, controller)  # sf
        # Generate the navigation buttons
        self.messageBox(tab4, controller)


        # ---- GRAPHING -------#
        canvas = FigureCanvasTkAgg(f4, tab4)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew",padx=15)

        
    def messageBox(self, tab, controller):
        self.messageFrame = tk.Frame(tab,width=100,height=400, bg=self.tabBG)
        message = ["System State: {}", "Target Temperature:  {}", "Top Battery Temperature:  {}","Bottom Battery Temperature:  {}", "Average n=  {}  Avg Voltage=  {}",
                    "Top Peltier: Duty=  {}  Dir=  {}", "Bot Peltier: Duty=  {}  Dir=  {}" ]
        numbers = [None,None,None,None,(None,None),(None,None),(None,None)]
        names = ["state", "targetTemp", "topAvgTemp", "botAvgTemp", "avgVolt", "topPelt", "botPelt"]
        self.labels = {}
        for i, (name, msg, num) in enumerate(zip(names,message,numbers)):
            if i < 4:
                txt = msg.format(num)
            else:
                txt = msg.format(num[0], num[1])
            label = Label(self.messageFrame, text=txt, fg="white",
                               bg=self.tabBG, font=messageFONT)
            label.pack(side=tk.TOP,expand=0)
            self.labels[name] = label
        self.messageFrame.grid(row=0, column=1, padx=20)#, sticky="ns")  # ns causes frame to expand vertically
        
    
# -------------------------------------------- EXPORT PAGE -----------------------------------------------#
class exportFrame(tk.Frame):  # The notebook has to sit on a frame in order for the tkraise to work properly
    def __init__(self, root, controller):
        tk.Frame.__init__(self, root)
        #self.pack()
        self.grid(row=0, column=0, sticky="nsew")
        Export(self, controller)


class Export(nb):
    def __init__(self, root, controller):  # controller is EntropyGUI, which has the show_book function
        nb.__init__(self, root)
        self.pack(pady=15)

        # ------ TAB 1 -------#
        tab1 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab1.pack(fill="both", expand=1)
        self.add(tab1, text="Tab 1")

        # ------ TAB 2 -------#
        tab2 = tk.Frame(self, width=self.tabW, height=self.tabH, bg=self.tabBG)
        tab2.pack(fill="both", expand=1)
        self.add(tab2, text="Live")

        # ------ BUTTONS ------#
        self.navButtons(tab1, controller)  # Generate the navigation buttons
        self.navButtons(tab2, controller)  # Generate the navigation buttons


#sys = system()

root = tk.Tk()
root.geometry('1023x550')  # set the size of the window
root.title("Tabs GUI")

i = 1

LARGE_FONT = ("Verdana", 12)
style.use("ggplot")  # style for the matplotlib

startButton = None

# Have to define graphs before as multiple functions use it
f1 = Figure(figsize=(5, 5), dpi=100)
f2 = Figure(figsize=(5, 5), dpi=100)
f3 = Figure(figsize=(5, 5), dpi=100)
f4 = Figure(figsize=(5, 5), dpi=100)
a = f1.add_subplot(1, 1, 1)
b = f2.add_subplot(1, 1, 1)
c = f3.add_subplot(1, 1, 1)
d = f4.add_subplot(1, 1, 1)

# ----------------------- NAME VARS -------------------#
usr_steps = tk.StringVar()
bufferLen = tk.StringVar()
avgLength = tk.StringVar()
avgLengthVolt = tk.StringVar()
voltLevelRange = tk.StringVar()
voltLevelSD = tk.StringVar()
voltMeasureLen = tk.StringVar()
predictionPeriod = tk.StringVar()
batteryKp = tk.StringVar()
batteryKi = tk.StringVar()
peltierKp = tk.StringVar()

# ------------------------ FONT ----------------------- #
buttonFont = font.Font(size=20, family='Helvetica', weight="bold")
messageFONT = font.Font(size=16,family = 'Helvetica')
txtFont = font.Font(size=13, family='Helvetica')

# ---------------------- BUTTON SETTINGS ----------------#
app = EntropyGUI(root)  # this begins the process of making seperate notebooks
app.style()
print("startPressesd = ", app.books[settingsFrame].settingPage.startPressed)


aniT = animation.FuncAnimation(f1, animateTemp,interval=500)  # (figure, animate function, how often is the animation run in (ms)
aniRT = animation.FuncAnimation(f2, animateRawTemp, interval=500)  # Raw temperature
aniV = animation.FuncAnimation(f3, animateVoltage, interval=500)  # Moving average Voltage
aniRV = animation.FuncAnimation(f4, animateRawVoltage, interval=500)  # Raw Voltage
root.after(1000, updateMessage)
root.mainloop()

#-----------------------------------------------------------------


