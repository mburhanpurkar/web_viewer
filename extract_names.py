#!/usr/bin/env python
import json
from math import ceil
from flask import Flask
from flask import url_for
from flask_classy import FlaskView
app = Flask(__name__)


"""
This is a modified version of the web viewer that works for the new plotter.

This does not  handle the bonsai dedisperser as it does not use the python
plotter transform (the triggers page will just show the last transform in
the fnames list).

DEPENDENCIES
Flask (pip install Flask)
Flask-Classy (pip install flask-classy)

SETUP
    mkdir static
    cd static
    ln -s /path/to/plots plots
It is assumed that the .json file is in the directory of this code, but that can
be modified by altering the call to get_images()

RUNNING
    ./extract_names.py

The Index page is at: localhost:5000/. 
    (Note: the class is called View because classy makes the base url the prefix to "View" in the class name.)
    Show tiles - displays all outputted plots (default: zoom 0, index1 0, index2 4)
    Show triggers - displays all triggers at a specified zoom (defult: 0)
"""


class View(FlaskView):
    def __init__(self, path='static/plots'):
        self.fnames = self._get_files(path)
        self.min_zoom, self.min_index = 0, 0
        self.max_zoom = len(self.fnames[0])
        self.max_index = [[len(zoom) for zoom in transform] for transform in self.fnames]

        # Helpful for debug:
        # print "Len fnames (num transforms):  ", len(self.fnames)
        # print "Len fnames[0] (num zooms):    ", len(self.fnames[0])
        # print "Len fnames[0][0] (num tiles): ", len(self.fnames[0][0])


    def show_tiles(self, zoom, index1, index2):
        """Tiled image viewer! Shows all of the plots produced from a pipeline
        run at different zooms across varying time intervals. The range of pictures
        shown can be changed to any values in the url (index1 is the index of the
        first image shown and index2 is the index of the last and defaults are set
        to 0 and 4 for the link accessed from the home page). """
        zoom = int(zoom)
        index1 = int(index1)
        index2 = int(index2)

        display = '<h3>Displaying Plots %d-%d at Zoom %d</h3>' % (index1, index2, zoom)
        display += '<table cellspacing="0" cellpadding="0">'

        for transform in reversed(range(len(self.fnames))):    # reversed to show triggers first
            display += '<tr>'
            # First, add plot names
            for index in range(index1, index2 + 1):
                if self._check_image(transform, zoom, index):
                    display += '<td>%s</td>' % self.fnames[transform][zoom][index]
            display += '</tr>'
            # Now, add the images
            for index in range(index1, index2 + 1):
                if self._check_image(transform, zoom, index):
                    display += '<td><img src="%s"></td>' % url_for('static', filename='plots/%s' % (self.fnames[transform][zoom][index]))
            display += '</tr><tr><td>&nbsp;</td></tr>'

        # Plots to be linked
        display += '<p> <center> [&nbsp;&nbsp;&nbsp;'

        if self._check_set(zoom, index1 - 1):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        zoom=zoom, index1=index1 - 1, index2=index2 - 1)), 'Prev Time')
        else:
            display += 'Prev Time&nbsp;&nbsp;&nbsp;'
        if self._check_set(zoom, index1 + 1):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        zoom=zoom, index1=index1 + 1, index2=index2 + 1)), 'Next Time')
        else:
            display += 'Next Time&nbsp;&nbsp;&nbsp;'

        if self._check_set(zoom, index1 - (index2 - index1)):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        zoom=zoom, index1=index1 - (index2 - index1), index2=index2 - (index2 - index1))), 'Jump Back')
        else:
            display += 'Jump Back&nbsp;&nbsp;&nbsp;'
        if self._check_set(zoom, index1 + (index2 - index1)):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
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

        if self._check_set(zoom + 1, index1 * 2):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
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

        if self._check_set(zoom - 1, index1 // 2):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        zoom=zoom - 1, index1=new_index1, index2=new_index2)), 'Zoom Out')
        else:
            display += 'Zoom Out&nbsp;&nbsp;&nbsp;'

        display += ']</p> </center>'

        return display


    def show_triggers(self, zoom):
        """Displays all trigger plots at a given zoom horizontally.
        The zoom level can be changed by changing the value in the url."""
        zoom = int(zoom)

        triggerList = self.fnames[-1]
        display = '<h3>Displaying Trigger Plots at Zoom %s</h3>' % zoom
        display += '<table cellspacing="0" cellpadding="0"><tr>'

        last_row = 0
        current_row = 0

        for i, trigger in enumerate(triggerList[zoom]):
            temp = url_for('static', filename='plots/%s' % trigger)
            if i > 1 and i < self.max_index[-1][zoom] - 2:
                temp_link = url_for('View:show_tiles', zoom=zoom, index1=i - 2, index2=i + 2)
                display += '<td><a href="%s"><img src="%s"></a></td>' % (temp_link, temp)
            else:
                display += '<td><img src="%s"></td>' % temp
            current_row += 1
            if (current_row - last_row) == 4:
                last_row = current_row
                display += '</tr><tr><td>&nbsp;</td></tr><tr>'
        display += '</tr></table>'

        return display


    def index(self):
        """Home page!"""
        s = '<li> <a href="%s">Show Tiles (default: zoom 0, index 0-4)</a>\n' % url_for('View:show_tiles', zoom=0, index1=0, index2=4)
        s += '<li> <a href="%s">Show Triggers (default: zoom 0)</a>\n' % url_for('View:show_triggers', zoom=0)
        return s


    def _get_files(self, path):
        """Outputs a list of plot filenames based on the .json file produced
        from pipeline runs. The output is in the following form:
        [[[z0tf0f0, z0tf0f1, ...], [z1tf0f0, z1tf0f1, ...], ..., [...]],
         [[z0tf1f0, z0tf1f0, ...], [z1tf1f0, z1tf1f1, ...], ..., [...]],
         [...]]
        Currently does not handle the bonsai dedisperser.
        """
        json_file = open(path + '/rf_pipeline_0.json').read()
        json_data = json.loads(json_file)
        transforms_list = json_data['transforms']
        fnames = []

        for transform in transforms_list:
            # This will iterate over all the transforms
            if transform['name'] == 'plotter_transform':
                # Start a new list for a new transform
                transform_group = []
                for zoom_level in transform['plots']:
                    # This iterates over each zoom level (plot group) for a particular plotter transform (list of dictionaries)
                    zoom_group = []
                    for file_info in zoom_level['files'][0]:
                        # We can finally access the file names :)
                        name = file_info['filename'][2:]
                        zoom_group.append(name)
                    transform_group.append(zoom_group)
                transform_group.reverse()
                fnames.append(transform_group)
        return fnames


    def _check_set(self, zoom, index):
        """Checks whether a link should be added at the top of the page
        to the next set of images in the series."""
        # For whatever reason, there are differing number of plots for
        # different transforms of the same zoom. This only returns false
        # if there are absolutely no images left (i.e. it will return true
        # if there is only one image available at a particular zoom because
        # one transform happened to output more than the rest). This means
        # we need to check again when we are displaying each individual
        # image whether it exists.
        if zoom >= self.max_zoom or zoom < self.min_zoom or index < self.min_index or index >= max([element[zoom] for element in self.max_index]):
            return False
        return True


    def _check_image(self, transform, zoom, index):
        """Checks whether a particular image is available (because some transforms seem
        to produce more plots than others)"""
        if zoom >= self.max_zoom or zoom < self.min_zoom or index < self.min_index or index >= self.max_index[transform][zoom]:
            return False
        return True


    def __str__(self):
        for tf_group in self.fnames:
            for zoom_group in tf_group:
                for file in zoom_group:
                    s += file,
                s += '\n'
            s += '\n\n'
        return s


View.register(app)
if __name__ == '__main__':
    app.run()

