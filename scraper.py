import requests
from bs4 import BeautifulSoup
import re
import os
import time
from pathlib import Path
import sys

def search_pokemon_cards(pokemon_name, page=1):
    """
    Search for Pokemon cards and return list of card detail URLs
    """
    base_url = "https://www.pokellector.com/search"
    params = {"criteria": pokemon_name.lower(), "p": page}
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"  ✗ Network error during search: {e}")
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    card_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if re.match(r'^/[^/]+-Expansion/[^/]+-Card-[^#]+', href):
            clean_href = href.split('#')[0]
            full_url = f"https://www.pokellector.com{clean_href}"
            if full_url not in card_links:
                card_links.append(full_url)
    return card_links

def get_card_image_url(card_url, pokemon_name=None):
    """
    Extract high-resolution image URL from card detail page
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(card_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"  ✗ Network error fetching card page: {e}")
        return None
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Try to find the main card image in the card info section (as in pokellector_source.txt)
    # Look for a div with class 'card' and an <img> inside
    card_div = soup.find('div', class_='card')
    if card_div:
        img = card_div.find('img')
        if img:
            src = img.get('src', '')
            if src and 'den-cards.pokellector.com' in src and src.split('.')[-1].lower() in ('png', 'jpg', 'jpeg', 'webp'):
                return src

    # 2. Fallback: look for og:image or itemprop=image meta tags
    meta_og = soup.find('meta', property='og:image')
    if meta_og and meta_og.get('content'):
        src = meta_og['content']
        if 'den-cards.pokellector.com' in src:
            return src
    meta_item = soup.find('meta', itemprop='image')
    if meta_item and meta_item.get('content'):
        src = meta_item['content']
        if 'den-cards.pokellector.com' in src:
            return src

    # 3. Fallback: scan all <img> tags for a den-cards.pokellector.com image
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'den-cards.pokellector.com' in src and src.split('.')[-1].lower() in ('png', 'jpg', 'jpeg', 'webp'):
            return src

    return None

def download_image(image_url, output_path):
    """
    Download image from URL and save to file
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(image_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"    ✗ Error downloading image: {e}")
        return False
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return True

def get_total_pages(pokemon_name):
    """
    Determine total number of search result pages
    """
    base_url = "https://www.pokellector.com/search"
    params = {"criteria": pokemon_name.lower(), "p": 1}
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"  ✗ Network error during pagination check: {e}")
        return 0
    soup = BeautifulSoup(response.text, 'html.parser')
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

def download_pokemon_cards(pokemon_name, output_dir='./cards'):
    """
    Main function to download all cards for a given Pokemon
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"Searching for {pokemon_name} cards...")
    total_pages = get_total_pages(pokemon_name)
    if total_pages == 0:
        print(f"No results found for '{pokemon_name}'. Exiting.")
        return
    print(f"Found {total_pages} page(s) of results")
    all_card_urls = set()
    for page in range(1, total_pages + 1):
        print(f"Scraping page {page}/{total_pages}...")
        card_urls = search_pokemon_cards(pokemon_name, page)
        all_card_urls.update(card_urls)
        time.sleep(1)
    print(f"Found {len(all_card_urls)} unique cards")
    downloaded = 0
    for idx, card_url in enumerate(sorted(all_card_urls), 1):
        print(f"Processing card {idx}/{len(all_card_urls)}: {card_url}")
        try:
            image_url = get_card_image_url(card_url, pokemon_name)
            if image_url:
                filename = image_url.split('/')[-1]
                output_path = os.path.join(output_dir, filename)
                if os.path.exists(output_path):
                    print(f"    ✓ Already downloaded: {filename}")
                else:
                    if download_image(image_url, output_path):
                        print(f"    ✓ Downloaded: {filename}")
                        downloaded += 1
                    else:
                        print(f"    ✗ Failed to download: {filename}")
            else:
                print(f"    ✗ No image found")
        except Exception as e:
            print(f"    ✗ Error: {e}")
        time.sleep(0.5)
        print(f"\nComplete! Downloaded {downloaded} new images to {output_dir}")

    def is_valid_input(pokemon_name):
        # Accept only non-empty, alphabetic (with possible dashes, spaces, apostrophes, dots, numbers)
        return bool(re.match(r"^[A-Za-z0-9\- '\.]+$", pokemon_name))

    def main():
        """Main function with input loop"""
        # If a command-line argument is provided, process it first
        if len(sys.argv) > 1:
            pokemon_name = sys.argv[1].strip()
            if not is_valid_input(pokemon_name):
                print("Invalid input. Please try again.")
            else:
                download_pokemon_cards(pokemon_name)

        while True:
            user_input = input("\nEnter Pokémon name (or press Enter to quit): ").strip()
            if not user_input:
                print("Exiting...")
                break
            if not is_valid_input(user_input):
                print("Invalid input. Please try again.")
                continue
            download_pokemon_cards(user_input)

    if __name__ == "__main__":
        main()
if __name__ == "__main__":
    if len(sys.argv) < 2:
        pokemon_name = input("Enter the name of the Pokémon to download cards for: ").strip()
        if not pokemon_name:
            print("No Pokémon name provided. Exiting.")
            sys.exit(1)
    else:
        pokemon_name = sys.argv[1]
    download_pokemon_cards(pokemon_name)
