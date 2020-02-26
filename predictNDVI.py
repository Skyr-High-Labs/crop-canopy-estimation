import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from joblib import load

from getSAR import arrayToSAR


def getFieldData(array, startDate, endDate):
    # data is a list where the even elements are a list of VVs for a field
    # and the odd ones are a list of VH. Each VV is followed by a VH of the
    # same field.
    data, dates = arrayToSAR(array, startDate, endDate, returnDates=True)
    Xs = []
    for i in range(0, len(data), 2):
        # Make pairs of VV and VH for each picture
        px_pairs = np.dstack((data[i][0], data[i + 1][0]))

        # Reshape array so it has two columns and any number of rows
        px_pairs = px_pairs.reshape(-1, px_pairs.shape[-1])

        # Eliminate pairs where any element is zero
        px_pairs = px_pairs[np.all(px_pairs != 0, axis=1)]

        vv = px_pairs[:, 0]
        vh = px_pairs[:, 1]
        nrpd = (vh - vv) / (vh + vv)
        Xs.append(np.stack([vv, vh, nrpd], axis=1))

    return dates, Xs


def predictNDVI(array, startDate, endDate, model="model_1582670452"):
    reg = load(model)
    dates, SARs = getFieldData(array, startDate, endDate)

    # dates are unordered, so we sort them. We also predict the NDVI and compute
    # the average for each picture
    zip_dates_SARs = sorted(zip(dates, [np.average(reg.predict(SAR)) for SAR in SARs]))
    unzip = list(zip(*zip_dates_SARs))

    # return list of dates and list of predicted values
    return unzip[0], unzip[1]


def plotPredictedNDVI(dates, NDVI):
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.plot(dates, NDVI)
    plt.gcf().autofmt_xdate()
    plt.show()


if __name__ == "__main__":
    from reader import parseKML

    for array in parseKML("2019_polygons.kml"):
        plotPredictedNDVI(*predictNDVI(array, "2019-05-01", "2019-09-30"))
