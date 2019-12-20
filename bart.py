# -*- coding: utf-8 -*-
"""
BART API wrapper for Python 3+

This wrapper's main purpose is to make it easy to make a call to the BART
API and receive a well-formed string/data that represents the contents of
the BART return.

BART API Documentation: https://api.bart.gov/docs/overview/index.aspx
"""

### from https://pypi.org/project/bart-api-ulloa/#files


import requests

__author__ = "Luis Ulloa"


class Bart:
    """
    ----- Bart API -----
    bart = Bart(key)  # key is optional, defaults to universal BART API key


    Advisories
    -----------
    bsa(orig)
    train_count()
    elev()
    elev_help()


    Real-Time Estimates
    -------------------
    etd(orig, plat, direction)
    etd_help()


    Route Information
    -----------------
    routeinfo(route_num, sched_num, date)
    routes(sched_num, date)
    route_help()


    Schedule Information
    --------------------
    arrive(orig, dest time, b, a)
    depart(orig, dest, time, b, a)
    fare(orig, dest, date, sched)
    holiday()
    routesched(route, date, time, sched)
    scheds()
    special()
    stnsched(orig, date)
    sched_help()


    Station Information
    -------------------
    stn_help()
    stninfo(orig)
    stnaccess(orig)
    stns()


    Version Information
    -------------------
    version()


    """
    # links are constants class variables, accessible with Bart.CONSTANT_NAME
    BSA_API_LINK = 'https://api.bart.gov/api/bsa.aspx'       # Advisories
    ETD_API_LINK = 'https://api.bart.gov/api/etd.aspx'       # Real-Time Estimates
    ROUTE_API_LINK = 'https://api.bart.gov/api/route.aspx'   # Route Information
    SCHED_API_LINK = 'https://api.bart.gov/api/sched.aspx'   # Schedule Information
    STN_API_LINK = 'https://api.bart.gov/api/stn.aspx'       # Station Information
    VERS_API_LINK = 'https://api.bart.gov/api/version.aspx'  # Version Information

    def __init__(self, key='MW9S-E7SL-26DU-VV8V'):
        self.key = key

    def bsa(self, orig=None):
        """
        Prints any announcements, if available
        :param orig: ignore this, bsa doesn't support station specific,
                     announcements but will in the future
        """
        cmd, res = 'bsa', ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'json': 'y'}
        r = requests.get(self.BSA_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            time = data['time']
            date = data['date']
            res += "The following announcements were available on %s at %s...\n" % (date, time)
            bsa = data['bsa']
            for elem in bsa:        # each element is a specific service announcement
                if elem['sms_text']:
                    res += "SMS text announcement: %s\n" % bsa[-1]['sms_text']['#cdata-section']
                if len(elem['station']) > 0:
                    res += "%s: %s\n" % (elem['station'], elem['description']['#cdata-section'])
        return res

    def train_count(self):
        """ Returns count of active trains. -1 if error occurs. """
        cmd = 'count'
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.BSA_API_LINK, params=payload)
        if "error" not in r.text:
            return r.json()['root']['traincount']
        return -1

    def elev(self):
        """ Returns elevator announcement details. """
        cmd, res = 'elev', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.BSA_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            time = data['time']
            date = data['date']
            res += "The following announcements were available on %s at %s...\n" % (date, time)
            bsa = data['bsa']

            for elem in bsa:    # each elem is a service announcement + accompanied sms
                if elem['sms_text']:
                    res += "SMS text announcement: %s\n" % elem['sms_text']['#cdata-section']

                if len(elem['station']) > 0:
                    res += "%s - %s\n" % (elem['station'], elem['description']['#cdata-section'])
        return res

    def elev_help(self):
        """ Returns/prints commands you can use with API. """
        cmd, res = 'help', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.BSA_API_LINK, params=payload)
        if "error" not in r.text:
            help_msg = r.json()['root']['message']['help']['#cdata-section']
            res += help_msg + '\n'
            res += "bsa(), train_count(), elev(), elev_help()\n"
        print(res)
        return res

    def etd(self, orig, plat=None, direction=None):
        """
        Returns estimated departure time for specified station

        :param orig: specific station, using its abbreviation, ALL for all ETD's
        :param plat: specific platform, ranges b/w 1-4
        :param direction: direction, 'n' north; 's' south

        Note: If orig is 'all', can't use plat or dir. Can't use plat
                and dir together either way (preference plat)
        """
        if plat is not None and direction is not None:  # preference to plat
            direction = None

        cmd, res = 'etd', ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'plat': plat,
                   'dir': direction, 'json': 'y'}
        r = requests.get(self.ETD_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            date, time = data['date'], data['time']
            res += "Estimated departure time(s) for %s on %s %s...\n" % (orig, date, time)
            if not data.get('station') and data.get('message') != "":
                res += data['message']['warning'] + '\n'
                return res      # nothing matching

            for station in data.get('station'):
                name = station['name']
                res += "Departures for %s...\n" % name
                for loc in station.get('etd'):
                    dest = loc['destination']
                    res += "For those leaving to %s:\n" % dest
                    for departure in loc.get('estimate'):
                        minutes = departure['minutes']
                        platform = departure['platform']
                        color = departure['color']
                        res += "%s bart on platform %s leaving in %s minutes!\n" % (color, platform, minutes)
                res += '\n'  # spacing b/w each station
        return res

    def etd_help(self):
        """ Shows commands for time departure part of api. """
        cmd, res = 'help', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.ETD_API_LINK, params=payload)
        if "error" not in r.text:
            help_msg = r.json()['root']['message']['help']['#cdata-section']
            res += help_msg + '\n'
            res += "etd(), etd_help()\n"
        print(res)  # show help details to user as well as return
        return res

    def route_info(self, route_num, sched_num=None, date=None):
        """
        Returns information on a route, can specify schedule number and date as well.

        :param route_num: route number
        :param sched_num: schedule number
        :param date: current date

        Note: don't use schedule and date together, otherwise date is dropped
        """
        cmd, res = 'routeinfo', ''
        payload = {'cmd': cmd, 'key': self.key, 'route': route_num, 'sched': sched_num, 'date': date, 'json': 'y'}
        r = requests.get(self.ROUTE_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['routes']['route']
            name, origin, destination, route = data['name'], data['origin'], data['destination'], data['routeID']
            res += '%s is %s, going from %s to %s.\n' % (route, name, origin, destination)
        return res

    def routes(self, sched_num=None, date=None):
        """
        Returns routes, can specify schedule numbers and dates uniquely.

        :param sched_num: schedule number
        :param date: current date

        Note: don't use schedule and date together, otherwise date is dropped
        """
        cmd, res = 'routes', ''
        payload = {'cmd': cmd, 'key': self.key, 'sched': sched_num, 'date': date, 'json': 'y'}
        r = requests.get(self.ROUTE_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['routes']
            for route in data['route']:
                name, abbr, route_id = route['name'], route['abbr'], route['routeID']
                res += "%s - %s with abbreviation \"%s\"\n" % (route_id, name, abbr)
        return res

    def route_help(self):
        """ Returns/prints commands for route (note: "help" refers to this method)"""
        cmd, res = 'help', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.ROUTE_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['message']['help']['#cdata-section']
            res += data + '\n'
            res += "route_help(), routes(), route_info()\n"
        print(res)
        return res

    def arrive(self, orig, dest, time=None, date=None, b=None, a=None, command="arrive"):
        """
        Requests a trip based on arriving at specified time, returns a printable statement.

        :param orig: origination station (abbreviation)
        :param dest: destination station (abbreviation)
        :param time: arrival time (defaults to current time) h:mm+am/pm
        :param date: specific date (defaults to today) mm/dd/yy
        :param b: specifies how many trips before specified time should be returned  (0-4, default 2)
        :param a: specifies how many trips after specified time should be returned  (0-4, default 2)
        :param command: used internally, no need to declare this, defaults to arrive
        """
        cmd, res = command, ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'dest': dest, 'time': time,
                   'date': date, 'b': b, 'a': a, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            res += "Trips from %s to %s...\n" % (data['origin'], data['destination'])
            trips = data['schedule']['request']['trip']
            for i in range(0, len(trips), 2):    # each trip has a leg following it
                trip = trips[i]
                # leg = trips[i+1]['leg']   # won't use any data from legs, but know it's here!
                res += "Trip from %s to %s on %s with the following fares...\n" \
                       % (trip['@origTimeMin'], trip['@destTimeMin'], trip['@origTimeDate'])
                res += "Standard: " + trip['@fare'] + '\n'
                for fare in trip['fares']['fare']:
                    res += "%s: %s (%s)\n" % (fare['@name'], fare['@amount'], fare['@class'])
                res += '\n'  # spacing
        return res

    def depart(self, orig, dest, time=None, date=None, b=None, a=None):
        """
        Requests a trip based on departing at specified time. Calls arrive
        but specifies depart as command, same data output format.

        :param orig: origination station (abbreviation)
        :param dest: destination station (abbreviation)
        :param time: departure time for trip h:mm+am/pm
        :param date: specific date (defaults to today) mm/dd/yy
        :param b: specifies how many trips before specified time should be returned  (0-4, default 2)
        :param a: specifies how many trips after specified time should be returned  (0-4, default 2)
        """
        return self.arrive(orig, dest, time, date, b, a, "depart")

    def fare(self, orig, dest, date=None, sched=None):
        """
        Requests the fare information for a trip between two stations.

        :param orig: origination station (abbreviation)
        :param dest: destination station (abbreviation)
        :param date: specific date mm/dd/yyyy, current date default
        :param sched: specific schedule to use (optional)
        """
        cmd, res = 'fare', ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'dest': dest, 'date': date, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            res += "A trip from %s to %s has the following fares...\n" % (data['origin'], data['destination'])
            for fare in data['fares']['fare']:
                res += "%s for %s (%s)\n" % (fare['@amount'], fare['@name'], fare['@class'])
        return res

    def holiday(self):
        """ Returns BART schedule type for any holiday. """
        cmd, res = 'holiday', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['holidays'][0]
            for hday in data['holiday']:
                name, date, sched_type = hday['name'], hday['date'], hday['schedule_type']
                res += "%s on %s has a %s schedule type.\n" % (name, date, sched_type)
        return res

    def routesched(self, route, date=None, time=None, sched=None):
        """
        Returns detailed schedule information for a specific route.

        :param route: specifies a route information to return
        :param date: specifies which date mm/dd/yyyy (defaults to today)
        :param time: specifies what time to use hh:mm tt (defaults to now)
        :param sched: specifies schedule to use (defaults to current schedule)
        """
        cmd, res = 'routesched', ''
        payload = {'cmd': cmd, 'key': self.key, 'route': route, 'time': time,
                   'date': date, 'sched': sched, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            res += "For schedule number %s on %s...\n" % (data['sched_num'], data['date'])
            for path in data['route']['train']:
                stops = ', '.join([loc['@station'] + "(" + loc["@origTime"] + ")"
                                   for loc in path['stop'] if loc.get('@origTime')])
                res += "Train with ID %s has the following stops: %s\n" % (path['@trainId'], stops)
        return res

    def scheds(self):
        """ Returns schedule id's and effective dates. """
        cmd, res = 'scheds', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        data = r.json()['root']['schedules']
        for sched in data['schedule']:
            res += "Schedule %s has effective date %s\n" % (sched['@id'], sched['@effectivedate'])
        return res

    def special(self):
        """ Returns information about current and upcoming BART special schedules. """
        cmd, res = 'special', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['special_schedules']
            for spec in data['special_schedule']:
                res += "From %s to %s: %s\n" % \
                      (spec['start_date'], spec['end_date'], spec['text']['#cdata-section'])
                res += "The routes affect are %s, more information here: %s\n" % \
                      (spec['routes_affected'], spec['link']['#cdata-section'])
        return res

    def stnsched(self, orig, date=None):
        """
        Requests detailed schedule information for a specific schedule.

        :param orig: station for which schedule is requested
        :param date: specifies date to use mm/dd/yy (default today)
        """
        cmd, res = 'stnsched', ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'date': date, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            res += "%s schedule (%s) details on %s...\n" % \
                  (data['station']['name'], data['sched_num'], data['date'])
            for route in data['station']['item']:
                res += "Train %s with %s, (Head Station %s): from %s to %s.\n" % \
                      (route['@trainId'], route['@line'], route['@trainHeadStation'],
                       route['@origTime'], route['@destTime'])
        return res

    def sched_help(self):
        """ Prints/Returns commands for time departure part of api. """
        cmd, res = 'help', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.SCHED_API_LINK, params=payload)
        if "error" not in r.text:
            help_msg = r.json()['root']['message']['help']['#cdata-section']
            res += help_msg + '\n'
            res += "arrive(), depart(), fare(), sched_help(), holiday(), routesched(), scheds(), special(), stnsched()\n"
        print(res)
        return res

    def stninfo(self, orig):
        """
        Returns detailed information on specified station.
        Specifically, station name, full address, link to website,
        The data returned could also be used to show north and south routes
        and platforms, but this function doesn't show that.

        :param orig: abbreviated name of target station
        """
        cmd, res = 'stninfo', ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'json': 'y'}
        r = requests.get(self.STN_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['stations']['station']
            name = data['name']
            address, city, state, zipcode = data['address'], data['city'], data['state'], data['zipcode']
            link = data['link']['#cdata-section']
            res += "%s is at %s, %s, %s %s and can be found at %s.\n" % (name, address, city, state, zipcode, link)
        return res

    def stns(self):
        """ Provides list of BART stations with their abbreviations, full names, and addresses. """
        cmd, res = 'stns', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.STN_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            for station in data['stations']['station']:
                name = station['name']
                abbr = station['abbr']
                address, city, state, zipc = station['address'], station['city'], station['state'], station['zipcode']
                res += "%s (\"%s\") is at %s, %s, %s %s.\n" % (name, abbr, address, city, state, zipc)
        return res

    def stnaccess(self, orig):
        """
        Returns access/neighborhood info for specified station.
        Showing the "legend" means showing what each flag in data stands
        for; won't be using that here.

        This function will report if it has parking/bike/bike_station/lockers,
        as well as the associated message.

        :param orig: target station (use abbreviation)
        """
        cmd, res = 'stnaccess', ''
        payload = {'cmd': cmd, 'key': self.key, 'orig': orig, 'json': 'y'}
        r = requests.get(self.STN_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']['stations']['station']
            parking, bike, bike_station, lockers = data['@parking_flag'],data['@bike_flag'],\
                data['@bike_station_flag'], data['@locker_flag']

            res += "%s: " % data['name'] + '\n'
            res += "Parking: " + ("yes" if parking == '1' else "no") + '\n'
            res += "Bike Racks: " + ("yes" if bike == '1' else "no") + '\n'
            res += "Bike Station: " + ("yes" if bike_station == '1' else "no") + '\n'
            res += "Lockers: " + ("yes" if lockers == '1' else "no") + '\n'
        return res

    def stn_help(self):
        """ Returns/prints commands for time departure part of api. """
        cmd, res = 'help', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.STN_API_LINK, params=payload)
        if "error" not in r.text:
            help_msg = r.json()['root']['message']['help']['#cdata-section']
            res += help_msg + '\n'
            res += "stn_help(), stninfo(), stnaccess(), stns()\n"
        print(res)
        return res

    def version(self):
        """ Returns version details. """
        cmd, res = 'ver', ''
        payload = {'cmd': cmd, 'key': self.key, 'json': 'y'}
        r = requests.get(self.VERS_API_LINK, params=payload)
        if "error" not in r.text:
            data = r.json()['root']
            api_version = data['apiVersion']
            api_copyright = data['copyright']
            api_license = data['license']
            res += "Version: %s\nCopyright: %s\nLicense: %s\n" % (api_version, api_copyright, api_license)
        print(res)
        return res

    def help(self):
        """ Return/print all help messages. """
        return self.route_help() \
            + self.elev_help() \
            + self.etd_help() \
            + self.stn_help() \
            + self.sched_help()


if __name__ == "__main__":
    # example usage, see test.py for import formatting
    bart = Bart()
    print(bart.bsa())
    # print(bart.train_count())

    # print(bart.elev())
    # print(bart.elev_help())

    #print(bart.etd('ALL'))
    #print(bart.etd('16TH'))

    # print(bart.etd_help())

    #print(bart.route_info(1))
    # print(bart.routes())

    # print(bart.route_help())

    #print(bart.stninfo('24TH'))

    #print(bart.stns())

    # print(bart.stnaccess('12th'))

    # print(bart.stn_help())

    # print(bart.arrive("ASHB", "CIVC"))

    #print(bart.depart("16TH", "CIVC"))

    # print(bart.fare("ASHB", "CIVC"))

    # print(bart.routesched(1))

    # print(bart.scheds())

    #print(bart.special())

    #print(bart.stnsched("ASHB"))
    #print(bart.stnsched("16TH"))

    #print(bart.stn_help())

    # print(bart.help())
