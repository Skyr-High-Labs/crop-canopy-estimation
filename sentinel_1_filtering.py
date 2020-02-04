import ee
import folium
import geehydro

# If you have not already, sign up at https://earthengine.google.com and log in once
#ee.Authenticate()

ee.Initialize()


Map = folium.Map(location=[40, -100], zoom_start=4)
Map.setOptions('HYBRID')


area = ee.Geometry.Polygon([
[0.7361428201236531,52.61884100314843], \
[0.7357123370721075,52.61796081132644], \
[0.735387309582145,52.61692592009805], \
[0.7383043267826928,52.61653655467957], \
[0.7407995589626104,52.61633915851081], \
[0.7410631723445538,52.61696328289204], \
[0.7414673790849924,52.61764074563146], \
[0.7419331341838609,52.61865427516544], \
[0.7419067852891148,52.61878763694049], \
[0.7396047240499803,52.61917708959558], \
[0.7366699741038008,52.6196411809938], \
[0.7361428201236531,52.61884100314843] \
])

# Load the Sentinel-1 ImageCollection.
sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filterBounds(area)

# Filter by metadata properties.
vh = sentinel1 \
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
  .filter(ee.Filter.eq('instrumentMode', 'IW'))

# Filter to get images from different look angles.
vhAscending = vh.filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
vhDescending = vh.filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))

# Create a composite from means at different polarizations and look angles.
composite = ee.Image.cat([
  vhAscending.select('VH').mean(),
  ee.ImageCollection(vhAscending.select('VV').merge(vhDescending.select('VV'))).mean(),
  vhDescending.select('VH').mean()
]).focal_median()

# Display as a composite of polarization and backscattering characteristics.
Map.setCenter(0.7361428201236531,52.61884100314843, 10)
Map.addLayer(composite, {'min': [-25, -20, -25], 'max': [0, 10, 0]}, 'composite')


vhAscending.select('VH').first()

"""## Display Earth Engine data layers"""

Map.setControlVisibility(layerControl=True, fullscreenControl=True, latLngPopup=True)
Map