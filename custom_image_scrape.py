import streamlit as st

# Example data (replace with your actual scraped results)
results = [
  {
    "title": "Press releases - Tata Motors",
    "url": "https://www.tatamotors.com/newsroom/press-releases/",
    "content": "Investors Access our latest announcements, results, share price information and other resources here..."
  },
  {
    "title": "Tata Motors Announces Major Demerger: A New Era for Passenger and ...",
    "url": "https://auto.economictimes.indiatimes.com/news/passenger-vehicle/tata-motors-announces-major-demerger-a-new-era-for-passenger-and-commercial-vehicles/121407055",
    "content": "Tata Motors demerger: Everything you need to know. Here are the key highlights..."
  },
  # more items...
]

st.title("Search Results Preview")

for item in results:
    title = item.get("title", "No title")
    url = item.get("url", "#")
    content = item.get("content", "")

    # Limit content snippet length for neatness
    snippet = content if len(content) <= 300 else content[:300] + "..."

    # Render a card with HTML and Markdown
    card_html = f"""
    <div style="
        border: 1px solid #ddd; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        background-color: #fff;
    ">
        <a href="{url}" target="_blank" style="
            font-size: 20px; 
            font-weight: 600; 
            color: #1a0dab; 
            text-decoration: none;">
            {title}
        </a>
        <p style="color: #4d4d4d; margin-top: 10px;">{snippet}</p>
        <a href="{url}" target="_blank" style="
            color: white;
            background-color: #1a73e8;
            padding: 8px 12px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: 500;
            display: inline-block;
            margin-top: 10px;
        ">Read More</a>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)
