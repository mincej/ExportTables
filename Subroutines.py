import ee
import CloudCodes as cc

def waterIsolationMNDWI(gsw, geom):
    def main(image):
        image = image.addBands(image.normalizedDifference(["green", "swir1"]).rename("MNDWI"))
        image = (image.updateMask(gsw.select("occurrence").gte(50)
                                  .And(image.select("MNDWI").gte(-0.1))
                                  .And(image.select("swir1").lt(1000))
                                  .And(image.select("TOA_Celsius").gt(1.5))))
        return image
    return main

def waterIsolationSWIR(gsw, geom):
    def main(image):
        image = (image.updateMask(gsw.select("occurrence").gte(50)
                                  .And(image.select("swir1").lt(900))
                                  .And(image.select("TOA_Celsius").gt(1.5))))
        return image
    return main

def getPixelBounds(img, geom):
    conn = img.connectedComponents({
        "connectedness": ee.Kernel.plus(1),
        "maxSize": 256
    })
    coll = conn.reduceToVectors({
        "geometry": geom, 
        "scale": 30, 
        "maxPixels": 1000,
        "geometryType": 'polygon',
        "eightConnected": False, 
        "labelProperty": 'labels', 
        "reducer": ee.Reducer.sum(),
        "bestEffort": True, 
        "tileScale": 16
    })
    return coll

def countPixels(geom):
    def main(image):
        img_to_cnt = ee.Image(image.select("blue"))
        reduced = img_to_cnt.reduceRegion(**{
            "reducer": ee.Reducer.count(),
            "geometry": ee.Geometry(geom), 
            "maxPixels": 10000000000,
            "bestEffort": True,
            "scale": 30
        })
        reduced = reduced.get("blue")
        return image.set({"Count": reduced})
    return main

def distinctMerged(img):
    img = (img.set({
        "Distinct_Sats": ee.List(ee.List(img.get("Merged_Satellites")).distinct()),
    }))
    img = (img.set({
        "Count_Distinct": ee.Number(ee.List(img.get("Distinct_Sats")).distinct().length())
    }))
    return img

def noClouds(image):
    return cc.maskClouds(image)

def satInt(img):
    strings = ee.String(img.get("SATELLITE")).split("_")
    return img.set({"sat": ee.String(ee.List(strings).get(1))})

def reduceColors(feat):
    def main(image):
        geom = feat.geometry()
        date = ee.Date(image.get("system:time_start")).format("yyyy-MM-dd")
        day = image.get("Day")
        year = image.get("Year")
        index = ee.String(image.get("system:index"))
        nhdplid = ee.String(feat.get("NHDPlID"))
        count = ee.Number(image.get("Count"))
        sat = ee.Number(image.get("sat"))
        
        temp_dict = ee.Dictionary({
            "system:index": index,
            "NHDPlID": nhdplid, 
            "Day": day,
            "Year": year, 
            "date": date, 
            "pixelCount": count,
            "sat": sat
        })
        
        colors = ee.List(["blue", "green", "red", "nir", "swir1", "swir2"])
        colors_sd = colors.map(lambda name: ee.String(name).cat("_sd"))
    
        reduced = image.select(colors).reduceRegion(**{
            "reducer": ee.Reducer.median(),
            "geometry": geom, 
            "maxPixels": 10000000000,
            "bestEffort": True,
            "scale": 30
        })
        
        sd = image.select(colors).reduceRegion(**{
            "reducer": ee.Reducer.stdDev(), 
            "geometry": geom, 
            "maxPixels": 10000000000,
            "bestEffort": True, 
            "scale": 30
        }).rename(colors, colors_sd)
        
        
        
        new_dict = ee.Dictionary(reduced.combine(sd).combine(temp_dict))
        
        
        return ee.Feature(None, ee.Dictionary(new_dict))
    return main 

        