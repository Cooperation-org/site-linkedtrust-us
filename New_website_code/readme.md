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

## Using website-update  

To use website-update, follow these steps:

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

- The livereload server will be running at `http://127.0.0.1:35729`
- Any changes to your code will automatically trigger a reload in your browser

## Troubleshooting

If you encounter any issues:

1. Ensure all prerequisites are correctly installed.
2. Verify that your virtual environment is activated.
