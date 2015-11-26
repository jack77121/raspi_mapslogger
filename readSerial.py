#!/usr/bin/python

import time
import serial
import re
import paho.mqtt.publish as publish
import os

ERROR=-999

def find_port():  
	port_num = ERROR 
	find = False
	cmd = "dmesg > dmesg.txt"
	os.system(cmd)
	with open("dmesg.txt") as f:
		for line in f:
			# print line
			m = re.search('(usb 1-1.[0-9]): Product: ARDUINO NANO',line)
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
	# T+2015+11+23+11+17+31+C+1.162286+25.511297+2548.54+D+24.90+66.80+P+11.00+B+1016.84
	while 1:
		line = ser.readline().strip()
		# print line
		maps_data = line.split('+')
		# check data format from arduino
		if maps_data[0] == 'T' and maps_data[7] == 'C' and maps_data[11] == 'D' and maps_data[14] == 'P' and maps_data[16] == 'B':
			# reset pi's time with RTC module on Arduino
			if time_check == False:
				cmd_date = "sudo date +%Y%m%d -s "
				ymd = maps_data[1].zfill(4)+maps_data[2].zfill(2)+maps_data[3].zfill(2)
				cmd_time = "sudo date +%T -s "
				hms = maps_data[4].zfill(2)+":"+maps_data[5].zfill(2)+":"+maps_data[6].zfill(2)
				os.system(cmd_date+ymd)
				os.system(cmd_time+hms)
				time_check = True
				print "time reset, done"
			myTimestamp = maps_data[1].zfill(4)+maps_data[2].zfill(2)+maps_data[3].zfill(2)+'_' \
						+maps_data[4].zfill(2)+maps_data[5].zfill(2)+maps_data[6].zfill(2)
			CO2_ratio = maps_data[8]
			CO2_temperature = maps_data[9]
			CO2_ppm = maps_data[10]
			ambient_temperature = maps_data[12]
			ambient_humidity = maps_data[13]
			pm25 = maps_data[15]
			ambient_pressure = maps_data[17]
			# display
			print "Time: 			" + maps_data[1].zfill(4) + "/" + maps_data[2].zfill(2) + "/" + maps_data[3].zfill(2) + " " + maps_data[4].zfill(2) + ":" +maps_data[5].zfill(2) + ":" + maps_data[6].zfill(2)
			print "pm2.5:			" + pm25
			print "CO2 ratio:		" + CO2_ratio
			print "CO2 temperature:	" + CO2_temperature
			print "CO2 ppm:		" + CO2_ppm
			print "Temperature:		" + ambient_temperature
			print "Humidity: 		" + ambient_humidity
			print "Air pressure:		" + ambient_pressure
			# write to a log
			log_name = LOG_HEADER + myTimestamp + LOG_FOOTER
			f = open(log_name, 'w')
			f.write(line)
			# for mqtt
			# LASS format:
			# |ver_format=3|fmt_opt=0|app=PM25|ver_app=0.7.3|device_id=LJ_PM25_001|tick=26795810|date=2015-10-15|time=22:35:07|device=LinkItONE| \
			# s_0=2234.00|s_1=100.00|s_2=1.00|s_3=0.00|s_d0=39.00|s_t0=25.50|s_h0=65.80|gps_lat=25.025362|gps_lon=121.371038|gps_fix=1|gps_num=9|gps_alt=2
			mqtt_msg = "|ver_format=3|fmt_opt=1|app=MAPS|ver_app=1.0|device_id=MAPS_4_001|tick=26795810|date=" + maps_data[1].zfill(4) + "-" + maps_data[2].zfill(2) + "-" + maps_data[3].zfill(2) + \
						"|time=" + maps_data[4].zfill(2) + ":" + maps_data[5].zfill(2) + ":" + maps_data[6].zfill(2) + "|device=ArduinoNano|s_0=1.00|s_1=-1.00|s_2=1.00|s_3=0.00|s_d0=" + pm25 + "|s_t0=" + \
						ambient_temperature + "|s_h0=" + ambient_humidity + "|g_0=" + CO2_ppm + "|b_0=" + ambient_pressure + "|gps_lat=-1.00|gps_lon=-1.00|gps_fix=0|gps_num=0|gps_alt=-1"
			print mqtt_msg
			publish.single("LASS/Test/MAPS", mqtt_msg, hostname="lass.iis.sinica.edu.tw")
		else:
			print line
			print "wrong format"

def main():
	port_num = find_port()
	logger_mqtt(port_num)



if __name__ == '__main__':
	main()
	

