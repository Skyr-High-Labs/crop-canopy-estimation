import matplotlib.pyplot as plt
import matplotlib.dates as dates
import model
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from joblib import load
from prepData import rasteriseField
import reader
import xlrd
import datetime
import pickle

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


def read_pixel_data(field_no):
    data = pickle.load(open("ee_download/2017_data.pickle", "rb"))
    field = rasteriseField(data[field_no])
    res_date, res_px = ([], [])

    def getNRPD(vv, vh):
        s = vh + vv
        s += np.sign(s)*0.00001
        s += 0.000001
        return (vh - vv) / s

    for ascending in field["ascending"]:
        desceding = min(field["descending"], key=lambda sarImage : abs(sarImage["date"]-ascending["date"]))
        res_px.append([ascending["VV"],ascending["VH"],
            getNRPD(ascending["VV"],ascending["VH"]),
            desceding["VV"],desceding["VH"],
            getNRPD(desceding["VV"],desceding["VH"])])
        res_date.append(datetime.datetime.utcfromtimestamp(int(ascending["date"]/1000)).strftime("%m/%d/%Y"))

    return res_date, res_px


def visualize(field_no, regr_model):
    date, px_pairs = read_pixel_data(field_no)
    #ndvi_mes = np.array([mean(day[:,0]) for day in px_pairs])
    
    ndvi_pred = np.array([])
    for day in px_pairs:
        X = np.stack(day[0:6]).transpose().reshape((np.size(day[0]),6))
        X = X[np.where(X[:,0] != 0)]
        if len(X) == 0:
            y = 0
        else:
            y = np.mean(regr_model.predict(X))
        ndvi_pred = np.append(ndvi_pred, y)
    
    plt_date = dates.datestr2num(date)
    #plt.plot_date(plt_date, ndvi_mes, xdate=True, fmt="g-")
    plt.plot_date(sorted(plt_date), [x for _,x in sorted(zip(plt_date,ndvi_pred))], xdate=True, fmt="r-")
    

    date, ndvi = read_ground_truth(field_no)
    plt_date = dates.datestr2num(date)
    plt.plot_date(plt_date, ndvi, xdate=True, fmt="b--")
    
    plt.savefig(f"images/field{field_no+1}.png")
    #plt.show()
    plt.clf()

    return


if __name__ == '__main__':
    #model_file = "model_2017"
    model_file = "dual_mixed_32"
    regr = load(model_file)
    #regr = RandomForestRegressor()
    #regr.fit([(0.0, 0.0, 0.0)], [0.0])
    
    ## Visualize NDVI mean values
    #for field_no in range(20):
    #    visualize(field_no, regr)

    ## Generate NDVI image comparions

    for field_no in range(20):
        print(f"Processing field #{field_no+1}...")
        visualize(field_no, regr)

