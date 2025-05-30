import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
import json
import os
# Ensure TimerCard and its DEFAULT constants are imported
from .components.timer_card import TimerCard, DEFAULT_TIME_FONT_SIZE, DEFAULT_TITLE_BG_COLOR, DEFAULT_TIME_BG_COLOR

# CONFIG_FILE path and keys for structured config
CONFIG_FILE = os.path.join("data", "timers_config.json")
GLOBAL_SETTINGS_KEY = "global_settings"
TIMERS_KEY = "timers"

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Countdown Timer") 
        self.resize(200, 600) 

        # Apply a global stylesheet for QToolTip
        QApplication.instance().setStyleSheet("""
            QToolTip {
                background-color: #E0E0E0; /* Lighter Grey */
                color: #000000; /* Black text for contrast */
                border: 1px solid #C0C0C0; /* Slightly darker grey border */
                padding: 4px;
                border-radius: 3px;
                opacity: 240; /* Optional: for slight transparency, 255 is fully opaque */
            }
        """)

        # Initialize global_settings dictionary structure
        self.global_settings = {
            "default_time_font_size": DEFAULT_TIME_FONT_SIZE,
            "default_bg_color_title": DEFAULT_TITLE_BG_COLOR,
            "default_bg_color_time": DEFAULT_TIME_BG_COLOR
        }
        self.timer_configs = {} 
        self.timers = {} 

        self.load_app_settings_and_timers() # Load settings and timers from file

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget) 

        self.controls_frame = QFrame(self.central_widget) 
        controls_layout = QVBoxLayout(self.controls_frame) 

        self.add_timer_button = QPushButton("Add New Timer") 
        self.add_timer_button.setFixedWidth(160) 
        self.add_timer_button.setStyleSheet("""
            QPushButton {
                background-color: #003366; 
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #004080; 
            }
            QPushButton:pressed {
                background-color: #002244; 
            }
        """)
        self.add_timer_button.clicked.connect(self.add_new_timer_action) 
        controls_layout.addWidget(self.add_timer_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.controls_frame)

        self.scroll_area = QScrollArea() 
        self.scroll_area.setWidgetResizable(True)
        
        self.scrollable_timers_widget = QWidget() 
        self.timers_layout = QVBoxLayout(self.scrollable_timers_widget) 
        self.timers_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 

        self.scroll_area.setWidget(self.scrollable_timers_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        self.create_timer_cards()

    def add_new_timer_action(self): 
        from datetime import datetime, timedelta
        timestamp_id = str(int(datetime.now().timestamp() * 1000))
        card_id = f"timer_{timestamp_id}_{len(self.timer_configs)}" 

        title = "New Timer"
        end_date_obj = (datetime.now() + timedelta(days=1)).date()
        end_datetime_midnight = datetime.combine(end_date_obj, datetime.min.time())
        date_str = end_datetime_midnight.strftime("%Y-%m-%d %H:%M:%S")

        new_config = {
            "title": title, 
            "end_date": date_str, 
            "comment": "", 
            # Use global defaults for colors and font size
            "bg_color_title": self.global_settings.get("default_bg_color_title", DEFAULT_TITLE_BG_COLOR), 
            "bg_color_time": self.global_settings.get("default_bg_color_time", DEFAULT_TIME_BG_COLOR),  
            "font_size_time": self.global_settings.get("default_time_font_size", DEFAULT_TIME_FONT_SIZE)
        }
        self.timer_configs[card_id] = new_config
        self.save_app_settings_and_timers() 
        self.create_timer_cards() 

    def create_timer_card(self, card_id, config, parent_layout): 
        card = TimerCard(master_layout=parent_layout, 
                         title=config["title"], 
                         end_date=config["end_date"], 
                         card_id=card_id, 
                         app_ref=self, 
                         config=config)
        
        parent_layout.addWidget(card) 
        self.timers[card_id] = card 
        return card

    def create_timer_cards(self):
        while self.timers_layout.count():
            child = self.timers_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.timers.clear()

        from datetime import datetime
        try:
            sorted_configs = sorted(
                self.timer_configs.items(), 
                key=lambda item: datetime.strptime(item[1]['end_date'], "%Y-%m-%d %H:%M:%S")
            )
        except KeyError as e:
            print(f"Error: Missing 'end_date' in one of the timer configurations: {e}. Check timers_config.json")
            sorted_configs = self.timer_configs.items()
        except ValueError as e:
            print(f"Error: Invalid date format in one of the timer configurations: {e}. Check timers_config.json")
            sorted_configs = self.timer_configs.items()

        for card_id, config in sorted_configs:
            self.create_timer_card(card_id, config, self.timers_layout) 

    def load_app_settings_and_timers(self):
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    loaded_global_settings = data.get(GLOBAL_SETTINGS_KEY, {})
                    # Load global settings, falling back to imported constants
                    self.global_settings["default_time_font_size"] = loaded_global_settings.get(
                        "default_time_font_size", DEFAULT_TIME_FONT_SIZE
                    )
                    self.global_settings["default_bg_color_title"] = loaded_global_settings.get(
                        "default_bg_color_title", DEFAULT_TITLE_BG_COLOR
                    )
                    self.global_settings["default_bg_color_time"] = loaded_global_settings.get(
                        "default_bg_color_time", DEFAULT_TIME_BG_COLOR
                    )
                    self.timer_configs = data.get(TIMERS_KEY, {})
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode {CONFIG_FILE}. Using default settings.")
                    # self.global_settings already initialized with DEFAULT_TIME_FONT_SIZE
                    self.timer_configs = {} 
        # If file doesn't exist, self.global_settings and self.timer_configs retain their initial values

    def save_app_settings_and_timers(self):
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        data_to_save = {
            GLOBAL_SETTINGS_KEY: self.global_settings,
            TIMERS_KEY: self.timer_configs
        }
            
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)

    def update_timer_config(self, card_id, new_config):
        if card_id in self.timer_configs:
            self.timer_configs[card_id].update(new_config)
            self.save_app_settings_and_timers() 

    def delete_timer_config_and_card(self, card_id):
        if card_id in self.timer_configs:
            del self.timer_configs[card_id]
            self.save_app_settings_and_timers() 
        if card_id in self.timers:
            widget_to_remove = self.timers[card_id]
            self.timers_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater() 
            del self.timers[card_id]

    def update_global_default_time_font_size(self, new_size):
        """Updates the global default font size for the time display on new cards."""
        self.global_settings["default_time_font_size"] = new_size
        self.save_app_settings_and_timers() # Save changes immediately
        print(f"Global default time font size updated to: {new_size}")

    def update_global_default_title_color(self, new_color_hex):
        """Updates the global default background color for the title region on new cards."""
        self.global_settings["default_bg_color_title"] = new_color_hex
        self.save_app_settings_and_timers()
        print(f"Global default title background color updated to: {new_color_hex}")

    def update_global_default_time_color(self, new_color_hex):
        """Updates the global default background color for the time region on new cards."""
        self.global_settings["default_bg_color_time"] = new_color_hex
        self.save_app_settings_and_timers()
        print(f"Global default time region background color updated to: {new_color_hex}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
