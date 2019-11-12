from pythonosc.dispatcher import Dispatcher
from typing import List, Any
import time
import datetime
import sys
import socket

# Set up server and client for testing
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
# docs at https://pypi.org/project/python-osc/


from threading import Timer


# local class to control Music Player Daemon
from mpd_logic import MPDLogic


# call sleep timer this many times before sleep
sleep_time = 15
# at this interval in seconds
sleep_interval = 60

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

class OscClient(object):
    def __init__(self,ip_str, port=10000):
        self.ip_str = ip_str
        self.dirty = False
        self.c = SimpleUDPClient(ip_str, 10000)

    def unclean(self,ip_str):
        if ip_str == self.ip_str:
            self.dirty = True
            #print(f"{ip_str} is dirty")

# osc_clients = [SimpleUDPClient("192.168.1.221", 10000),
#                SimpleUDPClient("192.168.1.225", 10000),
#                SimpleUDPClient("192.168.1.231", 10000)]
osc_clients = [OscClient("192.168.1.221"),
               OscClient("192.168.1.225"),
               OscClient("192.168.1.231")]


#osc_clients = [ SimpleUDPClient("192.168.1.231", 10000)]


mpl = MPDLogic()

dispatcher = Dispatcher()


def get_led_bar(ratio, num_leds, color, black="00000"):
    """return a list of colors corresponding to ratio"""
    clist = []
    # faces encoder leds go CCW, so reverse for CW 
    for i in range(num_leds):
        if float(i)/num_leds <= ratio:
            clist.append(color)
        else:
            clist.append(black)

    return clist


def button_handler(client, address: str, *args: List[Any]) -> None:
    global osc_clients
    global mpl
    # We expect two float arguments
    #if not len(args) == 2 or type(args[0]) is not float or type(args[1]) is not float:
    #    return

    # Check that address starts with filter
    #if not address[:-1] == "/filter":  # Cut off the last character
    #    return

    for c in osc_clients:
        # set dirty flag in the client that sent us this
        c.unclean(client[0])

    sys.stdout.flush()

    value1 = args[0]
    #value2 = args[1]
    filterno = address[-1]
    print(f"Got addr {address} values: {value1}")
    
    if  filterno == "A":
        #mpl.client.pause()
        mpl.toggle_play()

    if  filterno == "B":
        mpl.client.previous()

    if  filterno == "C":
        mpl.client.next()

def heartbeat_handler(client, address: str, *args: List[Any]) -> None:
    #print("heartbeat from " + str(client))
    pass
        
def encoder_handler(client, address: str, *args: List[Any]) -> None:
    global osc_clients
    global time_left
    global mpl

    value1 = args[0]
    for c in osc_clients:
        # set dirty flag in the client that sent us this
        c.unclean(client[0])

    print(f"Got addr {address} values: {value1}")
    
    if  address == "/encoder":
        if value1 > 0:
            mpl.volume_incr(+2)
        elif value1 == 0:
            print("push")
            #mpl.toggle_play()
            if time_left > 0:
                time_left = -1 # cancel sleep timer
            else:
                time_left = int(sleep_time) # time left in sleep timer
        elif value1 < 0:
            mpl.volume_incr(-2)
        sys.stdout.flush()

dispatcher.map("/button*", button_handler, needs_reply_address=True)  
dispatcher.map("/encoder", encoder_handler, needs_reply_address=True)  
dispatcher.map("/heartbeat", heartbeat_handler, needs_reply_address=True)  


last_status=[" "]


def log_status(status):
    status_str = " ".join(status)
    print("LOG: {} {}".format(datetime.datetime.now().isoformat(),
                              status_str)) 

def send_mpl_status(mpl, osc_clients):
    global last_status
    global time_left
    status = mpl.get_short() 
    if status is None:
        #time.sleep(1)
        return
    state_lu = {"stop":0, "pause":1, "play":2}

    for i, client in enumerate(osc_clients):
        if mpl.state == 'play':
            client.c.send_message("/labels", ["stop", "<<", ">>"])
        else:
            client.c.send_message("/labels", ["play", "<<", ">>"])
        if status != last_status:
            client.c.send_message("/status", status) 
            if i == 0:
                log_status(status)
        if mpl.state in state_lu:
            client.c.send_message("/volume", [mpl.volume, state_lu[mpl.state]] )
        else:
            client.c.send_message("/volume", [mpl.volume, -1] )

        #always send time
        client.c.send_message("/time", 
                              time.strftime("%H:%M:%S", time.localtime())) 

        if time_left > 0:
             client.c.send_message("/leds", get_led_bar(float(time_left)/sleep_time, 12, "ff0000"))
        else:
             client.c.send_message("/leds", ["000000"]*12)

    #print("sent at " + time.strftime("%H:%M:%S", time.localtime()))
    last_status = status


def sleep_timer(mpl, osc_clients):
    global time_left
    if time_left < 0:
        return

    time_left = time_left -1
    print(f"Time left in sleep timer: {time_left})")
    if time_left == 0:
        mpl.client.stop()


rt = RepeatedTimer(1, send_mpl_status,  mpl, osc_clients) # it auto-starts, no need of rt.start()

time_left = -1
st = RepeatedTimer(sleep_interval, sleep_timer,  mpl, osc_clients) # it auto-starts, no need of rt.start()


#server = BlockingOSCUDPServer(("192.168.1.148", 12000), dispatcher)

# Send message and receive exactly one message (blocking)
server = BlockingOSCUDPServer(("192.168.1.148", 12000), dispatcher)

while True:


    #client.send_message("/1/fader1", [0.555])
    try:
        server.handle_request()

    except socket.timeout:
        print("Caught socket timeout")

        server = BlockingOSCUDPServer(("192.168.1.148", 12000), dispatcher)
        #time.sleep(1)

    except Exception as e:
        print("Caught socket problem")
        raise e

    dirty_clients = []
    for c in osc_clients:
        if c.dirty:
            dirty_clients.append(c)

    send_mpl_status(mpl, dirty_clients)
    for c in dirty_clients:
        print(f"sent {c.ip_str} an update")
        c.dirty = False


    #client.send_message("/filter8", [6., -2.])
    #server.handle_request()
    #print("wait")
    #time.sleep(1)
    
