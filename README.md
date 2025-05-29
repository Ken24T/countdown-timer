# Countdown Timer Application

A simple desktop application to manage multiple countdown timers.

## Features

- Add multiple countdown timers with custom titles and end dates.
- Timers update in real-time.
- Edit existing timers.
- Change the color of timer cards.
- Delete timers.
- Configurations are saved locally in `data/timers_config.json`.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd countdown-timer
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Once the setup is complete, run the application using:

```bash
python run.py
```

## Project Structure

- `run.py`: Main entry point for the application.
- `src/`: Contains the source code for the application.
    - `main_app.py`: Defines the main application window and logic.
    - `components/`: Contains UI components like `timer_card.py`.
- `data/`: Stores application data, like `timers_config.json`.
- `requirements.txt`: Lists project dependencies.
