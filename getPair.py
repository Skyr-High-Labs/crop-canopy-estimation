from datetime import datetime, timedelta

import ee
import numpy as np
import common
import getNDVI
import rasteriser

def LatLonImgVHVV(img, area):
    img = img.addBands(ee.Image.pixelLonLat())

    img = img.reduceRegion(reducer=ee.Reducer.toList(), \
                           geometry=area, \
                           maxPixels=1e13, \
                           scale=10)

    vh = np.array((ee.Array(img.get("VH")).getInfo()))
    vv = np.array((ee.Array(img.get("VV")).getInfo()))
    lats = np.array((ee.Array(img.get("latitude")).getInfo()))
    lons = np.array((ee.Array(img.get("longitude")).getInfo()))
    return lats, lons, (vh, vv)

def makeNumDateTuple(orig_list):
    new_list = []
    list_size = 0
    try:
        list_size = orig_list.size().getInfo()
    except ee.ee_exception.EEException:
        return new_list

    for i in range(list_size):
        try:
            date = ee.Date(ee.Image(orig_list.get(i)).get('system:time_start'))
            new_list.append((i, date))  # num, date pair .format('Y-M-d').getInfo()
        except ee.ee_exception.EEException:
            pass
    return new_list


# delta (>=0) is the day-distance to allow between pairs
# 0 means that the timestamps need to match exactly
def arrayToPairs(array, startDate, EndDate, delta=1, CLOUDY_PIXEL_PERCENTAGE=10):
    ee.Initialize()
    area = ee.Geometry.Polygon(array)

    # query
    collection_NDVI = ee.ImageCollection("COPERNICUS/S2").filterBounds(area) \
        .filterDate(startDate, EndDate) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", CLOUDY_PIXEL_PERCENTAGE) \
        .select(['B8', 'B4', 'QA60']) \
        .sort('date')

    l_NDVI = collection_NDVI.toList(collection_NDVI.size().getInfo())
    l_NDVI_dates = makeNumDateTuple(l_NDVI)

    # use NDVI dates to make date-filter for SAR data, taking into account
    valid_dates = None
    for i_NDVI in l_NDVI_dates:
        if not valid_dates:
            valid_dates = ee.Filter.date(i_NDVI[1].advance(-delta, 'day'), i_NDVI[1].advance(delta, 'day'))
        else:
            valid_dates = ee.Filter.Or(valid_dates, ee.Filter.date(i_NDVI[1].advance(-delta, 'day'),
                                                                   i_NDVI[1].advance(delta, 'day')))

    if (not valid_dates):
        raise ValueError("no valid dates for the image")

    collection_SAR = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(area) \
        .filter(valid_dates) \
        .select(['VH', 'VV'])

    l_SAR = collection_SAR.toList(collection_SAR.size().getInfo())
    l_SAR_dates = makeNumDateTuple(l_SAR)

    # convert to standard datetime objects
    l_NDVI_dates = [(x[0], datetime.utcfromtimestamp(x[1].millis().getInfo() / 1000)) for x in l_NDVI_dates]
    l_SAR_dates = [(x[0], datetime.utcfromtimestamp(x[1].millis().getInfo() / 1000)) for x in l_SAR_dates]

    # map collections to their respective special data formats
    collection_NDVI = collection_NDVI.map(getNDVI.getNDVI)
    l_NDVI = collection_NDVI.toList(collection_NDVI.size().getInfo())

    # NDVI-[SAR] list
    pairs_i = {}
    for i_SAR in l_SAR_dates:
        for i_NDVI in l_NDVI_dates:
            if abs((i_SAR[1] - i_NDVI[1])) <= timedelta(days=delta):
                if not (i_NDVI[0] in pairs_i):
                    pairs_i[i_NDVI[0]] = [i_SAR[0]]
                else:
                    pairs_i[i_NDVI[0]].append(i_SAR[0])

    print(pairs_i)
    arr = []
    precomputed_SAR = dict()
    for NDVI in sorted(pairs_i):
        for SAR in pairs_i[NDVI]:
            try:
                ndvi_temp = common.LatLonImg(ee.Image(l_NDVI.get(NDVI)), area)
                if SAR not in precomputed_SAR:
                    lats, lons, (vh, vv) = LatLonImgVHVV(ee.Image(l_SAR.get(SAR)), area)
                    precomputed_SAR[SAR] = []
                    precomputed_SAR[SAR].append((lats, lons, vh) + (f'SAR (VH) {l_SAR_dates[SAR][1]:%B %d, %Y}',))
                    precomputed_SAR[SAR].append((lats, lons, vv) + (f'SAR (VV) {l_SAR_dates[SAR][1]:%B %d, %Y}',))
                arr.append(ndvi_temp + (f'NDVI {l_NDVI_dates[NDVI][1]:%B %d, %Y}',))
                arr.extend(precomputed_SAR[SAR])
            except ee.ee_exception.EEException:
                pass

    return rasteriser.rasteriseImages(arr)


if __name__ == "__main__":
    import reader

    for array in reader.parseKML("2017_polygons.kml"):
        p = arrayToPairs(array, "2017-05-01", "2017-09-30")
        common.plot(p[0])
