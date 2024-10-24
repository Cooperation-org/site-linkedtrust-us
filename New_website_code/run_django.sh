#!/bin/bash

# Function to kill existing processes
kill_existing_processes() {
    echo "Checking for existing processes..."
    
    # Kill any existing Django development server (port 8000)
    django_pid=$(lsof -ti:8000)
    if [ ! -z "$django_pid" ]; then
        echo "Killing existing Django server on port 8000"
        kill -9 $django_pid
    fi
    
    # Kill any existing livereload server (port 35729)
    livereload_pid=$(lsof -ti:35729)
    if [ ! -z "$livereload_pid" ]; then
        echo "Killing existing livereload server on port 35729"
        kill -9 $livereload_pid
    fi
    
    # Wait a moment for processes to fully terminate
    sleep 2
}

# Function to open browser
open_browser() {
    echo "Waiting for Django server to start..."
    sleep 5  # Wait for Django server to fully start
    
    # Check which browser opener is available and use it
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://127.0.0.1:8000"
    elif command -v gnome-open &> /dev/null; then
        gnome-open "http://127.0.0.1:8000"
    elif command -v open &> /dev/null; then
        open "http://127.0.0.1:8000"
    else
        echo "Could not detect a way to open the browser automatically"
        echo "Please open http://127.0.0.1:8000 in your browser"
    fi
}

# Function to check if gnome-terminal is available
use_gnome_terminal() {
    command -v gnome-terminal >/dev/null 2>&1
}

# Function to check if Terminal.app (macOS) is available
use_macos_terminal() {
    [ "$(uname)" == "Darwin" ]
}

# Kill any existing processes first
kill_existing_processes

if use_gnome_terminal; then
    # For Linux with gnome-terminal
    gnome-terminal -- bash -c "cd $(pwd) && python3 manage.py runserver; exec bash"
    gnome-terminal -- bash -c "cd $(pwd) && python3 manage.py livereload; exec bash"
    open_browser

elif use_macos_terminal; then
    # For macOS
    osascript <<EOF
        tell application "Terminal"
            do script "cd $(pwd) && python3 manage.py runserver"
            do script "cd $(pwd) && python3 manage.py livereload"
        end tell
EOF
    open_browser

else
    # For other terminals (generic approach using xterm)
    xterm -e "python3 manage.py runserver" &
    xterm -e "python3 manage.py livereload" &
    open_browser
fi

echo "Started Django development server and livereload server"
echo "Opening browser to http://127.0.0.1:8000"