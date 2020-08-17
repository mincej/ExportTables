import ee
def maskClouds(image):
    new_img = (ee.Image(
               ee.Algorithms.If(ee.Algorithms.IsEqual(image.get("SATELLITE"), "LANDSAT_8"), 
                                (image.addBands(image.select("pixel_qa").eq(322)
                                                .Or(image.select("pixel_qa").eq(324))
                                                .rename("No_Cloud"))),
                                
                                (image.addBands(image.select("pixel_qa").eq(66)
                                                .Or(image.select("pixel_qa").eq(68))
                                                .rename("No_Cloud"))))))
    new_img = new_img.updateMask(new_img.select("No_Cloud").eq(1))
    return new_img

    
    