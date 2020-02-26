import matplotlib.pyplot as plt
import matplotlib.dates as dates
import model
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from joblib import load
import reader
import pixelPairs
import getSAR
import getNDVI
import xlrd
import datetime

def mean(l): return sum(l)/len(l)

def read_ground_truth(field_no):
    workbook = xlrd.open_workbook("2017-ground-cover.xlsx")
    sheet = workbook.sheet_by_index(0)


    res_date, res_ndvi = ([], [])
    for c in range(1,sheet.ncols,1):
        date_cell = sheet.cell_value(rowx=0, colx=c)
        date_tuple = xlrd.xldate_as_tuple(date_cell, workbook.datemode)
        date = datetime.datetime(*date_tuple)
        date_str = date.strftime("%m/%d/%Y")

        ndvi = sheet.cell_value(rowx=field_no+1, colx=c)
        ndvi = float(ndvi/100.0) if not ndvi=='' else 0.0

        #date_to_ndvi[date_str] = ndvi if ndvi is float else 0.0
        
        res_date.append(date_str)
        res_ndvi.append(ndvi)

    return res_date, res_ndvi

def getSARPoints(array, startDate, EndDate):
    try:
        data, _ = getSAR.arrayToSAR(array, startDate, EndDate, False, 0.5)
        px_pairs = None
        for i in range(0, len(data), 2):
            # NDVI, SAR
            tmp = np.dstack((data[i][0], data[i + 1][0]))
            tmp = tmp.reshape(-1, tmp.shape[-1])
            tmp = tmp[np.all(tmp != 0, axis=1)]
            px_pairs = np.concatenate((px_pairs, tmp), axis=0) if not px_pairs is None else tmp

        vv = px_pairs[:, 0]
        vh = px_pairs[:, 1]
        nrpd = (vh - vv) / (vh + vv)

        X = np.stack([vv, vh, nrpd], axis=1)
        y = ndvi

        return X, y
    except ValueError:
        return [], []


def read_pixel_data(field_no):
    startDate, endDate = "2017-05-01", "2017-09-30"
    
    arrays = reader.parseKML("2017_polygons.kml")
    array = arrays[field_no]
    data, dates = getSAR.arrayToSAR(array, startDate, endDate, returnDates=True)
    #ndvi_data, ndvi_dates = getNDVI.arrayToNDVI(array, startDate, endDate, returnDates=True)
    
    res_date, res_px, res_ndvi, res_ndvi_dates = ([], [], [], [])
    for i in range(0, len(data), 2):
        # SAR
        tmp = np.dstack((data[i][0], data[i + 1][0]))
        tmp = tmp.reshape(-1, tmp.shape[-1])
        tmp = tmp[np.all(tmp != 0, axis=1)]
        res_px.append(tmp)
        res_date.append(f'{(dates[i//2]):%B %d, %Y}')
        
    #for i in range(len(ndvi_data)):
    #   tmp = np.array(ndvi_data[i][0])
    #   tmp = tmp.flatten() 
    #   tmp = tmp[tmp != 0]
    #   res_ndvi.append(np.mean(tmp))
    #   res_ndvi_dates.append(f'{(ndvi_dates[i//2]):%B %d, %Y}')

    return res_date, res_px, res_ndvi_dates, res_ndvi

def visualize(field_no, regr_model):
    date, px_pairs, ndvi_dates, ndvi_data = read_pixel_data(field_no)
    
    ndvi_pred = np.array([])
    for day in px_pairs:
        vv = day[:, 0]
        vh = day[:, 1]
        nrpd = (vh - vv) / (vh + vv)
        X = np.stack([vv, vh, nrpd], axis=1)
        y = regr_model.predict(X)
        ndvi_pred = np.append(ndvi_pred, mean(y))
    
    plt_date = dates.datestr2num(date)
    #ndvi_mes = 0.18 * np.exp(2.9 * ndvi_mes)
    #ndvi_pred = 0.18 * np.exp(2.9 * ndvi_pred)
    #plt.plot_date(dates.datestr2num(ndvi_dates), ndvi_data, xdate=True, fmt="g-")
    plt.plot_date(sorted(plt_date), [x for _,x in sorted(zip(plt_date,ndvi_pred))], xdate=True, fmt="r-")
    

    date, ndvi = read_ground_truth(field_no)
    plt_date = dates.datestr2num(date)
    plt.plot_date(plt_date, ndvi, xdate=True, fmt="b--")
    
    plt.savefig(f"images/field{field_no+1}.png")
    #plt.show()
    plt.clf()

    return



if __name__ == '__main__':
    model_file = "model_2018"
    regr = load(model_file)
    
    for field_no in range(20):
        visualize(field_no, regr)


