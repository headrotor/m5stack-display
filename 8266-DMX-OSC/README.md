DMX output from a ESP8266, controlled by OSC (Open Sound Control). Requires a MAX485 level converter or similar, and mating plugs. 

Custom firmware, but the heavy lifting is done by the Arduino OSC library https://github.com/hideakitai/ArduinoOSC
the DMX library from https://github.com/Rickgg/ESP-Dmx and the FastLED library https://github.com/FastLED/FastLED  for the gamma correction method `dim8_raw()`.

On the server side, look at dmx_logic.py in the directory aabove for examples of how to send the OSC commands. 
Some special commands can enable gamma correction, change ramp time (between color changes) and enable dithering. 
I'm especially proud of the dithering which uses [error diffusion](https://en.wikipedia.org/wiki/Error_diffusion) to  smooth the transitions between colors. 
Because DMX is only 8-bit resolution, this makes the visual transitions, especially dimming, far more pleasing. 

Here are the the OSC commands available: 

 - `/setgamma <i>` One integer argument `<i>`, if nonzero turns on gamma table mapping, 
 - `/setdither <i>` One integer argument `<i>`, if nonzero turns on dithering during color changes.
 - `/switch <i> <f>` One integer argument `<i>`, if nonzero sets GPIO RELAY_PIN high, used for external relay control. Optional second argument is timeout in seconds; after `<f>` seconds the switch output will revert back to what it was before the command.
 - `/hexfade <s> <f>` String `<s>`is is 4 bytes of color information in 8 ascii hex characters, formatted as `RRGGBBYY`. For example, full red and 50% yellow would be `FF00007F`. Second float argument `<f>` is change time in seconds, zero for instant color update.  Hexfade commands issued during a change interval are permitted: they reset the change timer and target color.  


Description of how I used this with theater RGBY PAR fixtures at my blog: http://rotormind.com/blog/2020/OSC-Controlled-DMX-LED-Fixtures/
