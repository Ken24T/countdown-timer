import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QMimeData, QByteArray, QUrl # Added QUrl
from PySide6 import QtGui # Added for type hints
# Ensure TimerCard and its DEFAULT constants are imported
from .components.timer_card import TimerCard, DEFAULT_TIME_FONT_SIZE, DEFAULT_TITLE_BG_COLOR, DEFAULT_TIME_BG_COLOR
import os
import json
import uuid # For generating unique IDs
from datetime import datetime, timedelta

# For parsing iCalendar data from Outlook
try:
    from icalendar import Calendar
    import pytz # For timezone handling
    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False
    print("INFO: icalendar and/or pytz library not found. Outlook event parsing will be limited. Install with 'pip install icalendar pytz'")

# Define constants for custom MIME types
CHROMIUM_CUSTOM_MIME = 'application/x-qt-windows-mime;value="Chromium Web Custom MIME Data Format"'
OUTLOOK_ITEM_MIME = 'application/x-outlook-item' # Standard Outlook item
TEXT_CALENDAR_MIME = 'text/calendar'
TEXT_PLAIN_MIME = 'text/plain'
TEXT_HTML_MIME = 'text/html'


# CONFIG_FILE path and keys for structured config
CONFIG_FILE = os.path.join("data", "timers_config.json")
GLOBAL_SETTINGS_KEY = "global_settings"
TIMERS_KEY = "timers"

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Countdown Timer")
        self.default_width = 220 
        self.default_height = 600

        q_app_instance = QApplication.instance()
        if q_app_instance and isinstance(q_app_instance, QApplication):
            q_app_instance.setStyleSheet("""
                QToolTip {
                    background-color: #E0E0E0;
                    color: #000000;
                    border: 1px solid #C0C0C0;
                    padding: 4px;
                    border-radius: 3px;
                    opacity: 240;
                }
            """)

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

        self.load_app_settings_and_timers()

        if self.global_settings.get("remember_window_position", False):
            raw_x = self.global_settings.get("window_x")
            raw_y = self.global_settings.get("window_y")
            raw_width = self.global_settings.get("window_width")
            raw_height = self.global_settings.get("window_height")
            if all(v is not None for v in [raw_x, raw_y, raw_width, raw_height]):
                try:
                    self.setGeometry(int(raw_x), int(raw_y), int(raw_width), int(raw_height)) # type: ignore
                except (ValueError, TypeError): 
                    self.resize(self.default_width, self.default_height) 
            else:
                self.resize(self.default_width, self.default_height) 
        else:
            self.resize(self.default_width, self.default_height)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget) 

        self.controls_frame = QFrame(self.central_widget) 
        controls_layout = QVBoxLayout(self.controls_frame) 
        self.add_timer_button = QPushButton("Add New Timer") 
        self.add_timer_button.setFixedWidth(160) 
        self.add_timer_button.setStyleSheet("""
            QPushButton { background-color: #003366; color: white; padding: 5px; border-radius: 5px; }
            QPushButton:hover { background-color: #004080; }
            QPushButton:pressed { background-color: #002244; }
        """)
        self.add_timer_button.clicked.connect(lambda: self.add_new_timer_action()) # Lambda to call with defaults
        controls_layout.addWidget(self.add_timer_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.controls_frame)

        self.scroll_area = QScrollArea() 
        self.scroll_area.setWidgetResizable(True)
        self.scrollable_timers_widget = QWidget() 
        self.timers_layout = QVBoxLayout(self.scrollable_timers_widget) 
        self.timers_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 
        self.scroll_area.setWidget(self.scrollable_timers_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        self.scrollable_timers_widget.setAcceptDrops(True)
        self.scrollable_timers_widget.dragEnterEvent = self.dragEnterEvent # type: ignore
        self.scrollable_timers_widget.dragMoveEvent = self.dragMoveEvent # type: ignore
        self.scrollable_timers_widget.dropEvent = self.dropEvent # type: ignore
        
        self.create_timer_cards()

    def add_new_timer_action(self, title="New Timer", end_date_str=None, comment=""):
        card_id = f"timer_{uuid.uuid4().hex}"

        final_end_date_str = end_date_str
        if final_end_date_str is None:
            end_date_obj = (datetime.now() + timedelta(days=1)).date()
            end_datetime_midnight = datetime.combine(end_date_obj, datetime.min.time())
            final_end_date_str = end_datetime_midnight.strftime("%Y-%m-%d %H:%M:%S")

        new_config = {
            "title": title,
            "end_date": final_end_date_str,
            "comment": comment,
            "bg_color_title": self.global_settings.get("default_bg_color_title", DEFAULT_TITLE_BG_COLOR),
            "bg_color_time": self.global_settings.get("default_bg_color_time", DEFAULT_TIME_BG_COLOR),
            "font_size_time": self.global_settings.get("default_time_font_size", DEFAULT_TIME_FONT_SIZE),
            "sort_order": self.get_next_sort_order()
        }
        self.timer_configs[card_id] = new_config
        self.save_app_settings_and_timers()
        self.create_timer_cards()

    def get_next_sort_order(self):
        if not self.timer_configs:
            return 0
        max_sort_order = -1
        for config in self.timer_configs.values():
            if isinstance(config.get("sort_order"), int) and config["sort_order"] > max_sort_order:
                max_sort_order = config["sort_order"]
        return max_sort_order + 1

    def create_timer_card(self, card_id, config, parent_layout):
        card = TimerCard(master_layout=parent_layout, title=config["title"], 
                         end_date=config["end_date"], card_id=card_id, app_ref=self, config=config)
        parent_layout.addWidget(card)
        self.timers[card_id] = card
        return card

    def create_timer_cards(self):
        while self.timers_layout.count():
            child = self.timers_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.timers.clear()

        try:
            valid_configs = {k: v for k, v in self.timer_configs.items() if 'end_date' in v and v['end_date'] is not None}
            sorted_configs = sorted(valid_configs.items(), 
                                    key=lambda item: (item[1].get('sort_order', float('inf')), 
                                                      datetime.strptime(item[1]['end_date'], "%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            print(f"Error sorting timer configs: {e}. Using fallback sort.")
            sorted_configs = sorted(self.timer_configs.items())

        for card_id, config in sorted_configs:
            self.create_timer_card(card_id, config, self.timers_layout)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        mime_data = event.mimeData()
        accepted = False
        print(f"DEBUG dragEnterEvent: All formats: {mime_data.formats()}") # Log all formats

        if mime_data.hasText() and mime_data.text().startswith("timer_"):
            print("DEBUG dragEnterEvent: Accepting internal timer card drag")
            accepted = True
        elif ICALENDAR_AVAILABLE and mime_data.hasFormat(TEXT_CALENDAR_MIME):
            print(f"DEBUG dragEnterEvent: Accepting drag for '{TEXT_CALENDAR_MIME}'")
            accepted = True
        elif mime_data.hasFormat(OUTLOOK_ITEM_MIME):
            print(f"DEBUG dragEnterEvent: Accepting drag for '{OUTLOOK_ITEM_MIME}'")
            accepted = True
        elif mime_data.hasUrls() and any(url.isLocalFile() and url.toLocalFile().lower().endswith(".ics") for url in mime_data.urls()):
            print("DEBUG dragEnterEvent: Accepting drag for .ics file URL")
            accepted = True
        elif mime_data.hasFormat(CHROMIUM_CUSTOM_MIME):
            print(f"DEBUG dragEnterEvent: Accepting drag for '{CHROMIUM_CUSTOM_MIME}'")
            accepted = True
        elif mime_data.hasFormat(TEXT_HTML_MIME): # Accept HTML
            print(f"DEBUG dragEnterEvent: Accepting drag for '{TEXT_HTML_MIME}'")
            accepted = True
        elif mime_data.hasFormat(TEXT_PLAIN_MIME): # Fallback for plain text
            print(f"DEBUG dragEnterEvent: Accepting drag for '{TEXT_PLAIN_MIME}' (fallback)")
            accepted = True
        
        if accepted:
            event.acceptProposedAction()
        else:
            print("DEBUG dragEnterEvent: Ignoring drag, no suitable MIME type found.")
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        mime_data = event.mimeData()
        accepted = False # Assume not accepted initially

        if mime_data.hasText() and mime_data.text().startswith("timer_"):
            accepted = True
        elif ICALENDAR_AVAILABLE and mime_data.hasFormat(TEXT_CALENDAR_MIME):
            accepted = True
        elif mime_data.hasFormat(OUTLOOK_ITEM_MIME):
            accepted = True
        elif mime_data.hasUrls() and any(url.isLocalFile() and url.toLocalFile().lower().endswith(".ics") for url in mime_data.urls()):
            accepted = True
        elif mime_data.hasFormat(CHROMIUM_CUSTOM_MIME):
            accepted = True
        elif mime_data.hasFormat(TEXT_HTML_MIME):
            accepted = True
        elif mime_data.hasFormat(TEXT_PLAIN_MIME):
            accepted = True
        
        if accepted:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        mime_data = event.mimeData()
        print(f"DEBUG dropEvent: All formats: {mime_data.formats()}")
        print(f"DEBUG dropEvent: Has text? {mime_data.hasText()}, Text: {mime_data.text()[:100] if mime_data.hasText() else 'N/A'}")
        print(f"DEBUG dropEvent: Has HTML? {mime_data.hasHtml()}, HTML: {mime_data.html()[:200] if mime_data.hasHtml() else 'N/A'}") # Increased length for HTML
        print(f"DEBUG dropEvent: Has URLs? {mime_data.hasUrls()}, URLs: {[url.toString() for url in mime_data.urls()] if mime_data.hasUrls() else 'N/A'}")

        # 1. Handle internal TimerCard drag
        if mime_data.hasText() and mime_data.text().startswith("timer_"):
            source_card_id = mime_data.text()
            source_widget = self.timers.get(source_card_id)
            if not source_widget:
                event.ignore()
                return

            target_widget = None
            target_index = -1
            # Use event.position() for PySide6, not event.pos()
            drop_pos_in_viewport = event.position() 
            # Map viewport coordinates to widget coordinates if the scroll area itself is the drop target
            # However, scrollable_timers_widget is the one accepting drops, so its local coordinates are fine.
            drop_pos_y = drop_pos_in_viewport.y()

            # Determine insert index based on drop position relative to existing cards
            # Iterate through widgets in the layout to find the correct insertion point
            insert_idx = 0
            for i in range(self.timers_layout.count()):
                item = self.timers_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, TimerCard):
                        # If drop_pos_y is less than the midpoint of the widget, insert before it
                        if drop_pos_y < widget.y() + widget.height() / 2:
                            insert_idx = i
                            break
                        insert_idx = i + 1 # Otherwise, prepare to insert after it
                else:
                    # If item is not a widget (e.g. spacer), or not a TimerCard, this logic might need adjustment
                    # For now, assume layout only contains TimerCards or this loop correctly finds the spot
                    pass 
            else:
                # If loop completes without break, means drop is after all existing items
                # or the layout is empty. insert_idx will be count() or 0 respectively.
                pass
            
            current_idx = self.timers_layout.indexOf(source_widget)
            self.timers_layout.removeWidget(source_widget)
            
            # Adjust insert_idx if the source_widget was before the target position
            if current_idx != -1 and current_idx < insert_idx:
                insert_idx -= 1
                
            self.timers_layout.insertWidget(insert_idx, source_widget)
            self.update_sort_order_after_drag()
            event.acceptProposedAction()
            return

        # 2. Handle Outlook calendar event drop
        title = "Outlook Event"
        end_date_str_parsed = None
        comment = ""

        # Try parsing .ics file from URL first if present
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(".ics"):
                        print(f"DEBUG dropEvent: Processing .ics file from URL: {file_path}")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                ics_data_from_file = f.read()
                            
                            cal = Calendar.from_ical(ics_data_from_file)
                            for component in cal.walk():
                                if component.name == "VEVENT":
                                    summary = component.get('summary')
                                    description = component.get('description')
                                    dtend = component.get('dtend')
                                    
                                    if summary: title = str(summary)
                                    if description: comment = str(description)
                                    if dtend:
                                        dt_value = dtend.dt
                                        if isinstance(dt_value, datetime):
                                            if dt_value.tzinfo:
                                                dt_value = dt_value.astimezone(pytz.utc).replace(tzinfo=None)
                                            end_date_str_parsed = dt_value.strftime("%Y-%m-%d %H:%M:%S")
                                        else: # date object
                                            end_datetime_obj = datetime.combine(dt_value, datetime.min.time())
                                            end_date_str_parsed = end_datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                                    break 
                            self.add_new_timer_action(title=title, end_date_str=end_date_str_parsed, comment=comment)
                            event.acceptProposedAction()
                            print(f"DEBUG dropEvent: Successfully added timer from .ics file URL: {title}")
                            return
                        except Exception as e:
                            print(f"ERROR dropEvent: Failed to parse .ics file from URL {file_path}: {e}")
                            # Fall through to try other MIME types if .ics file parsing fails
                        break # Processed first .ics file found

        if ICALENDAR_AVAILABLE and mime_data.hasFormat(TEXT_CALENDAR_MIME):
            print(f"DEBUG dropEvent: Processing '{TEXT_CALENDAR_MIME}' data")
            try:
                q_byte_array: QByteArray = mime_data.data(TEXT_CALENDAR_MIME)
                # QByteArray.data() returns a memoryview in PySide6 with Python 3.x
                # which can be converted to bytes.
                python_bytes = bytes(q_byte_array.data()) 
                ics_data = python_bytes.decode('utf-8', errors='replace')
                
                print(f"DEBUG dropEvent: ICS Data (first 500 chars):\\n{ics_data[:500]}...")
                cal = Calendar.from_ical(ics_data)
                for component in cal.walk():
                    if component.name == "VEVENT":
                        summary = component.get('summary')
                        description = component.get('description')
                        dtend = component.get('dtend')
                        
                        if summary: title = str(summary)
                        if description: comment = str(description)
                        if dtend:
                            dt_value = dtend.dt
                            if isinstance(dt_value, datetime):
                                if dt_value.tzinfo:
                                    # Convert to UTC then make naive for consistent storage
                                    dt_value = dt_value.astimezone(pytz.utc).replace(tzinfo=None)
                                end_date_str_parsed = dt_value.strftime("%Y-%m-%d %H:%M:%S")
                            else: # date object (all-day event)
                                # Treat as start of the day for the timer end
                                end_datetime_obj = datetime.combine(dt_value, datetime.min.time())
                                end_date_str_parsed = end_datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                        break # Process first event
                self.add_new_timer_action(title=title, end_date_str=end_date_str_parsed, comment=comment)
                event.acceptProposedAction()
                print(f"DEBUG dropEvent: Successfully added timer from '{TEXT_CALENDAR_MIME}': {title}")
                return
            except Exception as e:
                print(f"ERROR dropEvent: Failed to parse iCalendar data from '{TEXT_CALENDAR_MIME}': {e}.")
        
        # Try processing Chromium custom data
        if mime_data.hasFormat(CHROMIUM_CUSTOM_MIME):
            print(f"DEBUG dropEvent: Processing '{CHROMIUM_CUSTOM_MIME}'")
            try:
                q_byte_array: QByteArray = mime_data.data(CHROMIUM_CUSTOM_MIME)
                python_bytes = bytes(q_byte_array.data()) # Convert memoryview to bytes
                decoded_text = python_bytes.decode('utf-8', errors='replace')
                print(f"DEBUG dropEvent: Data from '{CHROMIUM_CUSTOM_MIME}' (UTF-8 decoded):\\n----BEGIN DATA----\\n{decoded_text}\\n----END DATA----")
                
                # Attempt to parse as JSON (common for web custom data)
                try:
                    json_data = json.loads(decoded_text)
                    print("DEBUG dropEvent: Successfully parsed Chromium data as JSON.")
                    # Placeholder: Extract info if JSON structure is known
                    # For now, using generic fields or the whole JSON as comment
                    evt_title = str(json_data.get('summary', json_data.get('title', "Chromium JSON Event")))
                    # Crude way to get a string representation for comment
                    evt_comment_detail = str(json_data) if len(str(json_data)) < 300 else str(json_data)[:300] + "..."
                    evt_comment = json_data.get('description', evt_comment_detail)
                    
                    # Date/time extraction from JSON is highly dependent on its structure
                    # Example: json_data.get('dtend'), json_data.get('end'), etc.
                    # Needs inspection of actual JSON from Outlook.
                    # For now, no date parsing from this JSON.
                    
                    self.add_new_timer_action(title=evt_title, comment=str(evt_comment))
                    event.acceptProposedAction()
                    print(f"DEBUG dropEvent: Successfully added timer from '{CHROMIUM_CUSTOM_MIME}' (parsed as JSON): {evt_title}")
                    return
                except json.JSONDecodeError:
                    print(f"DEBUG dropEvent: Chromium data from '{CHROMIUM_CUSTOM_MIME}' is not valid JSON. It might be HTML or other structured text.")
                    # If not JSON, it could be HTML embedded within this custom type, or another format.
                    # Check if the decoded_text looks like HTML
                    if decoded_text.strip().lower().startswith("<html") or decoded_text.strip().lower().startswith("<!doctype html"):
                        print(f"DEBUG dropEvent: '{CHROMIUM_CUSTOM_MIME}' data appears to be HTML. Processing as HTML.")
                        # Pass to HTML handler or parse here. For now, create a placeholder.
                        # A more sophisticated HTML parser (e.g., BeautifulSoup) would be needed for real extraction.
                        # For now, just a placeholder.
                        self.add_new_timer_action(title="Chromium HTML Event", comment=f"HTML via Chromium MIME: {decoded_text[:200]}...")
                        event.acceptProposedAction()
                        return
                    else:
                        # If not JSON and not obviously HTML, treat as plain text for now
                        self.add_new_timer_action(title="Chromium Custom Data", comment=f"Raw Data: {decoded_text[:200]}...")
                        event.acceptProposedAction()
                        return

            except Exception as e:
                print(f"ERROR dropEvent: Failed to process data from '{CHROMIUM_CUSTOM_MIME}': {e}")

        # Fallback to generic HTML if provided and not handled by Chromium specific path
        if mime_data.hasHtml():
            print(f"DEBUG dropEvent: Processing '{TEXT_HTML_MIME}' data as a fallback.")
            html_content = mime_data.html() # This is already a string
            print(f"DEBUG dropEvent: HTML Content (first 500 chars):\\n{html_content[:500]}...")
            # Placeholder: A proper HTML parser would be needed here.
            self.add_new_timer_action(title="Generic HTML Drop", comment=f"HTML: {html_content[:200]}...")
            event.acceptProposedAction()
            print(f"DEBUG dropEvent: Successfully added timer from '{TEXT_HTML_MIME}' (fallback): Generic HTML Drop")
            return

        if mime_data.hasFormat(OUTLOOK_ITEM_MIME):
            # This format is complex. If we reached here, it means other more specific formats weren't available or failed.
            print(f"DEBUG dropEvent: '{OUTLOOK_ITEM_MIME}' present, but no direct parser. Attempting fallback to plain text if available.")
            # No direct action, rely on plain text if also present.

        if mime_data.hasFormat(TEXT_PLAIN_MIME):
            print(f"DEBUG dropEvent: Processing '{TEXT_PLAIN_MIME}' data as final fallback")
            plain_text = mime_data.text()
            comment = plain_text 
            lines = plain_text.split('\n', 1)
            if lines:
                title = lines[0].strip()
                if len(lines) > 1: 
                    comment = lines[1].strip()
                else: # Only one line provided
                    comment = "" # Use the single line as title, no separate comment
            
            self.add_new_timer_action(title=title, end_date_str=None, comment=comment) # end_date_str is None, will use default
            event.acceptProposedAction()
            print(f"DEBUG dropEvent: Successfully added timer from '{TEXT_PLAIN_MIME}': {title}")
            return

        print("DEBUG dropEvent: Drop event not handled by any known type or all processing attempts failed.")
        event.ignore()

    def update_sort_order_after_drag(self):
        layout_items_ids = []
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, TimerCard) and hasattr(widget, 'card_id'):
                    layout_items_ids.append(widget.card_id)
        
        for i, card_id_in_layout in enumerate(layout_items_ids):
            if card_id_in_layout in self.timer_configs:
                self.timer_configs[card_id_in_layout]['sort_order'] = i
        self.save_app_settings_and_timers()

    def load_app_settings_and_timers(self):
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            try: os.makedirs(data_dir)
            except OSError as e: print(f"Error creating directory {data_dir}: {e}")
                
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    loaded_global_settings = data.get(GLOBAL_SETTINGS_KEY, {})
                    updated_global_settings = self.global_settings.copy()
                    updated_global_settings.update(loaded_global_settings)
                    self.global_settings = updated_global_settings
                    self.timer_configs = data.get(TIMERS_KEY, {})
            except Exception as e:
                print(f"Error loading {CONFIG_FILE}: {e}. Using defaults.")

    def save_app_settings_and_timers(self):
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            try: os.makedirs(data_dir)
            except OSError as e: print(f"Error creating dir {data_dir} for save: {e}"); return
        
        data_to_save = {GLOBAL_SETTINGS_KEY: self.global_settings, TIMERS_KEY: self.timer_configs}
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(data_to_save, f, indent=4)
        except IOError as e: print(f"Error writing to {CONFIG_FILE}: {e}")

    def update_timer_config(self, card_id, new_config):
        if card_id in self.timer_configs:
            if 'sort_order' not in new_config and 'sort_order' in self.timer_configs[card_id]:
                new_config['sort_order'] = self.timer_configs[card_id]['sort_order']
            self.timer_configs[card_id].update(new_config)
            self.save_app_settings_and_timers()

    def delete_timer_config_and_card(self, card_id):
        if card_id in self.timer_configs: del self.timer_configs[card_id]
        if card_id in self.timers:
            card_widget = self.timers.pop(card_id)
            if card_widget: card_widget.deleteLater()
        self.save_app_settings_and_timers()

    def update_global_default_time_font_size(self, new_size): # ... (rest of methods unchanged)
        self.global_settings["default_time_font_size"] = new_size
        self.save_app_settings_and_timers()

    def update_global_default_title_color(self, new_color_hex):
        self.global_settings["default_bg_color_title"] = new_color_hex
        self.save_app_settings_and_timers()

    def update_global_default_time_color(self, new_color_hex):
        self.global_settings["default_bg_color_time"] = new_color_hex
        self.save_app_settings_and_timers()

    def update_remember_window_position(self, state: bool):
        self.global_settings["remember_window_position"] = state
        if not state:
            self.global_settings["window_x"] = None
            self.global_settings["window_y"] = None
            self.global_settings["window_width"] = None
            self.global_settings["window_height"] = None
        self.save_app_settings_and_timers()

    def closeEvent(self, event: QtGui.QCloseEvent): # Added type hint
        if self.global_settings.get("remember_window_position", False):
            geometry = self.geometry()
            self.global_settings["window_x"] = geometry.x()
            self.global_settings["window_y"] = geometry.y()
            self.global_settings["window_width"] = geometry.width()
            self.global_settings["window_height"] = geometry.height()
            self.save_app_settings_and_timers()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
