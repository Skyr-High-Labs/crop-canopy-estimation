import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from joblib import load

from getNDVI import arrayToNDVI
from getSAR import arrayToSAR


def getFieldSAR(array, startDate, endDate):
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


def getFieldNDVI(array, startDate, endDate, CLOUDY_PIXEL_PERCENTAGE=10):
    data, dates = arrayToNDVI(array, startDate, endDate, returnDates=True,
                              CLOUDY_PIXEL_PERCENTAGE=CLOUDY_PIXEL_PERCENTAGE)
    ys = []
    new_dates = []
    for i in range(0, len(data)):
        px_pairs = data[i][0]

        # put all data in a row
        px_pairs = px_pairs.reshape(1, -1)

        # Eliminate pairs where any element is zero
        px_pairs = px_pairs[px_pairs != 0]

        if px_pairs.size != 0:
            ys.append(np.average(px_pairs))
            new_dates.append(dates[i])

    return new_dates, ys


def predictNDVI(array, startDate, endDate, model="model_1582670452"):
    reg = load(model)
    dates, SARs = getFieldSAR(array, startDate, endDate)

    # dates are unordered, so we sort them. We also predict the NDVI and compute
    # the average for each picture
    zip_dates_SARs = sorted(zip(dates, [np.average(reg.predict(SAR)) for SAR in SARs]))
    unzip = list(zip(*zip_dates_SARs))

    # return list of dates and list of predicted values
    return unzip[0], unzip[1]


def realNDVI(array, startDate, endDate, CLOUDY_PIXEL_PERCENTAGE=10):
    dates, NDVIs = getFieldNDVI(array, startDate, endDate, CLOUDY_PIXEL_PERCENTAGE=CLOUDY_PIXEL_PERCENTAGE)

    # dates are unordered, so we sort them.
    zip_dates_NDVIs = sorted(zip(dates, NDVIs))
    unzip = list(zip(*zip_dates_NDVIs))

    # return list of dates and list of predicted values
    return unzip[0], unzip[1]


def plotNDVI(dates_NDVI):
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    for dates, NDVI in dates_NDVI:
        plt.plot(dates, NDVI)
    plt.gcf().autofmt_xdate()
    plt.show()


if __name__ == "__main__":
    from reader import parseKML

    for array in parseKML("2019_polygons.kml"):
        plotNDVI([realNDVI(array, "2019-05-01", "2019-09-30", CLOUDY_PIXEL_PERCENTAGE=10),
                  predictNDVI(array, "2019-05-01", "2019-09-30")])
