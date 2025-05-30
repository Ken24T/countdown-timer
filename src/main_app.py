import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QByteArray
from PySide6 import QtGui
from .components.timer_card import TimerCard, DEFAULT_TIME_FONT_SIZE, DEFAULT_TITLE_BG_COLOR, DEFAULT_TIME_BG_COLOR
import os
import json
import uuid
from datetime import datetime, timedelta

CHROMIUM_CUSTOM_MIME = 'application/x-qt-windows-mime;value="Chromium Web Custom MIME Data Format"'
TEXT_PLAIN_MIME = 'text/plain'
TEXT_HTML_MIME = 'text/html'

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
        self.add_timer_button.setFixedWidth(120) 
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
        except Exception:
            sorted_configs = sorted(self.timer_configs.items())

        for card_id, config in sorted_configs:
            self.create_timer_card(card_id, config, self.timers_layout)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        mime_data = event.mimeData()
        accepted = False
        if mime_data.hasText() and mime_data.text().startswith("timer_"):
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

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        mime_data = event.mimeData()
        accepted = False
        if mime_data.hasText() and mime_data.text().startswith("timer_"):
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
        if mime_data.hasText() and mime_data.text().startswith("timer_"):
            source_card_id = mime_data.text()
            source_widget = self.timers.get(source_card_id)
            if not source_widget:
                event.ignore()
                return
            drop_pos_in_viewport = event.position()
            drop_pos_y = drop_pos_in_viewport.y()
            insert_idx = 0
            for i in range(self.timers_layout.count()):
                item = self.timers_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, TimerCard):
                        if drop_pos_y < widget.y() + widget.height() / 2:
                            insert_idx = i
                            break
                        insert_idx = i + 1
            current_idx = self.timers_layout.indexOf(source_widget)
            self.timers_layout.removeWidget(source_widget)
            if current_idx != -1 and current_idx < insert_idx:
                insert_idx -= 1
            self.timers_layout.insertWidget(insert_idx, source_widget)
            self.update_sort_order_after_drag()
            event.acceptProposedAction()
            return
        if mime_data.hasFormat(CHROMIUM_CUSTOM_MIME):
            try:
                q_byte_array: QByteArray = mime_data.data(CHROMIUM_CUSTOM_MIME)
                python_bytes = bytes(q_byte_array.data())
                decoded_text = python_bytes.decode('utf-8', errors='replace')
                try:
                    json_data = json.loads(decoded_text)
                    evt_title = str(json_data.get('summary', json_data.get('title', "Chromium JSON Event")))
                    evt_comment_detail = str(json_data) if len(str(json_data)) < 300 else str(json_data)[:300] + "..."
                    evt_comment = json_data.get('description', evt_comment_detail)
                    self.add_new_timer_action(title=evt_title, comment=str(evt_comment))
                    event.acceptProposedAction()
                    return
                except json.JSONDecodeError:
                    pass
                except Exception:
                    pass
            except Exception:
                pass
        if mime_data.hasText():
            text_content = mime_data.text()
            if len(text_content) > 50:
                title = text_content[:50] + "..."
                comment = text_content
            else:
                title = text_content
                comment = ""
            self.add_new_timer_action(title=title, comment=comment)
            event.acceptProposedAction()
            return
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
            try:
                os.makedirs(data_dir)
            except OSError as e:
                print(f"Error creating directory {data_dir}: {e}")
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
            try:
                os.makedirs(data_dir)
            except OSError as e:
                print(f"Error creating dir {data_dir} for save: {e}")
                return
        data_to_save = {GLOBAL_SETTINGS_KEY: self.global_settings, TIMERS_KEY: self.timer_configs}
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=4)
        except IOError as e:
            print(f"Error writing to {CONFIG_FILE}: {e}")

    def update_timer_config(self, card_id, new_config):
        if card_id in self.timer_configs:
            if 'sort_order' not in new_config and 'sort_order' in self.timer_configs[card_id]:
                new_config['sort_order'] = self.timer_configs[card_id]['sort_order']
            self.timer_configs[card_id].update(new_config)
            self.save_app_settings_and_timers()

    def delete_timer_config_and_card(self, card_id):
        if card_id in self.timer_configs:
            del self.timer_configs[card_id]
        if card_id in self.timers:
            card_widget = self.timers.pop(card_id)
            if card_widget:
                card_widget.deleteLater()
        self.save_app_settings_and_timers()

    def update_global_default_time_font_size(self, new_size):
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

    def closeEvent(self, event: QtGui.QCloseEvent):
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
