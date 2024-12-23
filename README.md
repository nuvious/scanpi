# ScanPi

A simple self-hosted scanner that is designed to allow scanning using document
scanners to automatically scan, save and ocr documents. While called ScanPi it
could be deployed to any system. Designed to give USB scanners or any scanner
that is supported by [scanadf](https://linux.die.net/man/1/scanadf) a second
life.

A list of supported hardware can be found at the
[SANE project site](http://www.sane-project.org/sane-mfgs.html).

## Demo

[![ScanPi Video Demo](http://img.youtube.com/vi/9Ftn02hEa44/0.jpg)](http://www.youtube.com/watch?v=9Ftn02hEa44 "ScanPi Video Demo")

NOTE: Demo video needs updating with authentication example.

## Quickstart

First install flask, scanadf and ocrmypdf. The application needs to run as root
for `scanadf` so install as the root user.

```bash
sudo pip3 install -r requirements.txt
sudo apt update
sudo apt install scanadf ocrmypdf -y
```

Next, create a configuration file `config.yaml` in either the directory the app
will be launched, `~/.config/scanpi/` of the user that the app will be run
under, or `/etc/scanpi/`.

```yaml
# Date format that is pre-pended to each generated pdf name
date_format: '%Y-%m-%d-%H-%M-%S'
# Set true to run in debug with extra debug output (developer use)
debug: false
# Scanner modes for the scanner
modes:
- Gray
- Halftone
- Color
- Lineart
# DPI resolutions for the scanner
resolutions:
- 100
- 200
- 300
- 400
- 500
- 600
# Where to save the scanned pdfs
scan_directory: /mnt/scannub
# This will be generated on first run but can be set manually if desired
# secret_key: [some OTP secret]
# Sources supported by the scanner
sources:
- ADF Front
- ADF Back
- ADF Duplex
# Session timeout for users before they have to re-enter an OTP
session_timeout: 30
```

Finally, launch the app.

```bash
sudo python3 app.py
```

The scan tool defaults to `http://localhost:5000`.

## Systemd Service Template

Below is an example of a systemd configuration. When deploying, be sure to
modify the `WorkingDirectory` and `ExecStart` accordingly to point to where
you have the application cloned to.

```ini
[Unit]
Description=ScanPi Python Application
After=network.target

[Service]
WorkingDirectory=/home/nuvious/scanpi
ExecStart=/usr/bin/python3 /home/nuvious/scanpi/app.py
Restart=always
RestartSec=30
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

Below is a copy-paste-ready command one could run that generates a default
configuration with scanpi cloned to /opt/scanpi. In this configuration, one
would need to either put the `config.yaml` in `/opt/scanpi`, `/etc/scanpi` or
in `/root/.config/scanpi`.

```bash
set -e # Stop on any error
mkdir -p /mnt/scan
git clone https://github.com/nuvious/scanpi.git /opt/scanpi
touch /lib/systemd/system/scanpi.service
cat > /lib/systemd/system/scanpi.service << EOF
[Unit]
Description=ScanPi Python Application
After=network.target

[Service]
WorkingDirectory=/opt/scanpi
ExecStart=/usr/bin/python3 /opt/scanpi/app.py
Restart=always
RestartSec=30
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF
# Edit accordingly if desired to add environment variables.
systemctl enable scanpi --now
```

## Tested Hardware

[Fujitsu/RICOH SnapScan S1500](https://www.pfu.ricoh.com/global/scanners/scansnap/discontinued/s1500/s1500.html)
