import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def scrape_twitter(username, total_scrolls=100):
    """
    Scrape tweets from a Twitter user's profile
    
    Args:
        username (str): Twitter username without '@'
        total_scrolls (int): Number of times to scroll the page
    """
    data = []
    link = f"https://twitter.com/{username}"
    
    with sync_playwright() as p:
        # Launch browser with specific arguments for restricted environments
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        try:
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto(link, wait_until="networkidle", timeout=60000)
            
            # Scroll the page
            for i in range(total_scrolls):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(2)  # Reduced sleep time for efficiency
                
                # Extract content after each scroll
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                posts = soup.find_all('div', {'data-testid': 'cellInnerDiv'})
                
                for post in posts:
                    if not post.find('div', {'role': 'link'}):  # Skip retweets
                        try:
                            tweet_elem = post.find('div', {'data-testid': 'tweetText'})
                            if tweet_elem:
                                tweet = tweet_elem.get_text(strip=True)
                                metrics = {
                                    'comments': post.find('div', {'data-testid': 'reply'}).get_text(strip=True),
                                    'retweets': post.find('div', {'data-testid': 'retweet'}).get_text(strip=True),
                                    'likes': post.find('div', {'data-testid': 'like'}).get_text(strip=True)
                                }
                                
                                data.append({
                                    'Tweet': tweet,
                                    'Comments': metrics['comments'],
                                    'Retweets': metrics['retweets'],
                                    'Likes': metrics['likes'],
                                    'Scraped_At': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                        except AttributeError:
                            continue
                
                print(f"Completed scroll {i+1}/{total_scrolls}")
                
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        finally:
            browser.close()
    
    # Create DataFrame and remove duplicates
    df = pd.DataFrame(data)
    df.drop_duplicates(subset=['Tweet'], inplace=True)
    
    # Save to Excel with timestamp
    filename = f"{username}_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")
    
    return df

if __name__ == "__main__":
    username = "elonmusk"
    df = scrape_twitter(username, total_scrolls=100)