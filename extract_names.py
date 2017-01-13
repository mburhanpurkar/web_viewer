#!/usr/bin/env python
import json
from flask import Flask
from flask import url_for
app = Flask(__name__)


def get_images(filename):

    """Outputs a list of plot filenames based on the .json file produced
    from pipeline runs. The output is in the following form:
    [[[z0tf0f0, z0tf0f1, ...], [z1tf0f0, z1tf0f1, ...], ..., [...]],
     [[z0tf1f0, z0tf1f0, ...], [z1tf1f0, z1tf1f1, ...], ..., [...]],
     [...]]
     """

    json_file = open(filename).read()
    json_data = json.loads(json_file)
    transforms_list = json_data['transforms']

    prev_tf_index = 0

    fnames, zoom_group = [], []
    first_dedisperser = True     # not nice, I know. Prevents dedisperser plots from being separated

    for i, transform in enumerate(transforms_list):
        if transform['name'] == 'plotter_transform' or 'bonsai_dedisperser' in transform['name']:
            current_tf_index = i
            if current_tf_index == 1 or current_tf_index != prev_tf_index + 1 or ('bonsai_dedisperser' in transform['name'] and first_dedisperser):
                # we need to start a new list for a new transform
                zoom_group = []
                for plot in transform['plots'][0]['files'][0]:
                    zoom_group.append(plot['filename'][2:])
                fnames.append([zoom_group])
            else:
                # we need to add to the current transform's list
                zoom_group = []
                for plot in transform['plots'][0]['files'][0]:
                    zoom_group.append(plot['filename'][2:])
                fnames[-1].append(zoom_group)
            if 'bonsai_dedisperser' in transform['name'] and first_dedisperser:
                first_dedisperser = False    # need to update to prevent from splitting the dedisperser zooms
            prev_tf_index = current_tf_index

    return fnames


def print_fnames_nicely(fnames):

    """Prints each sub-list on its own."""

    for tf_group in fnames:
        for zoom_group in tf_group:
            for file in zoom_group:
                print file,
            print
        print
        print


######################################################################


# Helpful global variables!

fnames = get_images("rf_pipeline_0.json")
min_zoom, min_index = 0, 0
max_zoom = len(fnames[0])
max_index = [[len(zoom) for zoom in transform] for transform in fnames]  # in the same format as fnames

# print "Len fnames (num transforms):  ", len(fnames)
# print "Len fnames[0] (num zooms):    ", len(fnames[0])
# print "Len fnames[0][0] (num tiles): ", len(fnames[0][0])


######################################################################


# Making the flask pages...


def check_params(zoom, index):
    """Checks whether a link should be added at the bottom of the page
    to the next set of images in the series."""
    # For whatever reason, there are differing number of plots for
    # different transforms of the same zoom. This only returns false
    # if there are absolutely no images left (i.e. it will return true
    # if there is only one image available at a particular zoom because
    # one transform happened to output more than the rest). This means
    # we need to check again when we are displaying each individual
    # image whether it exists.
    if zoom >= max_zoom or zoom < min_zoom or index < min_index or index >= max([element[zoom] for element in max_index]):
        return False
    return True


def check_image(transform, zoom, index):
    """Checks whether a particular image is available (because some transforms seem
    to produce more plots than others)"""
    if zoom >= max_zoom or zoom < min_zoom or index < min_index or index >= max_index[transform][zoom]:
        return False
    return True


@app.route('/bringup_series/<int:zoom>/<int:index>')
def bringup_series(zoom, index):

    """Tiled image viewer! Shows all of the plots prodiced from a pipeline
    run at different zooms across varying time intervals."""

    urlList, extraUrlList = [], []
    display = '<h3>Displaying Zoom %d Index %d</h3>' % (zoom, index)

    # First, get all the plots that need to be displayed (based on the link values)
    for transform in range(len(fnames)):
        if check_image(transform, zoom, index):
            urlList.append(url_for('static', filename='plots/%s' % (fnames[transform][zoom][index])))
        else:
            urlList.append(None)

    for image in urlList:
        if image is not None:
            display += '<img src="%s">\n' % image
        else:
            display += 'Image Is Not Available'

    # Now, add the links at the bottom!
    # Here, we check whether there are any images at a particular zoom or index
    # This will return true even if there is only one image to display because
    # one of the transforms outputted extra images. This is for the links at the
    # bottom of the page pointing to another set of images.
    if check_params(zoom, index - 1):
        extraUrlList.append(url_for('bringup_series', zoom=zoom, index=index - 1))
    else:
        extraUrlList.append(None)
    if check_params(zoom, index + 1):
        extraUrlList.append(url_for('bringup_series', zoom=zoom, index=index + 1))
    else:
        extraUrlList.append(None)
    if check_params(zoom + 1, index * 2):
        extraUrlList.append(url_for('bringup_series', zoom=zoom + 1, index=index * 2))
    else:
        extraUrlList.append(None)
    if check_params(zoom - 1, index // 2):
        extraUrlList.append(url_for('bringup_series', zoom=zoom - 1, index=index // 2))
    else:
        extraUrlList.append(None)

    display += '<p> <center> [&nbsp;&nbsp;&nbsp;'

    for i, extraImage in enumerate(['Prev Time', 'Next Time', 'Zoom In', 'Zoom Out']):
        if extraUrlList[i] is not None:
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % (extraUrlList[i], extraImage)
    display += ']</p> </center>'

    return display


@app.route('/display_triggers/<int:zoom>')
def display_triggers(zoom):
    """Displays all trigger plots at a given zoom horizontally."""
    triggerList = fnames[-1]
    display = '<center><table cellspacing="0" cellpadding="0"><tr>'
    for trigger in triggerList[zoom]:
        temp = url_for('static', filename='plots/%s' % trigger)
        display += '<td><img src="%s"></td>' % temp
    display += '</tr></table></center>'
    return display


@app.route('/')
def top():

    """Home page! Need to update with links later..."""

    return "Hello, world!"
