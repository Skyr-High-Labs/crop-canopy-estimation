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

    print("Number of images: ", collection.size().getInfo())

    # map over the image collection
    myCollection = collection.map(getSAR)

    # get all images
    l = myCollection.toList(min(40, collection.size().getInfo()))

    arr = []
    dates = []
    for i in range(l.size().getInfo()):
        try:
            img = ee.Image(l.get(i))
            lats, lons, (vh, vv) = LatLonImgVHVV(img, area)
            arr.append((lats, lons, vh) + (i,))
            arr.append((lats, lons, vv) + (i,))
            if returnDates:
                dates.append(datetime.utcfromtimestamp(
                    ee.Date(img.get('system:time_start')).millis().getInfo() / 1000))
        except ee.ee_exception.EEException:
            pass
    if returnDates:
        return rasteriser.rasteriseImages(arr)[0], dates
    return rasteriser.rasteriseImages(arr)
