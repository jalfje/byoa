import requests
import json
import os
import dateutil.parser

# The URL for the MUX camera
CBERS_MUX_URL = 'https://cbers-stac-0-6.s3.amazonaws.com/CBERS4/MUX/'

# Downloads a jpg from a URL and stores it in the specified folder
def download_jpg(url, file_path, file_id):
    os.makedirs(file_path, exist_ok = True)
    full_path = os.path.join(file_path, file_id + ".jpg")
    resp = requests.get(url)
    with open(full_path, 'wb') as f:
        f.write(resp.content)

# Trawl that catalog!
# Input:
# img_path          path to store each image in
# metadata_path     path to each image's metadata in
# bbox              lat/lon bounding box as list in form [left, bottom, right, top]
# time_range        time range as list in form [start, end]
# max_items         limit on number of items to get. will stop after this many. mainly for testing.
#
# Returns a list of saved image ids
def get_data_from_cbers(img_path, metadata_path, bbox, time_range, max_items):

    ########## TEMP ##########

    # Here we're directly downloading some random (non-satellite imagery) jpg
    # files, because our trawling code didn't appear to be working and was
    # too difficult to debug because it was running on a separate thread.
    # These images frankly do work to show our proof-of-concept, and the
    # subsequent code was working successfully outside of the project in
    # independent tests, but it failed when we tried to integrate it.

    # Just some random shenanigans
    download_jpg("https://i.imgur.com/g9KKuqs.jpg", img_path, "img_1.jpg")
    download_jpg("https://i.imgur.com/8WH1QxW.jpg", img_path, "img_2.jpg")
    download_jpg("https://i.imgur.com/nZhCWsm.jpg", img_path, "img_3.jpg")

    dict_1 = {
                "coordinates": [1, 2, 3, 4],
                "timestamp": time_range[1]
             }
    dict_2 = {
                "coordinates": [5, 6, 7, 8],
                "timestamp": time_range[0]
             }
    dict_3 = {
                "coordinates": [6, 6, 7, 7],
                "timestamp": time_range[1]
             }

    with open(os.path.join(metadata_path, "img_1.json"), 'w') as metadata_file:
        json.dump(dict_1, metadata_file)

    with open(os.path.join(metadata_path, "img_2.json"), 'w') as metadata_file:
        json.dump(dict_2, metadata_file)

    with open(os.path.join(metadata_path, "img_3.json"), 'w') as metadata_file:
        json.dump(dict_3, metadata_file)

    return

    ########## END TEMP ##########

    baseURL = CBERS_MUX_URL

    btime = [
        dateutil.parser.parse(time_range[0]),
        dateutil.parser.parse(time_range[1])
    ]


    item_ids = []

    # Get the MUX catalog object as a Python dictionary
    mux_json = requests.get(baseURL + "catalog.json").json()

    for path_link in mux_json["links"]:
        if path_link['rel'] == 'child':

            # Get each path's catalog object as a Python dictionary
            path_json = requests.get(baseURL + path_link['href']).json()

            for row_link in path_json["links"]:
                if row_link['rel'] == 'child':

                    # Get each row's catalog object as a Python dictionary
                    # note that the URL has the path's three digits and '/' added in
                    row_json_obj = requests.get(baseURL + path_link['href'][:4] + row_link['href']).json()

                    # Finally, we loop through the actual items
                    for item_link in row_json_obj["links"]:
                        if item_link['rel'] == 'item':

                            # Get each item as a Python dictionary
                            item_obj = requests.get(baseURL + path_link['href'][:4] + row_link['href'][:4] + item_link['href']).json()

                            # Save the Item's timestamp for later. If it's out of the search range,
                            # move on to the next Item
                            # If no time zone information is included, don't take it
                            # This is necessary in order to avoid causing errors
                            # which would occur when you compare datetimes and only one of
                            # the datetimes has a time zone
                            item_time = dateutil.parser.parse(item_obj["properties"]["datetime"])
                            if not item_time.tzinfo:
                                continue
                            if not (item_time > btime[0] and item_time < btime[1]):
                                continue

                            # Weird for conditions because the actual coordinates are buried a few layers deep.
                            # coordinates and layer1 each had only a single thing inside (on the ones I looked at):
                            # the next-level-down list (layer1 and layer2, respectively)
                            for layer1 in item_obj['geometry']['coordinates']:
                                for layer2 in layer1:
                                    # if any corner of the Item's polygon is inside our search bbox
                                    # AND the Item is within the desired timeframe, we want it!
                                    for coordinate in layer2:
                                        if (coordinate[0] > bbox[0] and coordinate[0] < bbox[2] and coordinate[1] > bbox[1] and coordinate[1] < bbox[3]):
                                            # download the Item's thumbnail
                                            download_jpg(item_obj['assets']['thumbnail']['href'], img_path, item_obj['id'])

                                            # save its metadata in a JSON file
                                            # make the json thing as a dict
                                            # the image shares its name with the JSON file
                                            # so there is no need for an image link/name entry here
                                            metadata_dict = {
                                                "coordinates": item_obj['geometry']['coordinates'],
                                                "timestamp": str(item_time)
                                            }
                                            with open(os.path.join(metadata_path, item_obj['id'] + '.json'), 'w') as metadata_file:
                                                json.dump(metadata_dict, metadata_file)

                                            item_ids.append(item_obj['id'])
                                            # stop if you've downloaded enough things
                                            if len(item_ids) >= max_items:
                                                print("Done: downloaded " + str(len(item_ids)) + " Items")
                                                return item_ids
                                            # once you've done that based on the one coordinate being in the bbox,
                                            # you've grabbed the Item and don't want to grab it again, so break
                                            break

