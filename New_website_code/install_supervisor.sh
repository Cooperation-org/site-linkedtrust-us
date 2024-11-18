#!/bin/bash

# Install supervisor
sudo apt update
sudo apt install -y supervisor

# Create log directory
sudo mkdir -p /var/log/supervisor

# Copy configuration
sudo cp supervisor_honcho.conf /etc/supervisor/conf.d/linkedtrust.conf

# Create log files
sudo touch /var/log/supervisor/linkedtrust.log
sudo touch /var/log/supervisor/linkedtrust.err.log

# Set proper permissions
sudo chown -R root:root /var/log/supervisor

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start the program
sudo supervisorctl start linkedtrust

# Check status
sudo supervisorctl status


