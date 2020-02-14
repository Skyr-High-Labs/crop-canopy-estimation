from datetime import datetime, timedelta

import ee

import common
import getNDVI
import getSAR
import rasteriser


def makeNumDateTuple(orig_list):
    new_list = []
    for i in range(orig_list.size().getInfo()):
        try:
            date = ee.Date(ee.Image(orig_list.get(i)).get('system:time_start'))
            new_list.append((i, date))  # num, date pair .format('Y-M-d').getInfo()
        except ee.ee_exception.EEException:
            pass
    return new_list


# delta (>=0) is the day-distance to allow between pairs
# 0 means that the timestamps need to match exactly
# take_first; if True, then take the first found pair, else, take the last found pair for a given NDVI image
def arrayToPairs(array, startDate, EndDate, take_first=True, delta=1):
    ee.Initialize()
    area = ee.Geometry.Polygon(array)

    # query
    collection_NDVI = ee.ImageCollection("COPERNICUS/S2").filterBounds(area) \
        .filterDate(startDate, EndDate) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 10) \
        .select(['B8', 'B4']) \
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
    collection_SAR = collection_SAR.map(getSAR.getSAR)
    l_SAR = collection_SAR.toList(collection_SAR.size().getInfo())

    # print("NDVI dates: ")
    # print([x[1].strftime("%b %d %Y") for x in l_NDVI_dates])
    # print("SAR dates: ")
    # print([x[1].strftime("%b %d %Y") for x in l_SAR_dates])

    # NDVI-[SAR] list
    pairs_i = {}
    for i_SAR in l_SAR_dates:
        for i_NDVI in l_NDVI_dates:
            if abs((i_SAR[1] - i_NDVI[1])) <= timedelta(days=delta):
                if not (i_NDVI[0] in pairs_i):
                    pairs_i[i_NDVI[0]] = [i_SAR[0]]
                else:
                    pairs_i[i_NDVI[0]].append(i_SAR[0])
                # if take_first and not (i_SAR[0] in pairs_i):
                #    pairs_i[i_SAR[0]] = i_NDVI[0]
                # elif not take_first:
                #    pairs_i[i_SAR[0]] = i_NDVI[0]

    print(pairs_i)
    arr = []
    precomputed_SAR = dict()
    for NDVI in sorted(pairs_i):
        for SAR in pairs_i[NDVI]:
            try:
                ndvi_temp = common.LatLonImg(ee.Image(l_NDVI.get(NDVI)), area)
                if SAR not in precomputed_SAR:
                    sar_temp = common.LatLonImg(ee.Image(l_SAR.get(SAR)), area)
                    precomputed_SAR[SAR] = sar_temp + (f'SAR {l_SAR_dates[SAR][1]:%B %d, %Y}',)
                arr.append(ndvi_temp + (f'NDVI {l_NDVI_dates[NDVI][1]:%B %d, %Y}',))
                arr.append(precomputed_SAR[SAR])
            except ee.ee_exception.EEException:
                pass

    return rasteriser.rasteriseImages(arr)


if __name__ == "__main__":
    import reader

    for array in reader.parseKML("2017_polygons.kml"):
        p = arrayToPairs(array, "2017-05-01", "2017-09-30")
        common.plot(p[0])
