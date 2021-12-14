import pygame
import pygame.midi
from pygame.locals import *
#from giantwin32 import *
import sys, time



# local
import dmx_logic


class APC_Lights(object):
    ''' helper class for AKAI APCmini light outputs'''
    def __init__(self, midi_output):
        self.out = midi_output
        # row of round buttons above sliders
        self.rowdot_ids = list(range(64,72))
        # round buttons on right column
        self.coldot_ids = list(range(82,90))
        # 8 x 8 array of rect buttons
        self.grid_ids = list(range(64))

    def set_global(self, color=0):
        self.set_all_grid(color)
        self.set_all_row(color)
        self.set_all_col(color)
        
    def set_grid(self, x, y, color):
        ''' set button grid light at x, y to color
            0,0 is bottom left  '''
        grid_id = 8*y + x
        assert(grid_id < len(self.grid_ids))
        self.out.note_on(grid_id, color)

    def set_rowdots(self, i, color):
        assert( i < len(self.rowdot_ids))
        self.out.note_on(self.rowdot_ids[i],color)

    def set_coldots(self, i, color):
        assert( i < len(self.coldot_ids))
        self.out.note_on(self.coldot_ids[i],color)
        
    def set_all_grid(self,color):
        for id in self.grid_ids:
            self.out.note_on(id, color)

    def set_all(self,ids, color):
        for id in ids:
            self.out.note_on(id, color)

    def set_all_grid(self, color):
        self.set_all(self.grid_ids,color)

    def set_all_row(self, color):
        self.set_all(self.rowdot_ids,color)

    def set_all_col(self, color):
        self.set_all(self.coldot_ids,color)


    
           
DMXlights = dmx_logic.DMXLEDS()

DMXlights.set_fade(0.01)



pygame.init()
# turn off audio or else ALSA takes 100% cpu
pygame.mixer.quit()

pygame.fastevent.init()
event_get = pygame.fastevent.get
event_post = pygame.fastevent.post



pygame.midi.init()
print("ids: " + str(pygame.midi.get_count()))
input_id = pygame.midi.get_default_input_id()


inp = None
out = None
for i in range(pygame.midi.get_count()):
    info = pygame.midi.get_device_info(i)
    #print(info[1])
    if info[1] == b'APC MINI MIDI 1':
        if info[2] == 1:
            inp = pygame.midi.Input(i)
            inputinfo = str(info)
        elif info[2] == 0:
            out = pygame.midi.Output(i)
            outputinfo = str(info)

if inp is not None:
    print(f'got input: "{inputinfo}"')
if out is not None:
    print(f'got output: "{outputinfo}"')
if inp is None and out is None:
    print("could not find AKAI APCmini")
    exit(0)

# helper class to take care of lighting buttons
lights = APC_Lights(out)

# this lists is the state of each button above each slider left to right
lamp_state = [0]*9
button_ids = list(range(64,72))
lamp_ids = list(range(64,72))

preset_ids = list(range(82,90))





# lamp codes: send Note On to these 
# 0 off
# 1 green
# 2 green blink
# 3 red
# 4 red blink
# 5 yellow
# 6 yellow blink

lights.set_global(5)
time.sleep(0.5)
lights.set_global(0)



#pygame.display.set_caption("midi test")
#screen = pygame.display.set_mode((400, 300), RESIZABLE, 32)


going = True

# left four sliders are rgba sliders
rgba_sliders = [48, 49, 50, 51]

# next three sliders are hsv sliders 
hsv_sliders = [52, 53, 54]

spread_slider = 55
spread = 0.

# rgba values from sliders
rgba = [0., 0., 0., 0.]

# hsv values for sliders
hsv = [0., 0., 0.]


# buttons for each lamp: button set means slider changes that lamp
buts = [1, 1, 1, 1]
# start with all lamps enabled
for i in range(4):
    out.note_on(i,buts[i])



store_flag = False

mode = "NONE"

while going:

    time.sleep(0.01)
    events = event_get()
    for e in events:
        if e.type in [QUIT]:
            going = False
        if e.type in [KEYDOWN]:
            going = False

    if inp.poll():
        midi_events = inp.read(10)
        #print("apc midi_events " + str(midi_events))
        sys.stdout.flush()
        for f in midi_events:
            #detect sliders
            # control codes: control change () Note On, Note Off ()
            code = f[0][0]
            # key or slider number
            key = f[0][1]
            # value or velocity
            val = f[0][2]

            # handle sliders
            if code == 176: 
                if key in rgba_sliders: # fistr four sliders are RGBA
                    if key == 48:
                        rgba[0] = val/127.
                    elif key == 49:
                        rgba[1] = val/127.
                    elif key == 50:
                        rgba[2] = val/127.
                    elif key == 51:
                        rgba[3] = val/127.

                    for i in range(4):
                        if buts[i] == 1:
                            DMXlights.send_rgba(i, rgba)
                    if mode != "RGBA":
                        mode = "RGBA"
                        lights.set_all_row(0);
                        lights.set_all([64, 65, 66, 67],1)
                elif key in hsv_sliders: # next three sliders are HSV
                    if key == 52:
                        hsv[0] = val/127.
                    elif key == 53:
                        hsv[1] = val/127.
                    elif key == 54:
                        hsv[2] = val/127.
                    h = hsv[0]
                    for i in range(4):
                        if buts[i] == 1:
                            DMXlights.send_hsv(i, h, hsv[1], hsv[2])
                        h = h + spread
                        while(h > 1.0):
                            h -= 1.0

                    if mode != "HSV":
                        mode = "HSV"
                        lights.set_all_row(0);
                        lights.set_all([68, 69, 70, 71],1)
                    
                elif key == 55: # eighth slider is spread
                    spread = (val*0.25)/127
                    print(f"spread time set to {spread}")
                    h = hsv[0]
                    for i in range(4):
                        if buts[i] == 1:
                            DMXlights.send_hsv(i, h, hsv[1], hsv[2])
                        h = h + spread


                elif key == 56: # rightmost slider is fade time
                    fade_time = 0.01*val
                    print(f"fade time set to {fade_time} s")
                    DMXlights.set_fade(fade_time) 

                    # handle button presses
            elif code == 144:
                for i in range(4):
                    # toggle enable for this channel
                    if key == i:
                        buts[i] = 1 - buts[i]
                    # display enable status for this channel    
                    out.note_on(i,buts[i])                        
                if key in lights.coldot_ids:
                    # index of pressed key
                    i = key - lights.coldot_ids[0]
                    if store_flag:
                        DMXlights.save_preset(i)
                        lights.set_all_col(0)
                        #set green
                        lights.set_coldots(i,1)
                        store_flag = False
                    else:
                        DMXlights.load_preset(i)
                        lights.set_all_col(0)
                        # set red
                        lights.set_coldots(i,3)
                elif key in lights.rowdot_ids:
                    # index of pressed key
                    i = key - lamp_ids[0]
                    lamp_state[i] = 1 - lamp_state[i]
                    print(i,lamp_ids[i])
                    # set color on or off
                    lights.set_rowdots(i, lamp_state[i])
                    # handle shift key
                elif key == 98:
                    if store_flag:
                        store_flag = False
                        lights.set_all_col(0)
                    else:
                        store_flag = True
                        # set gree blink
                        lights.set_all_col(2)
                
print("exit button clicked.")
inp.close()
out.close()
pygame.midi.quit()
pygame.quit()
exit()



