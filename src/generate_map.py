#!/usr/bin/env python

import roslib; roslib.load_manifest('wifi_lookup')
import rospy, os, re
from wifi_lookup.msg import WifiData, Wifi
from geometry_msgs.msg import *
from visualization_msgs.msg import *
from pymongo import *
from nav_msgs.msg import *
import time
import numpy as np



class GenMapNode():
  
  def GlobalCostMapCallback(self, gmap):      
	self.gmap = gmap  
	
  def frange(self, start, stop, step):
     i = start
     while i < stop:
         yield i
         i += step
	
  def __init__(self):
    
    self.thr_samples 	= 0
    
    self.conn    	= Connection('localhost', 27017)
    self.db   		= self.conn["wifi_data"]
    self.wifi_data 	= self.db["wifi_data"]

    self.db_map   	= self.conn["wifi_map"]
    self.wifi_map 	= self.db["wifi_map"]

    self.gmap = OccupancyGrid()
    rospy.Subscriber("/map", OccupancyGrid, self.GlobalCostMapCallback)
    
    time.sleep(1)
    
    resolution = self.gmap.info.resolution
    
    step = 2.0

    box_size = 2.0
    box_hsize = box_size/2.0 #half size
    
    for i in range(0, self.gmap.info.width, int(round(step/resolution))):
      for j in range(0, self.gmap.info.height, int(round(step/resolution))):
	
	idata = i*self.gmap.info.width + j;
	#Filter positions that are occupied or unknown
	if self.gmap.data[idata] != -1 and self.gmap.data[idata] != 100 :
	  ix = i*resolution + self.gmap.info.origin.position.x
	  jy = j*resolution + self.gmap.info.origin.position.y
	  
	  box = [[float(ix-box_hsize),float(jy-box_hsize)],
		[float(ix+box_hsize),float(jy+box_hsize)]]
	  
	  #print ix, jy, box
	  #print '-----------------', ix, jy
	  aps = {}
	  for mac_add in self.wifi_data.find().distinct("address"):
	    
	    ap_box = self.wifi_data.find({'loc' : {'$within' : {'$box' : box }} , "address": mac_add})
	    
	    #ap_data = data_box.find({"address": mac_add})
	    num_samples = ap_box.count()
	    if num_samples > self.thr_samples :
	      sls = []
	      for obj in ap_box:
		sls.append(obj['sl'])
		
	      essid = obj['essid'] 
	      mean_sl = np.mean(sls)
	      std_dev_sl = np.std(sls)
	      
	      aps[mac_add] = {'mean': mean_sl, 'std_dev': std_dev_sl, 'num_samples': num_samples}
	      #print essid, mac_add, ix, jy, mean_sl, std_dev_sl, num_samples
	  if aps:	    
	    map_data = {'data': aps, 'loc': [ix, jy] }
	    self.wifi_map.insert(map_data)
	
   
	
if __name__ == '__main__':
	rospy.init_node('generate_map')
	try:
	  
	  if not rospy.is_shutdown():
	    genmap = GenMapNode()
	    
	except rospy.ROSInterruptException: pass
	
