# MCFE Listener

MCFE Listener is a daemon program which connects to the Manchester MCFE MQTT
Broker and logs the different messages to a Radon instance.


# Build the Docker image

docker build -t mcfe-listener-image .


# Run Docker image

docker run -it --rm  mcfe-listener-image:latest /bin/bash



# Install the listener

cd /home/jerome/Work/MCFE/src/mcfe-listener
python3 -m venv ~/ve/mcfe-listener
source ~/ve/mcfe-listener/bin/activate
pip install -r requirements.txt 



# Run the listener

cd /home/jerome/Work/MCFE/src/mcfe-listener ; source ~/ve/mcfe-listener/bin/activate
python main.py



# License

Licensed under the Apache License, Version 2.0 (the "License"); 
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.

