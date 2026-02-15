# LinkedTrust Deployment and Maintenance Guide

This guide provides detailed instructions for deploying and maintaining the LinkedTrust project on a production server.
NB: Statics is served using whitenoise
## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Server Setup](#initial-server-setup)
- [Project Deployment](#project-deployment)
- [Database Setup](#database-setup)
- [Static Files](#static-files)
- [Process Management](#process-management)
- [Nginx Configuration](#nginx-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Backup Procedures](#backup-procedures)

## Prerequisites

Required software and tools:
```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-venv python3-pip nginx supervisor git
```

## Initial Server Setup

1. Clone the repository:
```bash
cd /linkedtrust
git clone [repository-url] site-linkedtrust-us
cd site-linkedtrust-us
```

2. Set up virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Install additional dependencies:
```bash
pip install gunicorn honcho whitenoise django-livereload-server
```

## Project Deployment

1. Create necessary directories:
```bash
mkdir -p /linkedtrust/site-linkedtrust-us/static
mkdir -p /linkedtrust/site-linkedtrust-us/media
```

2. Set up environment variables:
```bash
# Create .env file
cat > .env << EOL
DJANGO_SETTINGS_MODULE=linkedtrust.settings
DEBUG=False
ALLOWED_HOSTS=linkedtrust.us,www.linkedtrust.us
EOL
```

3. Update Django settings:
```python
# settings.py configurations
ALLOWED_HOSTS = ['linkedtrust.us', 'www.linkedtrust.us']
DEBUG = False
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
```

## Process Management

Configure Supervisor:
```bash
# Create supervisor configuration
sudo tee /etc/supervisor/conf.d/linkedtrust.conf << EOL
[program:linkedtrust]
command=gunicorn linkedtrust.wsgi:application --workers=3 --bind 0.0.0.0:8000
directory=/linkedtrust/site-linkedtrust-us
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/linkedtrust.log
stderr_logfile=/var/log/supervisor/linkedtrust.err.log
environment=DJANGO_SETTINGS_MODULE="linkedtrust.settings",PYTHONUNBUFFERED="true"
EOL
```

## Nginx Configuration

1. Create Nginx configuration:
```bash
sudo tee /etc/nginx/sites-available/linkedtrust << EOL
server {
    listen 80;
    server_name linkedtrust.us www.linkedtrust.us;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    location /static/ {
        alias /linkedtrust/site-linkedtrust-us/static/;
        expires 30d;
    }

    location /media/ {
        alias /linkedtrust/site-linkedtrust-us/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://0.0.0.0:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

sudo ln -s /etc/nginx/sites-available/linkedtrust /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

## Maintenance

### Regular Maintenance Tasks

1. Update system packages:
```bash
sudo apt update
sudo apt upgrade -y
```

2. Update Python packages:
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

3. Collect static files:
```bash
python manage.py collectstatic
```

4. Restart services:
```bash
sudo supervisorctl restart linkedtrust
sudo systemctl restart nginx
```

### Monitoring

1. Check service status:
```bash
sudo supervisorctl status linkedtrust
sudo systemctl status nginx
```

2. View logs:
```bash
# Application logs
sudo tail -f /var/log/supervisor/linkedtrust.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Common Issues and Solutions

1. Service won't start:
```bash
# Check supervisor logs
sudo tail -f /var/log/supervisor/linkedtrust.log

# Restart supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart linkedtrust
```

2. Static files not loading:
```bash
source .venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

3. Permission issues:
```bash
sudo chown -R www-data:www-data /linkedtrust/site-linkedtrust-us/static
sudo chown -R www-data:www-data /linkedtrust/site-linkedtrust-us/media
```


### Security Updates

1. Check for security updates:
```bash
sudo unattended-upgrade --dry-run
```

2. Apply security updates:
```bash
sudo unattended-upgrade
```

## Quick Reference

### Common Commands

```bash
# Restart application
sudo supervisorctl restart linkedtrust

# Reload Nginx
sudo systemctl reload nginx

# View logs
sudo tail -f /var/log/supervisor/linkedtrust.log

# Check status
sudo supervisorctl status
```

### Important Paths

- Project directory: `/linkedtrust/site-linkedtrust-us`
- Virtual environment: `/linkedtrust/site-linkedtrust-us/.venv`
- Static files: `/linkedtrust/site-linkedtrust-us/static`
- Media files: `/linkedtrust/site-linkedtrust-us/media`
- Logs: `/var/log/supervisor/linkedtrust.log`

Server Key: [Vault Key](https://vault.whatscookin.us/app/passwords/view/6f63a442-d3aa-400d-b730-d2c42480c086)
