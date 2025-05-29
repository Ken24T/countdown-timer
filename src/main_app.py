import customtkinter as ctk
from tkinter import simpledialog # Keep for now, or replace with ctk.CTkInputDialog later
import json
import os
from .components.timer_card import TimerCard # This will also need to be updated to use CustomTkinter

# Updated CONFIG_FILE path
CONFIG_FILE = os.path.join("data", "timers_config.json")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

        self.title("Countdown Timer")
        self.geometry("800x600")

        # Main frame for all content
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame for the "Add Timer" button
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(pady=10)

        self.add_timer_button = ctk.CTkButton(self.controls_frame, text="Add New Timer", command=self.add_timer_dialog)
        self.add_timer_button.pack(side="left", padx=5)

        # Scrollable frame for timer cards
        self.scrollable_timers_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scrollable_timers_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.timers = {}  # To store TimerCard instances
        self.timer_configs = self.load_timers_config()
        self.create_timer_cards()

    def add_timer_dialog(self):
        # For simpledialog, you might consider ctk.CTkInputDialog
        # This part will need more specific changes based on how you want the dialog to look with CustomTkinter
        dialog = simpledialog.Dialog(self, "Add New Timer")
        # Simplified: In a real scenario, you'd build a CTkInputDialog or a custom CTkToplevel window
        # For now, let's assume it returns title and date_str similar to before
        # title = simpledialog.askstring("Input", "Enter timer title:", parent=self)
        # if not title:
        #     return
        # date_str = simpledialog.askstring("Input", "Enter end date (YYYY-MM-DD HH:MM:SS):", parent=self)
        # if not date_str:
        #     return
        
        # Placeholder for getting title and date_str, as simpledialog might not integrate perfectly
        # without further adjustments or replacement.
        # This is a known area for further refinement.
        title = "New Timer (Edit Me)"
        from datetime import datetime, timedelta
        date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        if title and date_str:
            card_id = f"timer_{len(self.timer_configs) + 1}"
            new_config = {"title": title, "end_date": date_str}
            self.timer_configs[card_id] = new_config
            self.save_timers_config()
            self.create_timer_card(card_id, new_config, self.scrollable_timers_frame)

    def create_timer_card(self, card_id, config, parent_frame):
        card = TimerCard(parent_frame, 
                         title=config["title"], 
                         end_date=config["end_date"], 
                         card_id=card_id, 
                         app_ref=self, # Pass app reference for callbacks
                         config=config) # Pass full config if TimerCard handles its own sub-configs (e.g., color)
        card.pack(pady=10, padx=10, fill="x")
        self.timers[card_id] = card
        return card

    def create_timer_cards(self):
        for widget in self.scrollable_timers_frame.winfo_children():
            widget.destroy()
        self.timers.clear()
        for card_id, config in self.timer_configs.items():
            self.create_timer_card(card_id, config, self.scrollable_timers_frame)

    def load_timers_config(self):
        # Ensure the data directory exists
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def save_timers_config(self):
        # Ensure the data directory exists
        data_dir = os.path.dirname(CONFIG_FILE)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.timer_configs, f, indent=4)

    def update_timer_config(self, card_id, new_config):
        if card_id in self.timer_configs:
            self.timer_configs[card_id].update(new_config)
            self.save_timers_config()

    def delete_timer_config_and_card(self, card_id):
        if card_id in self.timer_configs:
            del self.timer_configs[card_id]
            self.save_timers_config()
        if card_id in self.timers:
            self.timers[card_id].destroy()
            del self.timers[card_id]
