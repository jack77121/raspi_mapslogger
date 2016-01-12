#!/usr/bin/python

import time
import serial
import re
import paho.mqtt.publish as publish
import os
from datetime import datetime

ERROR = -999
TIME_HEADER_NUM = 0
TIME_YEAR = 1
TIME_MONTH = 2
TIME_DATE = 3
TIME_HOUR = 4
TIME_MINUTE = 5
TIME_SECOND = 6
CO2_HEADER_NUM = 7
CO2_RATIO = 8
CO2_TEMPERATURE = 9
CO2_PPM = 10
DHT_HEADER_NUM = 11
DHT_TEMPERATURE = 12
DHT_HUMIDITY = 13
PM_HEADER_NUM = 14
PM_2_5 = 15
PM_10 = 16
BARO_HEADER_NUM = 17
BARO_PRESSURE = 18
CPU_HEADER_NUM = 19
CPU_TICK = 20
PACKAGE_HEADER_NUM = 21
PACKAGE_SEQUENCE = 22

TIME_HEADER = 'T'
CO2_HEADER = 'C'
DHT_HEADER = 'D'
PM_HEADER = 'P'
BARO_HEADER = 'B'
CPU_HEADER = 'U'
PACKAGE_HEADER = 'K'

# you should change this to your own server name file
# in mqtt_server.txt, there is only one line which should be your mqtt server's domain name or ip
SERVER_NAME_PATH = "mqtt_server.txt"

def find_port():  
	port_num = ERROR 
	find = False
	cmd = "dmesg > dmesg.txt"
	os.system(cmd)
	with open("dmesg.txt") as f:
		for line in f:
			# print line
			m = re.search('(usb 1-1.[0-9]): Product: (ARDUINO NANO|FT232R USB UART)',line)
			if m:
				for line in f:
					# print m.group(1)
					if m.group(1) in line: 
						n = re.search('FTDI USB Serial Device converter now attached to ttyUSB([0-9])', line)
						if n:
							find = True
							# print "found it"
							# print n.group(1)
							port_num = n.group(1)
							break
						else:
							continue
				if find is True:
					break
				else:
					continue

	return port_num				




def logger_mqtt(port_num):
	maps_ttyUSB = "/dev/ttyUSB"+port_num
	# print maps_ttyUSB
	time_check = False
	ser = serial.Serial(maps_ttyUSB, 9600, timeout = 40)
	find = False


	LOG_HEADER = "log/"
	LOG_FOOTER = ".log"
	# data format from Arduino:  
	# T+2015+11+23+11+17+31+C+1.162286+25.511297+2548.54+D+24.90+66.80+P+11.00+15.00+B+1016.84+U+2+K+3
	while 1:
		line = ser.readline().strip()
		print "our input is: "
		print line
		print "===================="
		# print line
		maps_data = line.split('+')
		# check data format from arduino

		
		if maps_data[TIME_HEADER_NUM] == TIME_HEADER and maps_data[CO2_HEADER_NUM] == CO2_HEADER and maps_data[DHT_HEADER_NUM] == DHT_HEADER and maps_data[PM_HEADER_NUM] == PM_HEADER and \
			maps_data[BARO_HEADER_NUM] == BARO_HEADER and maps_data[19] == CPU_HEADER and maps_data[PACKAGE_HEADER_NUM] == PACKAGE_HEADER:
			# reset pi's time with RTC module on Arduino
			year = maps_data[TIME_YEAR].zfill(4)
			month = maps_data[TIME_MONTH].zfill(2)
			date = maps_data[TIME_DATE].zfill(2)
			hour = maps_data[TIME_HOUR].zfill(2)
			minute = maps_data[TIME_MINUTE].zfill(2)
			second = maps_data[TIME_SECOND].zfill(2)
			cmd_date = "sudo date +%Y%m%d -s "
			ymd = year+month+date
			cmd_time = "sudo date +%T -s "
			hms = hour+":"+minute+":"+second
			os.system(cmd_date+ymd)
			os.system(cmd_time+hms)
			time_check = True
			print "time reset, done"
			myTimestamp = year+month+date+'_' \
						+hour+minute+second

			utc_date = datetime.utcnow().strftime("%Y-%m-%d")
			utc_time = datetime.utcnow().strftime("%H:%M:%S")
			CO2_ratio = maps_data[CO2_RATIO]
			CO2_temperature = maps_data[CO2_TEMPERATURE]
			CO2_ppm = maps_data[CO2_PPM]
			ambient_temperature = maps_data[DHT_TEMPERATURE]
			ambient_humidity = maps_data[DHT_HUMIDITY]
			pm25 = maps_data[PM_2_5]
			pm10 = maps_data[PM_10]
			ambient_pressure = maps_data[BARO_PRESSURE]
			tick = maps_data[CPU_TICK]
			package_num = maps_data[PACKAGE_SEQUENCE]
			# display
			print "Time: 			" + year + "/" + month + "/" + date + " " + \
										hour + ":" +minute + ":" + second
			print "pm2.5:			" + pm25
			print "CO2 ratio:		" + CO2_ratio
			print "CO2 temperature:	" + CO2_temperature
			print "CO2 ppm:		" + CO2_ppm
			print "Temperature:		" + ambient_temperature
			print "Humidity: 		" + ambient_humidity
			print "Air pressure:		" + ambient_pressure
			print "CPU tick:		" + tick
			print "Package sequence:" + package_num
			# write to a log
			log_name = LOG_HEADER + myTimestamp + LOG_FOOTER
			f = open(log_name, 'w')
			f.write(line)
			# for mqtt
			# LASS format:
			# |ver_format=3|fmt_opt=0|app=PM25|ver_app=0.7.3|device_id=LJ_PM25_001|tick=26795810|date=2015-10-15|time=22:35:07|device=LinkItONE| \
			# s_0=2234.00|s_1=100.00|s_2=1.00|s_3=0.00|s_d0=39.00|s_t0=25.50|s_h0=65.80|gps_lat=25.025362|gps_lon=121.371038|gps_fix=1|gps_num=9|gps_alt=2
			mqtt_msg = "|ver_format=3|fmt_opt=1|app=MAPS|ver_app=1.0|device_id=MAPS_4_001|tick=" + tick + "|date=" + maps_data[1].zfill(4) + "-" + maps_data[2].zfill(2) + "-" + maps_data[3].zfill(2) + \
						"|time=" + maps_data[4].zfill(2) + ":" + maps_data[5].zfill(2) + ":" + maps_data[6].zfill(2) + "|device=ArduinoNano|s_0=" + package_num + "|s_1=-1.00|s_2=1.00|s_3=0.00|s_d0=" + pm25 + \
						"|s_d1=" + pm10 + "|s_t0=" + ambient_temperature + "|s_h0=" + ambient_humidity + "|s_g0=" + CO2_ppm + "|s_b1=" + ambient_pressure + "|gps_lat=-1.00|gps_lon=-1.00|gps_fix=0|gps_num=0|gps_alt=-1"
			mqtt_utc_time_msg = "|ver_format=3|fmt_opt=1|app=MAPS|ver_app=1.0|device_id=MAPS_4_001|tick=" + tick + "|date=" + utc_date + \
						"|time=" + utc_time + "|device=ArduinoNano|s_0=" + package_num + "|s_1=-1.00|s_2=1.00|s_3=0.00|s_d0=" + pm25 + \
						"|s_d1=" + pm10 + "|s_t0=" + ambient_temperature + "|s_h0=" + ambient_humidity + "|s_g0=" + CO2_ppm + "|s_b1=" + ambient_pressure + "|gps_lat=-1.00|gps_lon=-1.00|gps_fix=0|gps_num=0|gps_alt=-1"
			print mqtt_msg
			print mqtt_utc_time_msg
			with open(SERVER_NAME_PATH, 'r') as f:
				# publish for our server list
				for server_name in f:
					# print server_name
					try:
						publish.single("RCEC/HOUSE/MAPS", mqtt_msg, hostname=server_name.strip())
					except:
						print "connection might be timeout"
			# publish to lass server, use UTC time
			try:
				publish.single("LASS/Test/MAPS", mqtt_utc_time_msg, hostname="gpssensor.ddns.net")
			except:
				print "connection might be timeout"
		else:
			print "wrong format with input...................."
			

def main():
	port_num = find_port()
	logger_mqtt(port_num)



if __name__ == '__main__':
	main()
	

