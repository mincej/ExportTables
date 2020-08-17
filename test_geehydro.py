import geehydro
import folium
# Get a composite of all Sentinal 2 images within a date range that include my point of interest.
poi = ee.Geometry.Point([-82.4572, 27.9506])
image = ee.ImageCollection('COPERNICUS/S2').filterBounds(poi).filterDate('2016-10-01', '2016-12-31').min()
Map = folium.Map(location=[27.9506, -82.4572], zoom_start=8)
# To see a google satellite view as a basemap
Map.setOptions('HYBRID')
nir = image.select('B8')
red = image.select('B4')
ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI Layer')
ndviParams = {'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']}
Map.addLayer(ndvi, ndviParams, 'NDVI image')
Map.setControlVisibility(layerControl=True, fullscreenControl=True, latLngPopup=True)
Map