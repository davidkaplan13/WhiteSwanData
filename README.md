# WhiteSwanData Inteview

### Packages
All packages are handled by poetry (Package manager). To run locally - run poetry install (--no-root).
To execute script - poetry run python main.py

### Files
- `main.py` is the main file that scrapes today and tommorw races as well as the bot automation to scrape market prices of participating horses from a randomly selected race.
- `df_races_data.csv` contains the scraped tracks and races for today and tomorrow (AU/NZ).
- `df_performed_bets.csv` contains the scraped and calculated market prices for each participant in a randonmly selected race.

The market price was calculated by doing 100 / Fixed(W). Future races that have no Fixed(W) have been assigned as null.


