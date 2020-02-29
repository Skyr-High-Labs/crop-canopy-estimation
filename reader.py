import numpy as np
from bs4 import BeautifulSoup

import common


def parseKML(inputfile):
    with open(inputfile, "r") as f:
        soup = BeautifulSoup(f, features="html.parser")
        return [np.array([i.split(",")[0:2] for i in node.string.split()]).astype(np.float).tolist() \
                for node in soup.findAll("coordinates")]


if __name__ == "__main__":
    import getNDVI

    for array in parseKML("2017_polygons.kml"):
        ndvi = getNDVI.arrayToNDVI(array, "2017-05-01", "2017-09-30", returnDates=True, CLOUDY_PIXEL_PERCENTAGE=100)
        for i in ndvi[1]:
            print(i, end=' ')
        print()
        common.plot(ndvi[0])
