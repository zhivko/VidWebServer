import multiprocessing as mp
import pandas as pd

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
    def update_crteD(self, symbol: str, crte: []):
        self._instance.crteD[symbol] = crte
        
                
                