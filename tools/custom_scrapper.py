from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import json
from urllib.parse import urlparse, urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
]


def get_url_logo(base_url):
    try:
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc
        clearbit_url = f"https://logo.clearbit.com/{domain}"
        return clearbit_url
    except Exception:
        return None
    
def search_and_scrape(query, max_results=5, retries=3):
    def get_random_user_agent():
        return random.choice(USER_AGENTS)

    def scrape_page(url):
        for attempt in range(retries):
            try:
                headers = {"User-Agent": get_random_user_agent()}
                logging.info(f"Fetching {url} (Attempt {attempt + 1})")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                article = soup.find('article')
                if article:
                    text = article.get_text(separator="\n", strip=True)
                else:
                    elements = soup.find_all(['h1', 'h2', 'h3', 'p'])
                    text = "\n".join(el.get_text(strip=True) for el in elements)

                return text[:2000]

            except requests.RequestException as e:
                logging.warning(f"Request failed: {e}")
                time.sleep(2 ** attempt)
        return f"Failed to scrape {url} after {retries} retries."

    results_list = []

    with DDGS() as ddgs:
        results = ddgs.text(query, region='in-en', safesearch='Off', max_results=max_results)

        for i, result in enumerate(results, 1):
            url = result['href']
            title = result['title']
            content = scrape_page(url)
            favicon = get_url_logo(url)
            results_list.append({
                "title": title,
                "url": url,
                "content": content,
                "favicon_url": favicon
            })

            # Optional polite delay
            # time.sleep(random.uniform(2, 5))
    
    return json.dumps(results_list, indent=2, ensure_ascii=False)


# if __name__ == "__main__":
#     json_result = search_and_scrape("what is multiple scelerosis")
#     print(json_result)
