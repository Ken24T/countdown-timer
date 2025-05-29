Generate a modular and extensible Python GUI app for countdown timers:

1. Create a JSON file `timers.json` containing a list of objects, each with:
   - `"title"`: the header text
   - `"end_date"`: an ISO date string `"YYYY-MM-DD"`
2. In `src/gui.py`, build a modern, clean and attractive timer 'card' that:
   - Reads `timers.json`
   - For each timer, creates a Frame styled like a card:
     • Header Label (bold, slightly larger font) showing the `"title"`
     • Body Label (extra-large font) displaying the number of days until `"end_date"`
   - The individual cards should be moveable and their destination position(s) should be remembered.
   - Updates the displayed days remaining once a day on startup or at midnight if the card is still active.
   - Each card is configurable. The card's size, position, header and body background colours can be changed. The time end date can be added and then changed.
3. Include:
   - A sample `timers.json` with at least two example entries
   - A build script that generates a onefolder executable.