import ee
import numpy as np
import matplotlib.pyplot as plt
import cv2
import rasteriser
import disp_multiple_images
 
# perform any calculation on the image collection here
def getNDVI(img):
    ndvi = ee.Image(img.normalizedDifference(['B8', 'B4'])).rename(["ndvi"])
    return ndvi
 
# export the latitude, longitude and data
def LatLonImg(img, area):
    img = img.rename("result")
    img = img.addBands(ee.Image.pixelLonLat())

    img = img.reduceRegion(reducer=ee.Reducer.toList(),\
                                        geometry=area,\
                                        maxPixels=1e13,\
                                        scale=10)
 
    data = np.array((ee.Array(img.get("result")).getInfo()))
    lats = np.array((ee.Array(img.get("latitude")).getInfo()))
    lons = np.array((ee.Array(img.get("longitude")).getInfo()))
    return lats, lons, data

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
            arr.append(LatLonImg(ee.Image(l.get(i)), area)+(i,))
        except:
            pass
    return rasteriser.rasteriseImages(arr)

def plotNDVI(images,roiMask):
    disp_multiple_images.show_images([im[0] for im in images], 2, [im[1] for im in images])