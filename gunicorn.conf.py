import os
import multiprocessing


# gunicorn.conf.py

# Server socket
bind = '127.0.0.1:8000'  # Specify the server's IP address and port

errorlog = './log/log.log'
loglevel = 'debug'
accesslog = './log/access.log'
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' 

wsgi_app = 'app:app'

# Worker processes
print("Number of available CPU cores:", multiprocessing.cpu_count())

number_of_cores = multiprocessing.cpu_count()
GUNICORN_PROCESSES = number_of_cores * 2 + 1

workers = int(os.environ.get('GUNICORN_PROCESSES', GUNICORN_PROCESSES))  # Number of worker processes
worker_class = 'sync'  # The type of worker (sync, gevent, eventlet, etc.)

# Reload on code changes
reload = True  # Enable auto-reloading when code changes

# Timeout
timeout = 30  # Worker timeout in seconds