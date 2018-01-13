#!/usr/bin/python
import socket
from subprocess import Popen, PIPE
import shlex
import json
import time
import logging

logging.basicConfig(filename='client_led.log', level=logging.DEBUG)


class Config(object):
    def __init__(self):
        # seconds -> 5Minutes
        self.timer = 300

class ConnectionError(Exception):
    """
    Connection to Server timed out.
    """


class Events(object):

    def __init__(self):
        pass

class Updates(Events):

    def update_available(self):
        proc = Popen(shlex.split('zypper lu'), stdout=PIPE)
        stdout, stderr = proc.communicate()
        if 'No updates found' in stdout:
            return False
        logging.error('Updates available')
        return True

class Raid(Events):
    
    def __init__(self):
        self.raid_names = ['md127', 'md126']
        self.crit_raid_states = ['degraded', 'resync', 'rebuild']

    def raid_failure(self, raid_name):
	cmd = "mdadm --detail /dev/{}".format(raid_name)
        proc1 = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc1.communicate()
        for state in self.crit_raid_states:
            if state in stdout.strip():
                return True
        return False

    def is_down(self):
        for name in self.raid_names:
            if self.raid_failure(name):
                logging.error('Raid {} is down'.format(name))
                return True
        
def check():
    msg = { 'reason': 'noop', 'code': 'green' }
    if Updates().update_available():
        msg = { 'reason': 'updates', 'code': 'yellow' }
    if Raid().is_down():
        msg = { 'reason': 'raid', 'code': 'red' }
    return msg

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    host = 'led-pi'
    port = 9997
    s.connect((host, port))                               
    if s:
        logging.info('Connected to {} on port {}'.format(host, port))
        return s
    logging.error('Error connecting to {} on port {}'.format(host, port))
    raise ConnectionError("Could not connect to server")

def main():
    """
    Main
    """
    while True:
        """
        Run every x seconds 
        """
        s = connect()
        data = check()
        logging.info('Sending data: {}'.format(data))
        s.send(json.dumps(data))
        tm = s.recv(1024)                                     
        s.close()
        print(tm.decode('ascii'))
        time.sleep(Config().timer)

main()

