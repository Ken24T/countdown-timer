import customtkinter as ctk
from tkinter import messagebox # Keep for now, CTk doesn't have a direct messagebox but system ones are fine
# For simpledialog, consider ctk.CTkInputDialog. For colorchooser, a custom solution is needed.
from tkinter import simpledialog, colorchooser 
from datetime import datetime, timedelta
import json

class TimerCard(ctk.CTkFrame):
    def __init__(self, master, title, end_date, card_id, app_ref, config=None):
        super().__init__(master)
        self.master = master
        self.title_text = title
        self.end_date_str = end_date
        self.card_id = card_id
        self.app_ref = app_ref # Reference to the main App instance
        self.config = config if config else {}

        self.end_datetime = datetime.strptime(self.end_date_str, "%Y-%m-%d %H:%M:%S")

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1) # Title and time
        self.grid_columnconfigure(1, weight=0) # Buttons frame

        # Frame for title and time
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.info_frame, text=self.title_text, font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w", padx=5)

        self.time_label = ctk.CTkLabel(self.info_frame, text="", font=ctk.CTkFont(size=20))
        self.time_label.grid(row=1, column=0, sticky="w", padx=5, pady=(0,5))

        # Frame for buttons
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=0, column=1, sticky="e", padx=5, pady=5)

        self.edit_button = ctk.CTkButton(self.buttons_frame, text="Edit", width=60, command=self.edit_timer)
        self.edit_button.pack(side="left", padx=2)

        self.color_button = ctk.CTkButton(self.buttons_frame, text="Color", width=60, command=self.change_color)
        self.color_button.pack(side="left", padx=2)
        
        self.delete_button = ctk.CTkButton(self.buttons_frame, text="Delete", width=60, command=self.delete_timer, fg_color="red", hover_color="darkred")
        self.delete_button.pack(side="left", padx=2)

        self.apply_card_color()
        self.update_timer()

    def apply_card_color(self):
        bg_color = self.config.get("bg_color")
        # fg_color = self.config.get("fg_color") # Text color
        if bg_color:
            self.configure(fg_color=bg_color)
            # For CTk, you might need to set fg_color for child frames/labels too if they don't inherit
            # self.info_frame.configure(fg_color=bg_color) # if info_frame shouldn't be transparent
            # self.title_label.configure(text_color=fg_color)
            # self.time_label.configure(text_color=fg_color)


    def update_timer(self):
        now = datetime.now()
        remaining = self.end_datetime - now

        if remaining.total_seconds() <= 0:
            self.time_label.configure(text="Time's up!")
            # Optionally change color or style when time is up
            self.configure(fg_color="gray") # Example: change card color
        else:
            days = remaining.days
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = ""
            if days > 0:
                time_str += f"{days}d "
            if hours > 0 or days > 0: # Show hours if days are present or hours > 0
                time_str += f"{hours}h "
            if minutes > 0 or hours > 0 or days > 0: # Show minutes if larger units are present or minutes > 0
                time_str += f"{minutes}m "
            time_str += f"{seconds}s"
            
            self.time_label.configure(text=time_str.strip())
            self.after(1000, self.update_timer) # Schedule next update

    def edit_timer(self):
        # Replace with CTkInputDialog or a custom CTkToplevel window
        new_title = simpledialog.askstring("Edit Timer", "Enter new title:", initialvalue=self.title_text, parent=self.app_ref)
        if new_title is not None:
            self.title_text = new_title
            self.title_label.configure(text=self.title_text)
            self.config["title"] = self.title_text
            self.app_ref.update_timer_config(self.card_id, {"title": self.title_text})

        new_date_str = simpledialog.askstring("Edit Timer", "Enter new end date (YYYY-MM-DD HH:MM:SS):", initialvalue=self.end_date_str, parent=self.app_ref)
        if new_date_str is not None:
            try:
                self.end_datetime = datetime.strptime(new_date_str, "%Y-%m-%d %H:%M:%S")
                self.end_date_str = new_date_str
                self.config["end_date"] = self.end_date_str
                self.app_ref.update_timer_config(self.card_id, {"end_date": self.end_date_str})
                self.update_timer() # Restart timer with new date
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD HH:MM:SS", parent=self.app_ref)


    def change_color(self):
        # colorchooser does not have a direct CTk equivalent.
        # This needs a custom solution, e.g., a CTkToplevel with color options or a CTkInputDialog for hex code.
        
        # Determine a safe initial color for the color chooser
        initial_color_candidate = self.config.get("bg_color")
        # Check if the candidate is a valid hex color string (e.g., "#RRGGBB")
        # A simple check: starts with # and has 7 chars, or common color names (less reliable across toolkits)
        # For robustness, one might use a regex or try-except block if more complex validation is needed.
        if isinstance(initial_color_candidate, str) and initial_color_candidate.startswith("#") and len(initial_color_candidate) == 7:
            initial_color = initial_color_candidate
        else:
            # Fallback to a default color if the stored one isn't a simple hex string
            # or if it's one of CTk's tuple/multi-string representations.
            # Try to get the current fg_color, but be careful as it might be a tuple.
            current_fg = super().cget("fg_color") # Use super().cget to bypass CTk's potential tuple return if possible, or handle it
            if isinstance(current_fg, tuple):
                initial_color = current_fg[0] # Use the light mode color
            elif isinstance(current_fg, str) and ' ' not in current_fg: # Check if it's a single color string
                 initial_color = current_fg
            else:
                initial_color = "#FFFFFF" # Default fallback

        colors = colorchooser.askcolor(title="Choose card background color", parent=self.app_ref, initialcolor=initial_color)
        if colors and colors[1]:  # colors[1] is the hex string
            self.config["bg_color"] = colors[1]
            # self.config["fg_color"] = <determine contrasting text color or ask user>
            self.app_ref.update_timer_config(self.card_id, {"bg_color": colors[1]})
            self.apply_card_color()


    def delete_timer(self):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.title_text}'?", parent=self.app_ref):
            self.app_ref.delete_timer_config_and_card(self.card_id)
            # The card itself will be destroyed by the app_ref method

# ... (rest of the file, if any)
