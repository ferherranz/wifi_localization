#!/usr/bin/env python

import roslib; roslib.load_manifest('wifi_lookup')
import rospy, os, re
from wifi_lookup.msg import WifiData, Wifi

class DataNode():
	def __init__(self):
		pub = rospy.Publisher('wifi_data', WifiData)

		r = rospy.Rate(rospy.get_param('~rate', 1))
		interface = rospy.get_param('~interface', 'wlan0')
		while not rospy.is_shutdown():
			os.system("iwlist " + interface + " scanning > datatemp.txt")

			wifiraw = open("datatemp.txt").read()
			os.remove("datatemp.txt")

			essids = re.findall("ESSID:\"(.*)\"", wifiraw)
			addresses = re.findall("Address: ([0-9A-F:]{17})", wifiraw)
			signals = re.findall("Signal level=.*?([0-9]+)", wifiraw)

			msg = WifiData()
			print "---------------------"
			for i in range(len(essids)):
				ssid = rospy.get_param('~ssid', '')
				if (ssid == '' or ssid == essids[i] ):
					temp = Wifi()			    
					temp.MAC = addresses[i] 
					temp.dB = int(signals[i])
					msg.HotSpots.append(temp)
					print essids[i], signals[i]

			msg.length = len(msg.HotSpots)
			pub.publish(msg)
			r.sleep()

if __name__ == '__main__':
	rospy.init_node('wifi_data')
	try:
		node = DataNode()
	except rospy.ROSInterruptException: pass
	
