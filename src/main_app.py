import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
# Ensure TimerCard and its DEFAULT constants are imported
from .components.timer_card import TimerCard, DEFAULT_TIME_FONT_SIZE, DEFAULT_TITLE_BG_COLOR, DEFAULT_TIME_BG_COLOR
import os # Ensure os is imported for CONFIG_FILE path
import json # Ensure json is imported for loading/saving config
import sys # Ensure sys is imported for QApplication

# CONFIG_FILE path and keys for structured config
CONFIG_FILE = os.path.join("data", "timers_config.json")
GLOBAL_SETTINGS_KEY = "global_settings"
TIMERS_KEY = "timers"

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Countdown Timer")
        # Default size, will be overridden if settings are loaded
        self.default_width = 220 
        self.default_height = 600

        # Apply a global stylesheet for QToolTip
        # Note: QApplication.instance() might be None if called too early or in a non-GUI context.
        # However, in a standard PySide app structure, this should work after QApplication is instantiated.
        q_app_instance = QApplication.instance()
        # Ensure q_app_instance is a QApplication before calling setStyleSheet
        if q_app_instance and isinstance(q_app_instance, QApplication):
            q_app_instance.setStyleSheet("""
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
            "default_bg_color_time": DEFAULT_TIME_BG_COLOR,
            "remember_window_position": False,
            "window_x": None,
            "window_y": None,
            "window_width": None,
            "window_height": None
        }
        self.timer_configs = {}
        self.timers = {}

        self.load_app_settings_and_timers() # Load settings and timers from file

        # Apply window geometry if remembered
        if self.global_settings.get("remember_window_position", False):
            raw_x = self.global_settings.get("window_x")
            raw_y = self.global_settings.get("window_y")
            raw_width = self.global_settings.get("window_width")
            raw_height = self.global_settings.get("window_height")

            if all(v is not None for v in [raw_x, raw_y, raw_width, raw_height]):
                try:
                    # Ensure they are integers before setting geometry
                    x = int(raw_x) # type: ignore
                    y = int(raw_y) # type: ignore
                    width = int(raw_width) # type: ignore
                    height = int(raw_height) # type: ignore
                    self.setGeometry(x, y, width, height)
                except (ValueError, TypeError): 
                    self.resize(self.default_width, self.default_height) 
            else:
                self.resize(self.default_width, self.default_height) 
        else:
            self.resize(self.default_width, self.default_height)


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
        
        # Enable drag and drop for the scrollable area
        self.scrollable_timers_widget.setAcceptDrops(True)
        self.scrollable_timers_widget.dragEnterEvent = self.dragEnterEvent
        self.scrollable_timers_widget.dragMoveEvent = self.dragMoveEvent
        self.scrollable_timers_widget.dropEvent = self.dropEvent
        
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
            # Filter out configs missing 'end_date' or where 'end_date' is None before sorting
            valid_configs = {k: v for k, v in self.timer_configs.items() if 'end_date' in v and v['end_date'] is not None}
            # Sort by 'sort_order' first, then by 'end_date'
            sorted_configs = sorted(valid_configs.items(), 
                                    key=lambda item: (item[1].get('sort_order', float('inf')), 
                                                      datetime.strptime(item[1]['end_date'], "%Y-%m-%d %H:%M:%S")))
        except KeyError as e:
            print(f"KeyError during sorting timer configs: {e} - some timers might not be displayed.")
            sorted_configs = sorted(self.timer_configs.items()) # Fallback to sort by key
        except ValueError as e:
            print(f"ValueError during date parsing for sorting: {e} - some timers might not be displayed.")
            sorted_configs = sorted(self.timer_configs.items()) # Fallback to sort by key
        except TypeError as e: # Catch TypeError if end_date is None and slips through strptime
            print(f"TypeError during date parsing for sorting (likely None date): {e} - some timers might not be displayed.")
            sorted_configs = sorted(self.timer_configs.items())


        for card_id, config in sorted_configs:
            self.create_timer_card(card_id, config, self.timers_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            source_card_id = event.mimeData().text()
            source_widget = self.timers.get(source_card_id)

            if not source_widget:
                event.ignore()
                return

            target_widget = None
            target_index = -1

            # Find the widget (TimerCard) at the drop position
            for i in range(self.timers_layout.count()):
                widget = self.timers_layout.itemAt(i).widget()
                if widget and widget.underMouse():
                    target_widget = widget
                    target_index = i
                    break
            
            if target_widget and target_widget != source_widget:
                # Re-insert the source_widget at the target_index
                self.timers_layout.removeWidget(source_widget)
                self.timers_layout.insertWidget(target_index, source_widget)

                # Update sort_order in configurations
                self.update_sort_order_after_drag(source_card_id, target_index)
                event.acceptProposedAction()
            elif not target_widget:
                # If dropped in an empty area, move to the end
                self.timers_layout.removeWidget(source_widget)
                self.timers_layout.addWidget(source_widget) # Add to the end
                self.update_sort_order_after_drag(source_card_id, self.timers_layout.count() -1)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def update_sort_order_after_drag(self, moved_card_id, new_visual_index):
        # Create a list of (card_id, widget) from the current layout order
        layout_items = []
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Ensure the widget is a TimerCard and has card_id
                if isinstance(widget, TimerCard) and hasattr(widget, 'card_id'):
                    layout_items.append(widget.card_id)
        
        # Update the sort_order in self.timer_configs based on the new visual order
        for i, card_id_in_layout in enumerate(layout_items):
            if card_id_in_layout in self.timer_configs:
                self.timer_configs[card_id_in_layout]['sort_order'] = i
        
        self.save_app_settings_and_timers()
        # No need to call create_timer_cards() here as we manually rearranged.
        # However, if create_timer_cards relies on sort_order for initial creation,
        # this new order will be used next time it's called.

    def load_app_settings_and_timers(self):
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir) # Create data directory if it doesn't exist
            except OSError as e:
                print(f"Error creating directory {data_dir}: {e}")
                # Depending on severity, might want to raise or handle differently
                
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # Load global settings, merging with defaults to ensure all keys are present
                    loaded_global_settings = data.get(GLOBAL_SETTINGS_KEY, {})
                    
                    # Start with a copy of the current default settings
                    # (which includes any new keys like window geometry)
                    updated_global_settings = self.global_settings.copy()
                    # Override with any values loaded from the config file
                    updated_global_settings.update(loaded_global_settings)
                    self.global_settings = updated_global_settings
                    
                    self.timer_configs = data.get(TIMERS_KEY, {})
            except json.JSONDecodeError:
                print(f"Error decoding {CONFIG_FILE}. Using default settings.")
                # self.global_settings retains initial defaults, self.timer_configs is empty
            except Exception as e:
                print(f"An unexpected error occurred while loading {CONFIG_FILE}: {e}. Using default settings.")
        # If file doesn't exist, self.global_settings and self.timer_configs retain their initial values

    def save_app_settings_and_timers(self):
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except OSError as e:
                print(f"Error creating directory {data_dir} before saving: {e}")
                return # Optionally, decide if saving should proceed or not
        
        data_to_save = {
            GLOBAL_SETTINGS_KEY: self.global_settings,
            TIMERS_KEY: self.timer_configs
        }
            
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=4)
        except IOError as e:
            print(f"Error writing to {CONFIG_FILE}: {e}")

    def update_timer_config(self, card_id, new_config):
        if card_id in self.timer_configs:
            self.timer_configs[card_id].update(new_config)
            self.save_app_settings_and_timers()

    def delete_timer_config_and_card(self, card_id):
        if card_id in self.timer_configs:
            del self.timer_configs[card_id]
        if card_id in self.timers:
            card_widget = self.timers.pop(card_id) # Get and remove from dict
            if card_widget: # Ensure widget exists before calling deleteLater
                card_widget.deleteLater() # Schedule for deletion
        self.save_app_settings_and_timers()
        # Consider a more targeted removal from layout if create_timer_cards is too heavy for just one deletion

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
        print(f"Global default time background color updated to: {new_color_hex}")

    def update_remember_window_position(self, state: bool):
        """Updates the global setting for remembering window position."""
        self.global_settings["remember_window_position"] = state
        if not state: # If we are disabling remember position, clear saved geometry
            self.global_settings["window_x"] = None
            self.global_settings["window_y"] = None
            self.global_settings["window_width"] = None
            self.global_settings["window_height"] = None
        self.save_app_settings_and_timers()
        print(f"Remember window position set to: {state}")

    def closeEvent(self, event):
        """Handle the window close event."""
        if self.global_settings.get("remember_window_position", False):
            geometry = self.geometry()
            self.global_settings["window_x"] = geometry.x()
            self.global_settings["window_y"] = geometry.y()
            self.global_settings["window_width"] = geometry.width()
            self.global_settings["window_height"] = geometry.height()
            self.save_app_settings_and_timers()
            print("Window position saved.")
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
