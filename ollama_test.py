import streamlit as st
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from urllib.parse import urlparse, urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def scrape_page(url, retries=3):
    for attempt in range(retries):
        try:
            headers = {"User-Agent": get_random_user_agent()}
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

        except requests.RequestException:
            time.sleep(2 ** attempt)
    return f"Failed to scrape {url} after {retries} retries."

def get_best_logo_url(base_url):
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        icon_candidates = []

        for link in soup.find_all("link", rel=lambda x: x and 'icon' in x.lower()):
            href = link.get('href')
            sizes = link.get('sizes')
            if href:
                full_url = urljoin(base_url, href)
                size_value = 0
                if sizes:
                    try:
                        size_value = max(int(s) for s in sizes.lower().split('x'))
                    except:
                        pass
                icon_candidates.append((size_value, full_url))

        for link in soup.find_all("link", rel=lambda x: x and 'apple-touch-icon' in x.lower()):
            href = link.get('href')
            sizes = link.get('sizes')
            if href:
                full_url = urljoin(base_url, href)
                size_value = 0
                if sizes:
                    try:
                        size_value = max(int(s) for s in sizes.lower().split('x'))
                    except:
                        pass
                icon_candidates.append((size_value, full_url))

        if icon_candidates:
            icon_candidates.sort(reverse=True)
            return icon_candidates[0][1]

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            return twitter_image["content"]

        parsed_url = urlparse(base_url)
        favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
        fav_response = requests.head(favicon_url, headers=headers, timeout=5)
        if fav_response.status_code == 200:
            return favicon_url

        domain = parsed_url.netloc
        clearbit_url = f"https://logo.clearbit.com/{domain}"
        return clearbit_url

    except requests.RequestException:
        return None

def search_and_scrape(query, max_results=5):
    results_list = []

    with DDGS() as ddgs:
        results = ddgs.text(query, region='uk-en', safesearch='Off', max_results=max_results)

        for result in results:
            url = result['href']
            title = result['title']

            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            content = scrape_page(url)
            favicon = get_best_logo_url(base_url)

            results_list.append({
                "title": title,
                "url": url,
                "favicon_url": favicon,
                "content": content
            })
            
    return results_list

@st.dialog("📰 Search Sources")
def show_sources():

    st.markdown("""
    <style>
    a:hover {
        color: #1e90ff !important;
        text-decoration: underline !important;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

    # Number and display each result nicely
    for i, res in enumerate(st.session_state.results, start=1):
        with st.container():
            cols = st.columns([0.3, 1, 11])
            with cols[0]:
                st.markdown(f"<div style='color: #888; font-weight: 600;'>{i}.</div>", unsafe_allow_html=True)
            with cols[1]:
                if res.get("favicon_url"):
                    st.image(res["favicon_url"], width=28)
            with cols[2]:
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.4rem;">
                        <a href="{res['url']}" target="_blank" style="text-decoration: none; font-weight: 600; font-size: 1.05rem; color: #fafafa;">
                            {res['title']}
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                snippet = res.get("content", "").strip().replace("\n", " ")
                short = snippet[:200] + "..." if len(snippet) > 200 else snippet
                st.markdown(
                    f"""
                    <div style="color: #ccc; font-size: 0.93rem; line-height: 1.5;">
                        {short}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.divider()

# --- Streamlit UI ---

st.title("🔎 DuckDuckGo Search & Scraper with Favicons")

query = st.text_input("Enter your search query:", value="who is Aditya hakani")
max_results = st.slider("Number of results:", 1, 10, 5)
icons_html=""
if st.button("Search"):
    with st.spinner("Searching and scraping..."):
        results = search_and_scrape(query, max_results=max_results)
        print(results)
        st.markdown("""
    <style>
    .circle-icon {
        width: 28px;
        height: 28px;
        border-radius: 55%;
        object-fit: cover;
        margin: 0 4px;
        outline: 18px solid transparent;
        vertical-align: middle;
    }
  
    .dialog-favicon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        object-fit: cover;
        border: 1px solid #ddd;
        margin-right: 12px;
        vertical-align: middle;
        transition: background-color 1s ease;
    }
    </style>
    """, unsafe_allow_html=True)

        icons_html = "".join(
        f'<img src="{res["favicon_url"]}" class="circle-icon" style="margin-right:-12px;" alt="icon"/>' 
        for res in results[:3] if res.get("favicon_url")
    )
    st.success(f"Found {len(results)} results")
    st.session_state.results = results  # store results

if "results" in st.session_state and st.session_state.results:
    st.markdown(icons_html, unsafe_allow_html=True)
    
    if st.button("Show All Sources"):
        show_sources()


  
    for res in results:
        cols = st.columns([1, 11])
        if res['favicon_url']:
            with cols[0]:
                st.image(res['favicon_url'], width=32)
        with cols[1]:
            st.markdown(f"### [{res['title']}]({res['url']})")
            description = res['content'][:300].replace('\n', ' ') + "..."
            st.write(description)

    st.markdown("---")

    # # CSS for circular favicons in button and dialog
   
    # icons_html = "".join(
    #     f'<img src="{res["favicon_url"]}" class="circle-icon" style="margin-right:-12px;" alt="icon"/>' 
    #     for res in results[:3] if res.get("favicon_url")
    # )
    # # Show centered button with favicons inline
    # st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
    # if st.button("📚 View All Sources"):
    #     show_sources_dialog = st.dialog("🧾 All Sources", width="large")(lambda: None)  # create dialog function dynamically

    #     def show_sources_dialog():
    #         for src in st.session_state.results:
    #             cols = st.columns([1, 11])
    #             if src.get("favicon_url"):
    #                 with cols[0]:
    #                     st.image(src["favicon_url"], width=24, clamp=True, use_column_width=False, output_format="PNG", classes="dialog-favicon")
    #             with cols[1]:
    #                 st.markdown(f"### [{src['title']}]({src['url']})")
    #                 st.write(src["content"][:600].replace('\n', ' ') + "...")
    #             st.markdown("---")

    #     show_sources_dialog()

    # # Render the button with icons manually using HTML + JS (disabled click, fallback to st.button above)
    # st.markdown(f"""
    # <button class="sources-button" type="button" disabled>
    # <span style="margin-right: 8px;" class="icon-wrapper">{icons_html}</span> Sources
    # </button>
    # """, unsafe_allow_html=True)
    # st.markdown('</div>', unsafe_allow_html=True)
