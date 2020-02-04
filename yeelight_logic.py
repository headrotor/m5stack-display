import time
import sys

from yeelight import Bulb
from yeelight import discover_bulbs
from yeelight import Flow, RGBTransition, HSVTransition, SleepTransition 
from yeelight import transitions
# docs at 

def constrain(val, min_val=0., max_val=1.):
    return min(max_val, max(min_val, val))

# pip install yeelight
#print(discover_bulbs())


bulbs = ["192.168.1.129"]


# b = Bulb("192.168.1.129", auto_on=True)
# b.effect = "smooth"
# b.duration = 5000
# b.turn_on()
# time.sleep(6)
# b.effect = "smooth"
# b.duration = 5000
# b.turn_off()
# time.sleep(6)


if __name__ == '__main__':

    b = Bulb(bulbs[0], auto_on=True)

    if len(sys.argv) == 2:
        if sys.argv[1] == "on":
            b.turn_on()
        elif sys.argv[1] == "off":
            b.turn_off()
        elif sys.argv[1] == "toggle":
            b.turn_toggle()
        elif sys.argv[1] == "flow":
            flow= Flow(1, 
                       action=Flow.actions.recover, 
                       transitions=transitions.lsd())
            b.start_flow(flow)
        
    elif len(sys.argv) == 3:
        if sys.argv[1] == "colortemp":
            ctemp = int(sys.argv[2])
            b.set_color_temp(ctemp)
        elif sys.argv[1] == "bright":
            bright = int(sys.argv[2])
            b.set_brightness(bright)

    elif len(sys.argv) == 4:
        pass



