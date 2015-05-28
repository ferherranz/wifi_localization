#!/usr/bin/env python

import roslib; 
import rospy, sys, tf
from wifi_localization.msg import WifiData, Wifi
from geometry_msgs.msg import *
from visualization_msgs.msg import *
from pymongo import *
import numpy as np

percent_aps = 0.5

class WifiLocNode():

	def findBestPose(self,locs, scores, num_aps):
	  
	  max_aps = max(num_aps)
	  #print 'scores ', scores 
	  
	  #penalize positions with a number of aps lower than max_aps multiply by a percentage
	  for i in range(len(scores)):
	    if num_aps[i] < max_aps*percent_aps :
	      scores[i] = float("inf")
	  id_best_pose = scores.index(min(scores))    
	  
	  
	  #print 'scores ', scores 
	  #print 'locs ', locs 
	  #print 'num_aps ', num_aps
	  #print id_best_pose,locs[id_best_pose],scores[id_best_pose], num_aps[id_best_pose], max_aps
	  return locs[id_best_pose]
	  
	def wifiDataCB(self, data):

	  scores = []
	  locs = []
	  num_aps = []
	  for fp in self.collection.find({}): # fingerprints in collection
	    #print '--------------------'
	    #print fp['loc']
	    keys = fp['data'].keys()
	    eu_dist = 0
	    count_aps = 0
	    for obj in data.HotSpots:
	      #print fp['data']	      
	      if obj.address in keys :
		ap_data = fp['data'][obj.address]		
		#print obj.address, ap_data['num_samples']
		eu_dist += (obj.signal - ap_data['mean'])**2
		count_aps += 1
		
	    eu_dist = np.sqrt(eu_dist)	    
	    locs.append(fp['loc'])
	    scores.append(eu_dist)
	    num_aps.append(count_aps)

	    
	
	  loc = self.findBestPose(locs, scores, num_aps)
	  print loc
	  #rospy.loginfo('wifi_loc: ' + loc)
	  #setting up the message
	  self.wifi_pose.header.stamp = rospy.Time.now()
	  self.wifi_pose.header.frame_id = '/map'
	  self.wifi_pose.pose.position.x = loc[0]
	  self.wifi_pose.pose.position.y = loc[1]
	  self.wifi_pose.pose.orientation = Quaternion(*tf.transformations.quaternion_from_euler(0, 0, 0))
	  
	  self.pub_loc.publish(self.wifi_pose)
	  #print self.wifi_pose
	  
	    
	  

	def __init__(self):		
		self.conn       = Connection('192.168.4.41', 27017)
		self.db   	= self.conn["wifi_data"]
		self.collection	= self.db["wifi_map"]
		self.wifi_pose	= PoseStamped()
		rospy.Subscriber('wifi_data', WifiData, self.wifiDataCB)
		self.pub_loc = rospy.Publisher('wifi_pose', PoseStamped, queue_size=10)
		
if __name__=='__main__':
	rospy.init_node('wifi_loc')
	try:
	  r = rospy.Rate(1)
	  loc_node = WifiLocNode()
	  while not rospy.is_shutdown():
	    r.sleep()
	except rospy.ROSInterruptException: pass
	
