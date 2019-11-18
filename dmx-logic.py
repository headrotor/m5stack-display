from typing import List, Any
import time
import sys
import socket

# Set up  client for testing
from pythonosc.udp_client import SimpleUDPClient
# docs at https://pypi.org/project/python-osc/

from threading import Timer


class OscDMXClient(object):
    def __init__(self,ip_str,  port=10000):
        self.ip_str = ip_str
        self.c = SimpleUDPClient(ip_str, port)

    def send_DMX_fade(self, color,fade_time):
        assert len(color) == 8
        print(f"sending color {color}")
        self.c.send_message("/hexfade", [color, fade_time])


    def set_gamma(self, gvalue):
        print(f"set gamma  {gvalue}")
        if gvalue:
            self.c.send_message("/setgamma", [1])
        else:
            self.c.send_message("/setgamma", [0])

    def set_dither(self, gvalue):
        print(f"set dither  {gvalue}")
        if gvalue:
            self.c.send_message("/setdither", [1])
        else:
            self.c.send_message("/setdither", [0])

#print("sent at " + time.strftime("%H:%M:%S", time.localtime()))

dmx_osc_client_ips = ["192.168.1.240",
                      "192.168.1.241",
                      "192.168.1.242",
                      "192.168.1.243"]

dmx_osc_client_ips = ["192.168.1.240"]

dmx_osc_clients = []
dmx_osc_client_dict = {}
for ip in dmx_osc_client_ips:

    client = OscDMXClient(ip)
    dmx_osc_clients.append(client)
    # make dict so we can look up clinet server from IP returned from handler
    dmx_osc_client_dict[ip] = client



while True:

    for c in dmx_osc_clients:
        c.set_gamma(False)
        c.set_dither(False)
        c.send_DMX_fade("0A0A0A0A",2.0)
        #c.send_DMX_fade("FFFFFFFF",1.0)
        #c.send_DMX_fade("00000000",5.0)

    time.sleep(3)

    for c in dmx_osc_clients:
        #c.send_DMX("000000FF")
        #c.send_DMX_fade("FFFFFFFF",10.0)
        c.set_dither(False)
        c.send_DMX_fade("00000000",2.0)

    time.sleep(3)
    for c in dmx_osc_clients:
        c.set_dither(True)

        c.send_DMX_fade("0A0A0A0A",2.0)
        #c.send_DMX_fade("FFFFFFFF",1.0)
        #c.send_DMX_fade("00000000",5.0)

    time.sleep(3)

    for c in dmx_osc_clients:
        #c.send_DMX("000000FF")
        #c.send_DMX_fade("FFFFFFFF",10.0)
        c.set_dither(True)
        c.send_DMX_fade("00000000",2.0)

    time.sleep(3)


