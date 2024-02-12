import json
from operator import index
import PIL.Image
import datetime

primitive = (int, str, bool,float,datetime.datetime)
collection = (list,tuple,dict)

def is_primitive(thing):
    return isinstance(thing, primitive)

def is_collection(thing):
    return isinstance(thing,collection)


class classbinder:

    # houses references to original objects
    refqueue:dict[int,object]={}
    classqueue:dict[type,dict[int,object]] = {}
    curref:int = 0

    #houses the output objects with references to be json parseable.
    outputstruct:dict[type,list] = []

    # this is the 'finish it up' member, call this after all calls to queuethem have been finished
    def outputJson(self, priority:list[type]=[]):

        self.outputstruct = {}
        
        if len(priority) > 0:
            # there are priority classes mentioned.

            for t in priority:
                
                if not (t in self.classqueue):
                    continue

                tstruct = self.outputstruct[t] = []
                currClasses = self.classqueue[t]

                for i in currClasses:
                     tstruct.append( self.processclass(currClasses[i]))
        
        for t in self.classqueue:
            
            if t in priority:
                continue

            tstruct = self.outputstruct[t] = []

            currClasses=self.classqueue[t]

            for i in currClasses:
                tstruct.append( self.processclass(currClasses[i]))

        # now that all the complex crap that doesn't nicely serialize is gone this should work.
        oldkeys = list(self.outputstruct.keys())

        for key in oldkeys:
            self.outputstruct[str(key)]= self.outputstruct[key]
            del self.outputstruct[key]

            
        return json.dumps(self.outputstruct)
      
    def processclass(self,val):

        out = {}

        id = self.getclasskey(val)
        out = {'classId':id}

        atts = [f for f in dir(val) if not callable(getattr(val,f)) and not f.startswith('__')]

        for k in atts:
            v = getattr(val,k)
            
            if is_collection(v):
                out[k] = self.processcollection(v)
                continue
            if is_primitive(v):
                out[k] = self.processval(v)
                continue
        return out

        # if hasattr(val,"__dict__"):
        #     for k in val.__dict__:
                
        #         v = val.__dict__[k]

        #         if is_collection(v):
        #             out[k] = self.processcollection(v)
        #             continue
        #         if is_primitive(v):
        #             out[k] = self.processval(v)
        #             continue
        #     return out

        # if hasattr(val,"__slots__"):
        #     for k in val.__slots__:
        #         v = getattr(val,k)

        #         if is_collection(v):
        #             out[k] = self.processcollection(v)
        #             continue
        #         if is_primitive(v):
        #             out[k] = self.processval(v)
        #             continue
        #     return out

        #return {}

    # processes a member that contains a val returning the original value or a class reference object
    def processval(self,val):
        if isinstance(val, datetime.datetime):
            return str(val)

        if is_primitive(val):
            return val
        return self.getrefclass(val)

    def processcollection(self,c):
        if isinstance(c,dict):
            return self.processdict(c)
        else:
            return self.proccesslist(c)

    def proccesslist(self,l):
        tob=[]

        for i in l:
            if is_collection(i):
               tob.append( self.processcollection(i))
            else:
                tob.append(self.processval(i))
        return tob

    def getrefclass(self,val):
        return {'fieldinfo':"reference", 'classtype':str(type(val)), 'ref':self.getclasskey(val)}

    def processdict(self,d):
        tob:dict={}
        for k  in d:
            k2=k
            if not is_primitive(k):
                if k==None:
                    k2='keyword=None'
                else:
                    k2=f'class={self.getrefclass(k)}'
            else:
                k2=f'val={k}'

            if is_collection(d[k]):
                tob[k2] = self.processcollection(d[k])
            else:
                tob[k2] = self.processval(d[k])
        return tob
                        
    def getclasskey(self,o):
        for k in self.refqueue:
            if self.refqueue[k] == o:
                return k
        
        return None

    # adds classes one at a time and data structures one at a time to the list
    def queuethem(self,o,level=1):
    
        
        if is_primitive(o):
            return 

        if isinstance(o,list):
            for o1 in o:
                self.queuethem(o1,level+1)
            return
        
        if isinstance(o,dict):
            for o2 in o:
                self.queuethem(o[o2],level+1) 
                # there are goddamn keys that are objects !!!
                # this fucks up the json serializer!
                self.queuethem(o2,level+1)
            return 

        keys = self.classqueue.keys()
        t = type(o)


        if not (t in keys):
            self.classqueue[t]={}

        vals = self.classqueue[t].values()
        
        if (o in vals):
            return

        self.classqueue[t][self.curref] = o
        self.refqueue[self.curref] = o
        self.curref+=1
        
        atts = [f for f in dir(o) if not callable(getattr(o,f)) and not f.startswith('__')]

        for key in atts:
            v = getattr(o,key)
            self.queuethem(v,level+1)