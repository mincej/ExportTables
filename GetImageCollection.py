# This script deals with reading in the image collections across Landsats 5, 7, and 8,
# harmonizing them, and merging the collections to make them ready for timeseries analysis
# with the Secchi depth estimation.

# Function matches the SR scene with the TOA scene and adds the TOA temperature band to the
# SR scene.
import ee

ee.Initialize()


def addTemp(toa):
    def main(img_sr):
        img_toa = toa.filterMetadata("system:index", "equals", img_sr.get("system:index")).first()
        img_sr = img_sr.addBands(img_toa.select("tir").subtract(ee.Number(273.15)).rename("TOA_Celsius"))
        return img_sr

    return main


def addMetadata(cent):
    def main(img):
        gotcha = (ee.Number(img.clip(ee.Geometry(cent)).reduceRegion(
            ee.Reducer.count()
        ).get("blue")).gt(0))
        date = ee.Date(img.get("system:time_start"))
        return (img.set({"Day": date.getRelative("day", "year").toInt(),
                         "Year": date.get("year"),
                         "Centroid": gotcha,
                         "Chunk": ee.Number.expression("n/16", {'n': date.getRelative("day", "year")}).toInt()
                         }))

    return main


def convertZenith(img):
    return (img.addBands(ee.Image(
        ee.Number(img.get("SOLAR_ZENITH_ANGLE")).toFloat()
    ).rename("SOLAR_ZENITH_ANGLE").toFloat()))

def satTypes(img):
    sat_type = ee.String(img.get("SATELLITE")).slice(8)
    return img.set("Merged_Satellites", ee.List([sat_type]))

def getImageCollection(feat, harm):
    area = feat.geometry()
    cent = feat.get("Centroid")
    l5 = (ee.ImageCollection("LANDSAT/LT05/C01/T1_SR")
          .select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa'],
                  ["blue", "green", "red", "nir", "swir1", "tir", "swir2", "pixel_qa"])
          .filterBounds(area)
          .filterMetadata("CLOUD_COVER_LAND", "not_greater_than", 80)
          .filterDate("1984-03-01", "2013-06-05")
          .map(addMetadata(cent))
          .map(convertZenith))
    l5_toa = ee.ImageCollection("LANDSAT/LT05/C01/T1_TOA").select(["B6"], ["tir"])

    l7 = (ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
          .select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa'],
                  ["blue", "green", "red", "nir", "swir1", "tir", "swir2", "pixel_qa"])
          .filterBounds(area)
          .filterMetadata("CLOUD_COVER_LAND", "not_greater_than", 80)
          .filterDate("1999-05-15", "2003-05-31")
          .map(addMetadata(cent))
          .map(convertZenith))
    l7_toa = ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA").select(["B6_VCID_1"], ["tir"])

    l8 = (ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
          .select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B10', 'pixel_qa'],
                  ["blue", "green", "red", "nir", "swir1", "swir2", "tir", "pixel_qa"])
          .filterBounds(area)
          .filterMetadata("CLOUD_COVER_LAND", "not_greater_than", 80)
          .filterDate("2012-01-01", "2019-12-31")
          .map(addMetadata(cent))
          .map(convertZenith))
    l8_toa = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA').select(["B10"], ["tir"])

    l5 = l5.map(addTemp(l5_toa))
    l7 = l7.map(addTemp(l7_toa))
    l8 = l8.map(addTemp(l8_toa))

    coefs = {
        "intercepts": ee.Image.constant([0.0003, 0.0088, 0.0061, 0.0412, 0.0254, 0.0172]).multiply(10000),
        "slopes": ee.Image.constant([0.8474, 0.8483, 0.9047, 0.8462, 0.8937, 0.9071])
    }

    def l5_harm_fnc(img):
        orig = img
        return (img.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2'])
                .multiply(coefs["slopes"])
                .add(coefs["intercepts"])
                .round()
                .toShort()
                .addBands(img.select(['pixel_qa', "TOA_Celsius", "SOLAR_ZENITH_ANGLE"]))
                .copyProperties(orig, orig.propertyNames()))

    l5_harm = l5.map(l5_harm_fnc)

    def l7_harm_fnc(img):
        orig = img
        return (img.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2'])
                .multiply(coefs["slopes"])
                .add(coefs["intercepts"])
                .round()
                .toShort()
                .addBands(img.select(['pixel_qa', "TOA_Celsius", "SOLAR_ZENITH_ANGLE"]))
                .copyProperties(orig, orig.propertyNames()))

    l7_harm = l7.map(l7_harm_fnc)

    images = (ee.ImageCollection(ee.Algorithms.If(harm,
                                                  ee.ImageCollection(l5_harm.merge(l7_harm).merge(l8)),
                                                  ee.ImageCollection(l5.merge(l7).merge(l8)))))
    images = images.map(satTypes)
    return images
