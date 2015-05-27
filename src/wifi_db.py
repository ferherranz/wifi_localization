#!/usr/bin/env python

import roslib; roslib.load_manifest('wifi_localization')
import rospy, sys
from wifi_localization.msg import WifiData, Wifi
from geometry_msgs.msg import *
from visualization_msgs.msg import *
from pymongo import *

class WifiDBNode():
  
	
	def robotPoseCB(self, pose):      
	  self.robot_pose = pose      
	
	def wifiDataCB(self, data):
	  new_data 	= {}	  
	  for obj in data.HotSpots:
		  if obj.address in self.prev_data:				  
		    prev_sl = self.prev_data[obj.address]
		  else:				  
		    prev_sl = None
		  
		  if prev_sl == None or prev_sl != int(obj.signal):	
		    ap_data = {'essid': obj.essid, 'address': obj.address, 'sl': int(obj.signal), 'loc': [self.robot_pose.position.x, self.robot_pose.position.y] }
		    self.collection.insert(ap_data)				  
		    #print addresses[i], int(signals[i])
		  
		  new_data[obj.address] = int(obj.signal)
		
	  
	  self.prev_data = new_data
	
	def __init__(self):		
		self.conn       = Connection('192.168.4.41', 27017)
		self.db   	= self.conn["wifi_data"]
		self.collection	= self.db["wifi_data"]
		self.prev_data 	= {}
		
		self.robot_pose = Pose()
		rospy.Subscriber('robot_pose',Pose, self.robotPoseCB)		
		
		rospy.Subscriber('wifi_data', WifiData, self.wifiDataCB)
		
if __name__=='__main__':
	rospy.init_node('wifi_db')
	try:
	  db_node = WifiDBNode()
	  while not rospy.is_shutdown():
	    rospy.spin()
	except rospy.ROSInterruptException: pass
	
