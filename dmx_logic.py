import time
import sys
import math
import socket
import json
import os.path

from pythonosc.udp_client import SimpleUDPClient
# pip install python-osc
# docs at https://pypi.org/project/python-osc/

# local color transform package
from colorxform import ColorXform


def constrain(val, min_val=0., max_val=1.):
    return min(max_val, max(min_val, val))

class DMXLEDS(object):
    ''' Top level class, orchestrates commands to and from subclients'''
    def __init__(self):
        self.dmx_osc_client_ips = ["192.168.1.240",
                                   "192.168.1.241",
                                   "192.168.1.242",
                                   "192.168.1.243"]
#                                   "192.168.1.245"]

        #self.dmx_osc_client_ips = ["192.168.1.241"]
        self.hue_spread = 0.
        self.hue = 0.
        self.sat = 0.5
        self.val = 0.
        self.clients = []
 

        for ip in self.dmx_osc_client_ips:
            client = OscDMXClient(ip)
            self.clients.append(client)

        # are we currently lit?   Need to do this on device to save state!
        self.on = 0

    def change_hue(self,incr):
        new_hue = self.hue + incr
        while new_hue > 1.0:
            new_hue -= 1.0
        while new_hue < 0.0:
            new_hue += 1.0
        self.hue = new_hue
        #print(f"new hue: {self.hue}")

    def change_val(self,incr):
        self.val = constrain(self.val + incr)
        #print(f"new value: {self.val}")

    def change_sat(self,incr):
        self.sat = constrain(self.sat + incr)
        #print(f"new sat: {self.sat}")

    def change_spread(self,incr):
        self.hue_spread = constrain(self.hue_spread + incr, 0, 0.5)
        #print(f"new spread: {self.hue_spread}")

    def send(self):
        self.send_hsv(self.hue, self.sat, self.val)
        self.send_hsv(self.hue, self.sat, self.val)


    def carbon_write_hsv(self, cid, hue, val, sat):
        sock = socket.socket()
        sock.connect( ("pidp.local", 2003) )
        now = time.time()
        msg = "{}-hue.metric {} {}\n".format(cid, hue, now)
        sock.send(msg.encode('utf-8'))
        msg = "{}-val.metric {} {}\n".format(cid, val, now)
        sock.send(msg.encode('utf-8'))
        msg = "{}-sat.metric {} {}\n".format(cid, sat, now)
        sock.send(msg.encode('utf-8'))
        sock.close()
        print("sent carbon " + msg)

    def test_function(self, flag):
        print(f"test function, {flag}")
        for client in self.clients:
            client.set_test_mode(flag)
        
    def save_preset(self,preset_number):
        print(f"Saving preset {preset_number}")
        for client in self.clients:
            client.save_preset(preset_number)

        
    def load_preset(self,preset_number):
        print(f"Loading preset {preset_number}")
        for client in self.clients:
            client.load_preset(preset_number)

    def send_rgba(self,client_index, rgba):
        self.clients[client_index].send_rgba(rgba)

    def send_hsv(self, client_index, h, s, v):
        print(f"sending hsv {h} {s} {v} to {client_index}")
        self.clients[client_index].send_hsv(h, s, v)
        
    def set_hsv_spread(self, spread):
        self.hue_spread = constrain(spread, 0, 0.5)
        
    def send_hsv_all(self, h, s, v):
        for i, c in enumerate(self.clients):
            c.send_hsv(h, s, v)
            self.carbon_write_hsv(i, h, s, v)
            h = h + self.hue_spread
            while(h > 1.0):
                h -= 1.0

    def send_hex(self,client_index, hexcolor):
        self.clients[client_index].send_hex(hexcolor)

    def set_fade(self,fade):
        for c in self.clients:
            c.fade_time=float(fade)
            c.set_gamma(True)
            c.set_dither(True)


    def toggle(self):
        if self.on == 1:
            self.set_fade(0.5)
            self.send_hsv(0., 0., 0.)
            print("turning off")
        else:
            self.set_fade(0.33)
            if self.val < 0.2:
                self.val = 0.5
            self.send()
            print("turning off")
        self.on = 1 - self.on


class OscDMXClient(object):
    '''one of these objects per OSC endpoint.'''
    def __init__(self,ip_str,  port=10000):
        self.ip_str = ip_str
        self.c = SimpleUDPClient(ip_str, port)
        # array of current RGBA values, 0-1
        # colors are tuples or lists of RGBA values (A=Amber)
        self.rgba = [0.,  0., 0., 0.]
        self.hsv = [0.,  0., 0.]
        self.gamma = True
        self.fade_time = 0.
        self.dither_flag = True
        self.num_presets = 8
        self.preset_fname = ip_str + "-presets.txt"
        self.cx = ColorXform()
        self.test_flag = 0

        if os.path.exists(self.preset_fname):
            self.presets = self.load_presets_from_file()
        else:
            print("Preset file not found, initializing black presets")
            self.presets = []
            for i in range(self.num_presets):
                self.presets.append([0.,  0., 0., 0.])

    def set_test_mode(self,flag):
        self.test_flag = flag
        print(f"client {self.ip_str} test flag: {flag}")        
        self.send_hsv(self.hsv[0], self.hsv[1], self.hsv[2])
        
    def load_presets_from_file(self):
        print(f"Loading presets from {self.preset_fname}")
        jsonfile = open(self.preset_fname, "r")
        presets = json.load(jsonfile)
        jsonfile.close()
        return presets
    
    def save_presets_to_file(self):
        print(f"Saving presets to {self.preset_fname}")
        with open(self.preset_fname, "w") as jsonfile:
            jsonfile.write(json.dumps(self.presets))
        
    def save_preset(self,preset_number):
        print(f"client {self.ip_str} saving preset {preset_number}")
        self.presets[preset_number] = self.rgba.copy()
        print(self.presets)
        self.save_presets_to_file()
        
    def load_preset(self,preset_number):
        print(f"client {self.ip_str} loading preset {preset_number}")
        #print(self.presets)
        self.rgba = self.presets[preset_number]
        self.send_hex(self.rgba2hex(self.rgba))
        print(self.presets)
                        
    def constrain(self, val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def send_hsv(self, h, s, v):
        self.hsv = [h, s, v]
        rgba = self.cx.hsv_to_rgba(h, s, v)
        self.cx.print_hsv(h, s, v)
        if self. test_flag:
            self.cx.print_hsv(h,s,v,"pre")
            R, G, B = self.cx.rgba_to_rgb(rgba[0],rgba[1],rgba[2],rgba[3])
            #print(f"RGB: {R:.3f} {G:.3f} {B:.3f}")
            H, S, V = self.cx.rgb_to_hsv(R, G, B)
            self.cx.print_hsv(H,S,V,"cooked")
            rgba = self.cx.hsv_to_rgba(H, S, V)
        self.send_rgba(rgba)

    def send_rgba(self, rgba):
        self.rgba = rgba
        self.send_hex(self.rgba2hex(rgba))

    def rgba2hex(self, rgba):
        """ rgba format [list of floats] to hex value 
        (str of 4 concatenated hex bytes"""
        assert len(rgba) == 4
        rgba_int = [math.floor(255. * self.constrain(c, 0, 1.)) for c in rgba]
        return "".join(["{:02x}".format(c) for c in rgba_int])

    def send_hex(self, hexcolor,fade_time=None):
        if fade_time is None:
            fade_time = self.fade_time
        assert len(hexcolor) == 8
        ##print(f"sending hexcolor {hexcolor} to {self.ip_str}")
        self.c.send_message("/hexfade", [hexcolor, fade_time])


    def set_gamma(self, gvalue):
        #print(f"set gamma  {gvalue}")
        self.gamma_flag = gvalue
        if gvalue:
            self.c.send_message("/setgamma", [1])
        else:
            self.c.send_message("/setgamma", [0])

    def set_dither(self, dvalue):
        #print(f"set dither  {dvalue}")
        self.dither_flag = dvalue
        if dvalue:
            self.c.send_message("/setdither", [1])
        else:
            self.c.send_message("/setdither", [0])

    def set_switch(self, svalue, timeout_s=None):
        """turn on/off relay-switched outlet. Svalue True to turn on, 
        False to turn off, timeout is seconds (int or fp) to turn off"""
        #print(f"set switch  {svalue}")
        if svalue:
            if timeout_s is not None:
                self.c.send_message("/switch", [1, int(1000*timeout_s)])
            else:
                self.c.send_message("/switch", [1])
        else:
            self.c.send_message("/switch", [0])


    def hsv_to_rgba(self, h, s, v):
        """Improved implementation of hsv colorspace to red, green, blue and
        amber channels red and amber squashed into 1/3 the hue range
        (instead of 1/2 as in naive) hsv inputs and rgby outputs all
        floats between 0 and 1
        this code is described as in http://rotormind.com/blog/2015/Generating-RGBY-from-Hue/
        """
        # offset h so 0 is pure red, needed to keep code pretty
        h = h - 1.0/12.0
        if h < 0:
            h += 1.0

        if s == 0.0:
            return [v, v, v, v]

        i = int(h*6.0) # what hue range are we in?

                                # v is top flat
        f = (h*6.0) - i         # slope for 1/6 hue range

        b = v*(1.0 - s)         # bottom flat
        d = v*(1.0 - s*f)       # downslope  
        u = v*(1.0 - s*(1.0-f)) # upslope

        i2 = int(h*12.0)        # what hue subrange are we in?
        f2 = (h*12.0) - i2      # slope for 1/12 hue range
        d2 = v*(1.0 - s*f2)       # steep downslope  
        u2 = v*(1.0 - s*(1.0-f2)) # steep upslope

        i2 = i2 % 12

        if i2 == 0:
            return [d2, b, b, v]  # max a, r down steep
        if i2 == 1: 
            return [b, u2, b, v]  # max a, g up steep
        if i2 == 2 or i2 == 3:
            return [b, v, b, d]   # max g, a down slow
        if i2 == 4 or i2 == 5:
            return [b, v, u, b]   # max g, b up slow
        if i2 == 6 or i2 == 7:
            return [b, d, v, b]   # max b, g down slow
        if i2 == 8 or i2 == 9:
            return [u, b, v, b]   # max b, r up slow
        if i2 == 10:
            return [v, b, d2, b]  # max r, b down steep 
        if i2 == 11:
            return [v, b, b, u2] # max r, a up steep



if __name__ == '__main__':

    lights = DMXLEDS()

    if len(sys.argv) == 1:

        client = 2


        while True:
            #lights.clients[client].set_switch(True,2)
            #time.sleep(3)
            lights.clients[client].set_switch(True)
            time.sleep(1)
            lights.clients[client].set_switch(False)
            time.sleep(1)
        #time.sleep(5)
        #lights.clients[2].set_switch(True,5)
        #lights.clients[0].set_switch(False)
        #time.sleep(0)


    elif len(sys.argv) == 2:
        print(str(sys.argv))
        lights.set_fade(1.0)
        lights.send_rgba(0, [0.5, 0, 0, 0.25])
        time.sleep(100)
        lights.send_rgba(0, [0., 0, 0, 0.])
        #time.sleep(5)
        #lights.set_fade(0.0)
        #lights.send_rgba(0, [0., 0, 0, 0.])
        #lights.send_hex(0, sys.argv[1])

    elif len(sys.argv) == 4:
        #print(sending)
        lights.set_fade(0.5)
        lights.hue_spread = 0.01
        lights.send_hsv(float(sys.argv[1]),
                        float(sys.argv[2]),
                        float(sys.argv[3]))


        #time.sleep(5)
        #lights.send_hsv(float(sys.argv[1]) + 0.1,
        #                float(sys.argv[2]),
        #                0.)
        

    elif len(sys.argv) == 6:
        # index, (int), rgba (hex, eg ff0000ff)
        lights.clients[int(sys.argv[1])].send_rgba((float(sys.argv[2]),
                                                    float(sys.argv[3]),
                                                    float(sys.argv[4]),
                                                    float(sys.argv[5])))

