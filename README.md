# Web Viewer for the L1 Pipeline
*N.B. the web viewer currently does not handle the plots produced by the 
bonsai dedisperser, meaning Show Last Transform and Show Triggers show the 
second last transform and last transform respectively. This will be updated soon!*

This isn't the prettiest image viewer around, but my goal is to make it as 
useful as possible for digesting pipeline outputs and sharing results!


### Basic Usage
A persistent web viewer is currently up at [frb1.physics.mcgill.ca:5000]
(http://frb1.physics.mcgill.ca:5000) displaying a list of users who have used the
web viewer. Their pipeline runs can be viewed by clicking on their names.

To do your own pipeline run visible to the web viewer, use the `‘web_viewer’`
plot type and `run_for_web_viewer` from the ch_frb_rfi repository. This will
create a new directory (if none already exists) with your username in
/data2/web_viewer/ in which all of your pipeline runs will reside. For
example, the following script:

<pre><code>
import ch_frb_rfi

p = ch_frb_rfi.transform_parameters(plot_type='web_viewer')
t = ch_frb_rfi.transform_chain(p)
s = ch_frb_rfi.acquisitions.small()

ch_frb_rfi.run_for_web_viewer('test-run', s, t)
</code></pre>

would generate a pipeline run in the user’s directory with the name
“test-run-##-##-##-##:##:##” with the hashes being replaced with the date and
time. Note that pipeline names are parsed by prefix - if there are several runs 
with the same prefix, they will be grouped together and indexed by time on your
user page. This was intended to be a helpful way of grouping together pipeline
runs on the same dataset using different transform chains. 

To view a new run, you must click the link to update the directories.

You can also do pipeline runs without using ch_frb_rfi and view them with the web
viewer, but note that the parser expects the final 8 characters of the pipeline
run's name to be a time and will try to group by prefix that way. (The time is 
important to generate a unique link for each pipeline run to prevent browser 
caching from displaying the incorrect plots!)


### Tiled Image Viewer
Show Tiles displays the output of every plotter transform run in the chain. The 
outputs of each plotter transform are displayed in separate rows, with the last 
plotter transform displayed first. It is available at 
frb1.../show_tiles/USER/PIPELINERUN/ZOOM/INDEX0/INDEX1.
If you follow the links from the users page, it will default to displaying plots 
0-3 at the most zoomed out level. 

The Prev Time and Next Time links allow you to increment the visible plots by 1 
and the Jump Back and Jump Forward links allow you to increment the visible 
plots by INDEX1-INDEX0. 

The Zoom In and Zoom Out buttons buttons switch between the zoom levels 
generated by the plotter transform. (That is, zoom levels produced using the 
add_plot_group function within the plotter transform.) Currently, it only 
zooms along the time axis. 

The starting timestamps in seconds for each plot is displayed atop each one. This 
can be useful if you would like to re-run the pipline on a small subsection of data
if, for example, you would like to see the effects of running a different transform chain on
particularly troublesome RFI. The `chime_stream_from_times` stream (currently awaiting 
merging to master) will make this process easier.

Note that the values of the zoom and indices visible can be changed manually. If, for 
example, you would like to view more than 4 plots at once, you may adjust the values in
the url. 


### Show Triggers and Show Last Transform
Show Triggers is available at frb1.../show_triggers/USER/PIPELINERUN/ZOOM. 
It displays all of the trigger plots produced at the zoom level defined in the url 
sequentially, providing a quick, high-level overview for a pipeline run. If you 
follow the links from the users page, it will default to the most zoomed out view. 
Each plot in Show Triggers is a link to a Show Tiles page that, if clicked, will 
allow you to see that section of the pipeline run in more detail. 

Show Last Transform has precisely the same functionality as Show Triggers, but it dislays the 
outputs of the final (non-bonsai) plotter transform that was run.


### Challenges
- For simplicity, the web viewer is currently implemented in Flask, which doesn't appear
  to be the hardiest of web servers. Occasional slow downs sometimes require that you 
  click a link a couple times before the page loads.
