import pickle
import numpy as np
import random
from multiprocessing import Pool
from rasteriser import rasteriseImages

def rasteriseField(field):
        #Build array with all images to rasterise
        toRasterise = []
        toRasterise += [[image["lats"], image["lons"], image["ndvi"], ["ndvi",image["date"]]] for image in field["ndvi"]]
        toRasterise += [[image["lats"], image["lons"], image["cloud"], ["cloud"]] for image in field["ndvi"]]
        toRasterise += [[image["lats"], image["lons"], image["VH"], ["avh",image["date"]]] for image in field["ascending"]]
        toRasterise += [[image["lats"], image["lons"], image["VV"], ["avv"]] for image in field["ascending"]]
        toRasterise += [[image["lats"], image["lons"], image["VH"], ["dvh",image["date"]]] for image in field["descending"]]
        toRasterise += [[image["lats"], image["lons"], image["VV"], ["dvv"]] for image in field["descending"]]

        #Rasterise images
        rasterised, _ = rasteriseImages(toRasterise)

        #Separate by type
        ndvi  = list(filter(lambda image : image[1][0] == "ndvi",  rasterised))
        cloud = list(filter(lambda image : image[1][0] == "cloud", rasterised))
        avh   = list(filter(lambda image : image[1][0] == "avh",   rasterised))
        avv   = list(filter(lambda image : image[1][0] == "avv",   rasterised))
        dvh   = list(filter(lambda image : image[1][0] == "dvh",   rasterised))
        dvv   = list(filter(lambda image : image[1][0] == "dvv",   rasterised))
        
        #Build formatted object
        formatted = {
            "ndvi" : [{
                "date"  : ndvi[i][1][1],
                "cloud" : cloud[i][0],
                "ndvi"  : ndvi[i][0]
            } for i in range(len(ndvi))],
            "ascending": [{
                "date"  : avh[i][1][1],
                "VH"    : avh[i][0],
                "VV"    : avv[i][0]
            } for i in range(len(avh))], 
            "descending": [{
                "date"  : dvh[i][1][1],
                "VH"    : dvh[i][0],
                "VV"    : dvv[i][0]
            } for i in range(len(dvh))]
        }

        return formatted

def getPairsFromField(field):
    testX = []
    testy = []
    trainX = np.array([]).reshape(0,6)
    trainy = []

    def getNRPD(vv, vh):
        s = vh + vv
        s += np.sign(s)*0.00001
        s += 0.000001
        return (vh - vv) / s

    for image in field["ndvi"]:
        ascending = min(field["ascending"],  key=lambda sarImage : abs(sarImage["date"]-image["date"]))
        desceding = min(field["descending"], key=lambda sarImage : abs(sarImage["date"]-image["date"]))

        if (np.all(image["cloud"] == 0) and random.random() < 0.15):
            ndvi = np.mean(image["ndvi"][np.where(image["ndvi"] > 0.25)])
            if (not ndvi > 0.25):
                continue
            testy.append(ndvi)
            testX.append([ascending["VV"],ascending["VH"],
            getNRPD(ascending["VV"],ascending["VH"]),
            desceding["VV"],desceding["VH"],
            getNRPD(desceding["VV"],desceding["VH"])])
        else:
            goodPixels = np.where(image["cloud"] == 0)
            goodPixelsMask = np.where(image["ndvi"][goodPixels] > 0.25)
            goodPixels = (goodPixels[0][goodPixelsMask], goodPixels[1][goodPixelsMask])
            trainy = np.concatenate([trainy, image["ndvi"][goodPixels]])
            trainX = np.concatenate([trainX,
                np.array([ascending["VV"][goodPixels],ascending["VH"][goodPixels],
                getNRPD(ascending["VV"][goodPixels],ascending["VH"][goodPixels]),
                desceding["VV"][goodPixels],desceding["VH"][goodPixels],
                getNRPD(desceding["VV"][goodPixels],desceding["VH"][goodPixels])]).transpose()
            ])

    return [testX, testy, trainX, trainy]

def getPairs(field):
    return getPairsFromField(rasteriseField(field))

def getAllPairs(year):
    data = pickle.load(open("ee_download/" + year + "_data.pickle", "rb"))

    #Get pairs on multiple threads
    with Pool() as p:
        pairs = p.map(getPairs, data)
    #pairs = [getPairs(field) for field in data[0:2]]

    testX = []
    testy = []
    trainX = np.array([]).reshape(0,6)
    trainy = []

    for pair in pairs:
        testX += pair[0]
        testy += pair[1]
        trainX = np.concatenate([trainX, pair[2]])
        trainy = np.concatenate([trainy, pair[3]])

    pickle.dump([trainX, trainy], open("training_data/" + year + "_data.pickle","wb"))
    pickle.dump([testX, testy], open("testing_data/" + year + "_data.pickle","wb"))


if __name__ == '__main__':
    for year in ["2018", "2019"]:
        getAllPairs(year)