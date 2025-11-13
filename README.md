# Pokellector Card Downloader

A Python script to download high-resolution Pokémon card images from [pokellector.com](https://www.pokellector.com) for a given Pokémon name.

## Features
- Downloads all available card images for a specified Pokémon
- Handles paginated search results
- Avoids duplicate downloads
- Graceful error handling and informative output
- Modular, reusable code

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python scraper.py <pokemon_name>
```

Example:
```bash
python scraper.py charmander
```

Images will be saved in the `cards/` directory with their original filenames.

## Requirements
- Python 3.7+
- requests
- beautifulsoup4

## [GitHub Repository](https://github.com/citronlegacy/pokellector_card_downloader)
