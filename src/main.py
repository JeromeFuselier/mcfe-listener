# Copyright 2023
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__doc_opt__ = """
MCFE Listener.

Usage:
  main.py
  main.py --version
  main.py --mqtt_host=<mh> --radon_host=<rh>

Options:
  -h --help     Show this screen.
  --version     Show version.
  --mqtt_host=<mh>
  --radon_host=<rh>

"""


import paho.mqtt.client as mqtt
from urllib.parse import urlsplit
from docopt import docopt
import json
import os
import pickle
import requests
from datetime import datetime
import time
from blessings import Terminal
from client import RadonClient

SESSION_PATH = os.path.join(os.path.expanduser("/.mcfe"), "session.pickle")

VERSION = "0.1"

LS_TOPICS = ["/galaxy/launch",
             "/galaxy/get_inputs",
             "/galaxy/get_outputs",
             "/galaxy/get_workflows",
             "/galaxy/error",
             "/galaxy/info",
             "/RADON/log"
             ]

#MQTT_HOST = "mcfe.itservices.manchester.ac.uk"
#MQTT_PORT = 1883
#MQTT_USER = "mcfe"
#MQTT_PWD = "newspaper-orange-eaten-loud"


MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PWD = None

RADON_HOST = "127.0.0.1"
RADON_PORT = 8000
RADON_USER = None
RADON_PWD = None



class MainApplication(object):
    
    
    def __init__(self, session_path, mqtt_host=MQTT_HOST, mqtt_port=MQTT_PORT,
                 mqtt_user=MQTT_USER, mqtt_pwd=MQTT_PWD, radon_host=RADON_HOST, 
                 radon_port=RADON_PORT, radon_user=RADON_USER, radon_pwd=RADON_PWD):
        self.session_path = session_path
        self.terminal = Terminal()
        
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_pwd = mqtt_pwd
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        #client.on_disconnect = on_disconnect
        if (self.mqtt_user):
            self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_pwd)
        
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
        
        self.radon_url = "http://{}:{}".format(radon_host, radon_port)
        self.radon_user = radon_user
        self.radon_pwd = radon_pwd
        self.init_radon_connection()
        
        


    def on_connect(self, mqtt_client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        self.mqtt_client.subscribe("#")


    def on_message(self, mqtt_client, userdata, msg):
        print("Message received on topic : " + msg.topic)
        client = self.get_client()
        if (msg.topic in LS_TOPICS):
            # Create collection in Radon (with extra levels if needed)
            colls = [ el for el in msg.topic.split('/') if el]
            
            cur = '/'
            for c in colls:
                cur = cur + c + '/'
                res = client.mkdir(cur)
                if not res.ok():
                    self.print_error(res.msg())
                    return
            
            log_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + msg.topic.replace('/', '_')
            print(log_name)
            
            payload_json = json.loads(msg.payload.decode('utf-8'))

            data = {
                "mime-type" : "text-plain",
                "value": json.dumps(payload_json),
                "metadata" : payload_json
            }
            res = client.put_cdmi(cur + log_name, json.dumps(data))
            
            if res.ok():
                self.print_success(res.msg())
            else:
                self.print_error(res.msg())
            


    def create_client(self):
        """Return a RadonClient."""
        client = RadonClient(self.radon_url)
        # Test for client connection errors here
        res = client.get_cdmi("/")
        if res.code() in [0, 401, 403]:
            # 0 means success
            # 401/403 means authentication problem, we allow for authentication
            # to take place later
            return client
        else:
            self.print_error(res.msg())
            sys.exit(res.code())


    def get_client(self):
        """Return a RadonClient.

        This may be achieved by loading a RadonClient with a previously saved
        session.
        """
        try:
            # Load existing session, so as to keep current dir etc.
            with open(self.session_path, "rb") as fhandle:
                return pickle.load(fhandle)
        except (IOError, pickle.PickleError):
            # Init a new RadonClient
            return self.create_client()
        
        if self.radon_url != None:
            if client.url != self.radon_url:
                client = self.create_client()
        client.session = requests.Session()
        return client
    
    
    def init_radon_connection(self):
        client = self.get_client()

        res = client.authenticate(self.radon_user, self.radon_pwd)
        if res.ok():
            print(
                "{0.bold_green}Success{0.normal} - {1} as "
                "{0.bold}{2}{0.normal} in Radon".format(self.terminal, 
                                               res.msg(), 
                                               self.radon_user)
            )
        else:
            print("{0.bold_red}Failed{0.normal} - {1}".format(
                self.terminal, res.msg()
            ))
            # Failed to log in
            # Exit without saving client
            return res.code()
        # Save the client for future use
        self.save_client(client)
        return 0


    def main_loop(self):
        self.mqtt_client.loop_forever()


    def print_error(self, msg):
        """Display an error message."""
        print("{0.bold_red}Error{0.normal} - {1}".format(self.terminal, msg))


    def print_success(self, msg):
        """Display a success message."""
        print("{0.bold_green}Success{0.normal} - {1}".format(self.terminal, msg))



    def print_warning(self, msg):
        """Display a warning message."""
        print("{0.bold_blue}Warning{0.normal} - {1}".format(self.terminal, msg))

        

    def save_client(self, client):
        """Save the status of the RadonClient for subsequent use."""
        if not os.path.exists(os.path.dirname(self.session_path)):
            os.makedirs(os.path.dirname(self.session_path))
        # Save existing session, so as to keep current dir etc.
        with open(self.session_path, "wb") as fh:
            pickle.dump(client, fh, pickle.HIGHEST_PROTOCOL)


def parse_user(s):
    username = None
    password = None
    ls_tmp = s.split(':')
    if len(ls_tmp) == 2:
        username = ls_tmp[0]
        password = ls_tmp[1]
    elif len(ls_tmp) == 1:
        username = ls_tmp[0]
    else:
        pass
    return (username, password)


def parse_host(s):
    hostname = None
    port = None
    ls_tmp = s.split(':')
    if len(ls_tmp) == 2:
        hostname = ls_tmp[0]
        port = int(ls_tmp[1])
    elif len(ls_tmp) == 1:
        hostname = ls_tmp[0]
    else:
        pass
    return (hostname, port)


def parse_url(s):
    username = None
    password = None
    hostname = None
    port = None
    
    ls_tmp = s.split('@')
    if len(ls_tmp) == 2:
        (username, password) = parse_user(ls_tmp[0])
        (hostname, port) = parse_host(ls_tmp[1])
    elif len(ls_tmp) == 1:
        (hostname, port) = parse_host(ls_tmp[0])
    else:
        pass

    return (username, password, hostname, port)


def main():
    arguments = docopt(__doc_opt__, 
                       version="Radon CLI {}".format(VERSION))
    kwargs = {
        "session_path" : SESSION_PATH,
    }
    if (arguments["--mqtt_host"]):
        (username, password, hostname, port) = parse_url(arguments["--mqtt_host"])
        if username != None:
            kwargs['mqtt_user'] = username
        if password != None:
            kwargs['mqtt_pwd'] = password
        if hostname != None:
            kwargs['mqtt_host'] = hostname
        if port != None:
            kwargs['mqtt_port'] = port
            
    if (arguments["--radon_host"]):
        (username, password, hostname, port) = parse_url(arguments["--radon_host"])
        if username != None:
            kwargs['radon_user'] = username
        if password != None:
            kwargs['radon_pwd'] = password
        if hostname != None:
            kwargs['radon_host'] = hostname
        if port != None:
            kwargs['radon_port'] = port

    app = MainApplication(**kwargs)
    app.main_loop()
    
    


if __name__ == '__main__':
    main()

