#!/usr/bin/env python
import json
from math import ceil
from flask import Flask
from flask import url_for
app = Flask(__name__)


"""
This is a modified version of the web viewer that works for the new plotter. 
It hasn't been tested with multiple plotter transforms yet, but it definitely groups the
different zoom levels for a single transform properly. This does not handle the bonsai
dedisperser as it does not use the python plotter transform (the triggers page will 
just show the last transform in the fnames list). 

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
    Show tiles - displays all outputted plots (default: zoom 0, index1 0, index2 4)
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
    fnames = []
  
    for transform in transforms_list:
        # This will iterate over all the transforms
        if transform['name'] == 'plotter_transform': # bonsai_dedisperser doesn't use plotter function... or 'bonsai_dedisperser' in transform['name']:
            # start a new list for a new transform
            # now, we need to iterate over each zoom level
            transform_group = []
            for zoom_level in transform['plots']:
                # This iterates over each zoom level (plot group) for a particular plotter transform (list of dictionaries)
                zoom_group = []
                for file_info in zoom_level['files'][0]:
                    # now, we can finally access the file names :)
                    name = file_info['filename'][2:]
                    zoom_group.append(name)
                transform_group.append(zoom_group)
            transform_group.reverse()   # accounts for the way the zoom levels are added in the plotter (zoom 0 is the most zoomed out now)
            fnames.append(transform_group)
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

fnames = get_images("static/plots/rf_pipeline_0.json")
print fnames
print 
print 
print_fnames_nicely(fnames)
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
    run at different zooms across varying time intervals. The range of pictures
    shown can be changed to any values in the url (index1 is the index of the
    first image shown and index2 is the index of the last and defaults are set
    to 0 and 3 for the link accessef from the home page). """
    display = '<h3>Displaying Plots %d-%d at Zoom %d</h3>' % (index1, index2, zoom)
    display += '<table cellspacing="0" cellpadding="0">'

    # Plots to be displayed
    for transform in reversed(range(len(fnames))):
        display += '<tr>'
        # First, add plot names
        for index in range(index1, index2 + 1):
            if check_image(transform, zoom, index):
                display += '<td>%s</td>' % fnames[transform][zoom][index]
        display += '</tr>'
        # Now, add the images
        for index in range(index1, index2 + 1):
            if check_image(transform, zoom, index):
                display += '<td><img src="%s"></td>' % url_for('static', filename='plots/%s' % (fnames[transform][zoom][index]))
        display += '</tr><tr><td>&nbsp;</td></tr>'

    # Plots to be linked
    display += '<p> <center> [&nbsp;&nbsp;&nbsp;'

    if check_set(zoom, index1 - 1):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    zoom=zoom, index1=index1 - 1, index2=index2 - 1)), 'Prev Time')
    else:
        display += 'Prev Time&nbsp;&nbsp;&nbsp;'
    if check_set(zoom, index1 + 1):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    zoom=zoom, index1=index1 + 1, index2=index2 + 1)), 'Next Time')
    else:
        display += 'Next Time&nbsp;&nbsp;&nbsp;'

    if check_set(zoom, index1 - (index2 - index1)):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    zoom=zoom, index1=index1 - (index2 - index1), index2=index2 - (index2 - index1))), 'Jump Back')
    else:
        display += 'Jump Back&nbsp;&nbsp;&nbsp;'
    if check_set(zoom, index1 + (index2 - index1)):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    zoom=zoom, index1=index1 + (index2 - index1), index2=index2 + (index2 - index1))), 'Jump Forward')
    else:
        display += 'Jump Forward&nbsp;&nbsp;&nbsp;'

    # For making the zooming preserve column number
    if (index2 - index1) % 2 == 0:
        new_index1 = index1 * 2 + (index2 - index1) / 2
        new_index2 = index2 * 2 - (index2 - index1) / 2
    else:
        new_index1 = index1 * 2 + ceil(index2 - index1) / 2 + 1
        new_index2 = index2 * 2 - ceil(index2 - index1) / 2 + 1

    if check_set(zoom + 1, index1 * 2):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    zoom=zoom + 1, index1=new_index1, index2=new_index2)), 'Zoom In')
    else:
        display += 'Zoom In&nbsp;&nbsp;&nbsp;'

    # More column preservation
    if (index2 - index1) % 2 == 0:
        new_index1 = (index1 - (index2 - index1) / 2) / 2
        new_index2 = (index2 + (index2 - index1) / 2) / 2
    else:
        new_index1 = (index1 - ceil((index2 - index1) / 2)) / 2
        new_index2 = (index2 + (ceil((index2 - index1) / 2) + 1)) / 2

    if check_set(zoom - 1, index1 // 2):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    zoom=zoom - 1, index1=new_index1, index2=new_index2)), 'Zoom Out')
    else:
        display += 'Zoom Out&nbsp;&nbsp;&nbsp;'

    display += ']</p> </center>'

    return display


@app.route('/show_triggers/<int:zoom>')
def show_triggers(zoom):
    """Displays all trigger plots at a given zoom horizontally.
    The zoom level can be changed by changing the value in the url."""
    triggerList = fnames[-1]
    display = '<h3>Displaying Trigger Plots at Zoom %s</h3>' % zoom
    display += '<table cellspacing="0" cellpadding="0"><tr>'

    last_row = 0
    current_row = 0

    for i, trigger in enumerate(triggerList[zoom]):
        temp = url_for('static', filename='plots/%s' % trigger)
        if i > 1 and i < max_index[-1][zoom] - 2:
            temp_link = url_for('show_tiles', zoom=zoom, index1=i - 2, index2=i + 2)
            display += '<td><a href="%s"><img src="%s"></a></td>' % (temp_link, temp)
        else:
            display += '<td><img src="%s"></td>' % temp
        current_row += 1
        if (current_row - last_row) == 4:
            last_row = current_row
            display += '</tr><tr><td>&nbsp;</td></tr><tr>'
    display += '</tr></table>'

    return display


@app.route('/')
def top():
    """Home page!"""
    s = '<h3>Hello, World!</h3>'
    s += '<li> <a href="%s">Show Tiles (default: zoom 0, index 0-3)</a>\n' % url_for('show_tiles', zoom=0, index1=0, index2=4)
    s += '<li> <a href="%s">Show Triggers (default: zoom 0)</a>\n' % url_for('show_triggers', zoom=0)
    return s
