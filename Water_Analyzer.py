#Importing the Libraries
import RPi.GPIO as GPIO
import time, sys
from firebase import firebase
import boto3
import matplotlib.pyplot as plt

# Initial Raspberry pi Setup
GPIO.setmode(GPIO.BOARD)
inpt = 7
GPIO.setup(inpt, GPIO.IN,pull_up_down = GPIO.PUD_UP)

#Initializing and Creating the Required Variables
time_new = 0.0
rpt_int = 10
global rate_cnt, tot_cnt
rate_cnt = 0
tot_cnt = 0

#Fetching the Data from Firebase
fb = firebase.FirebaseApplication("https://wateranalyzeriot-c2112.firebaseio.com/",None)
result = fb.get("/wateranalyzeriot-c2112/Consumption",'')

#Filtering Out the fetched Data
keys = []
for key in result:
    keys.append(key)


times = []
for x in keys:
    times.append(result[x]['time'])


volumes = []
for x in keys:
    volumes.append(result[x]['Volume'])

#Calculating the Average Water Conumption
avg=round(sum(volumes)/len(volumes),2)
average = [avg] * len(volumes)

#Function Definition of Messaging
def SMS(msg):
    client=boto3.client('sns')
    client.publish(PhoneNumber='+917906805094',Message=msg)
    print("Text message sent ")

#Function to Plot the Graph
def graph(avg):
   plt.scatter(times,volumes)
   plt.plot(times, volumes,'b-',label = 'trend')
   plt.plot(average,color = 'red',label = 'average')
   plt.ylabel('Water Consumption (Litres)')
   plt.xlabel('Timeline')
   plt.title('Water Consumption Trends')
   plt.xticks(rotation=45)
   plt.margins(0.2)
   plt.legend()
   plt.subplots_adjust(bottom=0.15)
   plt.tick_params(axis='x',labelsize=5)
   plt.show()

#Function to Increment the Pulse count
def Pulse_cnt(inpt_pin):
    global rate_cnt, tot_cnt
    rate_cnt += 1
    tot_cnt += 1

#Function to upload Data to Firebase's Real Time Database
def record_data(fb,TotLit):
    data = {"time":str(time.asctime(time.localtime(time.time()))),"Volume" : TotLit}
    result = fb.post("/wateranalyzeriot-c2112/Consumption",data)
    print("Data Recorded Successfully")

#Adding an Interrupt to Detect The Pulse
GPIO.add_event_detect(inpt,GPIO.FALLING, callback=Pulse_cnt,bouncetime=10)

#Main Program
print('Water Flow Approximate ', str(time.asctime(time.localtime(time.time()))))
rpt_int = int(input('Input desired report interval in sec '))       #Inputing the Report Interval
print ('Reports every ',rpt_int,' seconds')
print('Control C to exit')
print('\nWater Flow - Approximate - Reports Every ' + str(rpt_int)+ ' Seconds ' +
       str(time.asctime(time.localtime(time.time()))))
TotLit=0

#Infinite Loop to Calculate Water Flow...
while True:
    time_new = time.time() +rpt_int
    rate_cnt = 0
    try:
        #Counting Pulses for the input report Interval
        while time.time() <= time_new:
            None
            GPIO.input(inpt)
    except KeyboardInterrupt:
        #Checking the Water Consumption and Generating the appropriate Message
        if TotLit > avg:
           msg=("Your today's Consumption: "+str(TotLit)+"L\nIt is above the daily limit: "+str(avg)+"L\nPlease refrain from reckless usage of water\nFrom IoT_LNMIIT")
        else:
           msg=("Your today's Consumption: "+str(TotLit)+"L\nFrom IoT_LNMIIT")
        #Sending the Message
        SMS(msg)
        #Uploading the Data to Firebase
        record_data(fb,TotLit)
        #Displaying the Graph if Required
        x =  input("\n\nWould you like to see the Data Visualization[y/n]")
        if x=='y':
           print("\n\n\n\n") 
           print("**********************Please Wait While the Graph Loads**********************") 
           graph(avg)
        #Exiting
        print('\nCTRL C - Exiting nicely')
        GPIO.cleanup()
        print('Done')
        sys.exit()

    #Calculating the Water Flow Rate and total volume Consumed
    TotLit =round(tot_cnt/(7.5*60),2)
    LperM =  round((rate_cnt*(60/rpt_int))/(7.5*60),1)

    #Generating the Report....
    print('\nLiters /min',LperM,'(',rpt_int,'second sample)')
    print('total Liters ',TotLit)
    print('time (min & clock)','\t',time.asctime(time.localtime(time.time())),'\n')

GPIO.cleanup()
print('Done')
