import numpy as np
from bs4 import BeautifulSoup

def parseKML(inputfile):
    with open(inputfile, "r") as f:
        soup = BeautifulSoup(f, features="html.parser")
        return [np.array([i.split(",")[0:2] for i in node.string.split()]).astype(np.float).tolist() \
                for node in soup.findAll("coordinates")]
