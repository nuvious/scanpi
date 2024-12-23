from flask import Flask, render_template, request, session, redirect, url_for
import subprocess
import datetime as dt
import os
import yaml
import logging
import sys
import pyotp
import io
import base64
import qrcode
import uuid

_LOG = logging.getLogger(__name__)

# Set the configuration search path
_SEARCH_PATH = [
    'config.yaml',
    os.path.join(os.path.expanduser('~'), '.scanpi/config.yaml'),
    '/etc/scanpi/config.yaml'
]

# Load the configuration
CONFIG = None
CONFIG_PATH = None
for path in _SEARCH_PATH:
    if os.path.isfile(path):
        with open(path) as f:
            try:
                CONFIG = yaml.safe_load(f)
                CONFIG_PATH = path
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

# If the configuration has an OTP secret, create the TOTP object
_TOTP : pyotp.TOTP = None
if 'secret_key' in CONFIG:
    _TOTP = pyotp.TOTP(CONFIG['secret_key'])

# Set debug
if CONFIG['debug']:
    _LOG.setLevel(logging.DEBUG)

# An explicit lockfile path isn't required and should default to /var/lock
PROCESSING_LOCKFILE = CONFIG.get('processing_lockfile', '/var/lock/.scannub')

# Setup app with a secret key
app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

# Set session timeout
_SESSION_TIMEOUT = CONFIG.get('session_timeout', 30)
app.config['PERMANENT_SESSION_LIFETIME'] = dt.timedelta(minutes=_SESSION_TIMEOUT)
app.permanent_session_lifetime = dt.timedelta(minutes=_SESSION_TIMEOUT) 

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


@app.route("/login", methods=['GET','POST'])
def login():
    """Login path. Takes a OTP for authentication.

    Returns:
        str: The rendered template
    """
    if request.method == 'POST':
        otp = request.form['otp']
        otp_now = _TOTP.now()
        _LOG.debug(f"OTP: {otp} REQUIRED OTP: {otp_now}")
        if _TOTP.now() == otp:
            session['id'] = uuid.uuid4().hex
            _LOG.debug(f"Login successful!")
            return redirect(url_for('root_path'))
        else:
            _LOG.debug(f"Login failed!")
            return render_template("login.html")
    else:
        return render_template("login.html")

def render_setup():
    """
    Creates an OTP secret and renders a QR code with instructions to print and
    display the QR code near the scanner. This is what allows users who are
    in physical access of the scanner to register the OTP and use it. This is
    mainly done for ease-of-use for multiple users.

    Returns:
        str: The rendered template
    """
    global CONFIG, _TOTP
    CONFIG['secret_key'] = pyotp.random_base32()
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(CONFIG, f)
    otp_uri = f"otpauth://totp/ScanPi?secret={CONFIG['secret_key']}"
    qr_img = qrcode.make(otp_uri)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    _TOTP = pyotp.TOTP(CONFIG['secret_key'])
    return render_template(
        "setup.html", qr_img=qr_img_base64, secret_str=CONFIG['secret_key']
    )

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

@app.route('/', methods=['GET','POST'])
def root_path():
    """
    Front page renderer that also launches the scanner script. Root path
    defaults to '/' but can be modified via the ROOT_PATH environment variable.

    Returns:
        str: The rendered root path.
    """
    default_date = current_datetime()
    # Initial setup for OTP secret
    if 'secret_key' not in CONFIG:
        return render_setup()
    elif session.get('id') is None:
        return redirect(url_for("login"))
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
