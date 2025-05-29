import unittest
import os
import json
from datetime import datetime, timedelta

# Add src to path to allow importing gui
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui import TimerCard, App # Assuming your main GUI file is gui.py

class TestTimerCard(unittest.TestCase):
    def test_timer_card_creation(self):
        # Create a dummy master widget for testing
        master = App() # Or a simpler tk.Tk() if App has too many dependencies
        title = "Test Event"
        # Set end_date to tomorrow
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        card = TimerCard(master, title, end_date)
        self.assertEqual(card.title, title)
        self.assertEqual(card.days_remaining, 1)
        master.destroy() # Clean up the master widget

class TestApp(unittest.TestCase):
    def setUp(self):
        # Create a dummy timers.json for testing
        self.test_timers_file = "test_timers.json"
        self.sample_data = [
            {"title": "Test1", "end_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")},
            {"title": "Test2", "end_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")}
        ]
        with open(self.test_timers_file, "w") as f:
            json.dump(self.sample_data, f)

        # Temporarily replace the original timers.json path in the App
        self.original_timers_json_path = App.load_timers.__globals__['open']
        App.load_timers.__globals__['open'] = lambda path, mode: open(self.test_timers_file if path == "timers.json" else path, mode)


    def tearDown(self):
        # Clean up the dummy timers.json
        if os.path.exists(self.test_timers_file):
            os.remove(self.test_timers_file)
        # Restore the original open function
        App.load_timers.__globals__['open'] = self.original_timers_json_path

    def test_app_loads_timers(self):
        app = App()
        # Check if cards are created (adjust based on how cards are stored in App)
        # This is a basic check, more specific checks might be needed
        self.assertTrue(len(app.winfo_children()) >= len(self.sample_data))
        app.destroy()

    def test_app_handles_missing_timers_file(self):
        if os.path.exists(self.test_timers_file):
            os.remove(self.test_timers_file)
        app = App()
        # Check that the app starts without errors and no cards are loaded
        self.assertEqual(len(app.winfo_children()), 0) # Assuming no other widgets are added by default
        app.destroy()

if __name__ == '__main__':
    unittest.main()
