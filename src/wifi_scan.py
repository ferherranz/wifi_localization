#!/usr/bin/env python

import roslib; roslib.load_manifest('wifi_lookup')
import rospy, os, re
from wifi_lookup.msg import WifiData, Wifi
from geometry_msgs.msg import *
from visualization_msgs.msg import *
from pymongo import *


class DataNode():
  
	
	def robotPoseCB(self, pose):      
	  self.robot_pose = pose      

	
	def __init__(self):
		
		self.conn       = Connection('192.168.4.41', 27017)
		self.db   = self.conn["wifi_data"]
		self.wifi_data = self.db["wifi_data"]
		self.prev_data = {}
		
		self.robot_pose = Pose()
		pub = rospy.Publisher('wifi_data', WifiData, queue_size=10)

		rospy.Subscriber('robot_pose',Pose, self.robotPoseCB)
		
		r = rospy.Rate(rospy.get_param('~rate', 1))
		interface = rospy.get_param('~interface', 'wlan2')
		while not rospy.is_shutdown():
			os.system("iwlist " + interface + " scanning > datatemp.txt")
			
			wifiraw = open("datatemp.txt").read()
			os.remove("datatemp.txt")
			
			#print wifiraw

			essids = re.findall("ESSID:\"(.*)\"", wifiraw)
			print essids
			addresses = re.findall("Address: ([0-9A-F:]{17})", wifiraw)
			print addresses
			signals = re.findall("Signal level=.*?([0-9]+)", wifiraw)
			print signals
			msg = WifiData()
			
			#os.system('clear')
			new_data = {}
			for i in range(len(essids)):
				temp = Wifi()			    
				temp.MAC = addresses[i] 
				temp.dB = int(signals[i])
				msg.HotSpots.append(temp)	
				
				if addresses[i] in self.prev_data:				  
				  prev_sl = self.prev_data[addresses[i]]
				else:				  
				  prev_sl = None
				
				if prev_sl == None or prev_sl != int(signals[i]):
				  ap_data = {'essid': essids[i], 'address': addresses[i], 'sl': int(signals[i]), 'loc': [self.robot_pose.position.x, self.robot_pose.position.y] }
				  self.wifi_data.insert(ap_data)				  
				  #print addresses[i], int(signals[i])
				
				new_data[addresses[i]] = int(signals[i])
					
			self.prev_data = new_data
			
			msg.length = len(msg.HotSpots)
			pub.publish(msg)
			r.sleep()

if __name__ == '__main__':
	rospy.init_node('wifi_scan')
	try:
		node = DataNode()
	except rospy.ROSInterruptException: pass
	
