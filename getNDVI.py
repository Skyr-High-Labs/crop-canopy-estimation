import ee
import numpy as np
import matplotlib.pyplot as plt
import cv2
 
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

# rotate point cloud
def rotateByDeg(latDeg, lonDeg, latRot, lonRot):
    lat = np.radians(latDeg)
    lon = np.radians(lonDeg)
    latRot = np.radians(latRot)
    lonRot = np.radians(lonRot)
    x = np.cos(lon)*np.cos(lat)
    y = np.sin(lon)*np.cos(lat)
    z = np.sin(lat)
    Rz = np.array((
        ( np.cos(lonRot),np.sin(lonRot)),
        (-np.sin(lonRot),np.cos(lonRot)) ))
    Ry = np.array((
        ( np.cos(latRot),np.sin(latRot)),
        (-np.sin(latRot),np.cos(latRot)) ))
    x,y = Rz @ (x,y)
    x,z = Ry @ (x,z)
    lat = np.arcsin(z)
    lon = np.arctan2(y,x)
    return np.degrees(lat), np.degrees(lon)

# covert the lat, lon and array into an image
def toImage(lat,lon,data):
 
    # rotate coordinates to origin
    lat, lon = rotateByDeg(lat, lon, np.mean(lat), np.mean(lon))

    # get range
    minLat = np.min(lat)
    maxLat = np.max(lat)
    minLon = np.min(lon)
    maxLon = np.max(lon)

    scale = 10/(6371000*np.pi/180) #10m in degrees : 10m / degree arc length -> earth radius * pi / 180 degrees 
    imageSize = ((maxLat-minLat)/scale,(maxLon-minLon)/scale)
    imageSize = np.int_(np.floor(imageSize)+1)

    def coordToPixel(lat, lon):
        return tuple(np.int_(np.floor(((lat - minLat)/scale, (lon - minLon)/scale))))

    image = np.zeros(imageSize)
    imageSampled = np.zeros(imageSize)

    # rasterise point cloud
    for i in range(0, len(data)):
        px = coordToPixel(lat[i], lon[i])
        alpha = imageSampled[px] / (imageSampled[px]+1)
        imageSampled[px] += imageSampled[px] + 1
        image[px] = alpha*image[px] + (1-alpha)*data[i]

    # get mask for geometry and inpaint undersampled pixels
    kernel = np.ones((5,5), np.uint8)
    roiMask = cv2.erode(cv2.dilate(np.uint8(imageSampled>0), kernel), kernel)
    inpainted = cv2.inpaint(np.float32(image),np.uint8(imageSampled==0),3,cv2.INPAINT_NS)
    image = inpainted*roiMask

    return image

def exportImage(img, area):
    lat, lon, data = LatLonImg(img, area)
    return toImage(lat,lon,data)

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
            arr.append(exportImage(ee.Image(l.get(i)), area))
        except:
            pass
    return arr

def plotNDVI(images):
    for im in images:
        print(im)
        plt.imshow(im)
        plt.show()