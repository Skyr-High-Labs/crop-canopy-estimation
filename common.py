import ee
import numpy as np

import disp_multiple_images


# export the latitude, longitude and data
def LatLonImg(img, area):
    img = img.rename("result")
    img = img.addBands(ee.Image.pixelLonLat())

    img = img.reduceRegion(reducer=ee.Reducer.toList(), \
                           geometry=area, \
                           maxPixels=1e13, \
                           scale=10)

    data = np.array((ee.Array(img.get("result")).getInfo()))
    lats = np.array((ee.Array(img.get("latitude")).getInfo()))
    lons = np.array((ee.Array(img.get("longitude")).getInfo()))
    return lats, lons, data


def plot(images):
    disp_multiple_images.show_images([im[0] for im in images], 8, [im[1] for im in images])
