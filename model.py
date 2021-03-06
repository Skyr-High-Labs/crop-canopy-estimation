from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
import random
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime
from joblib import dump, load
import os.path

"""
Creates a dataset of SAR-NDVI values in the following format:

Features:
 * VV(db) - log scale
 * VH(db) - log scale
 * NRPB
 * LIA

Labels:
 * NDVI

The return value is the (X, y), where
    X = [[vv_0,vh_0,nrpb_0,lia_0],...,[vv_n,vh_n,nrpb_n,lia_n]]
    y = [ndvi_0,...,ndvi_n]
"""
def make_dataset():
    # TODO: replace with data from Earth Engine
    return [[-0.5 + i/100 + random.random(), 0.0, 0.0] for i in range(100)], \
            [i/100 for i in range(100)]


def train_and_test(X, y, test_split=0.33, file_name=None):
    if file_name is None:
        file_name = "model_" + str(int(datetime.now().timestamp()))
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_split, random_state=42)
    regr = None
    if os.path.isfile(file_name):
        print(f"Loading existing file {file_name}...")
        regr = load(file_name)
    else:
        print("Training new model...")
        print("Train set size: {}".format(len(y_train)))
        print("Test set size: {}".format(len(y_test)))
             
        regr = RandomForestRegressor()
        regr.fit(X_train, y_train)
        
        print(f"Saving to {file_name}...")
        dump(regr, file_name)
        print("Done!")
    print("Scoring...")
    score = regr.score(X_test, y_test)
    print("Regression score: R^2={}".format(score))
    return regr
    #plt.scatter(regr.predict(X_test), y_test)
    #plt.plot([-1.,1.],[-1.,1.], ls="--", c="r")
    #plt.xlim(-1,1)
    #plt.ylim(-1,1)
    #plt.show()


if __name__ == '__main__':
    X = np.concatenate(np.load("2017_sar_per_field.npy", allow_pickle=True))
    y = np.concatenate(np.load("2017_ndvi_per_field.npy", allow_pickle=True))
    train_and_test(X, y)