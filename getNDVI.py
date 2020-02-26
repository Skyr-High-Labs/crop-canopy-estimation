import ee
import numpy as np
import matplotlib.pyplot as plt
import cv2
import rasteriser
import disp_multiple_images
import common 
from datetime import datetime

# perform any calculation on the image collection here
def getNDVI(img):
    ndvi = ee.Image(img.normalizedDifference(['B8', 'B4'])).rename("ndvi")
    return ndvi
 
def arrayToNDVI(array, startDate, EndDate,returnDates=False):
    ee.Initialize()
    
    # Define the roi
    area = ee.Geometry.Polygon(array)
    
    # query
    collection = ee.ImageCollection("COPERNICUS/S2").filterBounds(area)\
                                        .filterDate(startDate, EndDate)\
                                        .select(['B8', 'B4'])
    
    print("Number of images: ",collection.size().getInfo())

    # map over the image collection
    myCollection  = collection #collection.map(getNDVI)

    # get all images
    l = myCollection.toList(collection.size().getInfo())
    arr = []
    dates = []
    for i in range(l.size().getInfo()):
        try:
            img = ee.Image(l.get(i))
            arr.append(common.LatLonImg(ee.Image(img.normalizedDifference(['B8', 'B4']).rename("ndvi")), area)+(i,))
            if returnDates:
                dates.append(datetime.utcfromtimestamp(ee.Date(img.get('system:time_start')).millis().getInfo() / 1000))
        except ee.ee_exception.EEException:
            pass

    if returnDates:
        return rasteriser.rasteriseImages(arr)[0], dates
    return rasteriser.rasteriseImages(arr)

