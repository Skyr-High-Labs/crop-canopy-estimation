from flask import Flask, request
from flask_restplus import Api, Resource, fields
import os
from joblib import dump, load
from pixelPairs import pixelPairs

flask_app = Flask(__name__)
app = Api(app = flask_app,
            version = "1.0",
            title = "Crop Canopy Estimation",
            description = "Estimate crop canopy cover for a location")

name_space = app.namespace('cce', description='Estimate Crop Canopy Cover')

model = app.model('CCE Model',
                  {'name': fields.String(required=True,
                                         description="Name of the person",
                                         help="Name cannot be blank.")})
                                         
# TODO: sort out parameters
@app.doc(responses={200: 'OK', 400: 'Error'},
         params={'placeholder': 'description'})

@name_space.route("/")
class MainClass(Resource):
    # do nothing
    def get(self):
        return {
            "status": "Did nothing, use POST Request"
        }

    def post(self):
        try:
            # TODO: get the data FROM the post request
            polygon = None
            startDate = None
            endDate = None
            # load model
            # TODO: how is file_name decided?
            file_name = None
            if os.path.isfile(file_name):
                print(f"Loading existing file {file_name}...")
                regr = load(file_name)
                # TODO: clearly y can't be generated. So how is this function modified?
                X, _ = pixelPairs(polygon, startDate, endDate)
                y = regr.predict(X)
                return {
                    "status": "Done",
                    "ndvi": y
                }
            else:
                raise Exception("Model file not available")
        except Exception as e:
            name_space.abort(400, e.__doc__, status = e.value, statusCode = "400")
        
