#!/usr/bin/env python
from os import walk
from os.path import isfile
from json import loads
from math import ceil
from flask import Flask, url_for
app = Flask(__name__)


"""
NB For now, we are assuming the bonsai transform is the final plot-producing transform in the pipeline run!

This is a modified version of the web viewer that works for the new plotter and the /data2/web_viewer 
directory. Running will display a list of users, each with a list of pipeline runs in their directories.

A persistent web viewer is running from the web_viewer account, and is up at frb1.physics.mcgill.ca:5000/!
    Show tiles - displays all outputted plots (default: zoom 0*, index1 0, index2 4)
    Show triggers - displays all triggers at a specified zoom - must be modified from url (defult: 0)
    Show last transform - same as show triggers, but for the last plotter transform (note this will display
    trigger plots if the bonsai plotter produced multiple groups of plots (with the multi-tree plotter)

DEPENDENCIES
Flask (pip install Flask)

SETUP
In your web_viewer directory, 
    mkdir static
    cd static
    ln -s /data2/web_viewer plots

RUNNING
    uwsgi --socket 0.0.0.0:5000 --plugin python --protocol=http -w wsgi --callable app


*Slightly annoying note: the zoom levels in the url are opposite those in the filenames, hence the 
 'reverse()' in the Parser class. This is only really relevant if a user is modifying the zoom level
 by hand from the url. 

"""


class Parser():
    """
    This gets fnames (the list of file names at different zoom levels produced by the plotter transforms)
    and helpful min/max index and zoom values by reading from the json file. This is called upon initialization
    and whenever the update directories page is navigated to. 
    """
    def __init__(self, path):
        self.fnames, self.ftimes = self._get_files(path)
        if self.fnames is not None and self._check_zoom():
            self.min_zoom, self.min_index = 0, 0
            self.max_zoom = len(self.fnames[0])
            self.max_index = [[len(zoom) for zoom in transform] for transform in self.fnames]
        else:   # In case a directory does not contain plots or transforms contain a different number of zoom levels
            self.min_zoom, self.min_index = None, None
            self.max_zoom = None
            self.max_index = None
        
        # Helpful for debug:
        # print "Len fnames (num transforms):  ", len(self.fnames)
        # print "Len fnames[0] (num zooms):    ", len(self.fnames[0])
        # print "Len fnames[0][0] (num tiles): ", len(self.fnames[0][0])
        
    def _get_files(self, path):
        """Outputs a list of plot filenames and plot start times as a tuple based on the .json file produced from 
        pipeline runs. The output is in the following form:
        [[[z0tf0f0, z0tf0f1, ...], [z1tf0f0, z1tf0f1, ...], ..., [...]],
         [[z0tf1f0, z0tf1f0, ...], [z1tf1f0, z1tf1f1, ...], ..., [...]],
         [...]]
        """
        json_file = open(path + '/rf_pipeline_0.json').read()
        json_data = loads(json_file)
        transforms_list = json_data['transforms']
        fnames = []
        ftimes = []

        s_per_sample = (json_data['t1'] - json_data['t0']) / json_data['nsamples']  # number of seconds per sample
        
        for transform in transforms_list:
            # Here, we establish whether we're using the regular plotter or old bonsai plotter (in which case, we don't need to 
            # worry about separating part of the outputs into different rows) or the new bonsai plotter
            if ('plotter_transform' in transform['name'] and 'plots' in transform) or \
                ('bonsai_dedisperser' in transform['name'] and 'plots' in transform and 'n_plot_groups' not in transform):
                nloops = 1
            elif 'bonsai_dedisperser' in transform['name'] and 'plots' in transform and 'n_plot_groups' in transform:
                nloops = transform['n_plot_groups']
            else:
                nloops = -1

            # This is for the regular plotter transform or the bonsai transform with only one zoom level. This will just 
            # index everything as normal. 
            if nloops == 1:
                n = 0
                group_size = len(transform['plots']) / nloops
                while n < len(transform['plots']):
                    # Start a new list for a new transform
                    ftransform_group = []
                    ttransform_group = []
                    for zoom_level in transform['plots'][n:n+group_size]:
                        # This iterates over each zoom level (plot group) for a particular plotter transform (list of dictionaries)
                        fzoom_group = []
                        tzoom_group = []
                        group_it0 = zoom_level['it0']
                        for file_info in zoom_level['files'][0]:
                            # We can finally access the file names :)
                            name = file_info['filename']
                            time = (group_it0 + file_info['it0']) * s_per_sample + json_data['t0']   # start time of the plot in seconds
                            fzoom_group.append(name)
                            tzoom_group.append(time)
                        ftransform_group.append(fzoom_group)
                        ttransform_group.append(tzoom_group)
                    # The plotter_transform defines zoom_level 0 to be most-zoomed-in, and zoom_level (N-1) to be
                    # most-zoomed-out. The web viewer uses the opposite convention, so we reverse the order here.
                    ftransform_group.reverse()
                    ttransform_group.reverse()
                    fnames.append(ftransform_group)
                    ftimes.append(ttransform_group)
                    n += group_size

            # This is for a bonsai transform that plots multiple trees. We need to reverse the list at the beginning so that tree 0
            # shows up in the first row and remove the reversals at the end so the zoom levels are displayed properly. A bit of an
            # ugly hack, but it works. 
            if nloops > 1:
                n = 0
                group_size = len(transform['plots']) / nloops
                transform['plots'].reverse()
                while n < len(transform['plots']):
                    # Start a new list for a new transform
                    ftransform_group = []
                    ttransform_group = []
                    for zoom_level in transform['plots'][n:n+group_size]:
                        # This iterates over each zoom level (plot group) for a particular plotter transform (list of dictionaries)
                        fzoom_group = []
                        tzoom_group = []
                        group_it0 = zoom_level['it0']
                        for file_info in zoom_level['files'][0]:
                            # We can finally access the file names :)
                            name = file_info['filename']
                            time = (group_it0 + file_info['it0']) * s_per_sample + json_data['t0']   # start time of the plot in seconds
                            fzoom_group.append(name)
                            tzoom_group.append(time)
                        ftransform_group.append(fzoom_group)
                        ttransform_group.append(tzoom_group)
                    # The plotter_transform defines zoom_level 0 to be most-zoomed-in, and zoom_level (N-1) to be
                    # most-zoomed-out. The web viewer uses the opposite convention, so we reverse the order here.
                    ftransform_group
                    ttransform_group
                    fnames.append(ftransform_group)
                    ftimes.append(ttransform_group)
                    n += group_size

            if nloops > 1:
                # It is using the new bonsai plotter, so we must reverse the order of the transforms so tree 0 shows up first
                pass

        if len(fnames) != 0:
            return fnames, ftimes
        else:
            return None, None

    def _check_zoom(self):
        if self.fnames is None:
            return False
        a = len(self.fnames[0])
        for element in self.fnames:
            if len(element) != a:
                return False
        return True

    def __str__(self):
        s = ''
        if self.fnames is None:
            return 'None\n'
        tf_counter = 0
        for tf_group in self.fnames:
            s+= '* TRANSFORM ' + str(tf_counter) + ' *\n'
            tf_counter += 1
            zoom_counter = 0
            for zoom_group in tf_group:
                s += 'ZOOM ' + str(zoom_counter) + '\n'
                zoom_counter += 1
                for file in zoom_group:
                    s += str(file) + ' '
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
        self.path = path
        self.pipeline_dir = self._get_dirs()

    def _get_dirs(self):
        pipeline_dir = dict()
        for user in walk(self.path).next()[1]:
            temp_usr_data = dict()
            for run in walk('%s/%s' % (self.path, user)).next()[1]:
                if run[0] != '_' and isfile('static/plots/' + user + '/' + run + '/rf_pipeline_0.json'):  
                    temp_usr_data[run] = Parser('static/plots/%s/%s' % (user, run))
            pipeline_dir[user] = temp_usr_data
        return pipeline_dir

    def _update_user(self, user):
        """This will just return the information to be added to the section of the dictionary for a particular user, 
        not a whole new dictionary of parser instances, as _get_dirs does."""
        temp_usr_data = dict()
        for run in walk('%s/%s' % (self.path, user)).next()[1]:
            if run[0] != '_' and isfile('static/plots/' + user + '/' + run + '/rf_pipeline_0.json'):
                temp_usr_data[run] = Parser('static/plots/%s/%s' % (user, run))
        return temp_usr_data

    def __str__(self):
        s = ""
        for user in self.pipeline_dir:
            if user == "mburhanpurkar":
                s += '*' * 160 + '\n'
                s += "USER: %s\n" % user
                for run in self.pipeline_dir[user]:
                    s += '-' * 160 + '\n'
                    s +=  "RUN: %s\n" % run
                    s += self.pipeline_dir[user][run].__str__()
        return s


"""
Class for the web viewer application. 

The index page shows a list of users, with links to each of the pipeline runs they have done (runs). 
Show tiles shows all the plots produced by the plotter transform for a particular pipeline run. 
Show triggers currently shows the last series of plots made, but will eventually display bonsai
trigger plots. 
Show last transform is the same as Show triggers, but for the second last plotting transform run.

If __init__ is present, it will be called once for each page when the viewer starts (hence, no
__init__ method). 
"""
def _get_run_info(user, run):
    # Get parser object for corresponding user/run
    fnames = master_directories.pipeline_dir[user][run].fnames
    ftimes = master_directories.pipeline_dir[user][run].ftimes
    min_zoom = master_directories.pipeline_dir[user][run].min_zoom
    min_index = master_directories.pipeline_dir[user][run].min_index
    max_zoom = master_directories.pipeline_dir[user][run].max_zoom
    max_index = master_directories.pipeline_dir[user][run].max_index
    return fnames, ftimes, min_zoom, min_index, max_zoom, max_index

@app.route("/")
def index():
    """Home page! Links to each of the users' pipeline runs."""

    display = '<h3>Users</h3>'
    for key in sorted(master_directories.pipeline_dir):
        display += '<li><a href="%s">%s</a>\n' % (url_for('runs', user=key), key)
    display += '<p>**Exciting news! The update directories button on your runs page now only updates your directories, meaning updating your \
               directories will no longer take an obscene 15 seconds (unless you\'re Masoud)! The button is now conveniently located at the top \
               of the page and points to your runs page after it is finished! Yay!**</p>'
    display += '<p><a href="%s">Click here to update all users\'s directories.</a></p>' % url_for('update_directories')
    display += '<p><a href="https://github.com/mburhanpurkar/web_viewer">Instructions / Help / Documentation</a></p>'
    return display

@app.route("/<string:user>/runs")
def runs(user):
    """Displays links to the pipeline runs for a particular user."""

    display = '<h3>%s\'s pipeline runs</h3>' % user
    display += '<p>[&nbsp;&nbsp;&nbsp;<a href="%s">Back to List of Users</a>&nbsp;&nbsp;&nbsp;<a href="%s">Update Directories</a>&nbsp;&nbsp;&nbsp;]</p>' \
               % (url_for('index'), url_for('update_your_directories', user=user))

    # Sort runs by prefix {prefix1: [run1, run2, run3, ...], prefix2: [...], ...}
    sorted_runs = dict()
    for run in master_directories.pipeline_dir[str(user)]:
        prefix = run[:-18]
        if prefix not in sorted_runs:
            # We need to add a new key
            sorted_runs[prefix] = [run]
        else:
            # Add to existing list
            sorted_runs[prefix].append(run)

    for prefix in sorted(sorted_runs):
        display += '<h4>%s</h4>' % prefix
        for run in sorted(sorted_runs[prefix]):
            display += '<h5>%s</h5>' % run[-17:]
            display += '<li><a href="%s">Show Tiles</a>\n' % url_for('show_tiles', user=user, run=run, zoom=0, index1=0, index2=3)
            display += '<li><a href="%s">Show Triggers</a>\n' % url_for('show_triggers', user=user, run=run, zoom=0)
            display += '<li><a href="%s">Show Last Transform</a>\n' % url_for('show_last_transform', user=user, run=run, zoom=0)
    return display

@app.route("/<string:user>/<string:run>/show_tiles/<int:zoom>/<int:index1>/<int:index2>")
def show_tiles(user, run, zoom, index1, index2):
    """Tiled image viewer! Shows all of the plots produced from a pipeline run at different zooms 
    across varying time intervals. The range of pictures shown can be changed to any values in 
    the url (index1 is the index of the first image shown and index2 is the index of the last 
    and defaults are set to 0 and 4 for the link accessed from the home page). The numbers displayed
    are the time in seconds at the start of the plot."""

    fnames, ftimes, min_zoom, min_index, max_zoom, max_index = _get_run_info(user, run)

    if fnames is None:
        return 'No files found.'

    if max_index is None:
        s = 'The number of zoom levels produced by the pipeline plotter was unequal to the number of plots produced ' \
            'by the bonsai plotter. This pipeline run cannot be displayed.'
        return s

    display = '<h3>Displaying Plots %d-%d at Zoom %d</h3>' % (index1, index2, (max_zoom - zoom - 1))  # account for resversal of zoom order in plotter
    display += '<table cellspacing="0" cellpadding="0">'

    for transform in reversed(range(len(fnames))):    # reversed to show triggers first
        display += '<tr>'
        # First, add plot times 
        for index in range(index1, index2 + 1):
            if _check_image(user, run, transform, zoom, index):
                display += '<td>%s</td>' % ftimes[transform][zoom][index]
        display += '</tr>'
        # Now, add the images
        for index in range(index1, index2 + 1):
            if _check_image(user, run, transform, zoom, index):
                display += '<td><img src="%s"></td>' % url_for('static', filename='plots/%s/%s/%s' % (user, run, fnames[transform][zoom][index]))
        display += '</tr><tr><td>&nbsp;</td></tr>'

    # Links to user and user/run pages
    display += '<p><center>[&nbsp;&nbsp;&nbsp;<a href="%s">Back to Users List</a>&nbsp;&nbsp;&nbsp;<a href="%s">Back to Your Runs</a>&nbsp;&nbsp;&nbsp;<a href="%s">' \
               'Show Triggers</a>&nbsp;&nbsp;&nbsp;<a href="%s">Show Last Transform</a>&nbsp;&nbsp;&nbsp;]</center></p>' \
               % (url_for('index'), url_for('runs', user=user), url_for('show_triggers', user=user, run=run, zoom=0), 
                  url_for('show_last_transform', user=user, run=run, zoom=zoom))

    # Plots to be linked
    display += '<p> <center> [&nbsp;&nbsp;&nbsp;'

    if _check_set(user, run, zoom, index1 - 1):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    user=user, run=run, zoom=zoom, index1=index1 - 1, index2=index2 - 1)), 'Prev Time')
    else:
        display += 'Prev Time&nbsp;&nbsp;&nbsp;'

    if _check_set(user, run, zoom, index1 + 1):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    user=user, run=run, zoom=zoom, index1=index1 + 1, index2=index2 + 1)), 'Next Time')
    else:
        display += 'Next Time&nbsp;&nbsp;&nbsp;'

    if _check_set(user, run, zoom, index1 - (index2 - index1)):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    user=user, run=run, zoom=zoom, index1=index1 - (index2 - index1), index2=index2 - (index2 - index1))), 'Jump Back')
    else:
        display += 'Jump Back&nbsp;&nbsp;&nbsp;'

    if _check_set(user, run, zoom, index1 + (index2 - index1)):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
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

    if _check_set(user, run, zoom + 1, index1 * 2):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    user=user, run=run, zoom=zoom + 1, index1=int(new_index1), index2=int(new_index2))), 'Zoom In')
    else:
        display += 'Zoom In&nbsp;&nbsp;&nbsp;'

    # More column preservation
    if (index2 - index1) % 2 == 0:
        new_index1 = (index1 - (index2 - index1) / 2) / 2
        new_index2 = (index2 + (index2 - index1) / 2) / 2
    else:
        new_index1 = (index1 - ceil((index2 - index1) / 2)) / 2
        new_index2 = (index2 + (ceil((index2 - index1) / 2) + 1)) / 2

    if _check_set(user, run, zoom - 1, index1 // 2):
        display += '<a href="%s">%s</a>&nbsp;&nbsp;&nbsp;' % ((url_for('show_tiles',
                    user=user, run=run, zoom=zoom - 1, index1=int(new_index1), index2=int(new_index2))), 'Zoom Out')
    else:
        display += 'Zoom Out&nbsp;&nbsp;&nbsp;'
    display += ']</p> </center>'
    return display

@app.route("/<string:user>/<string:run>/show_last_transform/<int:zoom>")
def show_last_transform(user, run, zoom):
    """Displays the plots for the last transform at a given zoom horizontally. The zoom level can be changed by 
    changing the value in the url. Currently just indexes the second last value in fnames."""

    fnames, ftimes, min_zoom, min_index, max_zoom, max_index = _get_run_info(user, run)

    if fnames is None:
        return 'No files found.'

    if max_index is None:
        s = 'The number of zoom levels produced by the pipeline plotter was unequal to the number of plots produced ' \
            'by the bonsai plotter. This pipeline run cannot be displayed.'
        return s

    triggerList = fnames[-2]
    display = '<h3>Displaying Last Transform Plots at Zoom %s</h3>' % (max_zoom - zoom - 1)
    display += '<p><center>[&nbsp;&nbsp;&nbsp;<a href="%s">Back to Users List</a>&nbsp;&nbsp;&nbsp;<a href="%s">Back to Your Runs</a>' \
               '&nbsp;&nbsp;&nbsp;]</center></p>' % (url_for('index'), url_for('runs', user=user))
    display += '<table cellspacing="0" cellpadding="0"><tr>'

    last_row = 0
    current_row = 0

    for i, trigger in enumerate(triggerList[zoom]):
        temp = url_for('static', filename='plots/%s/%s/%s' % (user, run, trigger))
        if i > 1 and i < max_index[-1][zoom] - 2:
            temp_link = url_for('show_tiles', user=user, run=run, zoom=zoom, index1=i - 2, index2=i + 1)
            display += '<td><a href="%s"><img src="%s"></a></td>' % (temp_link, temp)
        else:
            display += '<td><img src="%s"></td>' % temp
        current_row += 1
        if (current_row - last_row) == 5:
            last_row = current_row
            display += '</tr><tr><td>&nbsp;</td></tr><tr>'
    display += '</tr></table>'
    return display

@app.route("/<string:user>/<string:run>/show_triggers/<int:zoom>")
def show_triggers(user, run, zoom):
    """Displays all trigger plots at a given zoom horizontally. The zoom level can be changed by changing the value in the url. 
    Currently just indexes the last value in fnames."""

    fnames, ftimes, min_zoom, min_index, max_zoom, max_index = _get_run_info(user, run)

    if fnames is None:
        return 'No files found.'

    if max_index is None:
        s = 'The number of zoom levels produced by the pipeline plotter was unequal to the number of plots produced ' \
            'by the bonsai plotter. This pipeline run cannot be displayed.'
        return s

    zoom = int(zoom)

    triggerList = fnames[-1]
    display = '<h3>Displaying Trigger Plots at Zoom %s</h3>' % (max_zoom - zoom - 1)
    display += '<p><center>[&nbsp;&nbsp;&nbsp;<a href="%s">Back to Users List</a>&nbsp;&nbsp;&nbsp;<a href="%s">Back to Your Runs</a>' \
               '&nbsp;&nbsp;&nbsp;]</center></p>' % (url_for('index'), url_for('runs', user=user))
    display += '<table cellspacing="0" cellpadding="0"><tr>'

    last_row = 0
    current_row = 0

    for i, trigger in enumerate(triggerList[zoom]):
        temp = url_for('static', filename='plots/%s/%s/%s' % (user, run, trigger))
        if i > 1 and i < max_index[-1][zoom] - 2:
            temp_link = url_for('show_tiles', user=user, run=run, zoom=zoom, index1=i - 2, index2=i + 1)
            display += '<td><a href="%s"><img src="%s"></a></td>' % (temp_link, temp)
        else:
            display += '<td><img src="%s"></td>' % temp
        current_row += 1
        if (current_row - last_row) == 5:
            last_row = current_row
            display += '</tr><tr><td>&nbsp;</td></tr><tr>'
    display += '</tr></table>'
    return display

@app.route("/update_directories")
def update_directories():
    """Going here updates master_directories"""
    # Update directories... can do this better by re-writing crawler to check for keys
    # but it's not large enough to warrant doing that for now I think. 
    global master_directories
    master_directories = Crawler()
    # Provide link to user page
    display = '<center><p>Directories Updated!</p><p><a href="%s">Back to Users Page</a></p></center>' % url_for('index')
    return display

@app.route("/update_directories/<string:user>")
def update_your_directories(user):
    """Runs update_directories, but only for the specified user to speed things up."""
    global master_directories
    master_directories.pipeline_dir[user] = master_directories._update_user(user)
    display =  '<center><p>Directories updated for %s!</p><p><a href="%s">Back to your runs</a></p></center>' % (user, url_for('runs', user=user))
    return display

def _check_set(user, run, zoom, index):
    """Checks whether a link should be added at the top of the page to the next set of images in the series."""
    # For whatever reason, there are differing number of plots for
    # different transforms of the same zoom. This only returns false
    # if there are absolutely no images left (i.e. it will return true
    # if there is only one image available at a particular zoom because
    # one transform happened to output more than the rest). This means
    # we need to check again when we are displaying each individual
    # image whether it exists.
    fnames, ftimes, min_zoom, min_index, max_zoom, max_index = _get_run_info(user, run)
    if zoom >= max_zoom or zoom < min_zoom or index < min_index or index >= max([element[zoom] for element in max_index]):
        return False
    return True

def _check_image(user, run, transform, zoom, index):
    """Checks whether a particular image is available (because some transforms seem to produce more plots than others)"""
    fnames, ftimes, min_zoom, min_index, max_zoom, max_index = _get_run_info(user, run)
    if zoom >= max_zoom or zoom < min_zoom or index < min_index or index >= max_index[transform][zoom]:
        return False
    return True


master_directories = Crawler()     # dirs contains a dictionary in the form {'user1': {'run1': Parser1, 'run2': Parser2, ...}, ...}
