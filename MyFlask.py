'''
Created on 12 May 2024

@author: kleme
'''
from flask import Flask
import logging

class MyFlask(object):
    _app = None

    @classmethod
    def app(cls):
        if cls._app is None:
            cls._app = Flask(__name__, static_folder='./static', template_folder='./templates')
            handler = logging.FileHandler("MyApp.log")  # Create the file logger
            cls._app.logger.addHandler(handler)             # Add it to the built-in logger
            cls._app.logger.setLevel(logging.DEBUG)         # Set the log level to debug
            cls._app.logger.info("Started...")
            
        return cls._app