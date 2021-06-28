# Gateway to Azure IoT Hub
## Guide to setting up the Python3 program to Azure.

SSH into your gateway (make sure that setting is enabled on your gateway under admin, access configuration)

Log in with your username and password.

Run “sudo -s” and enter your password again. This will switch you into the root user account.
Run “opkg update”.
Run “opkg install python3-pip”. This will install the required python3 files to install the azure-iot-device Package, this may take a few minutes.
Run “pip3 install azure-iot-device”, this will install all the files required for the azure iothub sdk to function.
Set up your IoT Device connection string in the GatewaytoAzureIothub.py file.
The line to edit is 32. 
Load the GatewaytoAzureIothub.py file onto the gateway in the /var/config/home/admin directory.
To test the program go into the /var/config/home/admin directory and run “python3 GatewaytoAzureIothub.py” and you should expect to see the following output after a few seconds:
```
“[GCC 8.2.0]
IoT Hub Client for Python
Starting the IoT Hub Python sample...
    Protocol MQTT
    Connection string=HostName=hostname.azure-devices.net;DeviceId=DeviceId;SharedAccessKey=SharedAccessKey
2021-06-16 13:16:08,101 - app_log - INFO - IoTHubClient sending 1 messages
2021-06-16 13:16:08,206 - app_log - INFO - Connection returned 0”
```
If there are any errors, make sure you are running the program as a root user and double check your device connection string. 
Once the program is running locally you need to set up a cron.d file to start the program everytime the gateway starts up.
Create a new text file in the admin folder named “CronAzureIothubPy3”
With the contents of 
```
“@reboot root python3 /home/admin/GatewaytoAzureIothub.py &
**************** Extra Line ********************” 
```
(Without the quotes).
Change the owner of the file to root with the following command if it is not already.
```
chown root CronAzureIothubPy3
```
Then move the file to the correct cron directory.
Run **“mv CronAzureIothubPy3 /etc/cron.d”**
At this point it should be ready to run, now reboot your gateway and check to see if your lora data is reaching your AzureIotHub. 

If there is no traffic at the IotHub you can run the “top” command to look for a python3 process running. If there is no python3 process you can check the cron logs at “/var/volatile/log/cron” to see what the error may have been. 


