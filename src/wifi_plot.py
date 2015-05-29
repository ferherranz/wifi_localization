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
wifi_data 	= db["wifi_data"]   
  
def publishSignalLevel():

    
    #print "Publishing: "
    for mac_add in wifi_data.find().distinct("address"):
	#print "	", mac_add#["address"]
	
	#obj = wifi_data.find({"address": mac_add})
	essid = wifi_data.find_one({"address": mac_add})['essid']
	
	pub_ = rospy.Publisher("AP_" + essid[0:3] + "_" + mac_add.replace(":",""), MarkerArray, queue_size=10)
	markerArray = MarkerArray()
	for obj in wifi_data.find({"address": mac_add}):
	    #print "--- ", obj["address"]
	    #normalizing the sl
	    sl = 100 - ((obj['sl'] - 30) * 1.4) #convert the scale [30, 100] to [0, 100]. also invert the scale
	    
	    x = obj['loc'][0]
	    y = obj['loc'][1]
	    
	    marker = Marker()
	    marker.header.frame_id = "/map"
	    marker.type = marker.CUBE
	    marker.action = marker.ADD
	    marker.scale.x = 0.1
	    marker.scale.y = 0.1
	    marker.scale.z = 0.1
	    marker.color.a = 1.0
	    
	    gray = ((sl / 100.0) - 0.5)*2.0

	    marker.color.r = red(gray)
	    marker.color.g = green(gray)
	    marker.color.b = blue(gray)
	    #print sl, gray, marker.color.r, marker.color.g, marker.color.b
	    marker.pose.orientation.w = 1.0
		
	    marker.pose.position.x = x
	    marker.pose.position.y = y
	    
	    marker.pose.position.z = (sl / 100.0)*10.0
	    #print marker.pose.position.z 
	    markerArray.markers.append(marker)	    
	#end for      
	id = 0
	for m in markerArray.markers:
	    m.lifetime = rospy.Duration(1.0)
	    m.id = id
	    id += 1     
	#end for
	pub_.publish(markerArray)  
    #end for
   
	
if __name__ == '__main__':
	rospy.init_node('wifi_plot')
	try:
	  rate = rospy.Rate(10) # 0.5hz
	  while not rospy.is_shutdown():
	    publishSignalLevel()
	    rate.sleep()
	    
	except rospy.ROSInterruptException: pass
	
