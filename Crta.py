import time
from datetime import datetime
import pytz
import os.path
import jsonpickle 
import traceback
import sys
from MyFlask import MyFlask
import pathlib


from Util import read, write

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
        #print("convertTimeToValue: " + val)
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

    def writeCrteD(self, crteD):
        crteD[self.ime] = self
        
        crte=[]
        for crtaKey in crteD.keys():
            crta = crteD[crtaKey]
            if crta.symbol in self.symbol: 
                crte.append(crta) 

        crtePath = self.getDataPath() + os.sep + "crte.data"
        try:
            with open(crtePath,'w') as f:
                strJson = jsonpickle.encode(crte, indent=2)
                f.write(strJson)
                MyFlask().app().logger.info("Wrote crte for symbol: " + self.symbol)
                 
        except:
            if os.path.isfile(crtePath):        
                os.remove(crtePath)
            MyFlask().app().logger.error(traceback.format_exc())
            # or
            MyFlask().app().logger.info(sys.exc_info()[2])      
        write('crteD', crteD)
         
    def update_crteD(self):
        crteD = read('crteD')
        crteD[self.ime] = self
        
        MyFlask.app().logger.info("Updated new line for symbol: " + self.symbol + " " + self.ime);

    @classmethod
    def get_crteDforSymbol(cls, symbol, crteD):
        ret = []
        for crtaKey in crteD.keys():
            crta = crteD[crtaKey]
            if crta.symbol in symbol:
                ret.append(crta)         
        return ret
    
    def removeFromcrteD(self):
        crteD = read('crteD')
        del crteD[self.ime]
        write('crteD', crteD)
        self.writeCrteD()
        
    def to_json(self):
        return jsonpickle.encode(self, indent=2)
        
    def getDataPath(self):
        path = pathlib.Path("." + os.sep + self.symbol).resolve()
        if not (os.path.isdir(path)):
            os.mkdir(path, mode = 0o777)
            MyFlask().app().logger.info("Directory '% s' created" % path)
        return os.path.realpath(path);
