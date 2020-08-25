from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from osc4py3 import oscmethod as osm
import time

osc_startup()

osc_udp_client("192.168.1.220", 10000, "client_send")
osc_udp_client("192.168.1.220", 54345, "client_bind")
osc_udp_server("0.0.0.0", 12000, "server_recv")
osc_udp_server("0.0.0.0", 54445, "server_published")

def handler(address, *args):
    print(address, args)

osc_method("/*", handler, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)

try:
    while True:
        msg = oscbuildparse.OSCMessage('/switch', ",i", [1])
        osc_send(msg, "client_send")
        osc_process() # one message, one call

        time.sleep(1)
        
        msg = oscbuildparse.OSCMessage('/switch', ",i", [0])
        osc_send(msg, "client_send")
        osc_process() # one message, one call
        time.sleep(1)


except KeyboardInterrupt:

    # Properly close the system.
    osc_terminate()
