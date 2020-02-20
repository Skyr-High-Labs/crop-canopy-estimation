import ee

import model
from pixelPairs import pixelPairs
from reader import parseKML

if __name__ == "__main__":
    # Trigger the authentication flow.
    # ee.Authenticate()

    # Initialize the library.
    ee.Initialize()
    for array in parseKML("2017_polygons.kml"):
        X, y = pixelPairs(array, "2017-05-01", "2017-09-30")
        if len(X):
            model.train_and_test(X, y)
