import sys
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QApplication, QDialog, QLineEdit, QTextEdit, QColorDialog, QMessageBox,
    QSizePolicy, QDateEdit, QDateTimeEdit, QDialogButtonBox, QSpinBox, QCheckBox,
    QMenu, QToolTip, QFormLayout # Add QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QDate, QEvent, QMimeData # Add QMimeData
from PySide6.QtGui import QPalette, QColor, QMouseEvent, QFont, QAction, QCursor, QEnterEvent, QDrag, QPixmap # Add QDrag, QPixmap

from datetime import datetime, timedelta

# Default colors to be used if not specified in config
DEFAULT_TITLE_BG_COLOR = "#696969"  # DimGray
DEFAULT_TIME_BG_COLOR = "#D3D3D3"   # LightGray
DEFAULT_TIME_TEXT_COLOR = "#000000" # Black for time text
DEFAULT_TIME_FONT_SIZE = 48 # Default font size for the time/days display

class TimerSettingsDialog(QDialog):
    def __init__(self, parent_card, current_config):
        super().__init__(parent_card.app_ref) # Parent to the main app window for modality
        self.parent_card = parent_card
        self.current_config = current_config.copy() # Work on a copy
        self.app_ref = parent_card.app_ref # Store a reference to the main app

        self.setWindowTitle(f"Settings: {self.current_config.get('title', 'Timer')}")
        self.setFixedWidth(210)

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.title_entry = QLineEdit(self.current_config.get("title", ""))
        form_layout.addRow(QLabel("Title:"), self.title_entry)

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        current_end_datetime_str = self.current_config.get("end_date")
        if current_end_datetime_str:
            try:
                dt_obj = datetime.strptime(current_end_datetime_str, "%Y-%m-%d %H:%M:%S")
                self.date_edit.setDate(QDate(dt_obj.year, dt_obj.month, dt_obj.day))
            except ValueError:
                self.date_edit.setDate(QDate.currentDate().addDays(1))
        else:
            self.date_edit.setDate(QDate.currentDate().addDays(1))
        form_layout.addRow(QLabel("Date:"), self.date_edit)
        
        self.time_font_size_spinbox = QSpinBox()
        self.time_font_size_spinbox.setMinimum(8)
        self.time_font_size_spinbox.setMaximum(100)
        self.time_font_size_spinbox.setValue(self.current_config.get("font_size_time", DEFAULT_TIME_FONT_SIZE))
        form_layout.addRow(QLabel("Size:"), self.time_font_size_spinbox)

        main_layout.addLayout(form_layout)

        self.set_default_font_size_checkbox = QCheckBox("Default Font Size")
        main_layout.addWidget(self.set_default_font_size_checkbox)

        # Main Window Transparency Controls
        self.main_window_transparent_checkbox = QCheckBox("Transparent Main Window")
        initial_transparent_bg = self.app_ref.global_settings.get("main_window_transparent_background", False)
        self.main_window_transparent_checkbox.setChecked(initial_transparent_bg)
        main_layout.addWidget(self.main_window_transparent_checkbox)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity Level (if transparent):"))
        self.main_window_opacity_spinbox = QSpinBox()
        self.main_window_opacity_spinbox.setMinimum(0) # 0% opacity
        self.main_window_opacity_spinbox.setMaximum(100) # 100% opacity
        self.main_window_opacity_spinbox.setSuffix("%")
        initial_opacity_percent = int(self.app_ref.global_settings.get("main_window_opacity_level", 1.0) * 100)
        self.main_window_opacity_spinbox.setValue(initial_opacity_percent)
        self.main_window_opacity_spinbox.setEnabled(initial_transparent_bg) # Enable only if transparency is on
        opacity_layout.addWidget(self.main_window_opacity_spinbox)
        main_layout.addLayout(opacity_layout)

        self.main_window_transparent_checkbox.toggled.connect(self.main_window_opacity_spinbox.setEnabled)

        self.remember_window_pos_checkbox = QCheckBox("Remember window position on exit")
        initial_remember_pos = False
        if hasattr(self.app_ref, 'global_settings') and \
           isinstance(self.app_ref.global_settings, dict):
            initial_remember_pos = self.app_ref.global_settings.get("remember_window_position", False)
        self.remember_window_pos_checkbox.setChecked(initial_remember_pos)
        main_layout.addWidget(self.remember_window_pos_checkbox)
        
        main_layout.addSpacing(10)

        main_layout.addWidget(QLabel("Comment:"))
        comment_value = self.current_config.get("comment", "")
        print(f"DEBUG Dialog Init: Comment is '{comment_value}' (repr: {repr(comment_value)})")
        # self.comment_textbox = QTextEdit(comment_value) # Original line
        self.comment_textbox = QTextEdit()  # Create empty
        self.comment_textbox.setAcceptRichText(False)  # Explicitly set to plain text mode
        self.comment_textbox.setPlainText(comment_value)  # Set the text
        # self.comment_textbox.setFixedHeight(120) # Remove fixed height
        self.comment_textbox.setMinimumHeight(60) # Set a minimum height
        self.comment_textbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Allow expanding
        main_layout.addWidget(self.comment_textbox)

        main_layout.addSpacing(10)

        # Title Region Color
        self.title_color_button = QPushButton("Title Background")
        main_layout.addWidget(self.title_color_button)
        self.title_color_button.clicked.connect(self._choose_title_region_color)
        
        self._temp_selected_title_color = self.current_config.get("bg_color_title", DEFAULT_TITLE_BG_COLOR)
            
        self.title_color_preview = QLabel("Preview")
        self.title_color_preview.setAutoFillBackground(True)
        self.title_color_preview.setFixedHeight(20)
        main_layout.addWidget(self.title_color_preview)
        
        self.set_default_title_color_checkbox = QCheckBox("Default Title Background")
        main_layout.addWidget(self.set_default_title_color_checkbox)

        main_layout.addSpacing(10)

        # Time Region Background Color
        self.time_bg_color_button = QPushButton("Time Background") # Renamed for clarity
        main_layout.addWidget(self.time_bg_color_button)
        self.time_bg_color_button.clicked.connect(self._choose_time_bg_color) # Renamed method

        self._temp_selected_time_bg_color = self.current_config.get("bg_color_time", DEFAULT_TIME_BG_COLOR) # Renamed variable
            
        self.time_bg_color_preview = QLabel("Preview") # Renamed for clarity
        self.time_bg_color_preview.setAutoFillBackground(True)
        self.time_bg_color_preview.setFixedHeight(20)
        main_layout.addWidget(self.time_bg_color_preview)

        self.set_default_time_bg_color_checkbox = QCheckBox("Default Time Background") # Renamed for clarity
        main_layout.addWidget(self.set_default_time_bg_color_checkbox)

        main_layout.addSpacing(10) # Space after time background color section

        # Time Region Text Color
        self.time_text_color_button = QPushButton("Time Text Color")
        main_layout.addWidget(self.time_text_color_button)
        self.time_text_color_button.clicked.connect(self._choose_time_text_color)

        self._temp_selected_time_text_color = self.current_config.get("text_color_time", DEFAULT_TIME_TEXT_COLOR)
            
        self.time_text_color_preview = QLabel("Preview")
        self.time_text_color_preview.setAutoFillBackground(True) # Will show text on this bg
        self.time_text_color_preview.setFixedHeight(20)
        main_layout.addWidget(self.time_text_color_preview)

        self.set_default_time_text_color_checkbox = QCheckBox("Default Time Text Color")
        main_layout.addWidget(self.set_default_time_text_color_checkbox)
        
        self._update_color_previews()

        main_layout.addSpacing(10)
        main_layout.addStretch(1)

        # --- Action Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Reset)
        delete_button = self.button_box.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset_settings)
        if delete_button:
            delete_button.clicked.connect(self._delete_timer_from_dialog_button)

        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _update_color_previews(self):
        # Update title color preview
        if self._temp_selected_title_color:
            palette = self.title_color_preview.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(self._temp_selected_title_color))
            self.title_color_preview.setPalette(palette)
        else:
            self.title_color_preview.setPalette(QApplication.style().standardPalette())

        # Update time background color preview
        if self._temp_selected_time_bg_color: # Renamed variable
            palette = self.time_bg_color_preview.palette() # Renamed preview widget
            palette.setColor(QPalette.ColorRole.Window, QColor(self._temp_selected_time_bg_color)) # Renamed variable
            self.time_bg_color_preview.setPalette(palette) # Renamed preview widget
        else:
            self.time_bg_color_preview.setPalette(QApplication.style().standardPalette()) # Renamed preview widget

        # Update time text color preview
        if self._temp_selected_time_text_color:
            palette = self.time_text_color_preview.palette()
            # Set background to something contrasting to see the text color
            # For simplicity, let's use the time background color, or white if not set
            bg_for_text_preview = QColor(self._temp_selected_time_bg_color if self._temp_selected_time_bg_color else "#FFFFFF")
            palette.setColor(QPalette.ColorRole.Window, bg_for_text_preview)
            palette.setColor(QPalette.ColorRole.WindowText, QColor(self._temp_selected_time_text_color))
            self.time_text_color_preview.setPalette(palette)
            self.time_text_color_preview.setText("Text") # Show sample text
        else:
            self.time_text_color_preview.setPalette(QApplication.style().standardPalette())
            self.time_text_color_preview.setText("Preview")


    def _choose_title_region_color(self):
        initial_color = QColor(self._temp_selected_title_color) if self._temp_selected_title_color else Qt.GlobalColor.white
        color = QColorDialog.getColor(initial_color, self, "Choose title region background color")
        if color.isValid():
            self._temp_selected_title_color = color.name()
            self._update_color_previews()

    def _choose_time_bg_color(self): # Renamed method
        initial_color = QColor(self._temp_selected_time_bg_color) if self._temp_selected_time_bg_color else Qt.GlobalColor.white # Renamed variable
        color = QColorDialog.getColor(initial_color, self, "Choose time region background color")
        if color.isValid():
            self._temp_selected_time_bg_color = color.name() # Renamed variable
            self._update_color_previews()

    def _choose_time_text_color(self): # New method
        initial_color = QColor(self._temp_selected_time_text_color) if self._temp_selected_time_text_color else Qt.GlobalColor.black
        color = QColorDialog.getColor(initial_color, self, "Choose time text color")
        if color.isValid():
            self._temp_selected_time_text_color = color.name()
            self._update_color_previews()

    def accept(self):
        # Update the timer card's local config
        self.current_config["title"] = self.title_entry.text()
        
        qdate_val = self.date_edit.date()
        dt_obj = datetime(qdate_val.year(), qdate_val.month(), qdate_val.day(), 0, 0, 0)
        self.current_config["end_date"] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

        self.current_config["font_size_time"] = self.time_font_size_spinbox.value()
        self.current_config["comment"] = self.comment_textbox.toPlainText()
        
        self.current_config["bg_color_title"] = self._temp_selected_title_color
        self.current_config["bg_color_time"] = self._temp_selected_time_bg_color # Renamed variable
        self.current_config["text_color_time"] = self._temp_selected_time_text_color # New

        if self.set_default_font_size_checkbox.isChecked():
            if hasattr(self.app_ref, 'update_global_default_time_font_size'):
                self.app_ref.update_global_default_time_font_size(self.time_font_size_spinbox.value())
        
        if self.set_default_title_color_checkbox.isChecked():
            if hasattr(self.app_ref, 'update_global_default_title_color'):
                self.app_ref.update_global_default_title_color(self._temp_selected_title_color)

        if self.set_default_time_bg_color_checkbox.isChecked(): # Renamed checkbox
            if hasattr(self.app_ref, 'update_global_default_time_color'): # Existing method in main_app for time BG
                self.app_ref.update_global_default_time_color(self._temp_selected_time_bg_color) # Renamed variable

        if self.set_default_time_text_color_checkbox.isChecked(): # New checkbox
            if hasattr(self.app_ref, 'update_global_default_time_text_color'): # New method needed in main_app
                self.app_ref.update_global_default_time_text_color(self._temp_selected_time_text_color)

        # Update main window transparency settings
        if hasattr(self.app_ref, 'update_global_main_window_transparency'):
            self.app_ref.update_global_main_window_transparency(self.main_window_transparent_checkbox.isChecked())
        
        if hasattr(self.app_ref, 'update_global_main_window_opacity'):
            opacity_percent = self.main_window_opacity_spinbox.value()
            self.app_ref.update_global_main_window_opacity(opacity_percent / 100.0)

        if hasattr(self.app_ref, 'update_remember_window_position'):
            self.app_ref.update_remember_window_position(self.remember_window_pos_checkbox.isChecked())

        super().accept()

    def _reset_settings(self):
        self.title_entry.setText(self.parent_card.config.get("title", ""))
        original_end_date_str = self.parent_card.config.get("end_date")
        if original_end_date_str:
            try:
                dt_obj = datetime.strptime(original_end_date_str, "%Y-%m-%d %H:%M:%S")
                self.date_edit.setDate(QDate(dt_obj.year, dt_obj.month, dt_obj.day))
            except ValueError:
                self.date_edit.setDate(QDate.currentDate().addDays(1))
        else:
            self.date_edit.setDate(QDate.currentDate().addDays(1))
        self.comment_textbox.setText(self.parent_card.config.get("comment", ""))
        
        self._temp_selected_title_color = self.parent_card.config.get("bg_color_title", DEFAULT_TITLE_BG_COLOR)
        self._temp_selected_time_bg_color = self.parent_card.config.get("bg_color_time", DEFAULT_TIME_BG_COLOR) # Renamed
        self._temp_selected_time_text_color = self.parent_card.config.get("text_color_time", DEFAULT_TIME_TEXT_COLOR) # New
        self.time_font_size_spinbox.setValue(self.parent_card.config.get("font_size_time", DEFAULT_TIME_FONT_SIZE))
            
        self._update_color_previews()
        
        initial_remember_pos = False
        if hasattr(self.parent_card.app_ref, 'global_settings') and \
           isinstance(self.parent_card.app_ref.global_settings, dict):
            initial_remember_pos = self.parent_card.app_ref.global_settings.get("remember_window_position", False)
        self.remember_window_pos_checkbox.setChecked(initial_remember_pos)

        # Reset main window transparency controls
        initial_transparent_bg = self.app_ref.global_settings.get("main_window_transparent_background", False)
        self.main_window_transparent_checkbox.setChecked(initial_transparent_bg)
        initial_opacity_percent = int(self.app_ref.global_settings.get("main_window_opacity_level", 1.0) * 100)
        self.main_window_opacity_spinbox.setValue(initial_opacity_percent)
        self.main_window_opacity_spinbox.setEnabled(initial_transparent_bg)

    def _delete_timer_from_dialog_button(self):
        # This method is called specifically by the "Delete Timer" button in the QDialogButtonBox
        # It reuses the _delete_timer logic which shows a confirmation.
        # If confirmed, _delete_timer calls self.done(QDialog.DialogCode.Accepted + 1)
        self._delete_timer()

    def _handle_button_click(self, button):
        # This method might still be useful if you have other custom roles,
        # but for the specific "Delete Timer" button, direct connection is clearer.
        if self.button_box.buttonRole(button) == QDialogButtonBox.ButtonRole.DestructiveRole:
            # This will now call _delete_timer_from_dialog_button if the DestructiveRole button is clicked
            # and not directly connected. However, direct connection is preferred.
            pass # Or call self._delete_timer() if not directly connected

    def _delete_timer(self):
        reply = QMessageBox.question(self, "Delete Timer",
                                     f"Are you sure you want to delete '{self.current_config.get('title', 'this timer')}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.parent_card.app_ref.delete_timer_config_and_card(self.parent_card.card_id)
            self.done(QDialog.DialogCode.Accepted + 1) # Custom code to indicate deletion

    def get_updated_config(self):
        qdate = self.date_edit.date()
        year = qdate.year()
        month = qdate.month()
        day = qdate.day()
        end_date_str = datetime(year, month, day, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        
        comment_from_textbox = self.comment_textbox.toPlainText()
        print(f"DEBUG Dialog Save (get_updated_config): Comment from textbox is '{comment_from_textbox}' (repr: {repr(comment_from_textbox)})")
        
        # Normalize the doubled newlines from toPlainText().
        # This handles the observed behavior where each single visual newline (originally \n)
        # becomes \n\n when retrieved by toPlainText().
        normalized_comment = comment_from_textbox.replace('\n\n', '\n')
        print(f"DEBUG Dialog Save (get_updated_config): Normalized comment is '{normalized_comment}' (repr: {repr(normalized_comment)})")

        return {
            "title": self.title_entry.text(),
            "end_date": end_date_str,
            "comment": normalized_comment, # Use normalized comment
            "bg_color_title": self._temp_selected_title_color,
            "bg_color_time": self._temp_selected_time_bg_color, # Renamed
            "text_color_time": self._temp_selected_time_text_color, # New
            "font_size_time": self.time_font_size_spinbox.value(),
            "set_default_font_size": self.set_default_font_size_checkbox.isChecked(),
            "set_default_title_color": self.set_default_title_color_checkbox.isChecked(),
            "set_default_time_color": self.set_default_time_bg_color_checkbox.isChecked(), # Renamed
            "set_default_time_text_color": self.set_default_time_text_color_checkbox.isChecked() # New
        }

class TimerCard(QFrame): # Changed from ctk.CTkFrame
    def __init__(self, master_layout, title, end_date, card_id, app_ref, config=None):
        super().__init__(app_ref) 
        
        self.app_ref = app_ref 
        self.card_id = card_id
        self.config = config.copy() if config else {} 
        self.is_left_mouse_button_down = False
        
        if "comment" not in self.config: self.config["comment"] = ""
        if self.config.get("bg_color_title") is None:
            self.config["bg_color_title"] = DEFAULT_TITLE_BG_COLOR
        if self.config.get("bg_color_time") is None:
            self.config["bg_color_time"] = DEFAULT_TIME_BG_COLOR
        if self.config.get("text_color_time") is None: # New default for time text color
            self.config["text_color_time"] = DEFAULT_TIME_TEXT_COLOR
        if self.config.get("font_size_time") is None:
            self.config["font_size_time"] = DEFAULT_TIME_FONT_SIZE
        if self.config.get("sort_order") is None:
            self.config["sort_order"] = 0 
        
        self.title_str = title 
        self.end_date_str = end_date 

        # self.setMinimumWidth(160)
        self.setFixedWidth(120) # Set fixed width to 120px
        self.setFixedHeight(110)
        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Fixed size for both
        self.setFrameStyle(QFrame.Shape.NoFrame) 

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(0,0,0,0) 
        card_layout.setSpacing(0) 

        # --- Title Region ---
        self.title_region_frame = QFrame()
        self.title_region_frame.setAutoFillBackground(False) 
        self.title_region_frame.setMaximumHeight(35)
        title_region_layout = QVBoxLayout(self.title_region_frame)
        title_region_layout.setContentsMargins(5,2,5,2)

        self.title_label = QLabel(self.title_str)
        font_title = self.title_label.font()
        font_title.setPointSize(11)
        font_title.setBold(False) 
        self.title_label.setFont(font_title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_region_layout.addWidget(self.title_label)
        card_layout.addWidget(self.title_region_frame)

        # --- Time Region ---
        self.time_region_frame = QFrame()
        self.time_region_frame.setAutoFillBackground(False) 
        time_region_layout = QVBoxLayout(self.time_region_frame)
        time_region_layout.setContentsMargins(5,2,5,2)

        self.time_label = QLabel("")
        self._apply_time_label_font()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_region_layout.addWidget(self.time_label)
        card_layout.addWidget(self.time_region_frame)
        
        self.end_datetime = datetime.strptime(self.end_date_str, "%Y-%m-%d %H:%M:%S")

        self.apply_region_colors()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.timer.start(1000)
        self.update_timer_display()
        
        self.settings_dialog = None
        self.hover_timer = None

    def _apply_time_label_font(self):
        font_time = self.time_label.font()
        font_time.setPointSize(self.config.get("font_size_time", DEFAULT_TIME_FONT_SIZE))
        # font_time.setBold(True) # Remove or comment out for a non-bold font
        font_time.setWeight(QFont.Weight.Light) # Set to a lighter font weight
        self.time_label.setFont(font_time)

    def apply_region_colors(self):
        # Fetch colors from config (guaranteed to have defaults by __init__)
        title_bg_color_hex = self.config["bg_color_title"]
        time_bg_color_hex = self.config["bg_color_time"]
        time_text_color_hex = self.config["text_color_time"]
        
        title_text_color = "#FFFFFF" # Ensure title text is white

        border_radius = "10px"

        self.title_region_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {title_bg_color_hex};
                /* color property removed from here */
                border-top-left-radius: {border_radius};
                border-top-right-radius: {border_radius};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        # Explicitly set title label color to white and background to transparent
        self.title_label.setStyleSheet(f"color: {title_text_color}; background-color: transparent;")

        self.time_region_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {time_bg_color_hex};
                color: {time_text_color_hex}; /* Use configured time text color */
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: {border_radius};
                border-bottom-right-radius: {border_radius};
            }}
        """)

    def update_timer_display(self):
        # self.end_datetime is already midnight of the target day due to how it's saved
        target_date = self.end_datetime.date()
        today_date = datetime.now().date()

        days_remaining = (target_date - today_date).days

        if days_remaining < 0:
            self.time_label.setText("Ended") 
            if self.timer.isActive(): # Stop timer only if it's running
                self.timer.stop() 
        else:
            # Display the number of full days remaining until the target date
            # If target_date is today, days_remaining will be 0.
            self.time_label.setText(f"{days_remaining}")
            
            if not self.timer.isActive(): # Ensure timer is running if not ended
                 self.timer.start(1000) # Or your desired interval

    def enterEvent(self, event: QEnterEvent): # Override enterEvent
        # Only start hover timer if left mouse button is not down (i.e., not in a drag attempt)
        if not self.is_left_mouse_button_down:
            comment_for_tooltip = self.config.get("comment", "").strip()
            if comment_for_tooltip:
                print(f"DEBUG Tooltip (enterEvent): Comment is '{comment_for_tooltip}' (repr: {repr(comment_for_tooltip)})")
                if hasattr(self, 'hover_timer') and self.hover_timer and self.hover_timer.isActive(): # Check isActive before stopping
                    self.hover_timer.stop()
                
                self.hover_timer = QTimer(self)
                self.hover_timer.setSingleShot(True)
                self.hover_timer.timeout.connect(self._show_comment_tooltip)
                self.hover_timer.start(1000) # 1-second delay
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent): # Override leaveEvent
        if self.hover_timer and self.hover_timer.isActive():
            self.hover_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def _show_comment_tooltip(self):
        comment = self.config.get("comment", "").strip()
        if comment:
            # Show tooltip near the mouse cursor
            QToolTip.showText(QCursor.pos(), comment, self)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._open_settings_dialog()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_left_mouse_button_down = True
            self.drag_start_position = event.pos()
            # Stop tooltip timer and hide tooltip if a drag might start
            if hasattr(self, 'hover_timer') and self.hover_timer and self.hover_timer.isActive():
                self.hover_timer.stop()
            QToolTip.hideText() # Hide any currently visible tooltip
        super().mousePressEvent(event) # Call super to allow other processing (e.g. context menu on right click)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton and self.is_left_mouse_button_down):
            super().mouseMoveEvent(event)
            return
        
        if not hasattr(self, 'drag_start_position'):
            super().mouseMoveEvent(event)
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        # Drag is starting
        if hasattr(self, 'hover_timer') and self.hover_timer and self.hover_timer.isActive():
            self.hover_timer.stop()
        QToolTip.hideText()

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.card_id)
        drag.setMimeData(mime_data)

        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)
        # Note: is_left_mouse_button_down will be reset in mouseReleaseEvent
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent): # Add this method
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_left_mouse_button_down = False
            # Optionally, if a drag didn't occur, one might re-evaluate tooltip display,
            # but enter/leave events should handle this naturally.
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QMouseEvent): # Right-click
        menu = QMenu(self)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self._open_settings_dialog)
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._confirm_and_delete_card)
        menu.addAction(delete_action)

        menu.exec(event.globalPos())
        event.accept()

    def _confirm_and_delete_card(self):
        reply = QMessageBox.question(self, "Delete Timer",
                                     f"Are you sure you want to delete '{self.config.get('title', 'this timer')}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app_ref.delete_timer_config_and_card(self.card_id)
            # The main app will call create_timer_cards which redraws everything.
            # No need to self.deleteLater() here as the main app handles card removal from layout.

    def _open_settings_dialog(self):
        if self.settings_dialog is not None and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        self.settings_dialog = TimerSettingsDialog(self, self.config)
        result = self.settings_dialog.exec() # exec() is blocking

        if result == QDialog.DialogCode.Accepted:
            updated_config_from_dialog = self.settings_dialog.get_updated_config()
            
            # Update internal state and UI
            self.config.update(updated_config_from_dialog) # Update the card's own config
            self.title_str = self.config["title"]
            self.end_date_str = self.config["end_date"]
            
            try:
                # Ensure self.end_datetime is correctly set to midnight of the new date
                new_date_obj = datetime.strptime(self.end_date_str, "%Y-%m-%d %H:%M:%S").date()
                self.end_datetime = datetime.combine(new_date_obj, datetime.min.time())
            except ValueError:
                QMessageBox.warning(self.app_ref, "Date Error", "Invalid date format after edit. Reverting.")
                # Potentially revert self.config changes related to date or handle error more gracefully

            self.title_label.setText(self.title_str)
            self._apply_time_label_font() # Re-apply font in case it changed
            self.apply_region_colors() 
            self.update_timer_display() 
            
            # Restart timer if it's not active and the end date is in the future
            if self.end_datetime > datetime.now() and not self.timer.isActive():
                self.timer.start(1000)

            # Persist the updated configuration for this specific card
            self.app_ref.update_timer_config(self.card_id, self.config)

            # Handle "Set as Default" options from the dialog's returned config
            # These were already handled by the dialog's accept() method by calling app_ref directly.
            # No explicit action needed here for those, as they modify global settings.
            # The get_updated_config() in the dialog includes these boolean flags,
            # but their action (calling app_ref.update_global_default_... ) was done in TimerSettingsDialog.accept().

        elif result == QDialog.DialogCode.Accepted + 1: # Custom code for deletion
            # Deletion is handled by TimerSettingsDialog calling app_ref.delete_timer_config_and_card
            # The main app will then refresh the cards.
            pass
            
        self.settings_dialog = None # Allow dialog to be garbage collected


    # delete_timer method is now effectively handled within TimerSettingsDialog
    # and the main app's delete_timer_config_and_card

# Example usage (for testing this component in isolation)
if __name__ == '__main__':
    
    class MockApp: # Mock the main application for testing TimerCard
        def __init__(self):
            self.timers = {}
            self.global_settings = {"remember_window_position": False} 
            self.default_time_font_size = DEFAULT_TIME_FONT_SIZE
            self.default_title_color = DEFAULT_TITLE_BG_COLOR # bg_color_title
            self.default_time_color = DEFAULT_TIME_BG_COLOR   # bg_color_time
            self.default_time_text_color = DEFAULT_TIME_TEXT_COLOR # New global default

        def update_timer_config(self, card_id, config):
            print(f"MockApp: Update config for {card_id}: {config}")
        def delete_timer_config_and_card(self, card_id):
            print(f"MockApp: Delete timer {card_id}")
            if card_id in self.timers:
                self.timers[card_id].deleteLater() 
                del self.timers[card_id]
        def create_timer_cards(self):
            print("MockApp: Recreating timer cards (sorting)")

        def update_global_default_time_font_size(self, size):
            self.default_time_font_size = size
            print(f"MockApp: Global default time font size set to {size}")
            self.global_settings["default_time_font_size"] = size
            self.save_global_settings()

        def update_global_default_title_color(self, color_hex): # For title background
            self.default_title_color = color_hex
            print(f"MockApp: Global default title background color set to {color_hex}")
            self.global_settings["default_title_color"] = color_hex
            self.save_global_settings()

        def update_global_default_time_color(self, color_hex): # For time background
            self.default_time_color = color_hex
            print(f"MockApp: Global default time background color set to {color_hex}")
            self.global_settings["default_time_color"] = color_hex
            self.save_global_settings()
            
        def update_global_default_time_text_color(self, color_hex): # New method for time text color
            self.default_time_text_color = color_hex
            print(f"MockApp: Global default time text color set to {color_hex}")
            self.global_settings["default_time_text_color"] = color_hex # Save to global_settings
            self.save_global_settings()
            
        def update_global_main_window_transparency(self, is_transparent):
            print(f"MockApp: Global main window transparency set to {is_transparent}")
            self.global_settings["main_window_transparent_background"] = is_transparent
            self.save_global_settings()

        def update_global_main_window_opacity(self, opacity_level):
            print(f"MockApp: Global main window opacity level set to {opacity_level}")
            self.global_settings["main_window_opacity_level"] = opacity_level
            self.save_global_settings()
            
        def save_global_settings(self):
            print(f"MockApp: Saving global settings: {self.global_settings}")


    app = QApplication(sys.argv)
    
    # Create a main window to host the card for testing
    main_win = QWidget()
    main_layout = QVBoxLayout(main_win)
    
    mock_app_ref = MockApp()

    # Example config
    test_config = {
        "title": "Test Event", 
        "end_date": (datetime.now() + timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "comment": "This is a test comment.",
        "bg_color_title": "#aaffaa", 
        "bg_color_time": "#aaaaff",
        "text_color_time": "#FF0000", # Example: Red time text
        "font_size_time": 50
    }
    
    card1 = TimerCard(main_layout, 
                      title=test_config["title"], 
                      end_date=test_config["end_date"], 
                      card_id="test_timer_1", 
                      app_ref=mock_app_ref, 
                      config=test_config)
    main_layout.addWidget(card1)
    mock_app_ref.timers["test_timer_1"] = card1

    test_config_2 = {
        "title": "Short Timer", 
        "end_date": (datetime.now() + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "comment": "Expires soon!",
        "bg_color_title": "#ffaaaa", 
        "bg_color_time": None, # Will use default time background
        "text_color_time": None, # Will use default time text (black)
        "font_size_time": DEFAULT_TIME_FONT_SIZE
    }
    card2 = TimerCard(main_layout,
                      title=test_config_2["title"],
                      end_date=test_config_2["end_date"],
                      card_id="test_timer_2",
                      app_ref=mock_app_ref,
                      config=test_config_2)
    main_layout.addWidget(card2)
    mock_app_ref.timers["test_timer_2"] = card2
    
    main_win.setWindowTitle("TimerCard Test")
    main_win.resize(300, 400)
    main_win.show()
    
    sys.exit(app.exec())
