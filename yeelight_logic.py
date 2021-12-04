import time
import sys
import argparse

from yeelight import Bulb
from yeelight import Flow, RGBTransition, HSVTransition, SleepTransition 
from yeelight import transitions
# docs at 
# https://yeelight.readthedocs.io/en/latest/

def constrain(val, min_val=0., max_val=1.):
    return min(max_val, max(min_val, val))

# pip install yeelight
#print(discover_bulbs())


bulbs = ["192.168.1.101"]


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

    parser = argparse.ArgumentParser()
#    parser.add_argument("clients",
#                        help="client selection str, eg '13' - clients 1 & 3")
    parser.add_argument("-s", "--switch", 
                        help="turn bulbs 'on' or 'off'")
    parser.add_argument("-t", "--toggle",
                        help="toggle on/off",
                        action="store_true")
    parser.add_argument("-d", "--discover",
                        help="discover bulbs on network",
                        action="store_true")
    parser.add_argument('-v','--hsv', nargs='+', type=int,
                        help='hue (0-359), saturation (0-100), value (0-100)')
    parser.add_argument('-r','--rgb', nargs=3, type=int,
                        help='red, green, blue values (0-255)')

    args = parser.parse_args()

    if args.discover:
        from yeelight import discover_bulbs
        print(discover_bulbs())
        exit(0)
    else:
        b = Bulb(bulbs[0], auto_on=True)



    if args.toggle:
        b.toggle()
        
    elif args.switch:
        state = False
        if args.switch.lower() == "on":
            state = True
        if args.switch == "1":
            state = True

        if state:
            b.turn_on()
        else:
            b.turn_off()

    elif args.hsv:
        print(str(args.hsv))
        #bulb.set_hsv(*args.hsv))

    elif args.rgb:
        print(str(args.rgb))
        b.set_rgb(*args.rgb)
            
    # if len(sys.argv) == 2:
    #     if sys.argv[1] == "on":

    #     elif sys.argv[1] == "off":
    #         b.turn_off()
    #     elif sys.argv[1] == "toggle":
    #         b.turn_toggle()
    #     elif sys.argv[1] == "flow":
    #         flow= Flow(1, 
    #                    action=Flow.actions.recover, 
    #                    transitions=transitions.lsd())
    #         b.start_flow(flow)
        
    # elif len(sys.argv) == 3:
    #     if sys.argv[1] == "colortemp":
    #         ctemp = int(sys.argv[2])
    #         b.set_color_temp(ctemp)
    #     elif sys.argv[1] == "bright":
    #         bright = int(sys.argv[2])
    #         b.set_brightness(bright)

    # elif len(sys.argv) == 4:
    #     pass


