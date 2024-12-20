from flask import Flask, render_template, request, redirect, url_for
import subprocess
import datetime as dt
import os

DEBUG = os.environ.get("DEBUG", False)
ROOT_PATH = os.environ.get("ROOT_PATH", '/')
SOURCES = os.environ.get("SOURCES", "ADF Front,ADF Back,ADF Duplex").split(",")
MODES = os.environ.get("MODES", "Lineart,Halftone,Gray,Color").split(",")
RESOLUTIONS = os.environ.get("RESOLUTIONS", "50,100,150,200,250,300,350,400,450,500,550,600").split(",")
DATE_FORMAT = os.environ.get("DATE_FORMAT", "%Y-%m-%d-%H-%M-%S")

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
    return now.strftime(DATE_FORMAT)

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
        resolutions=RESOLUTIONS,
        sources=SOURCES,
        modes=MODES,
        message=message)

@app.route(ROOT_PATH, methods=['GET','POST'])
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
            name = f'{request.form['date']}-{request.form['name']}'
            mode = request.form['mode']
            resolution = f'{int(request.form['resolution'])}dpi'
            source = request.form['source']
            env_vars = os.environ.copy()
            env_vars["FILENAME"] = name
            env_vars["MODE"] = mode
            env_vars["RESOLUTION"] = resolution
            env_vars["SOURCE"] = source
            
            # Call the scan_adf.sh script with the provided arguments
            subprocess.Popen(['/bin/bash','scan_adf.sh'], env=env_vars)
            return render_root_path(default_date, message='Scan request submitted successfully!')
        else:
            return render_root_path(default_date)
    except Exception as _:
        if DEBUG:
            raise
        else:
            return render_root_path(default_date, 'There was an error. Check the server.')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=DEBUG)
