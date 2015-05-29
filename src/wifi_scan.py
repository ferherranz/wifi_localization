#!/usr/bin/env python

import roslib; 
import rospy, os, re
from wifi_localization.msg import WifiData, Wifi

filter_duplicated = True
class DataNode():
	def __init__(self):
		prev_data = {}
		pub = rospy.Publisher('wifi_data', WifiData, queue_size=10)

		r = rospy.Rate(rospy.get_param('~rate', 1))
		interface = rospy.get_param('~interface', 'wlan0')
		while not rospy.is_shutdown():
			os.system("iwlist " + interface + " scanning > datatemp.txt")
			
			wifiraw = open("datatemp.txt").read()
			os.remove("datatemp.txt")

			essids = re.findall("ESSID:\"(.*)\"", wifiraw)
			addresses = re.findall("Address: ([0-9A-F:]{17})", wifiraw)
			signals = re.findall("Signal level=.*?([0-9]+)", wifiraw)

			msg 		= WifiData()
			new_data 	= {}	
			for i in range(len(essids)):
			  #check if there are duplicated addresses
			  if addresses[i] in prev_data and filter_duplicated:				  
			    prev_sl = prev_data[addresses[i]]
			  else:				  
			    prev_sl = None
			  #if the sample is new (no duplicated), it's stored
			  if prev_sl == None or prev_sl != int(signals[i]) :	
			    temp = Wifi()			    
			    temp.address = addresses[i] 
			    temp.essid = essids[i] 
			    temp.signal = int(signals[i])
			    msg.HotSpots.append(temp)	
			  
			  new_data[addresses[i]] = int(signals[i])		
				
			msg.length = len(msg.HotSpots)
			
			pub.publish(msg)
			
			prev_data = new_data
			r.sleep()

if __name__ == '__main__':
	rospy.init_node('wifi_scan')
	try:
		node = DataNode()
	except rospy.ROSInterruptException: pass
	
