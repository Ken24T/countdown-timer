import sys
import os
from PySide6.QtWidgets import QApplication  # Import QApplication

# Get the project root directory.
# The directory containing run.py (PROJECT_ROOT) is automatically added to sys.path
# when the script is run. This allows Python to find the 'src' package
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Now we import App from main_app, treating src as a package
from src.main_app import App

if __name__ == "__main__":
    # If this script is executed directly, create and run the application
    q_app = QApplication(sys.argv)  # Create QApplication instance first
    window = App()
    window.show()  # QMainWindow needs to be explicitly shown
    sys.exit(q_app.exec())  # Start the Qt event loop
