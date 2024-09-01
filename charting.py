from datetime import datetime
import time
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import random
from trade_client import *

# initial data
x = [1]
y = [random.randint(1,10)]

# creating the first plot and frame
fig, ax = plt.subplots()
graph = ax.plot(x,y,color = 'g')[0]
plt.ylim(0,10)

def showChart(frames):
        currentTime = datetime.now()

        if(currentTime.microsecond//10000 == 0):
            #print(currentTime)
            hr = currentTime.hour
            min = currentTime.minute
            sec = currentTime.second
            #print("Hour: ", hr)
            #print("Minute: ", min)
            print("Second: ", sec)

            print(client.get_ticker(symbol='BTCUSDT')['lastPrice'])

            x.append(sec)
            y.append(client.get_ticker(symbol='BTCUSDT')['lastPrice'])

            graph.set_xdata(x//1)
            graph.set_ydata(y//1)
            plt.xlim(x[0], x[-1])

while True:
    time.sleep(0.1)
    currTime = datetime.now()

    if(currTime.microsecond//10000 == 0):
        print(currTime)
        hr = currTime.hour
        min = currTime.minute
        sec = currTime.second
        print("Hour: ", hr)
        print("Minute: ", min)
        print("Second: ", sec)

        print(client.get_ticker(symbol='BTCUSDT')['lastPrice'])

        x = [sec]
        y = [client.get_ticker(symbol='BTCUSDT')['lastPrice']]

        anim = FuncAnimation(fig, showChart, frames = 10, cache_frame_data=False)
        plt.show()
        break
    




 
# updates the data and graph
def update(frame):
 
    global graph
 
    # updating the data
    x.append(x[-1] + 1)
    y.append(random.randint(1,10))
 
    # creating a new graph or updating the graph
    graph.set_xdata(x)
    graph.set_ydata(y)
    plt.xlim(x[0], x[-1])
 
#anim = FuncAnimation(fig, update, frames = None)
#plt.show()



        
