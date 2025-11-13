
# Python Pokemon Card Image Scraper - Implementation Guide
*Version: 1.0 – Date: 2025-11-13*

## Overview
Build a Python script that automates downloading Pokemon card images from pokellector.com. The script should accept a Pokemon name as input, search for all cards of that Pokemon, and download high-resolution card images.


## Functional Requirements
- Accept a Pokemon name as input (via CLI argument).
- Search pokellector.com for all cards matching the Pokemon name.
- Handle paginated search results.
- Extract card detail URLs from search results.
- Extract high-resolution image URLs from card detail pages.
- Download images to a specified output directory.
- Avoid duplicate downloads.
- Handle network errors, missing images, and invalid input gracefully.
- Provide clear CLI usage instructions.
- Each major step should be implemented as a separate, reusable function.

## Non-Functional Requirements
- Use only open-source Python packages (`requests`, `beautifulsoup4`).
- Respect server rate limits (add delays between requests).
- Use a user-agent header for all HTTP requests.
- Code should be modular and easy to maintain.
- The script should run on Linux and other major OSes.
- All dependencies must be listed in `requirements.txt` and kept up-to-date.

## Constraints & Assumptions
- The script will only target pokellector.com.
- The HTML structure of pokellector.com may change; selectors may need updates.
- The workspace may not be empty; if a requirements document exists, it should be moved to a `.copilot/` subfolder for organization.
- The presence of other files in the workspace is not an error.

## Required Files
- `scraper.py`: Main script.
- `requirements.txt`: List of all dependencies (must be kept up-to-date).
- `README.md`: Explains the application, installation, and usage. Must include a placeholder for the GitHub repository link (e.g., `[GitHub Repository](<repo-link-here>)`).

If the workspace is not empty and already contains a requirements document, move it to a `.copilot/` subfolder for organization.

## Installation
```bash
pip install requests beautifulsoup4
```

## Website Structure Analysis

### 1. Search Page Structure
- **URL Pattern**: `https://www.pokellector.com/search?criteria={pokemon_name}&p={page_number}`
- **Example**: `https://www.pokellector.com/search?criteria=charmander&p=1`
- **Pagination**: Results are paginated, typically ~30 cards per page
- **Card Links**: Found in `<a>` tags with href pattern: `/{Expansion-Name}/Charmander-Card-{CardNumber}`

### 2. Card Detail Page Structure
- **URL Pattern**: `https://www.pokellector.com/{Expansion-Name}/{Pokemon}-Card-{CardNumber}`
- **Examples**:
  - `https://www.pokellector.com/Hidden-Fates-Expansion/Charmander-Card-SV6`
  - `https://www.pokellector.com/Obsidian-Flames-Expansion/Charmander-Card-26`
  - `https://www.pokellector.com/EX-Crystal-Guardians-Expansion/Charmander-Card-48`

### 3. Image URL Pattern
- **Host**: `den-cards.pokellector.com`
- **Full Pattern**: `https://den-cards.pokellector.com/{set_id}/{Pokemon}.{SetCode}.{CardNumber}.{card_id}.png`
- **Examples**:
  - `https://den-cards.pokellector.com/279/Charmander.HIF.SV6.29859.png`
  - `https://den-cards.pokellector.com/373/Charmander.OBF.26.48846.png`
  - `https://den-cards.pokellector.com/65/Charmander.CG.48.png`
- **Note**: The image URL must be extracted from the HTML `<img>` tag's `src` attribute on each card detail page

## HTML Parsing Guide

### Search Results Page
The search results contain card links that need to be extracted:

```html
<a href="/Hidden-Fates-Expansion/Charmander-Card-SV6">
    <img src="...thumbnail..." alt="Charmander...">
</a>
```

**CSS Selector Strategy**:
- Look for `<a>` tags where `href` contains the pattern `/{expansion}/Charmander-Card-{number}`
- Or search for links that match regex pattern: `r'\/[^\/]+-Expansion\/\w+-Card-[^"#]+`
- Remove any URL fragments (e.g., `#variants`)

### Card Detail Page
The main card image is typically in a prominent `<img>` tag:

```html
<img src="https://den-cards.pokellector.com/279/Charmander.HIF.SV6.29859.png" 
     alt="Charmander - Hidden Fates #6">
```

**CSS Selector Strategy**:
- Find `<img>` tags where `src` starts with `https://den-cards.pokellector.com/`
- The image is usually the largest image on the page (not thumbnails)
- Look for images with alt text containing the Pokemon name and card number

## Implementation Steps

### Step 1: Create Search Function
```python
def search_pokemon_cards(pokemon_name, page=1):
    """
    Search for Pokemon cards and return list of card detail URLs
    
    Args:
        pokemon_name: Name of Pokemon (e.g., 'charmander')
        page: Search results page number (default: 1)
    
    Returns:
        List of card detail URLs
    """
    base_url = "https://www.pokellector.com/search"
    params = {"criteria": pokemon_name.lower(), "p": page}
    
    # Make HTTP request with proper headers
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    response = requests.get(base_url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract card links using regex pattern
    # Pattern: /{expansion-name}/{pokemon}-Card-{number}
    card_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if re.match(r'^/[^/]+-Expansion/[^/]+-Card-[^#]+', href):
            # Remove fragments and clean URL
            clean_href = href.split('#')[0]
            full_url = f"https://www.pokellector.com{clean_href}"
            if full_url not in card_links:
                card_links.append(full_url)
    
    return card_links
```

### Step 2: Extract Image URL from Card Page
```python
def get_card_image_url(card_url):
    """
    Extract high-resolution image URL from card detail page
    
    Args:
        card_url: Full URL to card detail page
    
    Returns:
        Image URL string or None if not found
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    response = requests.get(card_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find image from den-cards.pokellector.com domain
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'den-cards.pokellector.com' in src and src.split('.')[-1].lower() in ('png', 'jpg', 'jpeg', 'webp'):
            return src
    
    return None
```

### Step 3: Download Image
```python
def download_image(image_url, output_path):
    """
    Download image from URL and save to file
    
    Args:
        image_url: URL of image to download
        output_path: Local file path to save image
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    response = requests.get(image_url, headers=headers, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
```

### Step 4: Handle Pagination
```python
def get_total_pages(pokemon_name):
    """
    Determine total number of search result pages
    
    Args:
        pokemon_name: Name of Pokemon
    
    Returns:
        Total number of pages (int)
    """
    base_url = "https://www.pokellector.com/search"
    params = {"criteria": pokemon_name.lower(), "p": 1}
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    
    response = requests.get(base_url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for pagination links (e.g., <a href="?p=2">2</a>)
    # Find the highest page number
    max_page = 1
    for link in soup.find_all('a', href=True):
        if '?p=' in link['href'] or '&p=' in link['href']:
            try:
                match = re.search(r'[?&]p=(\d+)', link['href'])
                if match:
                    page_num = int(match.group(1))
                    max_page = max(max_page, page_num)
            except:
                pass
    
    return max_page
```

### Step 5: Main Script
```python
import requests
from bs4 import BeautifulSoup
import re
import os
import time
from pathlib import Path

def download_pokemon_cards(pokemon_name, output_dir='./cards'):
    """
    Main function to download all cards for a given Pokemon
    
    Args:
        pokemon_name: Name of Pokemon to search for
        output_dir: Directory to save downloaded images
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Searching for {pokemon_name} cards...")
    
    # Get total pages
    total_pages = get_total_pages(pokemon_name)
    print(f"Found {total_pages} page(s) of results")
    
    all_card_urls = []
    
    # Collect all card URLs from all pages
    for page in range(1, total_pages + 1):
        print(f"Scraping page {page}/{total_pages}...")
        card_urls = search_pokemon_cards(pokemon_name, page)
        all_card_urls.extend(card_urls)
        time.sleep(1)  # Be polite to the server
    
    print(f"Found {len(all_card_urls)} unique cards")
    
    # Download each card image
    for idx, card_url in enumerate(all_card_urls, 1):
        print(f"Processing card {idx}/{len(all_card_urls)}: {card_url}")
        
        try:
            # Extract image URL
            image_url = get_card_image_url(card_url)
            
            if image_url:
                # Generate filename from image URL
                filename = image_url.split('/')[-1]
                output_path = os.path.join(output_dir, filename)
                
                # Download image
                download_image(image_url, output_path)
                print(f"  ✓ Downloaded: {filename}")
            else:
                print(f"  ✗ No image found")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        time.sleep(0.5)  # Be polite to the server
    
    print(f"\nComplete! Downloaded {len(os.listdir(output_dir))} images to {output_dir}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <pokemon_name>")
        sys.exit(1)
    
    pokemon_name = sys.argv[1]
    download_pokemon_cards(pokemon_name)
```


## Usage Examples
```bash
# Download all Charmander cards
python scraper.py charmander

# Download all Pikachu cards
python scraper.py pikachu
```


## Error Handling & Edge Cases

- **Rate Limiting**: Add `time.sleep()` between requests (0.5–1s).
- **Network Errors**: Use try-except blocks for all requests; set `timeout=10`.
- **Missing Images**: If no image is found, skip and log a warning.
- **Duplicate URLs**: Avoid duplicate downloads by checking before saving.
- **Invalid Pokemon Names**: If no results, print a warning and exit.
- **Pagination**: If pagination is not found, default to 1 page.
## Acceptance Criteria

- The script downloads all available card images for a given Pokemon name.
- All images are saved in the specified output directory with original filenames.
- The script handles errors gracefully and provides informative output.
- A `README.md` is included, explaining the application, installation, and usage, with a placeholder for the GitHub repository link (e.g., `[GitHub Repository](<repo-link-here>)`).
- A `requirements.txt` is included and kept up-to-date with all dependencies.
- If the workspace is not empty and contains a requirements document, it is moved to a `.copilot/` subfolder.

cards/

## Output Structure

Images will be saved with their original filenames:
```
cards/
├── Charmander.HIF.SV6.29859.png
├── Charmander.OBF.26.48846.png
├── Charmander.CG.48.png
└── ...
```


## Additional Enhancements 

1. **Progress Bar**: Use `tqdm` library for better progress visualization
4. **Metadata Export**: Save card information (name, set, number) to JSON/CSV


## Testing Notes

- Test with Pokemon names that have different numbers of cards
- Verify pagination works correctly for Pokemon with >30 cards
- Check handling of special characters in Pokemon names (e.g., "Farfetch'd")
- Test with Pokemon that have few cards (1-5) vs many cards (50+)
## Glossary (Optional)
- **Pagination**: Splitting search results across multiple pages.
- **Card Detail Page**: The page for a specific card, containing the high-res image.
- **requirements.txt**: File listing all Python dependencies.
- **README.md**: Documentation file explaining the project.

## Known Patterns from Exploration

From the browser exploration, we found:
- **Charmander** has ~30+ cards across 4 pages of results
- Card URLs can have variants (e.g., `#variants` fragment)
- Image URLs include a numeric set ID prefix (e.g., `/279/`, `/373/`, `/65/`)
- Set codes are abbreviated (HIF = Hidden Fates, OBF = Obsidian Flames, CG = Crystal Guardians)
- Some cards have numeric card IDs at the end of the filename (e.g., `.29859.png`)


## Rate Limiting
Include time.sleep() between requests even if responses are fast.

## Pokemon with no results
If get_total_pages() returns 0 or search results are empty, then respond with a warning that no results were found

## Function naming clarity
Each step should be implemented as a separate, reusable function (do not merge into one function).

## Improvement for pagination loop
If pagination numbers are not found, default to 1 page.

## Extra
Use requests.get() with timeout=10 to avoid hanging requests.