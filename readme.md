# Website-Update

## Prerequisites

Before you begin, ensure you have met the following requirements:

* Python3 installed 
* pip (Python package installer)
* Git

## Installing Website-Update Project

To install Website-Update, follow these steps:

1. Clone the repository:
```
git clone https://github.com/Cooperation-org/website-update.git
```

2. Navigate to the project directory:
```
cd website-update
```

3. Create a virtual environment:
```
python -m venv venv
```

4. Activate the virtual environment:
   * On Windows:
     ```
     venv\Scripts\activate
     ```
   * On macOS and Linux:
     ```
     source venv/bin/activate
     ```

5. Install the required packages:
```
pip install -r requirements.txt
```

6. Run migrations:
```
python3 manage.py migrate
```

## Configuration (Optional)

1. Create a `.env` file in the project root directory.
2. Add any necessary environment variables (e.g., `SECRET_KEY`, `DEBUG`, `DATABASE_URL`).

## Running the Project

You have two options to run the project:

### Option 1: Using the Automated Script (Linux/macOS)

1. Ensure your virtual environment is activated.

2. Verify that the run script exists:
```bash
ls run_django.sh
```

3. Make the script executable (if not already):
```bash
chmod +x run_django.sh
```

4. Run the project:
```bash
./run_django.sh
```

This script will:
- Start both the Django server and livereload server in separate terminals
- Open your browser automatically to the project
- Handle closing existing server processes if needed

### Option 2: Traditional Setup

1. Ensure your virtual environment is activated.

2. Start the livereload server:
```
python3 manage.py livereload
```

3. In a new terminal window, start the development server:
```
python3 manage.py runserver
```

4. Open your web browser and navigate to `http://localhost:8000`

## Development

- The Django development server will be running at `http://127.0.0.1:8000`
- The livereload server will be running at `http://127.0.0.1:35729`
- Any changes to your code will automatically trigger a reload in your browser

## Troubleshooting

If you encounter any issues:

1. Ensure all prerequisites are correctly installed.
2. Verify that your virtual environment is activated.
3. If using the script:
   - Make sure the script has execute permissions (`chmod +x run_django.sh`)
   - Check if required terminal emulator is installed (gnome-terminal on Linux, Terminal.app on macOS)
   - Try running servers manually using Option 2 if the script encounters issues

For the automated script (Option 1):
- If the browser doesn't open automatically, manually visit `http://127.0.0.1:8000`
- If you get port-in-use errors, try running the script again as it will attempt to close existing processes