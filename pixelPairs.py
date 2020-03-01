import numpy as np

import getPair


def pixelPairs(array, startDate, EndDate, CLOUDY_PIXEL_PERCENTAGE=10):
    try:
        data, _ = getPair.arrayToPairs(array, startDate, EndDate, delta=0.5, CLOUDY_PIXEL_PERCENTAGE=CLOUDY_PIXEL_PERCENTAGE)
        px_pairs = None
        for i in range(0, len(data), 3):
            # NDVI, SAR
            a1 = data[i][0][data[i][0] != 0]
            a2 = data[i+1][0][data[i+1][0] != 0]
            a3 = data[i+2][0][data[i+2][0] != 0]
            
            if len(a1) == 0:
                continue
            
            tmp = [[np.mean(a1), np.mean(a2), np.mean(a3)]]
            #tmp = np.dstack((data[i][0], data[i + 1][0], data[i + 2][0]))
            #tmp = tmp.reshape(-1, tmp.shape[-1])
            #tmp = tmp[np.all(tmp != 0, axis=1)]
            px_pairs = np.concatenate((px_pairs, tmp), axis=0) if not px_pairs is None else np.array(tmp)

        # print(px_pairs)
        # px_pairs is now pixel-pairs for a given field over a given time span
        ndvi = px_pairs[:, 0]
        vv = px_pairs[:, 1]
        vh = px_pairs[:, 2]
        nrpd = (vh - vv) / (vh + vv)

        X = np.stack([vv, vh, nrpd], axis=1)
        y = ndvi
        # print(X,y)

        return X, y
    except ValueError:
        # no valid dates for the image
        return [], []
