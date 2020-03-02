import pickle
import numpy as np
import model
import joblib
from sklearn.metrics import r2_score

def unison_shuffled_copies(a, b):
    assert len(a) == len(b)
    p = np.random.permutation(len(a))
    return a[p], b[p]

if __name__ == '__main__':
    year = "2018"
    data = pickle.load(open("training_data/" + year + "_data.pickle", "rb"))
    #Train dual model
    X, y = unison_shuffled_copies(data[0], data[1])
    model.train_and_test(X, y, file_name="dual_mixed")
    #Train descending model
    #X, y = unison_shuffled_copies(data[0][:,3:6], data[1])
    #model.train_and_test(X[0:300000], y[0:300000], file_name="descending_mixed")

    dual_mixed = joblib.load("dual_mixed")
    #descending_mixed = joblib.load("descending_mixed")
    test = pickle.load(open("testing_data/" + year + "_data.pickle", "rb"))
    
    yy = []
    for i in range(len(test[0])):
        X = np.stack(test[0][i][0:6]).transpose().reshape((np.size(test[0][i][0]),6))
        X = X[np.where(X[:,0] != 0)]
        if len(X) == 0:
            yy.append(0)
            continue
        yy.append(np.mean(dual_mixed.predict(X)))
        #X = np.stack(test[0][i][3:6]).transpose().reshape((np.size(test[0][i][0]),3))
        #X = X[np.where(X[:,0] != 0)]
        #descending_pred = np.mean(descending_mixed.predict(X))
        #yy.append(np.mean([ascending_pred]))

    print("Eval regression score: R^2={}".format(r2_score(np.array(yy), test[1])))
