import sys
import os

# Get the project root directory.
# The directory containing run.py (PROJECT_ROOT) is automatically added to sys.path
# when the script is run. This allows Python to find the 'src' package
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Now we import App from main_app, treating src as a package
from src.main_app import App

if __name__ == "__main__":
    # If this script is executed directly, create and run the application
    app = App()
    app.mainloop()
