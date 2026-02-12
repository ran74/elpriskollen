# Elpriskollen
Elpriskollen Pro (Electricity Price Monitor) Elpriskollen Pro is a real-time desktop application built with Python and Tkinter. It provides Swedish energy consumers with up-to-the-minute data on electricity prices, specifically adapted for the new 15-minute (quarterly) pricing model (MTU).

Features
Real-time Quarterly Pricing: Displays the current spot price for the specific 15-minute window you are in.

Total Cost Calculation: Includes Swedish energy tax, VAT, and certificates to show your actual cost per kWh.

Smart Savings: Automatically calculates the cheapest continuous 60-minute window for high-energy tasks like laundry or EV charging.

Weather Integration: Fetches local temperature and wind speeds to help correlate weather patterns with energy fluctuations.

Automatic Configuration: On the first run, the app prompts for your Electricity Area (SE1-SE4) and city, saving these settings for future launches.

Dynamic UI: The background color changes based on whether the current price is above or below the daily average.

Installation
Prerequisites
Python 3.x

requests library

Bash
pip install requests
Running the Script
Simply run the script via your terminal:

Bash
python elpris_gui.py
Building an Executable (.exe)
To create a standalone Windows application:

Bash
pip install pyinstaller
python -m PyInstaller --noconsole --onefile --name "Elpriskollen" elpris_gui.py
How It Works
The application fetches data from the Elpriset Just Nu API and weather data from the Open-Meteo API. It uses Python's threading to ensure the UI remains responsive while data is being fetched in the background every 5 minutes.
