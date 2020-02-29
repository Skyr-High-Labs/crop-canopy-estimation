from datetime import datetime

import ee

import rasteriser
from getPair import LatLonImgVHVV


# perform any calculation on the image collection here
def getSAR(img):
    sar = ee.Image(img.select('VH', 'VV'))
    return sar


def arrayToSAR(array, startDate, EndDate, returnDates=False):
    ee.Initialize()

    # Define the roi
    area = ee.Geometry.Polygon(array)

    # query
    collection = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(area) \
        .filterDate(startDate, EndDate) \
        .select(['VH', 'VV'])

    size = collection.size().getInfo()
    print("Number of images: ", size)

    # map over the image collection
    myCollection = collection.map(getSAR)

    # get all images
    l = myCollection.toList(size)
    arr = []
    LatLonImgsSAR = ee.List([LatLonImgVHVV(ee.Image(l.get(i)), area) for i in range(size)]).getInfo()
    for i in range(size):
        lats = LatLonImgsSAR[i][0]
        lons = LatLonImgsSAR[i][1]
        vh = LatLonImgsSAR[i][2]
        vv = LatLonImgsSAR[i][3]
        arr.append((lats, lons, vh) + (i,))
        arr.append((lats, lons, vv) + (i,))
    if returnDates:
        l1 = collection.toList(size)
        old_dates = ee.List(
            [ee.Date(ee.Image(l1.get(i)).get('system:time_start')).millis() for i in range(size)]).getInfo()
        dates = [datetime.utcfromtimestamp(date / 1000) for date in old_dates]
        return rasteriser.rasteriseImages(arr)[0], dates
    return rasteriser.rasteriseImages(arr)
