#!/usr/bin/env python

# Extracts the file names for produced by the plotter transform
# For example, if three plotter transoforms are applied in a
# single pipeline run, a list will be returned as follows:
# [[[z0tf0f0, z0tf0f1, ...], [z1tf0f0, z1tf0f1, ...], ..., [...]],
#  [[z0tf1f0, z0tf1f0, ...], [z1tf1f0, z1tf1f1, ...], ..., [...]],
#  [...]]


import json
from flask import Flask
from flask import url_for
app = Flask(__name__)


def get_images(filename):
    """Takes in the json file outputted whenever the pipeline is run
    and extracts the names of plots that were produced by the plotter
    transform. The output is a list of lists in which each constituent
    list contains the set of images produced by a single call of the
    plotter. This means each zoom level made for each transform is stored
    in its own list."""

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


fnames = get_images("rf_pipeline_0.json")


@app.route('/bringup_series/<int:zoom>/<int:index>')
def bringup_series(zoom, index):
    urlList, extraUrlList = [], []

    # NEED TO ADD LIMIT FOR EDGE CASES 


    for transform in range(len(fnames)):
        urlList.append(url_for('static', filename='plots/%s' % (fnames[transform][zoom][index])))
        display = '<h3>Displaying Zoom %d Index %d</h3>' % (zoom, index)

    for image in urlList:
        display += '<img src="%s">\n' % image

    # add links to next set of images
    extraUrlList.append(url_for('bringup_series', zoom=zoom, index=index - 1))
    extraUrlList.append(url_for('bringup_series', zoom=zoom, index=index + 1))
    extraUrlList.append(url_for('bringup_series', zoom=zoom + 1, index=index * 2))
    extraUrlList.append(url_for('bringup_series', zoom=zoom - 1, index=index // 2))

    display += '<p> <center> [&nbsp;&nbsp;&nbsp;'
    for i, extraImage in enumerate(['Prev Time', 'Next Time', 'Zoom In', 'Zoom Out']):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % (extraUrlList[i], extraImage)
    display += ']</p> </center>'

    return display


@app.route('/')
def top():
    return "Hello, world!"
