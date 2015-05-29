#!/usr/bin/env python

import roslib; 
import rospy, os, re

from geometry_msgs.msg import *
from visualization_msgs.msg import *
from pymongo import *


# jet color funtions using a -1 to 1 grayscale
def interpolate( val, y0, x0, y1, x1 ):
    return (val-x0)*(y1-y0)/(x1-x0) + y0

def base( val ):
    if val <= -0.75:
      return 0
    elif val <= -0.25:
      return interpolate( val, 0.0, -0.75, 1.0, -0.25 )
    elif val <= 0.25:
      return 1.0
    elif val <= 0.75:
      return interpolate( val, 1.0, 0.25, 0.0, 0.75 )
    else:
      return 0.0

def red( gray ): 
    return base( gray - 0.5 )

def green( gray ):
    return base( gray )

def blue( gray ):
    return base( gray + 0.5 )


conn    	= Connection('localhost', 27017)
db   		= conn["wifi_data"]
wifi_data 	= db["wifi_map"]   
  
def publishMap():

    pub_ = rospy.Publisher("wifi_map", MarkerArray, queue_size=10)
    markerArray = MarkerArray()
    #print "Publishing: "
    for obj in wifi_data.find() :
    
	num_aps = len(obj['data'])
	box_size = obj['box_size']
    
	marker = Marker()
	marker.header.frame_id = "/map"
	marker.type = marker.CUBE
	marker.action = marker.ADD
	marker.scale.x = 0.1
	marker.scale.y = 0.1
	marker.scale.z = 0.1
	marker.color.a = 1.0
	
	gray = ((num_aps / 30.0) - 0.5)*2.0
	#print num_aps, gray

	marker.color.r = red(gray)
	marker.color.g = green(gray)
	marker.color.b = blue(gray)
	
	marker.pose.orientation.w = 1.0
	    
	marker.pose.position.x = obj['loc'][0]
	marker.pose.position.y = obj['loc'][1]
	
	marker.pose.position.z = num_aps / 5.0
	
	markerArray.markers.append(marker)	
	
	#box
	box = Marker()
	box.header.frame_id = "/map"
	box.type = box.CUBE
	box.action = box.ADD
	box.scale.x = box_size
	box.scale.y = box_size
	box.scale.z = 0.1
	box.color.a = 0.2
	
	#print num_aps, gray

	box.color.r = 1.0
	box.color.g = 1.0
	box.color.b = 1.0
	
	box.pose.orientation.w = 1.0
	    
	box.pose.position.x = obj['loc'][0]
	box.pose.position.y = obj['loc'][1]
	
	box.pose.position.z = 0.0
	
	markerArray.markers.append(box)
	
    #end for      
    id = 0
    for m in markerArray.markers:
	m.lifetime = rospy.Duration(1.0)
	m.id = id
	id += 1     
    #end for
    pub_.publish(markerArray)  
    
   
	
if __name__ == '__main__':
	rospy.init_node('wifi_plot')
	try:
	  rate = rospy.Rate(10) # 0.5hz
	  while not rospy.is_shutdown():
	    publishMap()
	    rate.sleep()
	    
	except rospy.ROSInterruptException: pass
	
