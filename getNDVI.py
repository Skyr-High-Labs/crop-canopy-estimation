from datetime import datetime

import ee

import common
import rasteriser


# perform any calculation on the image collection here
def getNDVI(img):
    ndvi = ee.Image(img.normalizedDifference(['B8', 'B4'])).rename(["ndvi"])
    # cloudBitMask = ee.Number(2).pow(10).int();
    # cirrusBitMask = ee.Number(2).pow(11).int();
    # Cloud filter
    ndvi = ndvi.where(img.select('QA60').neq(0), 0)
    return ndvi


def arrayToNDVI(array, startDate, EndDate, returnDates=False, CLOUDY_PIXEL_PERCENTAGE=10):
    ee.Initialize()

    # Define the roi
    area = ee.Geometry.Polygon(array)

    # query
    collection = ee.ImageCollection("COPERNICUS/S2").filterBounds(area) \
        .filterDate(startDate, EndDate) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", CLOUDY_PIXEL_PERCENTAGE) \
        .select(['B8', 'B4', 'QA60']) \
        .sort('system:time_start')

    size = collection.size().getInfo()
    print("Number of images: ", size)

    # map over the image collection
    myCollection = collection.map(getNDVI)

    # get all images
    l = myCollection.toList(size)
    arr = []
    LatLonImgs = ee.List([common.fastLatLonImg(ee.Image(l.get(i)), area) for i in range(size)]).getInfo()
    for i in range(size):
        arr.append((LatLonImgs[i][0], LatLonImgs[i][1], LatLonImgs[i][2], i))
    if returnDates:
        l1 = collection.toList(size)
        old_dates = ee.List(
            [ee.Date(ee.Image(l1.get(i)).get('system:time_start')).millis() for i in range(size)]).getInfo()
        dates = [datetime.utcfromtimestamp(date / 1000) for date in old_dates]
        return rasteriser.rasteriseImages(arr)[0], dates
    return rasteriser.rasteriseImages(arr)
