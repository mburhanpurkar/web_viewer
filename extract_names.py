#!/usr/bin/env python
import json
from flask import Flask
from flask import url_for
app = Flask(__name__)


"""
SETUP
    mkdir static
    cd static
    ln -s /path/to/plots plots
It is assumed that the .json file is in the directory of this code, but that can
be modified by altering the call to get_images()

RUNNING
    export FLASK_APP=extract_names.py
    python -m flask run

The Index page is at: http://127.0.0.1:5000/.
    Show tiles - displays all outputted plots (default: zoom 0, index1 0, index2 5)
    Show triggers - displays all triggers at a specified zoom (defult: 0)
"""


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
    first_dedisperser = True

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


def check_set(zoom, index):
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


@app.route('/show_tiles/<int:zoom>/<int:index1>/<int:index2>')
def show_tiles(zoom, index1, index2):
    """Tiled image viewer! Shows all of the plots prodiced from a pipeline
    run at different zooms across varying time intervals."""
    display = '<h3>Displaying Plots %d-%d at Zoom %d</h3>' % (index1, index2, zoom)
    display += '<table cellspacing="0" cellpadding="0">'

    # Plots to be displayed
    for transform in range(len(fnames)):
        display += '<tr>'
        # First, add plot names
        for index in range(index1, index2 + 1):
            if check_image(transform, zoom, index):
                display += '<td>%s</td>' % fnames[transform][zoom][index]
        display += '</tr>'
        for index in range(index1, index2 + 1):
            if check_image(transform, zoom, index):
                display += '<td><img src="%s"></td>' % url_for('static', filename='plots/%s' % (fnames[transform][zoom][index]))
            else:
                display += '<td>&nbsp;Plot Is Not Available&nbsp;</td>'
        display += '</tr><tr><td>&nbsp;</td></tr>'

    # Plots to be linked
    display += '<p> <center> [&nbsp;&nbsp;&nbsp;'
    if check_set(zoom, index1 - 1):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles', zoom=zoom, index1=index1 - 1, index2=index2 - 1)), 'Prev Time')
    if check_set(zoom, index1 + 1):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles', zoom=zoom, index1=index1 + 1, index2=index2 + 1)), 'Next Time')
    if check_set(zoom + 1, index1 * 2):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles', zoom=zoom + 1, index1=index1 * 2, index2=index2 * 2)), 'Zoom In')
    if check_set(zoom - 1, index1 // 2):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles', zoom=zoom - 1, index1=index1 // 2, index2=index2 // 2)), 'Zoom Out')
    if check_set(zoom, index1 - (index2 - index1)):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles', zoom=zoom, index1=index1 - (index2 - index1), index2=index2 - (index2 - index1))), 'Time travel! (past)')
    if check_set(zoom, index1 + (index2 - index1)):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles', zoom=zoom, index1=index1 + (index2 - index1), index2=index2 + (index2 - index1))), 'Time travel! (future)')
    display += ']</p> </center>'

    return display


@app.route('/show_triggers/<int:zoom>')
def show_triggers(zoom):
    """Displays all trigger plots at a given zoom horizontally."""
    triggerList = fnames[-1]
    display = '<h3>Displaying Trigger Plots at Zoom %s</h3>' % zoom
    display += '<table cellspacing="0" cellpadding="0"><tr>'
    for plotname in triggerList[zoom]:
        display += '<td>%s</td>' % plotname
    display += '</tr>'
    for trigger in triggerList[zoom]:
        temp = url_for('static', filename='plots/%s' % trigger)
        display += '<td><img src="%s"></td>' % temp
    display += '</tr></table>'
    return display


@app.route('/')
def top():
    """Home page!"""
    s = '<h3>Hello, World!</h3>'
    s += '<li> <a href="%s">Show Tiles (default: zoom 0, index 0-5)</a>\n' % url_for('show_tiles', zoom=0, index1=0, index2=5)
    s += '<li> <a href="%s">Show Triggers (default: zoom 0)</a>\n' % url_for('show_triggers', zoom=0)
    return s
