#!/usr/bin/python3
# coding=utf-8

##
# TODO:
#
# 1. Mail, temp annunciator
# 2. Split long status lines
# 3. Test library metadata (as opposed to streaming)
# 4. sleep logic
# 5. Use volume bar to display LED values

# LED stuff (start w blinkinlights)
# A, LED presets recall/save (start with blinkinlights)
# B. Animation -- rotate (shuttle)  hue through spread

from pythonosc.dispatcher import Dispatcher
from typing import List, Any
import time
import sys
import socket
import os

# Set up server and client for testing
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
# docs at https://pypi.org/project/python-osc/


from threading import Timer


# local class to control Music Player Daemon
from mpd_logic import MPDLogic
from bus_logic import BusData
from dmx_logic import DMXLEDS

mailfile = '/home/pi/mail.txt'


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
    def __init__(self,ip_str, mplayer_logic, bus_data, leds, port=10000):
        self.name = "unnamed"
        self.ip_str = ip_str
        self.mpl = mplayer_logic
        self.bd = bus_data
        self.leds = leds
        self.c = SimpleUDPClient(ip_str, port)
        self.heart_count = 0 # seconds since we last saw a heartbeat


        # mode is one of PLAYER, BUS, or LIGHTS. 
        self.mode = "PLAYER"
        self.mode = "LEDS"
        self.state_lu = {"stop":0, "pause":1, "play":2}
        self.last_status = ""


        # stuff for led mode
        self.led_mode = 0
        self.led_modes = ["Value", "Hue", "Sat", "Spread"]
        self.hue_incr = 0.02
        self.val_incr = 0.02
        self.sat_incr = 0.02
        self.spred_incr = 0.005

    def handle_heartbeat(self):
        """ reset heartbeat timeout because we got a heartbeat"""
        self.heart_count = 0


    def next_mode(self):
        """ state machine to handle modes """
        if self.mode == "PLAYER":
#            newmode = "BUS"
#        elif self.mode == "BUS":
            newmode = "LEDS"
        elif self.mode == "LEDS":
            newmode = "PLAYER"

        self.mode = newmode
        #print(f"new mode {newmode}")

    def send_status(self):
        if self.mode == "PLAYER":
            self.send_mpl_status(self.mpl.get_short())

        elif self.mode == "BUS":
            self.send_bus_status()

        elif self.mode == "LEDS":
            self.send_led_status()

        self.send_time()


    def send_led_status(self):
        display = []
        display.append("LEDs")
        #display.append("Lighting Mode")
        for i, val in enumerate(self.led_modes):
            if i == self.led_mode:
                display.append(">" + self.led_modes[i] + "<")
            else:
                display.append(" " + self.led_modes[i] + " ")

        if display != self.last_status:
            self.c.send_message("/status", display) 
            self.last_status = display

        #self.c.send_message("/labels", ["on/off", "++", "--"])        
        self.c.send_message("/labels", ["on/off", "   ++   ", "   --   ", "  "])        


    def send_bus_status(self):
        self.c.send_message("/labels", ["MODE", "^^", "VV"])        
        status = bd.get_display_data()

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
             self.c.send_message("/leds", self.get_led_bar(float(time_left)/sleep_time, 12, "ff0000"))
        elif os.path.exists(mailfile):
            if self.name == 'pidp':
                # send green if we have mail
                self.c.send_message("/leds", ["00ff00"]*12)
                self.c.send_message("/leds", ["00ff00"]*12)
            else:
                self.c.send_message("/leds", ["000000"]*12)
                self.c.send_message("/leds", ["000000"]*12)


            
        self.heart_count += 1
        #print("client {} heartbeat count: {}".format(self.ip_str, self.heart_count))
        if self.heart_count > 30:
            #print("client {} watchdog!".format(self.ip_str))
            self.heart_count = 0
            
    def get_led_bar(self, ratio, num_leds, color, black="00000"):
        """return a list of colors corresponding to ratio, this is 
        not for DMX LEDs, it's for color ring on M5STACK encoder"""
        clist = []
        # faces encoder leds go CCW, so reverse for CW 
        for i in range(num_leds):
            if float(i)/num_leds <= ratio:
                clist.append(color)
            else:
                clist.append(black)

        return clist

    def handle_encoder(self, value, time_left):
        if self.mode == "PLAYER":
            time_left = self.handle_encoder_player(value, time_left)
        elif self.mode == "BUS":
            time_left = self.handle_encoder_player(value, time_left)
        elif self.mode == "LEDS":
            self.handle_encoder_leds(value)
        return time_left

    def handle_encoder_player(self, value, time_left):
        if value > 0:
            self.mpl.volume_incr(+3)
        elif value == 0:
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
        elif value < 0:
            self.mpl.volume_incr(-3)
        return time_left

    def handle_encoder_leds(self, value):
        if value == 0:
            self.led_mode += 1
            if self.led_mode >= len(self.led_modes):
                self.led_mode = 0

        elif value > 0:
            if self.led_modes[self.led_mode] == "Value":
                self.leds.change_val(0.01)
            elif self.led_modes[self.led_mode] == "Hue":
                self.leds.change_hue(0.005)
            elif self.led_modes[self.led_mode] == "Sat":
                self.leds.change_sat(0.02)
            elif self.led_modes[self.led_mode] == "Spread":
                self.leds.change_spread(0.005)
        elif value < 0:
            if self.led_modes[self.led_mode] == "Value":
                self.leds.change_val(-0.01)
            elif self.led_modes[self.led_mode] == "Hue":
                self.leds.change_hue(-0.005)
            elif self.led_modes[self.led_mode] == "Sat":
                self.leds.change_sat(-0.02)
            elif self.led_modes[self.led_mode] == "Spread":
                self.leds.change_spread(-0.005)
        self.leds.send()



    def handle_button(self, button, value):
        """ a button was pressed, dispatch to the right 
        handler depending on mode"""
        if self.mode == "PLAYER":
            self.handle_button_player(button, value)
        elif self.mode == "BUS":
            self.handle_button_bus(button, value)
        elif self.mode == "LEDS":
            self.handle_button_leds(button, value)



    def handle_button_bus(self, button, value):
        if  button == "A":
            if value < 0.5:
                self.mpl.toggle_play()
            else:
                self.next_mode()

        elif button == "B":
            if value < 0.5:
                self.bd.scroll_lines(-1)
            else:
                self.leds.toggle()

        elif  button == "C":
            self.bd.scroll_lines(+1)

    def handle_button_player(self, button, value):
        if  button == "A":
            if value < 0.5:
                self.mpl.toggle_play()
            else:
                self.next_mode()

        elif button == "B":
            if value < 0.5:
                self.mpl.client.previous()
            else:
                self.leds.toggle()

        elif  button == "C":
            self.mpl.client.next()

    def handle_button_leds(self, button, value):
        if  button == "A":
            if value < 0.5:
                self.leds.toggle()
            else:
                self.next_mode()

        elif button == "B":
            if value < 0.5:
                if self.led_modes[self.led_mode] == "Value":
                    self.leds.change_val(0.02)
                elif self.led_modes[self.led_mode] == "Hue":
                    self.leds.change_hue(0.01)
                elif self.led_modes[self.led_mode] == "Sat":
                    self.leds.change_sat(0.02)
                elif self.led_modes[self.led_mode] == "Spread":
                    self.leds.change_spread(0.005)
                self.leds.send()
            else: 
                self.led_mode += 1
                if self.led_mode >= len(self.led_modes):
                    self.led_mode = 0
                


        elif  button == "C":
            if value < 0.5:
                if self.led_modes[self.led_mode] == "Value":
                    self.leds.change_val(-0.02)
                elif self.led_modes[self.led_mode] == "Hue":
                    self.leds.change_hue(-0.01)
                elif self.led_modes[self.led_mode] == "Sat":
                    self.leds.change_sat(-0.02)
                elif self.led_modes[self.led_mode] == "Spread":
                    self.leds.change_spread(-0.005)
                self.leds.send() 
            else:
                self.led_mode += 1
                if self.led_mode < 0:
                    self.led_mode = len(self.led_mode) - 1


mpl = MPDLogic()
bd = BusData()
leds = DMXLEDS()

dispatcher = Dispatcher()


#print("sent at " + time.strftime("%H:%M:%S", time.localtime()))

osc_client_ips = [("192.168.1.225", "upstairs"),
                  ("192.168.1.221", "door"),
                  ("192.168.1.226", "pidp"),
                  ("192.168.1.227","desk")]


osc_clients = []
osc_client_dict = {}
for ip in osc_client_ips:

    client = OscClient(ip[0], mpl, bd, leds)
    client.name = ip[1]
    osc_clients.append(client)
    # make dict so we can look up clinet server from IP returned from handler
    osc_client_dict[client.ip_str] = client

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
    client = osc_client_dict[client[0]]
    client.handle_heartbeat()



def button_handler(client, address: str, *args: List[Any]) -> None:
    global osc_client_dict
    global dirty_clients

    value = args[0]
    button = address[-1]
    #print(f"Got button {button} values: {value}")

    client = osc_client_dict[client[0]]
    dirty_clients.append(client)
    client.handle_button(button, value)

        
def encoder_handler(client, address: str, *args: List[Any]) -> None:
    global osc_client_dict
    global dirty_clients
    global time_left

    value = args[0]

    client = osc_client_dict[client[0]]
    dirty_clients.append(client)
    time_left = client.handle_encoder(value, time_left)
    return

    #print(f"Got addr {address} values: {value1}")
    
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
    #print(f"Time left in sleep timer: {time_left})")
    if time_left == 0:
        mpl.client.stop()


rt = RepeatedTimer(1, send_status,  mpl, osc_clients) # it auto-starts, no need of rt.start()

time_left = -1
st = RepeatedTimer(sleep_interval, sleep_timer,  mpl, osc_clients) # it auto-starts, no need of rt.start()



# Send message and receive exactly one message (blocking)
#server = BlockingOSCUDPServer(("192.168.1.148", 12000), dispatcher)


try: 
    server = BlockingOSCUDPServer(("192.168.1.144", 12000), dispatcher)
    #server = BlockingOSCUDPServer(("127.0.0.1", 12000), dispatcher)

except OSError as e:
    print("could not connect, sorry")
    raise e

#server = BlockingOSCUDPServer(("127.0.0.1", 12000), dispatcher)

while True:


    #client.send_message("/1/fader1", [0.555])
    try:
        server.handle_request()

    except socket.timeout:
        print("Caught socket timeout")

        #server = BlockingOSCUDPServer(("127.0.0.1", 12000), dispatcher)
        server = BlockingOSCUDPServer(("192.168.1.144", 12000), dispatcher)
        #server = BlockingOSCUDPServer(("192.168.1.148", 12000), dispatcher)
        #time.sleep(1)

    except Exception as e:
        print("Caught socket problem")
        raise e

    send_status(mpl, dirty_clients)
    for c in dirty_clients:
        #print(f"sent {c.ip_str} an update")
        pass

    dirty_clients = []


    #client.send_message("/filter8", [6., -2.])
    #server.handle_request()
    #print("wait")
    #time.sleep(1)
    
