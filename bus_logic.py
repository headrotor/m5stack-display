
import sys
import time
import requests
import xml.etree.ElementTree as ET

class BusLogic(object):
    def __init__(self, route):
        #self.routes.append()
        self.route = route


    def get_data(self):
        self.r = requests.get(self.route) 
        if self.r.status_code == requests.codes.ok:
            try:
                self.root = ET.fromstring(self.r.content)
            except ET.ParseError:

                self.r.status_code = "XML parse error"
                self.root = ET.fromstring("")                

        else:
            self.root = ET.fromstring("")
       #print(response.content)

    def get_route_dict(self):
        stop, times = self.get_route_short()
        return {"stop":stop, "times":times}

    def get_route_short(self):
        self.get_data()
        stopstr = "parse error"
        predstr = ""
        if self.r.status_code != requests.codes.ok:
            print("Error fetching data, status: {}",format(str(self.r.status_code)))
            return((stopstr, predstr))    
        for child in self.root:
            if child.tag == 'predictions':
                stopstr = "{} at {}".format(child.attrib['routeTag'],
                                         child.attrib['stopTitle'])
        secs = []
        for p in self.root.iter('prediction'):
            secs.append(p.attrib['seconds'])
        #predstr = " - ".join(["{}".format(int(int(i)/60.)) for i in secs])
        if len(secs) > 0:
            minsecs = [ (int(int(i)/60), int(i)%60)  for i in secs]
            #predstr = ", ".join(["{}:{:02d}".format(ms[0],ms[1]) for ms in minsecs])
            predstr = ", ".join(["{}".format(ms[0]) for ms in minsecs])
        else:
            predstr = "no current prediction"
        return((stopstr, predstr))


    def get_message(self):
        self.get_data()
        msg = None
        for p in self.root.iter('message'):
            msg = p.attrib['text']
        return msg

    def parse_route(self):
        #root = tree.getroot()
        for child in self.root:
            print(child.tag, child.attrib)        

        for d in self.root.iter('direction'):
            print("direction" + str(d.attrib))

        for p in self.root.iter('prediction'):
            print("p" + str(p.attrib))


b12 = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=12&stopId=17733&useShortTitles=true'

b22= 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=22&stopId=13281&useShortTitles=true'

b49= 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=49&stopId=15557&useShortTitles=true'

b27 = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=27&stopId=13739&useShortTitles=true'


class BusData(object):
    def __init__(self):
        self.bus_url_dict = {}
        self.busses = {}
        self.lines = []
        self.populate_dict()


    def populate_dict(self):

        self.bus_url_dict['b12'] = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=12&stopId=17733&useShortTitles=true'

        self.bus_url_dict['b22']= 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=22&stopId=13281&useShortTitles=true'

        self.bus_url_dict['b49'] = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=49&stopId=15557&useShortTitles=true'

        self.bus_url_dict['b27'] = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions&a=sf-muni&r=27&stopId=13739&useShortTitles=true'

        for key, value in self.bus_url_dict.items():
            self.busses[key] = BusLogic(value)
            self.lines.append(key)

        print(self.lines)



if __name__ == '__main__':


    bd = BusData()

    for bus in ['b27','b12']:
        resp = bd.busses[bus].get_route_short()

        print(resp)

    exit(0)
        



    busses = [BusLogic(b) for b in [b12 , b22, b27, b49]]



    while(True):

        msg = ""
        for bus in busses:
            print(bus.get_route_short())
            msg  = bus.get_message()
        if msg is not None:
            print(msg)
            #bus.parse_route()
        time.sleep(5)
