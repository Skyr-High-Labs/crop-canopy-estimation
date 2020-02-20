import numpy as np

from pixelPairs import pixelPairs
from reader import parseKML


def getDataset():
    Xs = []
    ys = []
    for year in ["2017", "2018", "2019"]:
        counter = 0
        for array in parseKML(year + "_polygons.kml"):
            X, y = pixelPairs(array, year + "-05-01", year + "-09-30")
            Xs.append(X)
            ys.append(y)
            # print([np.concatenate(Xs), np.concatenate(ys)])
            print(year + ": " + str(counter))
            counter += 1
    return np.concatenate(Xs), np.concatenate(ys)


if __name__ == "__main__":
    X, y = getDataset()
    np.save("datasetX.npy", X)
    np.save("datasety.npy", y)
