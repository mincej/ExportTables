# Method to iterate through an image collection and merge images that are found within the
# same 16-day LANDSAT passover chunk.

import ee
import copy

ee.Initialize()

def mergeByChunk(imgcoll):
    imgcoll = imgcoll.toList(imgcoll.size())
    seq = ee.List.sequence(0, imgcoll.size().subtract(1), 1)
    
    def addID(item, imglist):
        new_img = ee.Image(imgcoll.get(ee.Number(item)))
        new_img = new_img.set({"Merge": ee.Number(imgcoll.size()).add(1),
                               "Amnt_Merge": ee.Number(1),
                               "ID": ee.Number(item)})
        return ee.List(imglist).add(ee.Image(new_img))
    
    tl = seq.iterate(addID, ee.List([]))
    templist = copy.deepcopy(tl)
    tl = ee.ImageCollection.fromImages(tl)
    list_max = ee.Number(tl.first().get("Merge"))
    
    def iterator(img, acc_list):

        img = ee.Image(img)
        placeholder = (ee.Image(0)
                       .set({"Centroid": 0, "Chunk": 20000, 
                             "Merge": list_max, "Day": 4000, 
                             "ID": 1000000000, "CLOUD_COVER_LAND": 200,
                             "SATELLITE": "MODIS"}))
        
        first_place = ee.Number(img.get("ID")).eq(0)
        
        diff_chunk = (ee.Number(ee.Image(ee.List(acc_list).get(-1)).get("Chunk"))
                                         .neq(ee.Number(img.get("Chunk"))))
        prev_img = (ee.List(acc_list).get(-1))
                                         
        prev = ee.Image(ee.Algorithms.If(first_place, 
                                         placeholder, 
                                         ee.Algorithms.If(diff_chunk,
                                                          placeholder, 
                                                          prev_img)))           
        prev = ee.Image(prev)
        
        last_place = (ee.Number(img.get("ID"))
                      .eq(ee.Number(ee.List(templist).size())
                          .subtract(1)))
        
        next_img = (ee.Image(ee.List(templist).get(ee.Number(img.get("ID")).add(1))))

        diff_chunk = (ee.Number(img.get("Chunk"))
                      .neq(ee.Number(next_img.get("Chunk")))
                      .Or(ee.String(img.get("SATELLITE"))
                                    .compareTo(next_img.get("SATELLITE")).neq(0)))
                                                        
        
        aft = ee.Image(ee.Algorithms.If(last_place,
                                        placeholder, 
                                        ee.Algorithms.If(diff_chunk,
                                                         placeholder, 
                                                         next_img)))
        
        already_merged = (ee.Number(img.get("ID")).eq(ee.Number(prev.get("Merge")))
                          .Or(ee.String(img.get("SATELLITE"))
                              .compareTo(ee.String(prev.get("SATELLITE"))).neq(0)))
        
        same_chunk = ee.Number(prev.get("Chunk")).eq(ee.Number(img.get("Chunk")))
        
        img_merge = ee.Image(ee.Algorithms.If(already_merged, 
                                              img, 
                                              ee.Algorithms.If(same_chunk,
                                                               prev, 
                                                               aft)))
        
        less_merge = (ee.Number(img.get("Amnt_Merge"))
                         .gt(ee.Number(img_merge.get("Amnt_Merge"))))
        
        amnt = ee.Number(ee.Algorithms.If(less_merge, 
                                          ee.Number(img.get("Amnt_Merge")), 
                                          ee.Number(img_merge.get("Amnt_Merge"))))
        
        img_m_c = ee.Number(img_merge.get("CLOUD_COVER_LAND"))
        img_c = ee.Number(img.get("CLOUD_COVER_LAND"))
        
        conditions = (ee.Number(img.get("ID")).eq(ee.Number(img_merge.get("ID")))
                      .Or(ee.Number(img.get("Chunk"))
                          .neq(ee.Number(img_merge.get("Chunk")))))
        
        props_keep = ["Chunk", "system:index", "system:time_start", "SATELLITE", 
                      "Day", "Year", "CLOUD_COVER_LAND", "LANDSAT_ID"]
        props_alt = {"ID": img.get("ID"), "Merge": img_merge.get("ID"),
                    "Amnt_Merge": amnt.add(1), 
                    "Merged_Satellites": ee.List(img.get("Merged_Satellites")).cat(ee.List(img_merge.get("Merged_Satellites")))}
        
        img_top = (ee.ImageCollection.fromImages([img_merge, img]).mosaic()
                   .copyProperties(img, props_keep)
                   .set(props_alt))
        merge_top = (ee.ImageCollection.fromImages([img, img_merge]).mosaic()
                   .copyProperties(img_merge, props_keep)
                   .set(props_alt))
        
        new_img = ee.Image(ee.Algorithms.If(conditions,
                                            img, 
                                            ee.Algorithms.If(img_m_c.gt(img_c), 
                                                             img_top,
                                                             merge_top)))
        new_img = new_img.set({"Day": ee.Number(new_img.get("Chunk")).multiply(16)})
        
        already_merged = ee.Number(img.get("ID")).eq(ee.Number(prev.get("Merge")))
        gotta_pop = ee.Number(new_img.get("Merge")).eq(ee.Number(prev.get("ID")))
        
        popped_list = (ee.List(acc_list)
                       .slice(0, ee.Number(ee.List(acc_list).size())
                              .subtract(1)).add(ee.List(new_img)))
        added_list = (ee.List(acc_list).add(ee.List(new_img)))
        
        acc_list = ee.List(ee.Algorithms.If(already_merged,
                                            acc_list, 
                                            ee.Algorithms.If(gotta_pop, 
                                                             popped_list, 
                                                             added_list)))
        return acc_list
    
    comb = ee.List(tl.iterate(iterator, ee.List([])))
    comb = ee.ImageCollection.fromImages(comb)
    return comb
        
        
        
        
        
        