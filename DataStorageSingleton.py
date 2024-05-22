# TODO: Implement https://www.giraycoskun.dev/blog/2023/12/18/sharing-data-in-a-flask-app-accross-gunicorn-workers/ 


import multiprocessing as mp
import pandas as pd
import jsonpickle
import os.path
import pathlib
import traceback
import sys


'''
Created on 7 May 2024

@author: kleme
'''
from Crta import Crta

class DataStorageSingleton:
    _instance = None
    
    '''
    manager: mp.Manager()
    dfs: manager.dict
    crteD: manager.dict
    '''  

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.manager = mp.Manager()
            cls._instance.dfs = cls._instance.manager.dict() 
            cls._instance.crteD = cls._instance.manager.dict()
            cls._instance.app = args[0]            
        return cls._instance

    @classmethod
    def get_dfs(self):
        return self._instance.dfs

    @classmethod
    def update_dfs(self, symbol: str, df: pd.DataFrame):
        self._instance.dfs[symbol] = df

    @classmethod
    def get_crteD(self):
        return self._instance.crteD


        
    @classmethod
    def getDataPath(symbol):
        path = pathlib.Path("." + os.sep + symbol).resolve()
        if not (os.path.isdir(path)):
            os.mkdir(path, mode = 0o777)
            self._instance.app.logger.info("Directory '% s' created" % path)
        return os.path.realpath(path);        
    
