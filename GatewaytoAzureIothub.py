#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import time
import sys, getopt
import os
import requests, time
import zipfile
import gzip
import asyncio
import threading
import logging
import logging.handlers
from time import sleep
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from  azure.iot.device.exceptions import ChainableException, ClientError

# global counters
RECEIVE_CALLBACKS = 0
MESSAGE_COUNT = 1

# String containing Hostname, Device Id & Device Key in the format:
# "HostName=<host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"

CONNECTION_STRING = ""

LOG_FILENAME = 'app.log'

# create logger
logger = logging.getLogger('app_log')
logger.setLevel(logging.DEBUG)
# create file handler
fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=500000, backupCount=1)
fh.setLevel(logging.ERROR)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def message_received_handler(message):
	global RECEIVE_CALLBACKS
	try:
		TestValue = message.data.decode('utf-8')
		size = len(TestValue)
		logger.info ( "Received Message [%d]:" % RECEIVE_CALLBACKS )
		logger.info ( "    Data: <<<%s>>> & Size=%d" % (TestValue, size) )
		TestDevEUI = TestValue.split('|')[0]
		TestData = TestValue.split('|')[1]
		logger.info ( "    DevEUI: %s, Data=%s" % (TestDevEUI, TestData) )
		publish.single("lora/" + TestDevEUI + "/down", '{ "data":"' + TestData + '" }', hostname="127.0.0.1")
		logger.info ( "    Properties: %s" % message.custom_properties )
		RECEIVE_CALLBACKS += 1
		logger.info ( "    Total calls received: %d" % RECEIVE_CALLBACKS )
	except Exception as e:
		logger.exception(e)


async def iothub_client_init():
	try:
		client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
		await client.connect()
		client.on_message_received = message_received_handler
		return client
	except Exception as e:
		logger.exception(e)


def send_message(client, message, counter):
	try:
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(client.send_message(message))
		loop.close()
		logger.info("Message [%d] sent." % counter)
		counter += 1
	except Exception as e:
		logger.exception(e)

async def iothub_client_sample_run():
	try:
		iothub_client = await iothub_client_init()
	
		# send a few messages every minute
		logger.info( "IoTHubClient sending %d messages" % MESSAGE_COUNT )

		def on_connect(client, userdata, flags, rc):
			try:
				logger.info("Connection returned " + str(rc))
				# Subscribing in on_connect() means that if we lose the connection and
				# reconnect then subscriptions will be renewed.
				client.subscribe("lora/+/up")
			except Exception as e:
				logger.exception(e)

		# The callback for when a PUBLISH message is received from the server.
		def on_message(client, userdata, msg):
			try:
				#Take the string and exclude the opening bracket, to place it into our custom string
				data2 = msg.payload.decode('utf-8')[1:]
				#changes the string into a json format
				x = json.loads(msg.payload.decode('utf-8'))
				#pulls the data field out of the msg.payload
				data = x['data']
				#gets the time stamp to add to the custom payload
				ts = time.time()
				#Creates the custom payload
				MSG_TXT = "{\"ts\":'"'%s'"',%s" % (ts, data2)

				#sends the message to the Azure IoT Hub
				for message_counter in range(0, MESSAGE_COUNT):
					msg_txt_formatted = MSG_TXT
					# messages can be encoded as string or bytearray
					message = Message(msg_txt_formatted)
					message.content_encoding = "utf-8"
					thread = threading.Thread(target=send_message, args=(iothub_client,message,message_counter))
					thread.start()
					logger.info( "IoTHubDeviceClient.send_message accepted message [%d] for transmission to IoT Hub.", message_counter )
			except Exception as e:
				logger.exception(e)

		#defines client, connects to MQTT broker, Sends message, Loops and waits for a new message on the MQTT broker
		client = mqtt.Client()
		client.on_connect = on_connect
		client.on_message = on_message
		client.connect("127.0.0.1", 1883, 60)
		client.loop_forever()
		
		# Wait for Commands or exit
		logger.info( "IoTHubClient waiting for commands, press Ctrl-C to exit" )
		time.sleep(1)

	except (ChainableException, ClientError) as iothub_error:
		logger.exception("Unexpected error from IoTHub:", iothub_error)
		return
	except KeyboardInterrupt:
		logger.info("IoTHubClient sample stopped")
	except Exception as e:
		logger.exception(e)


def usage():
	print ( "Usage: iothub_client_sample.py -c <connectionstring>" )
	print ( "connectionstring: <HostName=<host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>>" )


if __name__ == '__main__':
	print ( "\nPython %s" % sys.version )
	print ( "IoT Hub Client for Python" )

	try:
		opts, args = getopt.getopt(sys.argv[1:],"c:",["connectionstring="])
	except getopt.GetoptError as option_error:
		print ( option_error )
		usage()
		sys.exit(1)

	for opt, arg in opts:
		if opt in ("-c", "--connectionstring"):
			CONNECTION_STRING = arg

	print ( "Starting the IoT Hub Python sample..." )
	print ( "    Protocol MQTT" )
	print ( "    Connection string=%s" % CONNECTION_STRING )

	loop = asyncio.get_event_loop()
	loop.run_until_complete(iothub_client_sample_run())
	loop.close()

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
