import time
import sys
import math
# Set up  client for testing
from pythonosc.udp_client import SimpleUDPClient
# docs at https://pypi.org/project/python-osc/

class DMXLEDS(object):
    def __init__(self):
        self.dmx_osc_client_ips = ["192.168.1.240",
                              "192.168.1.241",
                              "192.168.1.242",
                              "192.168.1.243"]

        self.dmx_osc_client_ips = ["192.168.1.240"]

        self.clients = []
        for ip in self.dmx_osc_client_ips:
            client = OscDMXClient(ip)
            self.clients.append(client)

    def send_rgba(self,client_index, rgba):
        self.clients[client_index].send_rgba(rgba)

    def send_hsv(self,client_index, h, s, v):
        self.clients[client_index].send_hsv(h, s, v)


    def send_hex(self,client_index, hexcolor):
        self.clients[client_index].send_hex(hexcolor)

    def set_fade(self,fade):
        for c in self.clients:
            c.fade_time=float(fade)

class OscDMXClient(object):
    def __init__(self,ip_str,  port=10000):
        self.ip_str = ip_str
        self.c = SimpleUDPClient(ip_str, port)
        # array of current RGBA values, 0-1
        # colors are tuples or lists of RGBA values (A=Amber)
        self.rgba = [0.,  0., 0., 0.]
        self.gamma = True
        self.fade_time = 0.
        self.dither_flag = True

    def constrain(self, val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def send_hsv(self, h, s, v):
        rgba = self.hsv_to_rgba(h, s, v)
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
        print(f"sending hexcolor {hexcolor}")
        self.c.send_message("/hexfade", [hexcolor, fade_time])


    def set_gamma(self, gvalue):
        print(f"set gamma  {gvalue}")
        self.gamma_flag = gvalue
        if gvalue:
            self.c.send_message("/setgamma", [1])
        else:
            self.c.send_message("/setgamma", [0])

    def set_dither(self, dvalue):
        print(f"set dither  {gvalue}")
        self.dither_flag = dvalue
        if dvalue:
            self.c.send_message("/setdither", [1])
        else:
            self.c.send_message("/setdither", [0])

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
    if len(sys.argv) == 2:
        print(str(sys.argv))
        lights.set_fade(1.0)
        #lights.send_rgba(0, [0.5, 0, 0, 0.25])
        #time.sleep(5)
        #lights.set_fade(0.0)
        #lights.send_rgba(0, [0., 0, 0, 0.])
        #lights.send_hex(0, sys.argv[1])

    elif len(sys.argv) == 4:
        lights.send_hsv(0, 
                        float(sys.argv[1]),
                        float(sys.argv[2]),
                         float(sys.argv[3]))

    elif len(sys.argv) == 5:
        lights.send_rgba(0,
                         float(sys.argv[1]),
                         float(sys.argv[2]),
                         float(sys.argv[3]),
                         float(sys.argv[4])) 

