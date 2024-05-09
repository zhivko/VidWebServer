import time
from datetime import datetime
import pytz


class Crta(object):
    x0_timestamp=0
    x1_timestamp=0
    x0 = ''
    y0 = 0
    x1 = ''
    y1 = 0
    i=0
    ime=''

    def convertTimeToValue(self, val):
        print("convertTimeToValue: " + val)
        if val.count(':')==1:
            val = val + ":0.0"
        if not "." in val:
            val = val + ".0"
        #"%Y-%m-%dT%H:%M:%S.%fZ"
        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f").timestamp()*1000
    
    def __init__(self, i, x0, y0, x1, y1):
        #local = pytz.utc
        self.i = i
        self.changeX0(x0)
        self.y0 = y0
        self.changeX1(x1)
        self.y1 = y1
        self.ime= 'crta_' + str(round(time.time() * 1000))
    
    def changeX0(self, x0):
        self.x0 = x0
        self.x0_timestamp = self.convertTimeToValue(x0)
        
    def changeX1(self, x1):
        self.x1 = x1
        self.x1_timestamp = self.convertTimeToValue(x1)

        
    def plotlyLine(self):
        #{'editable': True, 'xref': 'x', 'yref': 'y', 'layer': 'above', 'opacity': 1, 'line': {'color': '#444', 'width': 4, 'dash': 'solid'}, 'type': 'line', 'x0': '2024-02-07 16:46:56.129', 'y0': 46809.4022260274, 'x1': '2024-02-11 19:10:14.5161', 'y1': 49194.83449391172}
        json = {"name": self.ime, "editable": 'true', "xref": 'x', "yref": 'y', "layer": 'above', "opacity": '1', "line": {"color": '#444', "width": 4, "dash": 'solid'}, "type": 'line', "x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1 }
        return json

