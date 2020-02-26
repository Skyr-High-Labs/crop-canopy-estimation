from flask import Flask, request
from flask_restplus import Api, Resource, fields
from joblib import dump, load
import os
import getSAR
import predictNDVI

flask_app = Flask(__name__)
app = Api(app = flask_app,
            version = "1.0",
            title = "Crop Canopy Estimation",
            description = "Estimate crop canopy cover for a location")

name_space = app.namespace('CCE Model', description='Estimate Crop Canopy Cover')

model = app.model('Estimator Model',
                  {'polygon': fields.List(cls_or_instance=fields.List(cls_or_instance=fields.Float), required=True,
                                          description="Polygon for a field",
                                          help="Array of coordinates (2-tuples)"),
                    'startDate': fields.DateTime(required=True,
                                            description="Start date",
                                            help="Start date"),
                  'endDate': fields.DateTime(required=True,
                                             description="End date",
                                             help="End date")})
                                        
# TODO: sort out parameters
@app.doc(responses={200: 'OK', 400: 'Error', 404:"FileNotFound", 500: 'Mapping Key Error'},
         params={})

@name_space.route("/")
class MainClass(Resource):
    # do nothing
    # def get(self):
    #     return {
    #         "status": "Did nothing, use POST Request"
    #     }

    @app.expect(model)
    def post(self):
        try:
            
            # get the data from the post request
            polygon = request.json["polygon"]
            startDate = request.json["startDate"]
            endDate = request.json["endDate"]
            # TODO: file_name needs to be changed
            file_name = "model_1582706447"  # fill this in later
            if os.path.isfile(file_name):
                dates, predicted_values = predictNDVI.predictNDVI(polygon, startDate, endDate, model=file_name)
                
                return {
                    "status": "OK",
                    "dates": dates,
                    "ndvi": predicted_values
                }
            else:
                raise FileNotFoundError
        except FileNotFoundError as e:
            name_space.abort(400, e.__doc__, status="Model file could not be found", statusCode="404")
        except KeyError as e:
            name_space.abort(
                500, e.__doc__, status="Could not find key", statusCode="500")
        except Exception as e:
            name_space.abort(400, e.__doc__, status ="Unspecified Error", statusCode = "400")
        
