#!/usr/bin/env python

import roslib; 
import rospy, sys, tf
from wifi_localization.msg import WifiData, Wifi
from geometry_msgs.msg import *
from visualization_msgs.msg import *
from pymongo import *
import numpy as np

import copy

percent_aps = 0.0
window_size = 5
max_scans	= 2
normalize_scores = True
nbest_poses = 3
class WifiLocNode():

	def SetWifiPose(self,loc):
	  wifi_pose = PoseStamped()
	  wifi_pose.header.stamp = rospy.Time.now()
	  wifi_pose.header.frame_id = '/map'
	  wifi_pose.pose.position.x = loc[0]
	  wifi_pose.pose.position.y = loc[1]
	  wifi_pose.pose.orientation = Quaternion(*tf.transformations.quaternion_from_euler(0, 0, 0))
	  self.wifi_pose = wifi_pose
	  
	def computePoseWindow(self):	  
	  scores = []
	  for i in range(len(self.window)):
	    scores.append(self.window.count(self.window[i]))
	  
	  ii = scores.index(max(scores))  
	  return self.window[ii]
	  
	  
	def findBestPose(self,locs, scores, num_aps):
	  
	  max_aps = max(num_aps)
	  #print 'scores ', scores 
	  scores_ = list(scores) # avoid pass-by-reference problem
	  #penalize positions with a number of aps lower than max_aps multiply by a percentage
	  for i in range(len(scores_)):
	    if normalize_scores :
	      scores_[i] = scores[i] / num_aps[i]
	    if num_aps[i] < max_aps*percent_aps :
	      scores_[i] = float("inf")
	  id_best_pose = scores_.index(min(scores_))    
	  
	  
	  print 'scores ', scores_ 
	  #print 'locs ', locs 
	  print 'num_aps ', num_aps
	  #print id_best_pose,locs[id_best_pose],scores[id_best_pose], num_aps[id_best_pose], max_aps
	  return id_best_pose, locs[id_best_pose], scores_[id_best_pose], num_aps[id_best_pose]
	  
	def wifiDataCB(self, data):
	  
	  for obj in data.HotSpots:
	    if obj.address in self.temp_data.keys() :
	      ap = self.temp_data[obj.address]
	      sum_sl = ap['sum_sl'] + obj.signal
	      num_samples = ap['num_samples'] + 1
	      self.temp_data[obj.address] = {'sum_sl': sum_sl, 'num_samples': num_samples}
	    else:
	      num_samples = 1
	      self.temp_data[obj.address] = {'sum_sl': obj.signal, 'num_samples': num_samples}
	      
	  self.num_scans += 1    
	  
	  if self.num_scans >= max_scans :
	    self.computePose()
	  
	def manageBestPoses(self, locs, scores, num_aps):
	  print '------'
	  #manage poses
	  for i in range(nbest_poses) :
	    ii, loc, min_scores,naps = self.findBestPose(copy.copy(locs), copy.copy(scores), copy.copy(num_aps)) # deep copy, pass-by-value
	    print loc, min_scores, naps
	    if i == 1 :
	      self.SetWifiPose(loc)
	      
	    #removes the actual pose to allow finding a next best pose
	    locs.pop(ii)
	    scores.pop(ii)
	    num_aps.pop(ii)
	    
	    
	    
	    self.id += 1
	    self.id = self.id % window_size*nbest_poses
	    self.window.append(self.wifi_pose.pose)
	    
	  # makes the list circular, removien the oldest nbest_poses 	  
	  if len(self.window) == window_size*nbest_poses :
	    for i in range(nbest_poses) :
	      self.window.pop(0)
	    
	  self.wifi_pose_window.header = self.wifi_pose.header
	  pose = self.computePoseWindow()
	  self.wifi_pose_window.pose = pose
	  
	  self.pub_loc.publish(self.wifi_pose)
	  self.pub_loc_window.publish(self.wifi_pose_window)
	  
	  
	  
	def computePose(self):  

	  scores = []
	  locs = []
	  num_aps = []
	  for fp in self.collection.find({}): # fingerprints in collection
	    #print '--------------------'
	    #print fp['loc']
	    eu_dist = 0
	    count_aps = 0
	    for key in fp['data'].keys():
	      #print fp['data']	      
	      if key in self.temp_data.keys() :
		ap_scan = self.temp_data[key]	      
		mean_sl = ap_scan['sum_sl'] / ap_scan['num_samples']
		ap_data = fp['data'][key]		
		#print obj.address, ap_data['num_samples']
		eu_dist += (mean_sl - ap_data['mean'])**2
		count_aps += 1
		  
	    eu_dist = np.sqrt(eu_dist)
	    
	    locs.append(fp['loc'])
	    scores.append(eu_dist)
	    num_aps.append(count_aps)

	  self.temp_data	= {}
	  self.num_scans	= 0 
	  
	  self.manageBestPoses(locs, scores, num_aps)

	  
	def __init__(self):		
		self.conn       = Connection('localhost', 27017)
		self.db   	= self.conn["wifi_data"]
		self.collection	= self.db["wifi_map"]
		
		self.temp_data	= {}
		self.num_scans	= 0
		
		self.wifi_pose	= PoseStamped()
		self.id 	= 0
		self.window	= []
		self.wifi_pose_window = PoseStamped()
		
		rospy.Subscriber('wifi_data', WifiData, self.wifiDataCB)
		
		self.pub_loc = rospy.Publisher('wifi_pose', PoseStamped, queue_size=10)
		self.pub_loc_window = rospy.Publisher('wifi_pose_window', PoseStamped, queue_size=10)
if __name__=='__main__':
	rospy.init_node('wifi_loc')
	try:
	  r = rospy.Rate(1)
	  loc_node = WifiLocNode()
	  while not rospy.is_shutdown():
	    r.sleep()
	except rospy.ROSInterruptException: pass
	
