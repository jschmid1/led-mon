#!/usr/bin/python
# server.py 
import socket                                         
import time
import shlex
import os
import sys
import termios
import pigpio
import tty
import json
import logging
import time
from subprocess import Popen, PIPE

logging.basicConfig(filename='srv_mon.log', level=logging.DEBUG)

# create a socket object
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
# reuse the old socket address
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

host = socket.gethostname()                           
port = 9997                                           

# bind to the port
serversocket.bind((host, port))                                  

# queue up to 5 requests
serversocket.listen(5)                                           

RED_PIN   = 18
GREEN_PIN = 23
BLUE_PIN  = 17
r = 0.0
g = 0.0
b = 0.0

pi = pigpio.pi()

class Colors(object):
  def __init__(self, name, r=r, g=g, b=b):
    self.name = name
    self.red = r
    self.green = g
    self.blue = b
    self.dct = {RED_PIN: self.red, 
                GREEN_PIN: self.green, 
                BLUE_PIN: self.blue}
 
  def set(self):
    for pin, color in self.dct.iteritems():
        pi.set_PWM_dutycycle(pin, color)

green = Colors('green', r=0, g=255, b=0)
red = Colors('red', r=255, g=0, b=0)
blue = Colors('blue', r=0, g=0, b=255)
yellow = Colors('yellow', r=255, g=165, b=0)


class Heartbeat(object):

    def __init__(self):
        # Allow 20min without alerting
        # 20m * 60 ->
        self.timeout = 1200

    def write_timestamp(self):
        with open('last_write.time', 'w') as _fd:
            return _fd.write(str(time.time()))

    def read_timestamp(self):
        with open('last_write.time', 'r') as _fd:
            return _fd.read()

    def ok(self):
        last_message = self.read_timestamp()
        curr_time = time.time()
        if (int(curr_time) - int(float(last_message))) <= self.timeout:
            return True
        return False

heart_beat = Heartbeat()
# where to put this? A server waits for connections and can't check..

while True:
    clientsocket,addr = serversocket.accept()      
    print("Got a connection from %s" % str(addr))
    BUFFER_SIZE = 250 # whats the correct buf size for a 3 k/v dict?
    data = clientsocket.recv(BUFFER_SIZE)
    logging.info("received data: {}".format(data))
    data = json.loads(data)
    color_code = data['code']
    reason = data['reason']
    if color_code == 'red':
        color = red
    elif color_code == 'yellow':
        color = yellow 
    elif color_code == 'green':
        color = green
    else:
        color = red
        msg = "{} is not implemented. Setting red flag".format(data)
        reason = 'internal error'
        print(msg)
        logging.error(msg)

    color.set()
    clientsocket.send(color.name.encode('ascii'))
    clientsocket.close()

pi.stop()
