import sys
import os
import time
import traceback
import _thread
import datetime

# uses mpd2 for python 3 compat
# for python 3: sudo pip3 install python-mpd2
# command ref https://python-mpd2.readthedocs.io/en/latest/
from mpd import MPDClient
from mpd import CommandError
from mpd.base import ProtocolError
from mpd.base import ConnectionError




class MPDLogic(object):
    def __init__(self,host='pidp.local'):
        self.host = host
        self.client = None               # create client object
        self.reconnect()
        self.volume = 0
        self.state='stop'
        self.status_str =""

    def log_status(self, status):
        status_str = " ".join(status)
        if status_str != self.status_str:
            print("LOG: {} {}".format(datetime.datetime.now().isoformat(),
                                      status_str)) 
            self.status_str = status_str

    def reconnect(self):
        print("connecting")
        if self.client is not None:
            del self.client
        self.client = MPDClient()               # create client object
        self.client.timeout = 1                 # network timeout in secs (floats allow
        self.client.idletimeout = 2          # timeout for idle is handled seperately

        self.client.connect(self.host, 6600)  # connect to localhost:6600


    def clean_str(self, instr):
        cstr = instr.encode("ascii","ignore")
        print(f"cleanstr: {cstr}")
        return cstr.decode("ascii")

    def get_short(self):
        """ return list of short string description of now playing info"""
        data = self.nowplaying()
        #print("data dict:")
        #print(str(data))

        if "error" in data:
            print("mpd error detected, skipping status")
            return data["error"]

        #truncate strings to 60 chars cause that's what we have on the MCU
        
        msg_list = []
        if len(data['title']) > 0:
            msg_list.append(data['title'][:60])
        msg_list.append(data['name'][:60])
        if data['state'] == 'play':
            msg_list.append("-{}-".format(data['artist'][:60]))
            msg_list.append("{} ".format(data['song'][:60]))
        else:
            msg_list.append("* {} *".format(data['state']))

        #print("msg_list:")
        #print(str(msg_list))
        sys.stdout.flush()

        return msg_list

    def get_volume(self):
        return self.volume

    def get_status(self, client):
        e = None
        result = {}
        try:
            result = client.status()

        except ConnectionError as e:
            result["error"] =  "status-connection error"
            
        except UnboundLocalError as e:
            result["error"] = "status-MPD error"

        except OSError as e:
            result["error"] = "status-OSError"

        except  Exception as e:
            # OK no good way to catch this when client has closed.
            # exit to shell and use restart loop
            result["error"] = "status-unknown error"

        else: 

            if "volume" in result:
                self.volume = int(result["volume"])
            if "state" in result:
                self.state = result["state"]

            self.status = result
            self.log_status(result)
            return result

        if "error" in result:
            self.handle_error(result["error"])
        return result

    def handle_error(self, errstr):
        print("******************** Error caught:") 
        print(f"{errstr}")
        traceback.print_exc()
        self.reconnect()

    def toggle_play(self):
        status = self.get_status(self.client)
        if 'state' in status:
            if status['state'] == 'play':
                self.client.stop()
            else:
                self.client.play()


    def volume_incr(self, incr):
        status = self.get_status(self.client)
        if "error" in status:
            return
        if 'volume' in status:
            vol = int (status['volume'])
            vol += incr
            if vol > 100:
                vol= 100
            if vol < 0:
                vol = 0
            print(f"setting vol to {vol}")
            try:
                self.client.setvol(vol)
            except ProtocolError as e:
                print("set volume: MPD protocol error")
                raise e
                return
            self.volume = vol
        else:
            print("error setting vol")

    def nowplaying(self):

        fields = ['title', 'file', 'name', 'song', 'artist']
        playd = {"state":"offline"}
        for f in fields:
            playd[f] = " "

        status = self.get_status(self.client)

        if 'error' in status:
            print("Status error: " + status['error'])
            return status

        songdict = {}
        try: 
            songdict = self.client.currentsong()
        except ConnectionError as e:
            playd["error"] =  "csong-connection error"
            
        except UnboundLocalError as e:
            playd["error"] = "csong-MPD error"

        except OSError as e:
            playd["error"] = "cscong-OSError"

        except  Exception as e:
            # OK no good way to catch this when client has closed.
            # exit to shell and use restart loop
            playd["error"] = "csong-unknown error"

        else:
            pass

        if "error" in playd:
            handle_error(playd['error'])
            return playd

        if 'state' in status:
            playd["state"] = status['state']
            self.state = status['state']                

        for f in fields:
            if f in songdict:
                if f == 'title':
                    # attempt to parse artist name out of title
                    tsplit = songdict['title'].split("-")
                    if len(tsplit) == 2:
                        playd["song"] =  tsplit[1].strip()
                        playd["artist"] = tsplit[0].strip()
                    else:
                        playd[f] = songdict[f]
                else:
                    playd[f] = songdict[f]
        return playd

    # def get_mpd_status(client):     
    #     """ use mpd2 to get mpd status. Right now just returns volume 
    #     as a 0-100 int and playlist"""
    #     # deprecated by use

    #     for entry in self.client.lsinfo("/"):
    #         print("%s" % entry)
    #     for key, value in self.client.status().items():
    #         print("%s: %s" % (key, value))
    #     print(self.client.currentsong())




if __name__ == "__main__":

    mpl  = MPDLogic()

    while(True):

        msg = ""
        print(str(mpl.nowplaying()))
        print(str(mpl.get_short()))
        time.sleep(1)
