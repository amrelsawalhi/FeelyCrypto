import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser

def clean_html(raw_html):
    if not isinstance(raw_html, str):
        return ""
    if "<" not in raw_html:
        return raw_html.strip()  # Not HTML, just return cleaned string

    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for a in soup.find_all("a"):
            a.replace_with(a.get_text())
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"Error cleaning HTML: {e}")
        return raw_html.strip()

def fetch_coindesk_news_rss(url="https://feeds.feedburner.com/CoinDesk"):
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries:
        published = getattr(entry, 'published', None)
        published_at = parser.parse(published) if published else None
        title = getattr(entry, 'title', "").strip()

        # Extract raw content safely
        if hasattr(entry, 'content'):
            raw_content = entry.content[0].value
        elif hasattr(entry, 'summary'):
            raw_content = entry.summary
        else:
            raw_content = ""

        # Sanity check to avoid warnings from BeautifulSoup
        if isinstance(raw_content, str) and "<" in raw_content:
            cleaned_content = clean_html(raw_content)
        else:
            cleaned_content = raw_content

        if not published_at or not title:
            continue

        articles.append({
            "published_at": published_at,
            "title": clean_html(title),
            "content": cleaned_content,
            "source": "CoinDesk",
            "sentiment": None,
            "confidence": None
        })

    return pd.DataFrame(articles)


