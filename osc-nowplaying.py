from pythonosc.dispatcher import Dispatcher
from typing import List, Any
import time
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
from bus_logic import BusData


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




class OscClient(object):
    def __init__(self,ip_str, mplayer_logic, bus_data, port=10000):
        self.ip_str = ip_str
        self.mpl = mplayer_logic
        self.bd = bus_data
        self.c = SimpleUDPClient(ip_str, port)
        # mode is one of PLAYER, BUS, or LIGHTS. 
        self.mode = "PLAYER"
        self.state_lu = {"stop":0, "pause":1, "play":2}
        self.last_status = ""

    def next_mode(self):
        if self.mode == "PLAYER":
            newmode = "BUS"
        elif self.mode == "BUS":
            newmode = "PLAYER"

        self.mode = newmode
        print(f"new mode {newmode}")

    def send_status(self):
        if self.mode == "PLAYER":
            self.send_mpl_status(self.mpl.get_short())

        elif self.mode == "BUS":
            self.send_bus_status()

        self.send_time()


    def send_bus_status(self):
        self.c.send_message("/labels", ["MODE", "^^", "VV"])        
        status = []
        for bus in ['b27','b12']:
            resp = bd.busses[bus].get_route_short()
            status.append(resp[0])
            status.append(resp[1])
            #print(resp)

        if status != self.last_status:
            self.c.send_message("/status", status) 
            self.last_status = status


    def send_mpl_status(self,status):

        if self.mpl.state == 'play':
            self.c.send_message("/labels", ["stop", "<<", ">>"])
        else:
            self.c.send_message("/labels", ["play", "<<", ">>"])

        if status != self.last_status:
            self.c.send_message("/status", status) 
            #if i == 0:
            #    log_status(status)
        if self.mpl.state in self.state_lu:
            self.c.send_message("/volume", [mpl.volume, self.state_lu[mpl.state]] )
        else:
            self.c.send_message("/volume", [mpl.volume, -1] )
        self.last_status = status


    def send_time(self):
        global time_left
        #always send time
        self.c.send_message("/time", 
                              time.strftime("%H:%M:%S", time.localtime())) 

        if time_left > 0:
             self.c.send_message("/leds", self.get_led_bar(float(time_left)/sleep_time, 12, "ff0000"))
        else:
             self.c.send_message("/leds", ["000000"]*12)


    def get_led_bar(self, ratio, num_leds, color, black="00000"):
        """return a list of colors corresponding to ratio"""
        clist = []
        # faces encoder leds go CCW, so reverse for CW 
        for i in range(num_leds):
            if float(i)/num_leds <= ratio:
                clist.append(color)
            else:
                clist.append(black)

        return clist


    def handle_button(self, button, value):
        if  button == "A":
            if value < 0.5:
                self.mpl.toggle_play()
            else:
                self.next_mode()

        elif button == "B":
            self.mpl.client.previous()

        elif  button == "C":
            self.mpl.client.next()



mpl = MPDLogic()
bd = BusData()

dispatcher = Dispatcher()


#print("sent at " + time.strftime("%H:%M:%S", time.localtime()))

osc_client_ips = ["192.168.1.221",
                  "192.168.1.225",
                  "192.168.1.231"]

osc_clients = []
osc_client_dict = {}
for ip in osc_client_ips:

    client = OscClient(ip, mpl, bd)
    osc_clients.append(client)
    # make dict so we can look up clinet server from IP returned from handler
    osc_client_dict[ip] = client

# list of clients that sent aus an osc command and need to be refreshed. 
dirty_clients = []

#osc_clients = [ SimpleUDPClient("192.168.1.231", 10000)]




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



def heartbeat_handler(client, address: str, *args: List[Any]) -> None:
    #print("heartbeat from " + str(client))
    pass


def button_handler(client, address: str, *args: List[Any]) -> None:
    global osc_client_dict
    global dirty_clients

    value = args[0]
    button = address[-1]
    print(f"Got button {button} values: {value}")

    client = osc_client_dict[client[0]]
    dirty_clients.append(client)
    client.handle_button(button, value)

        
def encoder_handler(client, address: str, *args: List[Any]) -> None:
    global osc_client_dict
    global dirty_clients
    global time_left
    global mpl

    value1 = args[0]

    dirty_clients.append(osc_client_dict[client[0]])

    print(f"Got addr {address} values: {value1}")
    
    if  address == "/encoder":
        if value1 > 0:
            mpl.volume_incr(+2)
        elif value1 == 0:
            print("push")
            # logic: not playing, press enc to play
            # when playing, press enc to start sleep timer
            # when sleep timer is on, pressing again within 1 min cancels
            # when sleep timer is on, pressing after 1 min cancels and stops.
            if time_left > int(sleep_time - 1):
                time_left = -1 # cancel sleep timer
            elif time_left > 0:
                time_left = -1
                mpl.toggle_play()                
            else:
                if mpl.state == 'play':
                    time_left = int(sleep_time) # time left in sleep timer
                else:
                    mpl.toggle_play()
        elif value1 < 0:
            mpl.volume_incr(-2)
        sys.stdout.flush()

dispatcher.map("/button*", button_handler, needs_reply_address=True)  
dispatcher.map("/encoder", encoder_handler, needs_reply_address=True)  
dispatcher.map("/heartbeat", heartbeat_handler, needs_reply_address=True)  


def send_status(mpl, osc_clients):
    for c in osc_clients:
        c.send_status()
    

# def send_mpl_status_old(mpl, osc_clients):
#     global time_left
#     status = mpl.get_short() 
#     if status is None:
#         #time.sleep(1)
#         return
#     state_lu = {"stop":0, "pause":1, "play":2}

#     for i, client in enumerate(osc_clients):
#         if mpl.state == 'play':
#             client.c.send_message("/labels", ["stop", "<<", ">>"])
#         else:
#             client.c.send_message("/labels", ["play", "<<", ">>"])
#         if status != last_status:
#             client.c.send_message("/status", status) 
#             if i == 0:
#                 log_status(status)
#         if mpl.state in state_lu:
#             client.c.send_message("/volume", [mpl.volume, state_lu[mpl.state]] )
#         else:
#             client.c.send_message("/volume", [mpl.volume, -1] )

#         #always send time
#         client.c.send_message("/time", 
#                               time.strftime("%H:%M:%S", time.localtime())) 

#         if time_left > 0:
#              client.c.send_message("/leds", get_led_bar(float(time_left)/sleep_time, 12, "ff0000"))
#         else:
#              client.c.send_message("/leds", ["000000"]*12)


def sleep_timer(mpl, osc_clients):
    global time_left
    if time_left < 0:
        return

    time_left = time_left -1
    print(f"Time left in sleep timer: {time_left})")
    if time_left == 0:
        mpl.client.stop()


rt = RepeatedTimer(1, send_status,  mpl, osc_clients) # it auto-starts, no need of rt.start()

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

    send_status(mpl, dirty_clients)
    for c in dirty_clients:
        print(f"sent {c.ip_str} an update")

    dirty_clients = []


    #client.send_message("/filter8", [6., -2.])
    #server.handle_request()
    #print("wait")
    #time.sleep(1)
    
