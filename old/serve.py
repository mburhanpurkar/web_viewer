"""
- Make symlink to plots folder
    mkdir static
    cd static
    ln -s </directory/with/pictures> plots
    cd ..
- stick html templates in their own folder
    mkdir templates
    mv *.html /templates
"""

from flask import Flask
from flask import url_for
from flask import render_template
import os.path
app = Flask(__name__)


@app.route('/bringup_series/<int:zoom>/<int:time>')
def bringup_series(zoom, time):
    urlList, extraUrlList = [], []
    for name in ['input', 'intermediate', 'output']:
        urlList.append(url_for('static', filename='plots/%s_zoom%d_%d.png' % (name, zoom, time)))
    urlList.append(url_for('static', filename='plots/triggers_zoom%d_%d_tree0.png' % (zoom, time)))

    # extraUrlList is prev_time next_time zoom_in zoom_out
    if os.path.isfile('static/plots/input_zoom%d_%d.png' % (zoom, time - 1)):
        extraUrlList.append(url_for('bringup_series', zoom=zoom, time=time - 1))
    else:
        extraUrlList.append(None)

    if os.path.isfile('static/plots/input_zoom%d_%d.png' % (zoom, time + 1)):
        extraUrlList.append(url_for('bringup_series', zoom=zoom, time=time + 1))
    else:
        extraUrlList.append(None)

    if os.path.isfile('static/plots/input_zoom%d_%d.png' % (zoom + 1, time * 2)):
        extraUrlList.append(url_for('bringup_series', zoom=zoom + 1, time=time * 2))
    else:
        extraUrlList.append(None)

    if os.path.isfile('static/plots/input_zoom%d_%d.png' % (zoom - 1, time // 2)):
        extraUrlList.append(url_for('bringup_series', zoom=zoom - 1, time=time // 2))
    else:
        extraUrlList.append(None)

    return render_template('display_series.html', input=urlList[0], intermediate=urlList[1],
                           output=urlList[2], trigger=urlList[3], prevt=extraUrlList[0],
                           nextt=extraUrlList[1], zoomi=extraUrlList[2], zoomo=extraUrlList[3],
                           zoom=zoom, time=time)


@app.route('/')
def top():
    default = url_for('bringup_series', zoom=0, time=0)
    return render_template('index.html', default=default)
