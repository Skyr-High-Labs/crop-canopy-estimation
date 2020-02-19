from bs4 import BeautifulSoup
import getNDVI
import getSAR
import common
import numpy as np
import ee
import getPair
from datetime import datetime
import disp_multiple_images
import model


# Trigger the authentication flow.
#ee.Authenticate()

# Initialize the library.
ee.Initialize()

def parseKML(inputfile):
  with open(inputfile, "r") as f:
    soup = BeautifulSoup(f, features="html.parser")
    return [np.array([i.split(",")[0:2] for i in node.string.split()]).astype(np.float).tolist()\
            for node in soup.findAll("coordinates")]

if __name__ == "__main__":
  for array in parseKML("2017_polygons.kml"):
    startDate, EndDate = "2017-01-01","2017-02-01"    
    data, _ = getPair.arrayToPairs(array, startDate, EndDate, False, 0.5)
    
    px_pairs = None
    for i in range(0, len(data), 3):
        # NDVI, SAR
        tmp = np.dstack((data[i][0], data[i+1][0], data[i+2][0]))
        tmp = tmp.reshape(-1, tmp.shape[-1])
        tmp = tmp[np.all(tmp != 0, axis=1)]
        px_pairs = np.concatenate((px_pairs, tmp), axis = 0) if not px_pairs is None else tmp
    
    print(px_pairs)
    # px_pairs is now pixel-pairs for a given field over a given time span
    ndvi = px_pairs[:,0]
    vv = px_pairs[:,1]
    vh = px_pairs[:,2]
    nrpd = (vh-vv)/(vh+vv)

    X = np.stack([vv,vh,nrpd], axis=1)
    y = ndvi
    print(X,y)

    model.train_and_test(X,y)


    break