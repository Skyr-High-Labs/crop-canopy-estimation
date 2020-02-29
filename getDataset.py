import numpy as np
import ee

from pixelPairs import pixelPairs
from reader import parseKML


def getDataset():
    Xs = []
    ys = []
    for year in ["2017", "2018", "2019"]:
        counter = 0
        fields = parseKML(year + "_polygons.kml")
        total = str(len(fields))
        for array in fields:
            try:
                X, y = pixelPairs(array, year + "-05-01", year + "-09-30", CLOUDY_PIXEL_PERCENTAGE=100)
                Xs.append(X)
                ys.append(y)
                # print([np.concatenate(Xs), np.concatenate(ys)])
            except ee.ee_exception.EEException as e:
                # TODO: fix exception (exception is related to some empty ee.Array)
                print(e)
                print("Exception occurred, skipping")
            print(year + ": " + str(counter) + "/" + total)
            counter += 1

    return np.concatenate(Xs), np.concatenate(ys)


if __name__ == "__main__":
    X, y = getDataset()
    np.save("datasetSAR.npy", X)
    np.save("datasetNDVI.npy", y)
