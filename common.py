import ee

import disp_multiple_images


# export the latitude, longitude and data
def fastLatLonImg(img, area):
    img = img.rename("result")
    img = img.addBands(ee.Image.pixelLonLat())

    img = img.reduceRegion(reducer=ee.Reducer.toList(), \
                           geometry=area, \
                           maxPixels=1e13, \
                           scale=10)
    return ee.List([img.get("latitude"), img.get("longitude"), img.get("result")])


def plot(images):
    disp_multiple_images.show_images([im[0] for im in images], 8, [im[1] for im in images])
