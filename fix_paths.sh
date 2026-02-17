#!/bin/bash

# Define paths
PROJECT_DIR="/linkedtrust/site-linkedtrust-us/New_website_code"
VENV_DIR="/linkedtrust/site-linkedtrust-us/.venv"
PYTHON_PATH="$VENV_DIR/bin/python"
GUNICORN_PATH="$VENV_DIR/bin/gunicorn"

echo "Fixing path issues..."

# Check if virtualenv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment and install requirements
source $VENV_DIR/bin/activate
pip install -r requirements.txt


# Create new supervisor configuration
sudo tee /etc/supervisor/conf.d/linkedtrust.conf << EOL
[program:linkedtrust]
command=$VENV_DIR/bin/honcho start
directory=$PROJECT_DIR
user=root
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
redirect_stderr=true
stdout_logfile=/var/log/supervisor/linkedtrust.log
stderr_logfile=/var/log/supervisor/linkedtrust.err.log
environment=PATH="$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            VIRTUAL_ENV="$VENV_DIR",
            DJANGO_SETTINGS_MODULE="linkedtrust.settings",
            PYTHONPATH="$PROJECT_DIR",
            PYTHONUNBUFFERED="true"

[supervisord]
logfile=/var/log/supervisor/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200
EOL

# Create log directory if it doesn't exist
sudo mkdir -p /var/log/supervisor
sudo touch /var/log/supervisor/linkedtrust.log
sudo touch /var/log/supervisor/linkedtrust.err.log

# Set proper permissions
sudo chown -R root:root /var/log/supervisor
sudo chmod -R 755 /var/log/supervisor

# Verify installations
echo "Verifying installations..."
$PYTHON_PATH --version
$GUNICORN_PATH --version
$VENV_DIR/bin/honcho --version

# Restart supervisor
echo "Restarting supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart linkedtrust

# Display status and logs
echo "Supervisor status:"
sudo supervisorctl status linkedtrust
echo "Recent logs:"
sudo tail -n 20 /var/log/supervisor/linkedtrust.log
