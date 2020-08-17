import ee
import folium
import IPython.display as ip
import geehydro
import GetImageCollection as ic

ee.Initialize()
nhd = ee.FeatureCollection('users/mincej20/NHD_Filtered_50')
feat = nhd.first()

centroid = ee.Geometry(feat.geometry().centroid())
long = centroid.coordinates().get(0).getInfo()
lat = centroid.coordinates().get(1).getInfo()

imgs = ic.getImageCollection(feat, True)
Map = folium.Map(location=[long, lat], zoom_start=8)

print(imgs.first().getInfo())
viz = {
    'bands': ["RED", "GREEN", "BLUE"],
    'min': 0,
    'max': 3000,
    'gamma': 1.4
}

Map.setOptions('HYBRID')
Map.addLayer(imgs.first(), viz, "Test", True)
Map.setControlVisibility(layerControl=True, fullscreenControl=True, latLngPopup=True)
html_string = Map.get_root().render()
ip.HTML(html_string)
