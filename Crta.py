import time

class Crta(object):
    x0 = ''
    y0 = 0
    x1 = ''
    y1 = 0
    i=0
    ime=''

    def __init__(self, i, x0, y0, x1, y1):
        self.i = i
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.ime= 'crta_' + str(round(time.time() * 1000))
        
    def plotlyLine(self):
        #{'editable': True, 'xref': 'x', 'yref': 'y', 'layer': 'above', 'opacity': 1, 'line': {'color': '#444', 'width': 4, 'dash': 'solid'}, 'type': 'line', 'x0': '2024-02-07 16:46:56.129', 'y0': 46809.4022260274, 'x1': '2024-02-11 19:10:14.5161', 'y1': 49194.83449391172}
        json = {"name": self.ime, "editable": 'True', "xref": 'x', "yref": 'y', "layer": 'above', "opacity": '1', "line": {"color": '#444', "width": 4, "dash": 'solid'}, "type": 'line', "x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1 }
        return json

