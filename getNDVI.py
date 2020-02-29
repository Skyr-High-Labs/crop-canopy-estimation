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

    print("Number of images: ", collection.size().getInfo())

    # map over the image collection
    myCollection = collection.map(getNDVI)

    # get all images
    l = myCollection.toList(collection.size().getInfo())
    arr = []
    if returnDates:
        dates = []
        l1 = collection.toList(collection.size().getInfo())
    for i in range(l.size().getInfo()):
        try:
            arr.append(common.LatLonImg(ee.Image(l.get(i)), area) + (i,))
            if returnDates:
                dates.append(datetime.utcfromtimestamp(
                    ee.Date(ee.Image(l1.get(i)).get('system:time_start')).millis().getInfo() / 1000))
        except ee.ee_exception.EEException:
            pass
    if returnDates:
        return rasteriser.rasteriseImages(arr)[0], dates
    return rasteriser.rasteriseImages(arr)
