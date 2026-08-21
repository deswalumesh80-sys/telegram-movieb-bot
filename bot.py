import cloudscraper
from bs4 import BeautifulSoup
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

scraper = cloudscraper.create_scraper()

def search_vegamovies(query):
    search_url = f"https://new2.vegamovies.futbol/?s={query.replace(' ', '+')}"
    try:
        response = scraper.get(search_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        # VegaMovies articles parsing
        articles = soup.find_all("article", class_="post-item")
        
        for article in articles[:6]:  # Top 6 results
            title_tag = article.find("h3", class_="entry-title") or article.find("h2", class_="entry-title")
            link_tag = article.find("a")
            
            if title_tag and link_tag:
                title = title_tag.get_text().strip()
                link = link_tag.get("href")
                results.append((title, link))
        return results
    except Exception:
        return []
        
