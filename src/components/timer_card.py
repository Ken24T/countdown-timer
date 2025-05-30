import sys
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QApplication, QDialog, QLineEdit, QTextEdit, QColorDialog, QMessageBox,
    QSizePolicy, QDateEdit, QDateTimeEdit, QDialogButtonBox, QSpinBox, QCheckBox,
    QMenu, QToolTip, QFormLayout # Add QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QDate, QEvent # Add QEvent
from PySide6.QtGui import QPalette, QColor, QMouseEvent, QFont, QAction, QCursor, QEnterEvent # Add QCursor, QEnterEvent

from datetime import datetime, timedelta

# Default colors to be used if not specified in config
DEFAULT_TITLE_BG_COLOR = "#696969"  # DimGray
DEFAULT_TIME_BG_COLOR = "#D3D3D3"   # LightGray
DEFAULT_TIME_FONT_SIZE = 48 # Default font size for the time/days display

class TimerSettingsDialog(QDialog):
    def __init__(self, parent_card, current_config):
        super().__init__(parent_card.app_ref) # Parent to the main app window for modality
        self.parent_card = parent_card
        self.current_config = current_config.copy() # Work on a copy
        self.app_ref = parent_card.app_ref # Store a reference to the main app

        self.setWindowTitle(f"Settings: {self.current_config.get('title', 'Timer')}")
        # self.setMinimumWidth(80) # Set width to 80
        self.setFixedWidth(260) # Force width to 320px (80 + 300%)

        main_layout = QVBoxLayout() # Main vertical layout

        # --- Form Section for basic inputs ---
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # Align labels to the right

        # Title
        self.title_entry = QLineEdit(self.current_config.get("title", ""))
        form_layout.addRow(QLabel("Title:"), self.title_entry) # Shortened label

        # End Date
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yy-MM-dd") # Shortened display format
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
        form_layout.addRow(QLabel("Date:"), self.date_edit) # Shortened label
        
        # Time Display Font Size
        self.time_font_size_spinbox = QSpinBox()
        self.time_font_size_spinbox.setMinimum(8)
        self.time_font_size_spinbox.setMaximum(100)
        self.time_font_size_spinbox.setValue(self.current_config.get("font_size_time", DEFAULT_TIME_FONT_SIZE))
        form_layout.addRow(QLabel("Size:"), self.time_font_size_spinbox) # Shortened label

        main_layout.addLayout(form_layout)

        # Checkbox to set as default font size (placed after form layout)
        self.set_default_font_size_checkbox = QCheckBox("Default Font Size") # Updated text
        main_layout.addWidget(self.set_default_font_size_checkbox)

        # Checkbox for remembering window position
        self.remember_window_pos_checkbox = QCheckBox("Remember window position on exit")
        initial_remember_pos = False
        # Try to get the setting from app_ref, assuming it has a global_settings dictionary
        if hasattr(self.app_ref, 'global_settings') and \
           isinstance(self.app_ref.global_settings, dict):
            initial_remember_pos = self.app_ref.global_settings.get("remember_window_position", False)
        self.remember_window_pos_checkbox.setChecked(initial_remember_pos)
        main_layout.addWidget(self.remember_window_pos_checkbox)
        
        main_layout.addSpacing(10) # Space after font size section

        # Comment
        main_layout.addWidget(QLabel("Comment:")) # Label can remain as is, on its own line
        self.comment_textbox = QTextEdit(self.current_config.get("comment", ""))
        self.comment_textbox.setFixedHeight(120) # Increased height (80 * 1.5)
        main_layout.addWidget(self.comment_textbox)

        main_layout.addSpacing(10) # Space after comment section

        # --- Color Choosers ---
        # Title Region Color
        self.title_color_button = QPushButton("Title Background") # Updated text
        main_layout.addWidget(self.title_color_button)
        self.title_color_button.clicked.connect(self._choose_title_region_color)
        
        self._temp_selected_title_color = self.current_config.get("bg_color_title", DEFAULT_TITLE_BG_COLOR)
            
        self.title_color_preview = QLabel("Preview")
        self.title_color_preview.setAutoFillBackground(True)
        self.title_color_preview.setFixedHeight(20) # Fixed height for preview
        main_layout.addWidget(self.title_color_preview)
        
        self.set_default_title_color_checkbox = QCheckBox("Default Title Background") # Updated text
        main_layout.addWidget(self.set_default_title_color_checkbox)

        main_layout.addSpacing(10) # Space after title color section

        # Time Region Color
        self.time_color_button = QPushButton("Time Background") # Updated text
        main_layout.addWidget(self.time_color_button)
        self.time_color_button.clicked.connect(self._choose_time_region_color)

        self._temp_selected_time_color = self.current_config.get("bg_color_time", DEFAULT_TIME_BG_COLOR)
            
        self.time_color_preview = QLabel("Preview")
        self.time_color_preview.setAutoFillBackground(True)
        self.time_color_preview.setFixedHeight(20) # Fixed height for preview
        main_layout.addWidget(self.time_color_preview)

        self.set_default_time_color_checkbox = QCheckBox("Default Time Background") # Updated text
        main_layout.addWidget(self.set_default_time_color_checkbox)
        
        self._update_color_previews() # Call after previews are created

        main_layout.addSpacing(10) # Space before action buttons (above stretch)

        main_layout.addStretch(1) # Add stretch to push buttons to the bottom

        # --- Action Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Reset)
        delete_button = self.button_box.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole) # Changed text to "Delete"

        self.button_box.accepted.connect(self.accept) # Keep existing accept
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset_settings)
        # self.button_box.clicked.connect(self._handle_button_click) # Connect to the specific delete button if needed, or handle via role
        if delete_button: # Ensure button was added
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

        # Update time color preview
        if self._temp_selected_time_color:
            palette = self.time_color_preview.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(self._temp_selected_time_color))
            self.time_color_preview.setPalette(palette)
        else:
            self.time_color_preview.setPalette(QApplication.style().standardPalette())


    def _choose_title_region_color(self):
        initial_color = QColor(self._temp_selected_title_color) if self._temp_selected_title_color else Qt.GlobalColor.white
        color = QColorDialog.getColor(initial_color, self, "Choose title region background color")
        if color.isValid():
            self._temp_selected_title_color = color.name() # Corrected variable name
            self._update_color_previews()

    def _choose_time_region_color(self):
        initial_color = QColor(self._temp_selected_time_color) if self._temp_selected_time_color else Qt.GlobalColor.white
        color = QColorDialog.getColor(initial_color, self, "Choose time region background color")
        if color.isValid():
            self._temp_selected_time_color = color.name()
            self._update_color_previews()

    def accept(self):
        # Update the timer card's local config
        self.current_config["title"] = self.title_entry.text()
        
        # Date handling - ensure it's stored in the correct string format
        qdate_val = self.date_edit.date()
        # Assuming time is always midnight for simplicity, adjust if time component is needed
        dt_obj = datetime(qdate_val.year(), qdate_val.month(), qdate_val.day(), 0, 0, 0)
        self.current_config["end_date"] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

        self.current_config["font_size_time"] = self.time_font_size_spinbox.value()
        self.current_config["comment"] = self.comment_textbox.toPlainText()
        
        # Update colors from temp selections
        self.current_config["bg_color_title"] = self._temp_selected_title_color
        self.current_config["bg_color_time"] = self._temp_selected_time_color

        # The TimerCard._open_settings_dialog() method handles updating the card's
        # configuration after this dialog is accepted and returns the new config.
        # self.parent_card.update_config(self.current_config) # This line caused the AttributeError

        # Handle "Set as Default" checkboxes
        if self.set_default_font_size_checkbox.isChecked():
            if hasattr(self.app_ref, 'update_global_default_time_font_size'):
                self.app_ref.update_global_default_time_font_size(self.time_font_size_spinbox.value())
        
        if self.set_default_title_color_checkbox.isChecked():
            if hasattr(self.app_ref, 'update_global_default_title_color'):
                self.app_ref.update_global_default_title_color(self._temp_selected_title_color)

        if self.set_default_time_color_checkbox.isChecked():
            if hasattr(self.app_ref, 'update_global_default_time_color'):
                self.app_ref.update_global_default_time_color(self._temp_selected_time_color)

        # Handle "Remember window position" checkbox
        if hasattr(self.app_ref, 'update_remember_window_position'):
            self.app_ref.update_remember_window_position(self.remember_window_pos_checkbox.isChecked())

        super().accept() # Call QDialog's accept method

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
        self._temp_selected_time_color = self.parent_card.config.get("bg_color_time", DEFAULT_TIME_BG_COLOR)
        self.time_font_size_spinbox.setValue(self.parent_card.config.get("font_size_time", DEFAULT_TIME_FONT_SIZE))
            
        self._update_color_previews()
        
        # Note: The "Remember window position" checkbox is a global app setting
        # and should not be reset by this timer-specific reset function.
        # Its state reflects the current global setting.
        initial_remember_pos = False
        if hasattr(self.parent_card.app_ref, 'global_settings') and \
           isinstance(self.parent_card.app_ref.global_settings, dict):
            initial_remember_pos = self.parent_card.app_ref.global_settings.get("remember_window_position", False)
        self.remember_window_pos_checkbox.setChecked(initial_remember_pos)


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
            # To avoid double-handling if direct connection is used, this might need adjustment
            # or rely solely on direct connections for specific buttons.
            # For now, let's assume direct connection for delete is primary.
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
        # Ensure we get year, month, day from QDate (works in all PySide6 versions)
        year = qdate.year()
        month = qdate.month()
        day = qdate.day()
        end_date_str = datetime(year, month, day, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "title": self.title_entry.text(),
            "end_date": end_date_str,
            "comment": self.comment_textbox.toPlainText(),
            "bg_color_title": self._temp_selected_title_color,
            "bg_color_time": self._temp_selected_time_color,
            "font_size_time": self.time_font_size_spinbox.value(),
            "set_default_font_size": self.set_default_font_size_checkbox.isChecked(),
            "set_default_title_color": self.set_default_title_color_checkbox.isChecked(),
            "set_default_time_color": self.set_default_time_color_checkbox.isChecked()
        }

class TimerCard(QFrame): # Changed from ctk.CTkFrame
    def __init__(self, master_layout, title, end_date, card_id, app_ref, config=None):
        super().__init__(app_ref) 
        
        self.app_ref = app_ref 
        self.card_id = card_id
        self.config = config.copy() if config else {} 
        
        if "comment" not in self.config: self.config["comment"] = ""
        if self.config.get("bg_color_title") is None:
            self.config["bg_color_title"] = DEFAULT_TITLE_BG_COLOR
        if self.config.get("bg_color_time") is None:
            self.config["bg_color_time"] = DEFAULT_TIME_BG_COLOR
        if self.config.get("font_size_time") is None: # Add default for time font size
            self.config["font_size_time"] = DEFAULT_TIME_FONT_SIZE
        
        self.title_str = title 
        self.end_date_str = end_date 

        # self.setFixedWidth(160) # Removed to allow horizontal resizing
        self.setMinimumWidth(160) # Set a minimum width
        self.setFixedHeight(120) # Keep fixed height
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Allow horizontal expansion, fixed vertical
        self.setFrameStyle(QFrame.Shape.NoFrame) 

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(0,0,0,0) 
        card_layout.setSpacing(0) 

        # --- Title Region ---
        self.title_region_frame = QFrame()
        self.title_region_frame.setAutoFillBackground(False) 
        self.title_region_frame.setMaximumHeight(35) # Reduce title section height
        title_region_layout = QVBoxLayout(self.title_region_frame)
        title_region_layout.setContentsMargins(5,2,5,2) # Adjust margins for new height

        self.title_label = QLabel(self.title_str)
        font_title = self.title_label.font()
        font_title.setPointSize(11) # Increase title font size
        font_title.setBold(False) 
        self.title_label.setFont(font_title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_region_layout.addWidget(self.title_label)
        card_layout.addWidget(self.title_region_frame)

        # --- Time Region ---
        self.time_region_frame = QFrame()
        self.time_region_frame.setAutoFillBackground(False) 
        time_region_layout = QVBoxLayout(self.time_region_frame)
        time_region_layout.setContentsMargins(5,2,5,2) # Compact margins for time region

        self.time_label = QLabel("")
        self._apply_time_label_font() # Apply font size from config
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_region_layout.addWidget(self.time_label)
        card_layout.addWidget(self.time_region_frame)
        
        # Remove stretch factors as the card height is now fixed, and title region has a max height.
        # The time region will naturally take the remaining space within the fixed card height.
        # card_layout.setStretchFactor(self.title_region_frame, 0) 
        # card_layout.setStretchFactor(self.time_region_frame, 1)  


        # The self.end_datetime will be parsed from a string like "YYYY-MM-DD 00:00:00"
        self.end_datetime = datetime.strptime(self.end_date_str, "%Y-%m-%d %H:%M:%S")

        self.apply_region_colors()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.timer.start(1000)  # Update every second
        self.update_timer_display()
        
        self.settings_dialog = None
        self.hover_timer = None # Timer for delayed tooltip

    def _apply_time_label_font(self):
        font_time = self.time_label.font()
        font_time.setPointSize(self.config.get("font_size_time", DEFAULT_TIME_FONT_SIZE))
        font_time.setBold(True)
        self.time_label.setFont(font_time)

    def apply_region_colors(self):
        # Fetch colors from config (guaranteed to have defaults by __init__)
        title_color_hex = self.config["bg_color_title"]
        time_color_hex = self.config["bg_color_time"]
        
        # Determine text color based on background (simple version: white for dark, black for light)
        # For simplicity, we'll use a fixed light color for now, assuming backgrounds can be dark.
        # A more robust solution would calculate luminance.
        text_color = "#FFFFFF" # White text for visibility on potentially dark backgrounds

        border_radius = "10px" # Define radius once

        self.title_region_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {title_color_hex};
                color: {text_color};
                border-top-left-radius: {border_radius};
                border-top-right-radius: {border_radius};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)

        self.time_region_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {time_color_hex};
                color: {text_color};
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
        comment = self.config.get("comment", "").strip()
        if comment:
            if self.hover_timer:
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
            updated_config = self.settings_dialog.get_updated_config()
            
            # Update internal state and UI
            self.config.update(updated_config)
            self.title_str = self.config["title"]
            self.end_date_str = self.config["end_date"]
            
            try:
                # Ensure self.end_datetime is correctly set to midnight of the new date
                new_date_obj = datetime.strptime(self.end_date_str, "%Y-%m-%d %H:%M:%S").date()
                self.end_datetime = datetime.combine(new_date_obj, datetime.min.time())
            except ValueError:
                QMessageBox.warning(self.app_ref, "Date Error", "Invalid date format after edit. Reverting.")
                # Potentially revert or handle error more gracefully
                return

            self.title_label.setText(self.title_str)
            self._apply_time_label_font() # Re-apply font in case it changed
            self.apply_region_colors() 
            self.update_timer_display() 
            if self.end_datetime > datetime.now() and not self.timer.isActive():
                self.timer.start(1000) # Restart timer if it was stopped and date is in future

            # If "set as default font size" was checked, update the global default in the main app
            if updated_config.get("set_default_font_size"):
                if hasattr(self.app_ref, "update_global_default_time_font_size"):
                    self.app_ref.update_global_default_time_font_size(updated_config["font_size_time"])
                else:
                    print("Warning: Main app does not have 'update_global_default_time_font_size' method.")
            
            # If "set as default title color" was checked
            if updated_config.get("set_default_title_color"):
                if hasattr(self.app_ref, "update_global_default_title_color"):
                    self.app_ref.update_global_default_title_color(updated_config["bg_color_title"])
                else:
                    print("Warning: Main app does not have 'update_global_default_title_color' method.")

            # If "set as default time color" was checked
            if updated_config.get("set_default_time_color"):
                if hasattr(self.app_ref, "update_global_default_time_color"):
                    self.app_ref.update_global_default_time_color(updated_config["bg_color_time"])
                else:
                    print("Warning: Main app does not have 'update_global_default_time_color' method.")

            # Handle the "Remember window position" setting
            remember_pos_pref = self.settings_dialog.remember_window_pos_checkbox.isChecked()
            if hasattr(self.app_ref, 'global_settings') and \
               isinstance(self.app_ref.global_settings, dict):
                self.app_ref.global_settings["remember_window_position"] = remember_pos_pref
                if hasattr(self.app_ref, 'save_global_settings'):
                    self.app_ref.save_global_settings() # Persist global settings
                else:
                    print("Warning: Main app does not have 'save_global_settings' method.")
            else:
                print("Warning: Main app does not have 'global_settings' dictionary to save window position preference.")

            self.app_ref.update_timer_config(self.card_id, self.config)
            self.app_ref.create_timer_cards() # Re-sort and re-draw all cards

        elif result == QDialog.DialogCode.Accepted + 1: # Custom code for deletion
            # Deletion is handled by the dialog calling app_ref.delete_timer_config_and_card
            # and then main_app calls create_timer_cards which redraws everything.
            pass 
            
        self.settings_dialog = None # Allow it to be garbage collected

    # delete_timer method is now effectively handled within TimerSettingsDialog
    # and the main app's delete_timer_config_and_card

# Example usage (for testing this component in isolation)
if __name__ == '__main__':
    
    class MockApp: # Mock the main application for testing TimerCard
        def __init__(self):
            self.timers = {}
            self.global_settings = {"remember_window_position": False} # Default global setting
            self.default_time_font_size = DEFAULT_TIME_FONT_SIZE
            self.default_title_color = DEFAULT_TITLE_BG_COLOR
            self.default_time_color = DEFAULT_TIME_BG_COLOR

        def update_timer_config(self, card_id, config):
            print(f"MockApp: Update config for {card_id}: {config}")
        def delete_timer_config_and_card(self, card_id):
            print(f"MockApp: Delete timer {card_id}")
            if card_id in self.timers:
                self.timers[card_id].deleteLater() # Remove from layout if it was added
                del self.timers[card_id]
        def create_timer_cards(self):
            print("MockApp: Recreating timer cards (sorting)")

        def update_global_default_time_font_size(self, size):
            self.default_time_font_size = size
            print(f"MockApp: Global default time font size set to {size}")
            # In a real app, this would also save to a global config
            self.global_settings["default_time_font_size"] = size
            self.save_global_settings()


        def update_global_default_title_color(self, color_hex):
            self.default_title_color = color_hex
            print(f"MockApp: Global default title color set to {color_hex}")
            self.global_settings["default_title_color"] = color_hex
            self.save_global_settings()

        def update_global_default_time_color(self, color_hex):
            self.default_time_color = color_hex
            print(f"MockApp: Global default time color set to {color_hex}")
            self.global_settings["default_time_color"] = color_hex
            self.save_global_settings()
            
        def save_global_settings(self):
            # In a real app, this would save self.global_settings to a file
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
        "font_size_time": 50 # Example custom font size
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
        "bg_color_time": None,
        "font_size_time": DEFAULT_TIME_FONT_SIZE # Uses default
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
