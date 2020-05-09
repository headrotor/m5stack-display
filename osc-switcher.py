import time
import sys
from dmx_logic import DMXLEDS
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("clients",
                    help="client selection str, eg '13' - clients 1 & 3")
parser.add_argument("onoff",
                    help="turn switch(es) 'on' or 'off'")
parser.add_argument("-d", "--off_delay",
                    help="turn switches off after OFF_DELAY seconds",
                    type=int)

args = parser.parse_args()




lights = DMXLEDS()


print(args.clients)
print(args.onoff)
if args.off_delay:
    print(args.off_delay)


# figure out clients:
client_list = []
for c in args.clients:
    try:
        c_int = int(c)
    except ValueError:
        parser.print_help(sys.stderr)        
        exit()
    else:
        client_list.append(c_int)


    state = False
    if args.onoff.lower() == "on":
        state = True
    if args.onoff == "1":
        state = True
    
for c in client_list:
    
    if args.off_delay:
        lights.clients[c].set_switch(state,args.off_delay)
    
    else: 
        lights.clients[c].set_switch(state)
            
