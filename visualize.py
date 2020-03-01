import matplotlib.pyplot as plt
import matplotlib.dates as dates
import model
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from joblib import load
import reader
import pixelPairs
import getSAR
import xlrd
import datetime
#from PIL import Image
import getPair

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
    data, dates  = getSAR.arrayToSAR(array, startDate, endDate, returnDates=True)
    
    res_date, res_px = ([], [])
    for i in range(0, len(data), 2):
        a1 = data[i][0][data[i][0] != 0]
        a2 = data[i+1][0][data[i+1][0] != 0]
            
        tmp = np.array([[np.mean(a1), np.mean(a2)]])
        res_px.append(tmp)
        res_date.append(f'{(dates[i//2]):%B %d, %Y}')

    return res_date, res_px


def visualize(field_no, regr_model):
    date, px_pairs = read_pixel_data(field_no)
    #ndvi_mes = np.array([mean(day[:,0]) for day in px_pairs])
    
    ndvi_pred = np.array([])
    for day in px_pairs:
        vv = day[:, 0]
        vh = day[:, 1]
        nrpd = (vh - vv) / (vh + vv)
        X = np.stack([vv, vh, nrpd], axis=1)
        y = regr_model.predict(X)
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



def fieldToImages(ndvi_mes, ndvi_pred):
    img_mes = Image.fromarray(np.uint8(ndvi_mes * 255) , 'L')
    img_pred = Image.fromarray(np.uint8(ndvi_pred * 255) , 'L')

    return img_mes, img_pred


def imagePredict(regr, vv, vh, mask):
    nrpd = [(vh[i] - vv[i]) / (vh[i] + vv[i]) for i in range(len(vv))]
    ndvi_pred = np.zeros_like(mask)
    for i in range(len(mask)):
      for j in range(len(mask[i])):
        if mask[i][j] <= 0: continue
        
        vv_val = vv[i][j]
        vh_val = vh[i][j]
        nrpd_val = nrpd[i][j] if not np.isnan(nrpd[i][j]) else 0.0
        #nrpd_val = nrpd[i][j]
        
        ndvi_pred[i][j] = regr.predict([(vv_val,vh_val,nrpd_val)])[0]
    return ndvi_pred


def generateFieldImages(field_no, regr_model, year="2017"):
    try:
        startDate, endDate = f"{year}-05-01", f"{year}-09-30"
        arrays = reader.parseKML(f"{year}_polygons.kml")
        array = arrays[field_no]
        data, mask = getPair.arrayToPairs(array, startDate, endDate, False, 0.5)
        ndvi_images = [data[i][0] for i in range(0, len(data), 3)]
        vv_images = [data[i+1][0] for i in range(0, len(data), 3)]
        vh_images = [data[i+2][0] for i in range(0, len(data), 3)]
        
        for i in range(len(ndvi_images)):
            print(f"Processing image #{i+1}...")
            y = imagePredict(regr, vv_images[i], vh_images[i], mask)
    
            ndvi_mes, ndvi_pred = ndvi_images[i], y
            
            img_mes, img_pred = fieldToImages(ndvi_mes, ndvi_pred)
            #img_mes.show()
            #img_pred.show()
            img_mes.save(f"images/field_NDVI/{year}/measured/field{field_no+1}_{i+1}.jpg", "JPEG")
            img_pred.save(f"images/field_NDVI/{year}/predicted/field{field_no+1}_{i+1}.jpg", "JPEG")
    except ValueError:
        return


if __name__ == '__main__':
    #model_file = "model_2017"
    model_file = "model_1582706447.dms"
    regr = load(model_file)
    #regr = RandomForestRegressor()
    #regr.fit([(0.0, 0.0, 0.0)], [0.0])
    
    ## Visualize NDVI mean values
    #for field_no in range(20):
    #    visualize(field_no, regr)

    ## Generate NDVI image comparions

    for field_no in range(20):
        print(f"Processing field #{field_no+1}...")
        generateFieldImages(field_no, regr)

