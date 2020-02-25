import ee
import numpy as np
import matplotlib.pyplot as plt
import cv2
import rasteriser
import disp_multiple_images
import common
from getPair import LatLonImgVHVV
    
# perform any calculation on the image collection here
def getSAR(img):
    sar = ee.Image(img.select('VH', 'VV'))
    return sar
 
def arrayToSAR(array, startDate, EndDate):
    ee.Initialize()
    
    # Define the roi
    area = ee.Geometry.Polygon(array)
    
    # query
    collection = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(area)\
                                        .filterDate(startDate, EndDate)\
                                        .select(['VH', 'VV'])
    
    print("Number of images: ",collection.size().getInfo())

    # map over the image collection
    myCollection  = collection.map(getSAR)

    # get all images
    l = myCollection.toList(min(40,collection.size().getInfo()))

    arr = []
    for i in range(l.size().getInfo()):
        try:
            lats, lons, (vh, vv) = LatLonImgVHVV(ee.Image(l.get(i)), area)
            arr.append((lats, lons, vh)+(i,))
            arr.append((lats, lons, vv)+(i,))
        except ee.ee_exception.EEException:
            pass
    return rasteriser.rasteriseImages(arr)