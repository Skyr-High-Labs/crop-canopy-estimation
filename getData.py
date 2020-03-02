import ee
import numpy as np
import pickle
import reader

def LatLonImgNDVI(img, area):
    img = ee.Image(img)
    img = img.addBands(img.normalizedDifference(['B8', 'B4']).rename(["ndvi"]))
    img = img.addBands(ee.Image.pixelLonLat())

    reduced = img.reduceRegion(reducer=ee.Reducer.toList(),
        geometry=area,
        maxPixels=1e13,
        scale=10)

    return ee.List([
        ee.Date(img.get('system:time_start')), 
        reduced.get("latitude"), 
        reduced.get("longitude"), 
        reduced.get("QA60"), 
        reduced.get("ndvi")])

def LatLonImgSAR(img, area):
    img = ee.Image(img)
    img = img.addBands(ee.Image.pixelLonLat())

    reduced = img.reduceRegion(reducer=ee.Reducer.toList(),
        geometry=area,
        maxPixels=1e13,
        scale=10)

    return ee.List([
        ee.Date(img.get('system:time_start')), 
        reduced.get("latitude"),
        reduced.get("longitude"),
        reduced.get("VH"),
        reduced.get("VV")])

def downloadYear(year):
    areas = [array for array in reader.parseKML(year + "_polygons.kml")]

    def AreaQuery(array):
        area = ee.Geometry.Polygon(array)

        def NDVIQuery():
            NDVICollection = ee.ImageCollection("COPERNICUS/S2").filterBounds(area) \
                .filterDate(year + "-05-01", year + "-09-30") \
                .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 100) \
                .select(['B8', 'B4', 'QA60']) \
                .sort('date')

            NDVIImages = NDVICollection.toList(100000)
            NDVIData = NDVIImages.map(lambda image : LatLonImgNDVI(image, area))
            return NDVIData

        def SARQuery(orbit):
            SARCollection = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(area) \
                .filterDate(year + "-05-01", year + "-09-30") \
                .filterMetadata("orbitProperties_pass", "equals", orbit) \
                .select(['VH', 'VV']) \
                .sort('date')
            
            SARImages = SARCollection.toList(100000)
            SARData = SARImages.map(lambda image : LatLonImgSAR(image, area))
            return SARData
        
        AreaData = ee.List([NDVIQuery(), SARQuery("ASCENDING"), SARQuery("DESCENDING")])
        return AreaData

    CHUNK_SIZE = 10
    YearData = []
    for i in range(0,len(areas),CHUNK_SIZE):
        YearData += ee.List([AreaQuery(area) for area in areas[i:i+CHUNK_SIZE]]).getInfo()

    formatted = [{
        "ndvi" : [{
            "date"  : image[0]["value"],
            "lats"  : image[1],
            "lons"  : image[2],
            "cloud" : image[3],
            "ndvi"  : image[4]
        } for image in field[0]],
        "ascending": [{
            "date"  : image[0]["value"],
            "lats"  : image[1],
            "lons"  : image[2],
            "VH"    : image[3],
            "VV"    : image[4]
        } for image in field[1]], 
        "descending": [{
            "date"  : image[0]["value"],
            "lats"  : image[1],
            "lons"  : image[2],
            "VH"    : image[3],
            "VV"    : image[4]
        } for image in field[2]]
    } for field in YearData]

    pickle.dump(formatted, open("ee_download/" + year + "_data.pickle","wb"))

if __name__ == "__main__":
    ee.Initialize()
    for year in ["2017", "2018", "2019"]:
        downloadYear(year)