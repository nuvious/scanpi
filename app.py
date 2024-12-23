from flask import Flask, render_template, request
import subprocess
import datetime as dt
import os
import yaml
import logging
import sys

_LOG = logging.getLogger(__name__)

_SEARCH_PATH = [
    'config.yaml',
    os.path.join(os.path.expanduser('~'), '.scanpi/config.yaml'),
    '/etc/scanpi/config.yaml'
]

CONFIG = None
for path in _SEARCH_PATH:
    if os.path.isfile(path):
        with open(path) as f:
            try:
                CONFIG=yaml.safe_load(f)
                break
            except yaml.YAMLError as _:
                _LOG.error(
                    "Error in configuration file %s.", path,
                    exc_info=sys.exc_info()
                )
                sys.exit(1)

if CONFIG is None:
    _LOG.error(
        "No configuration found. "
        "Place configuration in one of the following paths: %s", 
        _SEARCH_PATH
    )
    sys.exit(1)

# Set debug
if CONFIG['debug']:
    _LOG.setLevel(logging.DEBUG)

# An explicit lockfile path isn't required and should default to /var/lock
PROCESSING_LOCKFILE = CONFIG.get('processing_lockfile', '/var/lock/.scannub')

app = Flask(__name__)

# Function to generate current date-time formatted as specified
def current_datetime():
    """
    Generates a datetime string for the file folder and name. Format defaults
    to %Y-%m-%d-%H-%M-%S and can be modified by setting the DATE_FORMAT
    environment variable.

    Returns:
        str: Formatted datetime string
    """
    now = dt.datetime.now()
    return now.strftime(CONFIG['date_format'])

def render_root_path(default_date, message=""):
    """Renders the root path with an optional message

    Args:
        default_date (str): A datetime string
        message (str, optional): A status message. Defaults to "".

    Returns:
        str: The rendered template
    """
    return render_template('form.html', 
        default_date=default_date, 
        resolutions=CONFIG['resolutions'],
        sources=CONFIG['sources'],
        modes=CONFIG['modes'],
        message=message)

@app.route(CONFIG['root_path'], methods=['GET','POST'])
def root_path():
    """
    Front page renderer that also launches the scanner script. Root path
    defaults to '/' but can be modified via the ROOT_PATH environment variable.

    Returns:
        str: The rendered root path.
    """
    default_date = current_datetime()
    try:
        if request.method == 'POST':
            # Extract form data
            name = f"{request.form['date']}-{request.form['name']}"
            mode = request.form['mode']
            resolution = f"{int(request.form['resolution'])}dpi"
            source = request.form['source']
            env_vars = os.environ.copy()
            env_vars["FILENAME"] = name
            env_vars["MODE"] = mode
            env_vars["RESOLUTION"] = resolution
            env_vars["SOURCE"] = source
            env_vars["SCAN_DIRECTORY"] = CONFIG['scan_directory']
            env_vars["PROCESSING_LOCKFILE"] = PROCESSING_LOCKFILE
            
            # Call the scan_adf.sh script with the provided arguments
            subprocess.Popen(['/bin/bash','scan_adf.sh'], env=env_vars)
            return render_root_path(
                default_date, 
                message='Scan request submitted successfully!'
            )
        else:
            return render_root_path(default_date)
    except Exception as e:
        _LOG.debug("Error scanning %s.", name, exc_info=sys.exc_info())
        if CONFIG['debug']:
            return render_root_path(
                'Error processing scan %s:\n%s', name, e
            )
        else:
            return render_root_path(
                default_date, 'There was an error. Check the server.'
            )

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=CONFIG['debug'])
