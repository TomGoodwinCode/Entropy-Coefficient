import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

import collections
from collections import deque

import math

import RPi.GPIO as GPIO

import matplotlib.pyplot as plt
import numpy as np
from numpy import cumsum
from itertools import count

from timeit import default_timer as timer

from scipy.signal import butter, lfilter, filtfilt, freqz
from scipy.optimize import curve_fit


# read a file into and array
def readFile(filename):  # Read files into a list
    pullData = open(filename, "r").read()
    dataList = pullData.split('\n')
    xList = []
    # yList = []   # kept here incase y value is needed in another function
    for eachLine in dataList:
        if len(eachLine) > 1:  # stops blank lines from being .split()
            # x = eachLine.split(',')  # " csv" splitting
            xList.append(float(eachLine))  # Because it's going to be read as a sting ??
            # yList.append(int(y))
    return xList


# for the prediction function, not sure how it works lol
def func(x, a, b, c):
    return a * np.exp(-b * x) + c

# gives moving average of using the last n(here=3) values
def movingAverage(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


# --------------------------------- READING VOLT & TEMP --------------------------------- #
class readVal():
    def __init__(self):
        # ----------------------------------------SETTING UP ADCs-----------------------------------------#
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        ads0 = ADS.ADS1115(i2c, address=0x48)  # Peltier & Battery ADC
        ads1 = ADS.ADS1115(i2c, address=0x49)  # Block thermistor ADC
        ads2 = ADS.ADS1115(i2c, address=0x4A)  # BLock thermistor ADC
        ads3 = ADS.ADS1115(i2c, address=0x4B)  # Battery Voltage ADC

        ### GAIN OF ADC ###
        ads3.gain = 2 / 3
        ads2.gain = 2 / 3

        # Creating channels for data to be read from
        self.chan00 = AnalogIn(ads0, ADS.P0)  # TOP PELTIER
        self.chan01 = AnalogIn(ads0, ADS.P1)  # TOP BATTERY
        self.chan02 = AnalogIn(ads0, ADS.P2)  # BOTTOM PELTIER
        self.chan03 = AnalogIn(ads0, ADS.P3)  # BOTTOM BATTERY

        self.chan10 = AnalogIn(ads1, ADS.P0)  # TOP LHS
        self.chan11 = AnalogIn(ads1, ADS.P1)  # TOP RHS
        self.chan12 = AnalogIn(ads1, ADS.P2)  # BOTTOM LHS
        self.chan13 = AnalogIn(ads1, ADS.P3)  # BOTTOM RHS

        self.chanVnorm = AnalogIn(ads2, ADS.P0, ADS.P1)  # RAIL VOLTAGE FROM PI
        self.chan22 = AnalogIn(ads2, ADS.P2)  # TOP CORNER
        self.chan23 = AnalogIn(ads2, ADS.P3)  # BOTTOM CORNER

        self.chanV = AnalogIn(ads3, ADS.P0, ADS.P1)  # VOLTAGE FEEDBACK  ( measured voltage )

        self.voltRead()  # Read voltages

        # --------RESISTOR VALUES---------#
        self.Rnorm = np.asarray(readFile("ResistorNorm.txt"))  # Resistances at RTP
        self.Rcali = np.asarray(readFile("ResistorCali.txt")) / 10000  # Calibration R's and /10000

    # ----- READING VOLTAGE ------ #
    def voltRead(self):  # Reads voltage from the pins
        self.Vnorm = self.chanVnorm.voltage  # From the pi +ve and -ve lines
        self.VnormArry = np.full(10, self.Vnorm)  # Makes into 10 long np.array for calculations later
        self.Vfeed = self.chanV.voltage  # Voltage from Battery
        self.Vsens = np.asarray([i.voltage for i in [self.chan00, self.chan01, self.chan02, self.chan03,
                                                     self.chan10, self.chan11, self.chan12, self.chan13,
                                                     self.chan22, self.chan23]])  # np.array of V from thermistors

    def resist(self, Rnorm, Vnorm, Vsens):  # Vsens is all the measured voltages from the
        with np.errstate(divide='ignore'):
            Rsens = -(Rnorm * Vsens) / (Vsens - Vnorm)

        return Rsens

    # calculates the temperature from the resistance at 0 and the current resistance
    def fitwithfudge(self, res, res0):
        fudge = 2.8024 - res0
        adjres = res + fudge
        fudgetemp = 175.169386336537 * (np.sign(adjres) * np.abs(
            adjres) ** -0.149487726808224) - 150.164035918377  # sign()abs() needed to deal with numpy issue w/ (-ve)**x
        return fudgetemp

    def fitwithfudge2(self, res, res0):
        fudge = 27.70 - res0
        adjres = res + fudge
        fudgetempTop = 246.2015192087679 * (np.sign(adjres) + np.abs(adjres) ** -0.153315768371400) - 147.972335603963
        return fudgetempTop

        # ------ CALULATING ALL THERMISTOR TEMPERATURES ------ #

    def temp(self):
        self.voltRead()  # getting latest readings
        self.temps = self.fitwithfudge(self.resist(self.Rnorm, self.VnormArry, self.Vsens) / 10000, self.Rcali)
        # self.temps[0] = self.fitwithfudge2(self.resist(self.Rnorm[0], self.VnormArry[0], self.Vsens[0]) / 10000, self.Rcali[0])
        # self.temps[2] = self.fitwithfudge2(self.resist(self.Rnorm[2], self.VnormArry[2], self.Vsens[2]) / 10000, self.Rcali[2])

        return self.temps

    def tempPeltier(self):
        self.voltRead()  # getting latest readings
        self.temps = self.fitwithfudge(self.resist(self.Rnorm, self.VnormArry, self.Vsens) / 10000, self.Rcali)
        return self.tempsPeltier


# ---------------------------------- PELTIER CONTROL -------------------------------------- #
class controlPeltiers():
    def __init__(self):

        #self.batteryKp = 15
        #self.batteryKi = 0
        #self.peltierKp = 4

        self.topErrorTime = 0
        self.botErrorTime = 0

        # ------ SETTING UP THE PI--------#
        ### SET UP GPIO PINS ###
        GPIO.setup(13, GPIO.OUT)  # bot PMW
        GPIO.setup(19, GPIO.OUT)  # top PMW
        GPIO.setup(20, GPIO.OUT)  # top Peltier
        GPIO.setup(21, GPIO.OUT)  # bot pelt

        GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # 14 GPIO.IN high is for the stop button

        # GPIO.PWM(pin,freq)
        self.top_pwm = GPIO.PWM(19, 100)
        self.top_dir = GPIO.output(20, 0)  # 0 = POSITIVE 1 = NEGATIVE
        self.bot_pwm = GPIO.PWM(13, 100)
        self.bot_dir = GPIO.output(21, 0)  # 0 = POSITIVE 1 = NEGATIVE

        ### START PWM DUTY CYCLE ###
        self.top_pwm.start(0)
        self.bot_pwm.start(0)

    def run(self, desired_temp, top_bat, bot_bat, top_pelt, bot_pelt):  # top_pelt and bot_pelt may be used later
        # runs the control methods and changes the duty cycle and direciton accordingly

        if sys.commandPeltier == 0:  # Effectively turning off the peltiers
            self.top_duty, self.bot_duty = 0, 0
            self.top_direction, self.bot_direction = 0, 0

        else:
            top_pelt_desired_temp = self.BatteryTempControl(desired_temp, top_bat, "top")
            bot_pelt_desired_temp = self.BatteryTempControl(desired_temp, bot_bat, "bot")

            [self.top_direction, self.top_duty] = self.PeltierTempControl(top_pelt_desired_temp)
            [self.bot_direction, self.bot_duty] = self.PeltierTempControl(bot_pelt_desired_temp)

            #  !! SAFETY !!  #     stops the peltiers from going above 50 degrees
            if top_pelt >= 50:  # Control part
                self.top_duty = 0

            if bot_pelt >= 50:
                self.bot_duty = 0
                
            if top_pelt <= 5:
                self.top_duty = 0
            if bot_pelt <= 5:
                self.bot_duty = 0
        # Setting the peltiers
        
        
        self.top_dir = GPIO.output(20, self.top_direction)
        self.bot_dir = GPIO.output(21, self.bot_direction)

        self.top_pwm.ChangeDutyCycle(self.top_duty)
        self.bot_pwm.ChangeDutyCycle(self.bot_duty)
        print("bot_dir =",self.bot_direction, "top_dir =",self.top_direction)
        print("bot_duty =",self.bot_duty," top_duty =",self.top_duty)

    # ----- BATTERY TEMPERATURE CONTROL ----- # takes battery temp and commands desired peltier temp
    def BatteryTempControl(self, desired_temp, batt_temp, topOrBot):
        # feedback signal
        error = desired_temp - batt_temp
        if abs(error) <= 1:
            if topOrBot == "top":
                self.topErrorTime += error
                errorOverTime = self.topErrorTime
            elif topOrBot == "bot":
                self.botErrorTime += error
                errorOverTime = self.botErrorTime
        else:
            errorOverTime = 0
            print("no integral now")
            
        print("cmd Kp=", error*self.batteryKp, "cmd Ki=", errorOverTime*self.batteryKi)
        print("ki= ", self.batteryKi)
        print("error over time=", errorOverTime)

        desired_peltier_temp = error * self.batteryKp  +errorOverTime * self.batteryKi

        return desired_peltier_temp

    def PeltierTempControl(self, pelt_desired_temp):  # side("top","bot")
        # feedback signals
        error = pelt_desired_temp

        # peltier temp is lower than desired
        if error >= 0:
            direction = 0
            duty = error * self.peltierKp
            if duty >= 100:
                duty = 99

        # peltier temp is greater than desired
        elif error < 0:
            direction = 1
            duty = -error * self.peltierKp
            if duty >= 100:
                duty = 99

        # Run functions to change output
        # self.PeltierDirection(side, direction)
        # self.PeltierHeat(side, duty)

        return direction, duty


# ---------------------------------- PREDICTIOR -------------------------------------- #
class predict():
    def __init__(self):
        self.derGap = 5  # gap between points in derivative calculation
        self.finalPredictions = []  # from predictor

    # Once the targetTemp has been reached this function will wait a certain mount of time
    # before prompting the pred.() function to find where the predictions should be made from
    def waitToPredict(self):
        print("WaitToPredict")
        time.sleep(5)  # arbitary value as of now

    # After the target temp is reached, this will find the point where the predictions can be made from
    # as the predictions can only be made once the exponential decay has begun.
    # Therefore this function finds where the maximum of the derivative is
    def predictStart(self, vBuff, timeBuff):
        print("Predict Start")
        vBuffShift = deque(vBuff)
        vBuffShift.rotate(self.derGap)  # shift it along so they can be taken away from eachother

        for i in range(self.derGap):  # takes away the first 5 to avoid the rotated array from causing problems
            vBuffShift.popleft()
            vBuff.popleft()
            timeBuff.popleft()

        vBuffAvgShift = movingAverage(vBuffShift)

        delta = sys.vBuffAvg - vBuffAvgShift  # taking the difference
        delta = delta[0::self.derGap]  # getting every 5th element from this np. array
        timeBuff = np.asarray(timeBuff)[0::self.derGap]  # getting time which can be plotted with the results
        timeDelta = timeBuff[1] - timeBuff[0]  # timestep
        diff = delta / timeDelta  # crude derivative

        self.timeStart = timeBuff[np.argmax(diff)]  # getting the time where
        sys.predictStart = "predict"  # Predictions can now be made
        print("timeStart = ", self.timeStart)

    # the voltage array given to exponential() must start at timestart
    # this function cuts the data off there
    def cutData(self, vBuff, timeBuff):
        print("cut data")
        pos = timeBuff.index(self.timeStart)  # finding timeStart in the buffer
        self.timeBuffCut = list(timeBuff)[pos:]
        self.vBuffCut = list(vBuff)[pos:]

    # Predicts a single value given the current voltage data
    # The func requires an x-axis which starts from 0 and continues very far, that's why x is generated here
    def exponential(self):  # this needs to start from timeStart every time
        print("exponential start")
        # print("seconds", sys.seconds)
        # print("prediction Period",sys.predictionPeriod)

        lengthData = len(self.timeBuffCut) # length of this data

        if (round(sys.seconds) % sys.predictionPeriod) == 0:
            print("making a prediction")
            x = np.linspace(0, 10000, 20001)  # if we're taking one reading every 0.5 s
            try:
                b, a = butter(3, 0.02)  # get filter
                yfil = filtfilt(b, a, self.vBuffCut)  # filter voltage values
                popt, pcov = curve_fit(func, self.timeBuffCut, yfil)  # make guess curve based on available data
                print("popt", type(popt), popt)
                print("pcov", type(pcov), pcov)
                curveY = func(x, *popt) # for plotting
                plotY = curveY[lengthData] # plot the first 4000 points
                plotX = [i + self.timeBuffCut[0] for i in x[lengthData]]

                final = curveY[20000]  # evaluates function and takes final value from the "predicted" curve


            except RuntimeError:
                print("curve not found")

            self.finalPredictions.append(final)

    # checks sd of the last 3 predictions
    def sDeviation(self):
        print("standard deviation")
        count = len(self.finalPredictions)
        test = self.finalPredictions[count - 3:count]
        if count >= 3:
            if np.std(test) > 0.00001:  # checks the sd of the last 3 predictions
                self.predicted = np.average(test)
                sys.state = "Measure"  # The prediction has been made
                sys.entropy()  # calls the function to measure entropy
                done = True
                print("predicted", self.predicted)
            else:
                done = False
                print("list of bad predictions", self.finalPredictions)

            return done


# ---------------------------------- SYSTEM -------------------------------------- #
class system():
    def __init__(self):
        # initialise the read() & control() classes
        print("called")

        self.message = "Initialising"
        self.state = "Rest"  # determines the actions which the experiment takes
        self.predictStart = "wait"  # have the predictions begun
        # self.tempSteps =readFile("targetTemps.txt") # Read file into numpy array
        self.tempStepCount = 1

        self.lastTargetTemp = 0  # initial target temp of 0 -> peltier duty cycle = 0
        self.seconds = 0  # inital time
        self.wait = 0.5  # time between itterations in (s)

        # for the period where average voltage is not being written
        self.temp0Avg = [0]
        self.temp1Avg = [0]
        self.temp2Avg = [0]
        self.temp3Avg = [0]
        self.vBuffAvg = [0]

        self.commandPeltier = 0  # for the checkbox in the settings page

        # --- to be definied later ---#
        self.temps = []

        # ---- RECORDING ----- #
        self.clearFile()

        self.voltages = []
        self.lastVoltage = readVal().Vfeed  # first voltage reading

        self.message = "Finished initalizing"

    def setBuffer(self):
        # buffers: deque datatype to hold the most recent values (last 500 maybe)
        self.temp0 = deque(range(self.bufferLen))  # top Pelt
        self.temp1 = deque(range(self.bufferLen))  # top Bat
        self.temp2 = deque(range(self.bufferLen))  # bot Pelt
        self.temp3 = deque(range(self.bufferLen))  # bot Bat
        self.vBuff = deque(range(self.bufferLen))
        self.timeBuff = deque(range(self.bufferLen))

    # Gets the steps from the user input in the settings page
    def usrStepChoice(self, usrSteps):
        stepList = usrSteps.split(',')
        self.tempSteps = []
        for step in stepList:
            if len(step) > 0:  # stops blank lines from being .split()
                self.tempSteps.append(float(step))  # Because it's going to be read as a sting ??
                # yList.append(int(y))

    # Calls the readVal() class to read all voltage values, and gets the calculated temperature values
    def read(self):
        self.temps = readVal().temp()
        self.vfeed = readVal().Vfeed

    def rotateBuffer(self):  # updates the buffers with the new values
        # Buffers
        for index, x in enumerate([self.temp0, self.temp1, self.temp2, self.temp3]):
            x.pop()
            x.appendleft(self.temps[index])
        self.vBuff.pop()
        self.vBuff.appendleft(self.vfeed)
        self.timeBuff.pop()
        self.timeBuff.appendleft(self.seconds)

    def write(self):
        # File
        self.dataFile = open("Data.txt", "a")  # opens the file in append mode
        self.dataFile.write(
            str(self.seconds) + "," + str(self.temps[0]) + "," + str(self.temps[1]) + "," + str(self.temps[2]) + ","
            + str(self.temps[3]) + "," + str(self.vfeed) + "\n")
        self.dataFile.close()

        if self.seconds * 1 >= self.avgLengthVolt:  # this prevents dodgy moving average values from printing
            # File  this reads the newest value from the moving average data
            self.dataFile = open("MovingData.txt", "a")  # opens the file in append mode
            self.dataFile.write(
                str(self.seconds) + "," + str(self.temp0Avg[0]) + "," + str(self.temp1Avg[0]) + "," + str(
                    self.temp2Avg[0]) + ","
                + str(self.temp3Avg[0]) + "," + str(self.vBuffAvg[0]) + "\n")
            self.dataFile.close()

        # Writes the results when status = "Collect"

    def writeResults(self):
        self.dataFile = open("ResultsData.txt", "a")  # opens the file in append mode
        self.dataFile.write(
            str(self.lastTargetTemp) + "," + str(self.targetTemp) + "," + str(self.entropyCoeff) + "," + str(
                self.lastVoltage) + ","
            + str(self.vBuffAvg[0]) + "," + str(self.seconds) + "\n")
        self.dataFile.close()

    # Performes a moving average of the buffers
    def avgBuffer(self):
        # leaving only the latest few values
        # lengthen the average list
        if self.seconds * 1 >= self.avgLengthVolt:  # if the amount of data points is greater than the moving avg no. so it doesn't give funny resuslts at the start
            self.temp0Avg = movingAverage(self.temp0, self.avgLength) # pelt top
            self.temp1Avg = movingAverage(self.temp1, self.avgLength) # bat top
            self.temp2Avg = movingAverage(self.temp2, self.avgLength) # pelt bot
            self.temp3Avg = movingAverage(self.temp3, self.avgLength) # bat bot
            self.vBuffAvg = movingAverage(self.vBuff, self.avgLengthVolt)

    def clearFile(self):
        file = open("Data.txt", "w").close()  # opening in write mode clears the file.
        file = open("MovingData.txt", "w").close()
        # still need to write to a file for PLOTTING

    def timeLog(self):
        elapsedtime = self.end_time - self.predictStart_time
        elapsedtime = round(elapsedtime, 3)
        self.seconds += elapsedtime  # records time

    # This function checks what state the the system is in and directs to the relevant process.
    # This is the 'window' into the code from the while loop
    # STATE_FUNCTION is a function which might bring along the next state
    def stateCheck(self, control):
        go = True

        if self.state == 'Rest':
            pass

        elif self.state == "Command":  # The peltiers are being commanded
            print("predict start", self.predictStart)
            control.run(self.targetTemp, self.temps[1], self.temps[3], self.temps[0], self.temps[2])  # Control peltiers
            if self.predictionState == 1 and self.tempStepCount > 1:  # if is selelcted in settings and if is not the first step
                if self.predictStart == "wait":
                    pred.waitToPredict()  # gives 5s for the voltage to start rising

                    pred.predictStart(self.vBuff,
                                      self.timeBuff)  # STATE_FUNCTION    Vfeed & time are the current buffers


                elif self.predictStart == "predict":
                    pred.cutData(self.vBuff, self.timeBuff)  # cuts the buffers down

                    pred.exponential()  # Makes a single prediction

                    pred.sDeviation()  # STATE_FUNCTION  # doesn't need to wait for temperature to level off before predicting

            else:  # waits until the temperature is pretty much even to start waiting for voltage
                self.checktargetTemp()  # STATE_FUNCTION

        elif self.state == "Equalising":  # The target temperature has now been reached
            control.run(self.targetTemp, self.temps[1], self.temps[3], self.temps[0],
                        self.temps[2])  # Maintain temperature

            if self.predictionState == 0:  # from the radio button in settings
                self.voltageLevel()


        elif self.state == "Measure":
            control.run(self.targetTemp, self.temps[1], self.temps[3], self.temps[0],
                        self.temps[2])  # Maintain temperature#

            self.entropy()  # STATE_FUNCTION  -> "Collect" measure entropy finally

        elif self.state == "Collect":
            control.run(self.targetTemp, self.temps[1], self.temps[3], self.temps[0],
                        self.temps[2])  # Maintain temperature#

            self.writeResults()

            self.reset()
            print("step list =",sys.tempSteps)
            print("step count",self.tempStepCount)
            self.start()

        elif self.state == "Finished":

            go = False
            print("go", go)
            self.off()
        return go

    # Checking that the voltage has leveled out
    def voltageLevel(self):
        if abs(self.vBuffAvg[0] - self.vBuffAvg[
            self.voltMeasureLen]) < self.voltLevelRange:  # voltMeasureLen is how much of the buffer you take
            self.State = "Measure"

    # called by a button in the live tab
    def forceStep(self):
        self.state = "Measure"
        print(" Button pressed")

    # When a new temperature is commanded, this sets the targetTemp and lastTargetTemp
    def start(self):
        #print("step list =",sys.tempSteps)
        #print("step count",self.tempStepCount)
        if self.tempStepCount > len(self.tempSteps):  # is this the last step
            self.state = "Finished"  # everything is done
            print("Last temperature step complete. The experiment has finished")  # NEED TO LOG THIS

        else:
            self.targetTemp = self.tempSteps[self.tempStepCount - 1]  # set target temp to the next one
            if self.tempStepCount > 1:
                self.lastTargetTemp = self.tempSteps[
                    self.tempStepCount - 2]  # -1 because the first step is at index [0]
            else:
                self.lastTargetTemp = 22 
            self.state = "Command"  # a temperature is being commanded
            print("Starting new temperature step. \nPrevious temp = %d   New temp = %d" % (
            self.lastTargetTemp, self.targetTemp))

    # This checks weather the target temp has been reached. It uses std dev of the target temp and the temps
    def checktargetTemp(self):
        print("checking target temp")
        # last 2 temps and target temp
        print("Target Temp =", self.targetTemp)
        print("checking temp", "self.State =", self.state)
        if (abs(self.temp1Avg[0] - self.targetTemp) < 0.1) and (abs(self.temp3Avg[0] - self.targetTemp) < 0.1):
            self.state = "Equalising"  # the temperature has been reached, now the battery is equalising
            print("Reached temperature", "self.State =", self.state)

    # Calculates entropy of the cell once the voltage has stabilised
    def entropy(self):

        voltMeasure = sum(self.vBuffAvg[
                          :self.voltMeasureLen]) / self.voltMeasureLen  # gets an average of the voltages measured over the range

        tempChange = self.targetTemp - self.lastTargetTemp
        voltChange = voltMeasure - self.lastVoltage

        self.entropyCoeff = voltChange / tempChange
        print(
            " \n!!!!!!\nAaaaand now... fighting in the blue corner... \n weighing in at 70 grams, having an entropy coefficient of...%.7f \n .... iiitss the 21700  whooo!!!!  " % self.entropyCoeff)
        time.sleep(10)
        self.state = "Collect"

    # Prepares the attributs for the next run
    def reset(self):
        self.lastVoltage = self.vBuffAvg[0]
        self.tempStepCount += 1  # this will trigger the next temperature step to be commanded
        control.topErrorTime = 0  # for integral control
        control.botErrorTime = 0
        self.predictStart = "wait"  # reset the prediction wait variable

        self.state = "Command"

    def off(self):
        print("Quit pressed in ENTROPY")
        control.top_pwm.ChangeDutyCycle(0)
        control.bot_pwm.ChangeDutyCycle(0)
        sys.state = "Finished"
        raise SystemExit(0)  # quits the program

    # Is run every tick, and quits the EntropyCoefficient.py if button is pressed
    def buttonCheck(self):
        buttonState = GPIO.input(14)
        if buttonState == 1:
            self.State = "ButtonPressed"
            self.off()
            print("button pressed")
            # app.ButtonPress = buttonState # Links to the GUI
            raise SystemExit(0)  # quits the program

    # measures start time
    def measureStartTime(self):
        self.predictStart_time = time.time()

    # measures end time
    def measureendtime(self):
        self.end_time = time.time()


sys = system()  # initialises system
control = controlPeltiers()  # while go == True:
val = readVal()  # initialises the readVal() object val
pred = predict()


def begin(i):
    
    sys.state = "Command"

    sys.setBuffer()  # Sets the buffer fresh

    sys.targetTemp = sys.tempSteps[0]  # setting first target temp

    print("predictionState", sys.predictionState)

    print("temperature step = ", sys.targetTemp)

    runGUI()  # Starts the experiment


def runGUI():
    go = True

    while go == True:
        # measure start time
        sys.measureStartTime()

        sys.read()  # LIST reads temperatures and sets as system attribute

        sys.rotateBuffer()  # Moves old data out of the buffer

        sys.avgBuffer()  # takes the moving average of the last few buffer points

        sys.write()  # write values * needs file saving and graphing

        print("Target Temp = ", sys.targetTemp)
        #print("step list =",sys.tempSteps)
        print("state = ", sys.state)
        #print("top dir:",control.top_dir,"bot dir:",control.bot_dir)
        go = sys.stateCheck(control)

        # measure finish time
        sys.measureendtime()

        sys.timeLog()  # i have stopped running your code because it isnt working atm

        sys.buttonCheck()

    sys.clearFile()

    print("Main finished")
    # probably set peltiers to 0
















