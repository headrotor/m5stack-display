from pythonosc.dispatcher import Dispatcher
from typing import List, Any
import time
import sys
# Set up server and client for testing
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
# docs at https://pypi.org/project/python-osc/

global dirty
dirty = False


from threading import Timer


# local class to control Music Player Daemon
from mpd_logic import MPDLogic





#from https://stackoverflow.com/a/13151104

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.function   = function
        self.interval   = interval
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False



global mpl
global client


osc_clients = [SimpleUDPClient("192.168.1.221", 10000),
           SimpleUDPClient("192.168.1.225", 10000)]


mpl = MPDLogic()

dispatcher = Dispatcher()


def button_handler(address: str, *args: List[Any]) -> None:
    global mpl
    # We expect two float arguments
    #if not len(args) == 2 or type(args[0]) is not float or type(args[1]) is not float:
    #    return

    # Check that address starts with filter
    #if not address[:-1] == "/filter":  # Cut off the last character
    #    return

    print('got! ' + address)
    sys.stdout.flush()

    value1 = args[0]
    #value2 = args[1]
    filterno = address[-1]
    print(f"Got addr {address} values: {value1}")
    
    if  filterno == "A":
        mpl.client.pause()

    if  filterno == "B":
        mpl.client.previous()

    if  filterno == "C":
        mpl.client.next()

        
def encoder_handler(address: str, *args: List[Any]) -> None:
    global mpl
    global dirty
    # We expect two float arguments
    #if not len(args) == 2 or type(args[0]) is not float or type(args[1]) is not float:
    #    return

    # Check that address starts with filter
    #if not address[:-1] == "/filter":  # Cut off the last character
    #    return
    value1 = args[0]
    print(f"Got addr {address} values: {value1}")
    
    if  address == "/encoder":
        if value1 > 0:
            print("incr")
            mpl.volume_incr(+5)
        elif value1 == 0:
            print("push")
        elif value1 < 0:
            print("decr")
            mpl.volume_incr(-5)
        sys.stdout.flush()
        dirty = True

dispatcher.map("/button*", button_handler)  # Map wildcard address 
dispatcher.map("/encoder", encoder_handler)  


server = BlockingOSCUDPServer(("192.168.1.148", 12000), dispatcher)



def send_mpl_status(mpl, osc_clients):

    for c in osc_clients:
        c.send_message("/labels", ["Pause", "<prev", "next>"])
        c.send_message("/status", mpl.get_short()) 
        state_lu = {"stop":0, "pause":1, "play":2}
        if mpl.state in state_lu:
            c.send_message("/volume", [mpl.volume, state_lu[mpl.state]] )
        else:
            c.send_message("/volume", [mpl.volume, -1] )
        c.send_message("/time", 
                       time.strftime("%H:%M:%S", time.localtime())) 

    print("sent at " + time.strftime("%H:%M:%S", time.localtime()))


rt = RepeatedTimer(1, send_mpl_status,  mpl, osc_clients) # it auto-starts, no need of rt.start()





# Send message and receive exactly one message (blocking)
while True:

    #client.send_message("/1/fader1", [0.555])
    server.handle_request()
    if dirty:
        print("Gotcha!")
        dirty=False
        send_mpl_status(mpl, osc_clients)
    else: 
        print(".")

    #client.send_message("/filter8", [6., -2.])
    #server.handle_request()
    #print("wait")
    #time.sleep(1)
    
