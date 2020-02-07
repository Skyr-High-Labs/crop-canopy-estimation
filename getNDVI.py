import ee
import numpy as np
import matplotlib.pyplot as plt
import cv2
import rasteriser
import disp_multiple_images
import common 

# perform any calculation on the image collection here
def getNDVI(img):
    ndvi = ee.Image(img.normalizedDifference(['B8', 'B4'])).rename(["ndvi"])
    return ndvi
 
def arrayToNDVI(array, startDate, EndDate):
    ee.Initialize()
    
    # Define the roi
    area = ee.Geometry.Polygon(array)
    
    # query
    collection = ee.ImageCollection("COPERNICUS/S2").filterBounds(area)\
                                        .filterDate(startDate, EndDate)\
                                        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE","less_than",10)\
                                        .select(['B8', 'B4'])
    
    print("Number of images: ",collection.size().getInfo())

    # map over the image collection
    myCollection  = collection.map(getNDVI)

    # get all images
    l = myCollection.toList(collection.size().getInfo())
    arr = []
    for i in range(l.size().getInfo()):
        try:
            arr.append(common.LatLonImg(ee.Image(l.get(i)), area)+(i,))
        except ee.ee_exception.EEException:
            pass
    return rasteriser.rasteriseImages(arr)

