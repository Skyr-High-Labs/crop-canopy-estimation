from bs4 import BeautifulSoup
import getNDVI
import numpy as np

def parseKML(inputfile):
  with open(inputfile, "r") as f:
    soup = BeautifulSoup(f, features="html.parser")
    return [np.array([i.split(",")[0:2] for i in node.string.split()]).astype(np.float).tolist()\
            for node in soup.findAll("coordinates")]

if __name__ == "__main__":
  for array in parseKML("2017_polygons.kml"):
    getNDVI.plotNDVI(getNDVI.arrayToNDVI(array, "2017-01-01","2018-01-01"))
