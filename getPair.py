from datetime import datetime, timedelta

import ee

import common
import getNDVI
import rasteriser


def LatLonImgVHVV(img, area):
    img = img.addBands(ee.Image.pixelLonLat())

    img = img.reduceRegion(reducer=ee.Reducer.toList(), \
                           geometry=area, \
                           maxPixels=1e13, \
                           scale=10)

    return ee.List([ee.Array(img.get("latitude")),
                    ee.Array(img.get("longitude")), ee.Array(img.get("VH")), ee.Array(img.get("VV"))])


def getDates(orig_list, size, process=True):
    old_dates = [ee.Date(ee.Image(orig_list.get(i)).get('system:time_start')) for i in range(size)]
    if not process:
        return old_dates
    old_dates2 = ee.List([date.millis() for date in old_dates]).getInfo()
    dates = [datetime.utcfromtimestamp(date / 1000) for date in old_dates2]
    return dates


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

    NDVI_size = collection_NDVI.size().getInfo()
    l_NDVI = collection_NDVI.toList(NDVI_size)
    l_NDVI_dates = getDates(l_NDVI, NDVI_size, process=False)

    # use NDVI dates to make date-filter for SAR data, taking into account
    valid_dates = None
    for i_NDVI in range(NDVI_size):
        NDVI_date = l_NDVI_dates[i_NDVI]
        if not valid_dates:
            valid_dates = ee.Filter.date(NDVI_date.advance(-delta, 'day'), NDVI_date.advance(delta, 'day'))
        else:
            valid_dates = ee.Filter.Or(valid_dates, ee.Filter.date(NDVI_date.advance(-delta, 'day'),
                                                                   NDVI_date.advance(delta, 'day')))

    if (not valid_dates):
        raise ValueError("no valid dates for the image")

    collection_SAR = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(area) \
        .filter(valid_dates) \
        .select(['VH', 'VV'])

    SAR_size = collection_SAR.size().getInfo()
    l_SAR = collection_SAR.toList(SAR_size)
    l_SAR_dates = getDates(l_SAR, SAR_size)
    l_NDVI_dates = getDates(l_NDVI, NDVI_size)

    # map collections to their respective special data formats
    collection_NDVI = collection_NDVI.map(getNDVI.getNDVI)
    l_NDVI = collection_NDVI.toList(NDVI_size)
    # NDVI-[SAR] list
    pairs_i = {}
    for i_SAR in range(SAR_size):
        SAR_date = l_SAR_dates[i_SAR]
        for i_NDVI in range(NDVI_size):
            NDVI_date = l_NDVI_dates[i_NDVI]
            if abs(SAR_date - NDVI_date) <= timedelta(days=delta):
                if i_NDVI not in pairs_i:
                    pairs_i[i_NDVI] = [i_SAR]
                else:
                    pairs_i[i_NDVI].append(i_SAR)

    sorted_pairs = sorted(pairs_i)
    print(pairs_i)
    arr = []
    precomputed_SAR = dict()
    LatLonImgsNDVI = ee.List(
        [common.fastLatLonImg(ee.Image(l_NDVI.get(NDVI)), area) for NDVI in sorted_pairs])
    LatLonImgsSAR = ee.List([LatLonImgVHVV(ee.Image(l_SAR.get(SAR)), area) for SAR in range(SAR_size)])
    both_lists = ee.List([LatLonImgsNDVI, LatLonImgsSAR]).getInfo()
    LatLonImgsNDVI = both_lists[0]
    LatLonImgsSAR = both_lists[1]

    for NDVI in range(len(LatLonImgsNDVI)):
        i = sorted_pairs[NDVI]
        for SAR in pairs_i[i]:
            ndvi_temp = (LatLonImgsNDVI[NDVI][0], LatLonImgsNDVI[NDVI][1], LatLonImgsNDVI[NDVI][2])
            if SAR not in precomputed_SAR:
                lats = LatLonImgsSAR[SAR][0]
                lons = LatLonImgsSAR[SAR][1]
                vh = LatLonImgsSAR[SAR][2]
                vv = LatLonImgsSAR[SAR][3]
                precomputed_SAR[SAR] = []
                precomputed_SAR[SAR].append((lats, lons, vh) + (f'SAR (VH) {l_SAR_dates[SAR]:%B %d, %Y}',))
                precomputed_SAR[SAR].append((lats, lons, vv) + (f'SAR (VV) {l_SAR_dates[SAR]:%B %d, %Y}',))
            arr.append(ndvi_temp + (f'NDVI {l_NDVI_dates[NDVI]:%B %d, %Y}',))
            arr.extend(precomputed_SAR[SAR])

    return rasteriser.rasteriseImages(arr)


if __name__ == "__main__":
    import reader

    for array in reader.parseKML("2017_polygons.kml"):
        p = arrayToPairs(array, "2017-05-01", "2017-09-30")
        common.plot(p[0])
