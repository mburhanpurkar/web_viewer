#!/usr/bin/env python
from os import walk
from json import loads
from math import ceil
from flask import Flask, url_for
from flask_classy import FlaskView
app = Flask(__name__)


"""
This is a modified version of the web viewer that works for the new plotter 
and the /data2/web_viewer directory. Running will display a list of users, 
each with a list of pipeline runs in their directories.

Both show_tiles (show all plots) and show_triggers (show the last set of 
plots made) can be viewed, but this does not handle the bonsai dedisperser
outouts as it does not use the python plotter transform (the triggers page 
will just show the last transform in the fnames list).

A persistent web viewer is running from the web_viewer account, and is up 
at frb1.physics.mcgill.ca:5000/! 

DEPENDENCIES
Flask (pip install Flask)
Flask-Classy (pip install flask-classy)

SETUP
In your web_viewer directory, 
    mkdir static
    cd static
    ln -s /data2/web_viewer plots

RUNNING
    ./extract_names.py

The Index page is at: localhost:5001/ for development! 
    (Note: the class is called View because classy makes the base url the prefix to "View" in the class name.)
    Show tiles - displays all outputted plots (default: zoom 0, index1 0, index2 4)
    Show triggers - displays all triggers at a specified zoom (defult: 0)

TODO
- links back to other pages
- check whether dictionary entries exist, if not, reparse (maybe do "don't see your run?" link)
- change defaults for show_tiles (4) and show_triggers (5) -- tell Kendrick he can change those from url
- add show_last_transform, similar to show_triggers
- outer list grouping by prefix, inner list grouping by time (for running different transform chains
  on the same dataset)
- display time ranges next to index/zoom at the top of the page
"""


class Parser():
    """
    This gets fnames (the list of file names at different zoom levels produced by the plotter transform)
    and helpful min/max index and room values by reading from the json file.
    It is also handy because it prevents the files from being re-parsed for each webpage View creates! 
    """
    def __init__(self, path):
        self.fnames = self._get_files(path)
        self.min_zoom, self.min_index = 0, 0
        self.max_zoom = len(self.fnames[0])
        self.max_index = [[len(zoom) for zoom in transform] for transform in self.fnames]

        # Helpful for debug:
        # print "Len fnames (num transforms):  ", len(self.fnames)
        # print "Len fnames[0] (num zooms):    ", len(self.fnames[0])
        # print "Len fnames[0][0] (num tiles): ", len(self.fnames[0][0])
        
    def _get_files(self, path):
        """Outputs a list of plot filenames based on the .json file produced
        from pipeline runs. The output is in the following form:
        [[[z0tf0f0, z0tf0f1, ...], [z1tf0f0, z1tf0f1, ...], ..., [...]],
         [[z0tf1f0, z0tf1f0, ...], [z1tf1f0, z1tf1f1, ...], ..., [...]],
         [...]]
        Currently does not handle the bonsai dedisperser.
        """
        json_file = open(path + '/rf_pipeline_0.json').read()
        json_data = loads(json_file)
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
                        name = file_info['filename']
                        zoom_group.append(name)
                    transform_group.append(zoom_group)
                # The plotter_transform defines zoom_level 0 to be most-zoomed-in, and zoom_level (N-1) to be
                # most-zoomed-out.  The web viewer uses the opposite convention, so we reverse the order here.
                transform_group.reverse()
                fnames.append(transform_group)
        return fnames

    def __str__(self):
        for tf_group in self.fnames:
            for zoom_group in tf_group:
                for file in zoom_group:
                    s += file,
                s += '\n'
            s += '\n\n'
        return s


class Crawler():
    """
    Searches the two top directories pointed to by plots (assumed to be users -> pipeline runs). 
    Parser() is called for each pipeline run, creating a dictionary with information about 
    each pipeline run for each user. 
    Separate class here because I thought it might be nice for it to get other interesting metadata
    at some point. Could just be added to Parser if not. 
    """
    def __init__(self, path='static/plots'):
        self.pipeline_dir = self._get_dirs(path)    

    def _get_dirs(self, path):
        pipeline_dir = dict()
        for user in walk(path).next()[1]:
            temp_usr_data = dict()
            for run in walk('%s/%s' % (path, user)).next()[1]:
                temp_usr_data[run] = Parser('static/plots/%s/%s' % (user, run))
            pipeline_dir[user] = temp_usr_data
        return pipeline_dir


class View(FlaskView):
    """
    Class for the web viewer application. Flask Classy uses the classname to determine the url base
    'xView' would be localhost:/x, hence the name View. Classy also makes web pages for all methods
    that do not begin with an underscore. Urls are autogenerated to be method_name/arg1/arg2...

    The index page shows a list of users, with links to each of the pipeline runs they have done (runs). 
    Show tiles shows all the plots produced by the plotter transform for a particular pipeline run. 
    Show triggers currently shows the last series of plots made, but will eventually display bonsai
    trigger plots. 

    If __init__ is present, it will be called once for each page when the viewer starts (hence, no
    __init__ method). 
    """
    def _get_run_info(self, user, run):
        # Get parser object for corresponding user/run
        self.fnames = master_directories.pipeline_dir[user][run].fnames
        self.min_zoom = master_directories.pipeline_dir[user][run].min_zoom
        self.min_index = master_directories.pipeline_dir[user][run].min_index
        self.max_zoom = master_directories.pipeline_dir[user][run].max_zoom
        self.max_index = master_directories.pipeline_dir[user][run].max_index
    
    def index(self):
        """Home page! Links to each of the users' pipeline runs."""
        display = '<h3>Users</h3>'
        for key in master_directories.pipeline_dir:
            display += '<li><a href="%s">%s</a>\n' % (url_for('View:runs', user=key), key)
        return display


    def runs(self, user):
        """Displays links to the pipeline runs for a particular user."""
        display = '<h3>Pipeline Runs</h3>'
        for run_name in master_directories.pipeline_dir[str(user)]:
            display += '<h4>%s</h4>' % run_name
            display += '<li><a href="%s">Show Tiles</a>\n' % url_for('View:show_tiles', user=user, run=run_name, zoom=0, index1=0, index2=4)
            display += '<li><a href="%s">Show Triggers</a>\n' % url_for('View:show_triggers', user=user, run=run_name, zoom=0)
        display += '<p>[<a href="%s">Back to List of Users</a>]</p>' % url_for('View:index')
        return display


    def show_tiles(self, user, run, zoom, index1, index2):
        """Tiled image viewer! Shows all of the plots produced from a pipeline
        run at different zooms across varying time intervals. The range of pictures
        shown can be changed to any values in the url (index1 is the index of the
        first image shown and index2 is the index of the last and defaults are set
        to 0 and 4 for the link accessed from the home page). """
        
        self._get_run_info(user, run)

        zoom = int(zoom)
        index1 = int(index1)
        index2 = int(index2)

        display = '<h3>Displaying Plots %d-%d at Zoom %d</h3>' % (index1, index2, (self.max_zoom - zoom - 1))  # account for resversal of zoom order in plotter
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
                    display += '<td><img src="%s"></td>' % url_for('static', filename='plots/%s/%s/%s' % (user, run, self.fnames[transform][zoom][index]))
            display += '</tr><tr><td>&nbsp;</td></tr>'

        # Links to user and user/run pages
        display += '<p><center>[&nbsp;&nbsp;&nbsp;<a href="%s">Back to Users List</a>&nbsp;&nbsp;&nbsp;<a href="%s">Back to Your Runs</a>&nbsp;&nbsp;&nbsp;<a href="%s">' \
                   'Show Triggers</a>&nbsp;&nbsp;&nbsp;]</center></p>' % (url_for('View:index'), url_for('View:runs', user=user), url_for('View:show_triggers', user=user, run=run, zoom=0))

        # Plots to be linked
        display += '<p> <center> [&nbsp;&nbsp;&nbsp;'

        if self._check_set(zoom, index1 - 1):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        user=user, run=run, zoom=zoom, index1=index1 - 1, index2=index2 - 1)), 'Prev Time')
        else:
            display += 'Prev Time&nbsp;&nbsp;&nbsp;'
        if self._check_set(zoom, index1 + 1):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        user=user, run=run, zoom=zoom, index1=index1 + 1, index2=index2 + 1)), 'Next Time')
        else:
            display += 'Next Time&nbsp;&nbsp;&nbsp;'

        if self._check_set(zoom, index1 - (index2 - index1)):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        user=user, run=run, zoom=zoom, index1=index1 - (index2 - index1), index2=index2 - (index2 - index1))), 'Jump Back')
        else:
            display += 'Jump Back&nbsp;&nbsp;&nbsp;'
        if self._check_set(zoom, index1 + (index2 - index1)):
            display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('View:show_tiles',
                        user=user, run=run, zoom=zoom, index1=index1 + (index2 - index1), index2=index2 + (index2 - index1))), 'Jump Forward')
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
                        user=user, run=run, zoom=zoom + 1, index1=new_index1, index2=new_index2)), 'Zoom In')
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
                        user=user, run=run, zoom=zoom - 1, index1=new_index1, index2=new_index2)), 'Zoom Out')
        else:
            display += 'Zoom Out&nbsp;&nbsp;&nbsp;'
        display += ']</p> </center>'

        return display


    def show_triggers(self, user, run, zoom):
        """Displays all trigger plots at a given zoom horizontally.
        The zoom level can be changed by changing the value in the url."""

        self._get_run_info(user, run)
        zoom = int(zoom)

        triggerList = self.fnames[-1]
        display = '<h3>Displaying Trigger Plots at Zoom %s</h3>' % (self.max_zoom - zoom - 1)
        display += '<p><center>[&nbsp;&nbsp;&nbsp;<a href="%s">Back to Users List</a>&nbsp;&nbsp;&nbsp;<a href="%s">Back to Your Runs</a>' \
                   '&nbsp;&nbsp;&nbsp;]</center></p>' % (url_for('View:index'), url_for('View:runs', user=user))
        display += '<table cellspacing="0" cellpadding="0"><tr>'

        last_row = 0
        current_row = 0

        for i, trigger in enumerate(triggerList[zoom]):
            temp = url_for('static', filename='plots/%s/%s/%s' % (user, run, trigger))
            if i > 1 and i < self.max_index[-1][zoom] - 2:
                temp_link = url_for('View:show_tiles', user=user, run=run, zoom=zoom, index1=i - 2, index2=i + 2)
                display += '<td><a href="%s"><img src="%s"></a></td>' % (temp_link, temp)
            else:
                display += '<td><img src="%s"></td>' % temp
            current_row += 1
            if (current_row - last_row) == 4:
                last_row = current_row
                display += '</tr><tr><td>&nbsp;</td></tr><tr>'
        display += '</tr></table>'
        return display

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


if __name__ == '__main__':
    master_directories = Crawler()     # dirs contains a dictionary in the form {'user1': {'run1': Parser1, 'run2': Parser2, ...}, ...}
    View.register(app)                 # it is only accessed in the _get_run_info method, index, and runs
    app.run(host='0.0.0.0', port=5000, debug=False)
