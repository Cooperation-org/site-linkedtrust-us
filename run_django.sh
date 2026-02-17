#!/bin/bash

# Check if the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please activate your virtual environment first."
    exit 1
fi

# Function to kill any processes running on port 8000
kill_port_8000() {
    echo "Killing any processes running on port 8000..."
    fuser -k 8000/tcp > /dev/null 2>&1
}

# Function to start the Django development server and open in Chrome
start_django() {
    settings_file=$1
    
    # Wait a bit and open the URL in Chrome (running in background)
    (
        sleep 2  # Wait for Django to start
        if command -v google-chrome &> /dev/null; then
            google-chrome --new-tab "http://127.0.0.1:8000" &
        elif command -v chrome &> /dev/null; then
            chrome --new-tab "http://127.0.0.1:8000" &
        else
            echo "Unable to open the URL in Google Chrome. Please open the URL manually."
        fi
    ) &

    # Start Django server
    echo "Starting Django server with $settings_file"
    python manage.py runserver --settings=$settings_file
}

# Prompt user to choose settings file
echo "Choose the settings file to use:"
echo "1. settings.py"
echo "2. dev-settings.py"
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        kill_port_8000
        start_django "linkedtrust.settings"
        ;;
    2)
        kill_port_8000
        start_django "linkedtrust.dev-settings"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac