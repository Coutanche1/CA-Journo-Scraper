#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from playwright.sync_api import sync_playwright, TimeoutError
import os
from datetime import datetime
import sheets_client

# --- HELPER FUNCTION ---
def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

# --- CONFIGURATION ---
MASTER_LIST_FILE = 'master_list_uk.csv'
PENDING_FILE = 'pending_verification_uk.csv'
BLACKLIST_FILE = 'blacklist_emails.txt' # Can be shared with the other script
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

# --- UK OUTLET SOURCES ---
OUTLET_SOURCES = [
    # National
    {
        "outlet": "BBC News", "url": "https://www.bbc.co.uk/news", "location": "UK",
        "rss_url": "http://feeds.bbci.co.uk/news/uk/rss.xml"
    },
    {
        "outlet": "The Guardian", "url": "https://www.theguardian.com/uk", "location": "UK",
        "rss_url": "https://www.theguardian.com/uk/rss"
    },
    {
        "outlet": "The Telegraph", "url": "https://www.telegraph.co.uk/", "location": "UK",
        "rss_url": "https://www.telegraph.co.uk/rss.xml"
    },
    {
        "outlet": "Sky News", "url": "https://news.sky.com/uk", "location": "UK",
        "rss_url": "http://feeds.skynews.com/feeds/rss/uk.xml"
    },
    {
        "outlet": "Financial Times", "url": "https://www.ft.com/", "location": "UK",
        "rss_url": "https://www.ft.com/rss/home-uk"
    },
    {
        "outlet": "The Independent", "url": "https://www.independent.co.uk/", "location": "UK",
        "rss_url": "https://www.independent.co.uk/rss"
    },
    {
        "outlet": "Daily Mail", "url": "https://www.dailymail.co.uk/home/index.html", "location": "UK",
        "rss_url": "https://www.dailymail.co.uk/news/index.rss"
    },
    {
        "outlet": "The Sun", "url": "https://www.thesun.co.uk/", "location": "UK",
        "rss_url": "https://www.thesun.co.uk/feed/"
    },
    {
        "outlet": "The Mirror", "url": "https://www.mirror.co.uk/", "location": "UK",
        "rss_url": "https://www.mirror.co.uk/?service=rss"
    },
    {
        "outlet": "Daily Express", "url": "https://www.express.co.uk/", "location": "UK",
        "rss_url": "https://feeds.feedburner.com/daily-express-news"
    },
    {
        "outlet": "Metro.co.uk", "url": "https://metro.co.uk/", "location": "UK",
        "rss_url": "https://metro.co.uk/feed/"
    },
    {
        "outlet": "Evening Standard", "url": "https://www.standard.co.uk/", "location": "London",
        "rss_url": "https://www.standard.co.uk/rss"
    },
    {
        "outlet": "HuffPost UK", "url": "https://www.huffingtonpost.co.uk/", "location": "UK",
        "rss_url": "https://www.huffingtonpost.co.uk/feeds/index.xml"
    },
    {
        "outlet": "The New Statesman", "url": "https://www.newstatesman.com/", "location": "UK",
        "rss_url": "https://www.newstatesman.com/feed"
    },
    {
        "outlet": "The Week UK", "url": "https://www.theweek.com/uk", "location": "UK",
        "rss_url": "https://www.theweek.com/uk/rss.xml"
    },
    {
        "outlet": "Politics.co.uk", "url": "https://www.politics.co.uk/", "location": "UK",
        "rss_url": "https://www.politics.co.uk/feed/"
    },
    {
        "outlet": "PinkNews", "url": "https://www.thepinknews.com/", "location": "UK",
        "rss_url": "https://www.thepinknews.com/feed/"
    },
    {
        "outlet": "The Daily Mash", "url": "https://www.thedailymash.co.uk/", "location": "UK",
        "rss_url": "https://www.thedailymash.co.uk/feed"
    },
    {
        "outlet": "Positive News", "url": "https://www.positive.news/", "location": "UK",
        "rss_url": "https://www.positive.news/feed/"
    },
    {
        "outlet": "The Poke", "url": "https://www.thepoke.co.uk/", "location": "UK",
        "rss_url": "https://www.thepoke.co.uk/feed/"
    },
    {
        "outlet": "Guido Fawkes", "url": "https://order-order.com/", "location": "UK",
        "rss_url": "https://feeds.feedburner.com/guidofawkes"
    },
    # Regional News
    {
        "outlet": "Manchester Evening News", "url": "https://www.manchestereveningnews.co.uk/", "location": "Manchester",
        "rss_url": "https://www.manchestereveningnews.co.uk/rss.xml"
    },
    {
        "outlet": "Liverpool Echo", "url": "https://www.liverpoolecho.co.uk/", "location": "Liverpool",
        "rss_url": "https://www.liverpoolecho.co.uk/rss.xml"
    },
    {
        "outlet": "Birmingham Mail", "url": "https://www.birminghammail.co.uk/", "location": "Birmingham",
        "rss_url": "https://www.birminghammail.co.uk/rss.xml"
    },
    {
        "outlet": "WalesOnline", "url": "https://www.walesonline.co.uk/", "location": "Wales",
        "rss_url": "https://www.walesonline.co.uk/rss.xml"
    },
    {
        "outlet": "The Scotsman", "url": "https://www.scotsman.com/", "location": "Scotland",
        "rss_url": "https://www.scotsman.com/rss"
    },
    {
        "outlet": "The Herald (Scotland)", "url": "https://www.heraldscotland.com/", "location": "Scotland",
        "rss_url": "https://www.heraldscotland.com/news/rss"
    },
    {
        "outlet": "Belfast Live", "url": "https://www.belfastlive.co.uk/", "location": "Northern Ireland",
        "rss_url": "https://www.belfastlive.co.uk/rss.xml"
    },
    {
        "outlet": "Belfast Telegraph", "url": "https://www.belfasttelegraph.co.uk/", "location": "Northern Ireland",
        "rss_url": "https://www.belfasttelegraph.co.uk/rss/"
    },
    {
        "outlet": "The Yorkshire Post", "url": "https://www.yorkshirepost.co.uk/", "location": "Yorkshire",
        "rss_url": "https://www.yorkshirepost.co.uk/rss"
    },
    {
        "outlet": "The Argus (Brighton)", "url": "https://www.theargus.co.uk/", "location": "Brighton",
        "rss_url": "https://www.theargus.co.uk/news/rss/"
    },
    {
        "outlet": "The York Press", "url": "https://www.yorkpress.co.uk/", "location": "York",
        "rss_url": "https://www.yorkpress.co.uk/news/rss/"
    },
    {
        "outlet": "The Northern Echo", "url": "https://www.thenorthernecho.co.uk/", "location": "North England",
        "rss_url": "https://www.thenorthernecho.co.uk/news/rss/"
    },
    {
        "outlet": "The Bolton News", "url": "https://www.theboltonnews.co.uk/", "location": "Bolton",
        "rss_url": "https://www.theboltonnews.co.uk/news/rss/"
    },
    {
        "outlet": "The News (Portsmouth)", "url": "https://www.portsmouth.co.uk/", "location": "Portsmouth",
        "rss_url": "https://www.portsmouth.co.uk/rss"
    },
    {
        "outlet": "Cambridgeshire Live", "url": "https://www.cambridge-news.co.uk/", "location": "Cambridge",
        "rss_url": "https://www.cambridge-news.co.uk/rss.xml"
    },
    {
        "outlet": "Grimsby Telegraph", "url": "https://www.grimsbytelegraph.co.uk/", "location": "Grimsby",
        "rss_url": "https://www.grimsbytelegraph.co.uk/news/rss.xml"
    },
    {
        "outlet": "Glasgow Times", "url": "https://www.glasgowtimes.co.uk/", "location": "Glasgow",
        "rss_url": "https://www.glasgowtimes.co.uk/news/rss/"
    },
    {
        "outlet": "Deadline News (Scotland)", "url": "https://www.deadlinenews.co.uk/", "location": "Scotland",
        "rss_url": "https://www.deadlinenews.co.uk/feed/"
    },
    # Blogs & Niche
    {
        "outlet": "A Lady in London", "url": "https://www.aladyinlondon.com/", "location": "London",
        "rss_url": "https://www.aladyinlondon.com/feed"
    },
    {
        "outlet": "The Londoner", "url": "https://www.thelondoner.me/", "location": "London",
        "rss_url": "https://www.thelondoner.me/feed"
    },
    {
        "outlet": "UK Human Rights Blog", "url": "https://ukhumanrightsblog.com/", "location": "UK",
        "rss_url": "https://ukhumanrightsblog.com/feed/"
    },
    {
        "outlet": "UK Constitutional Law Association", "url": "https://ukconstitutionallaw.org/", "location": "UK",
        "rss_url": "https://ukconstitutionallaw.org/blog/feed/"
    },
    {
        "outlet": "In the frow", "url": "https://www.inthefrow.com/", "location": "UK",
        "rss_url": "https://inthefrow.com/feed"
    },
    {
        "outlet": "A Luxury Travel Blog", "url": "https://www.aluxurytravelblog.com/", "location": "UK",
        "rss_url": "https://www.aluxurytravelblog.com/feed/"
    },
    {
        "outlet": "Love My Dress", "url": "https://www.lovemydress.net/", "location": "UK",
        "rss_url": "https://www.lovemydress.net/feed/"
    },
    {
        "outlet": "Age UK", "url": "https://www.ageuk.org.uk/", "location": "UK",
        "rss_url": "https://www.ageuk.org.uk/discover/rss/"
    },
    {
        "outlet": "We Are Social UK", "url": "https://wearesocial.com/uk/", "location": "UK",
        "rss_url": "https://wearesocial.com/uk/feed/"
    },
    {
        "outlet": "London Review of Books Blog", "url": "https://www.lrb.co.uk/", "location": "UK",
        "rss_url": "https://www.lrb.co.uk/blog/feed"
    },
    {
        "outlet": "British Beauty Blogger", "url": "https://britishbeautyblogger.com/", "location": "UK",
        "rss_url": "https://britishbeautyblogger.com/feed/"
    },
    {
        "outlet": "Rock n Roll Bride", "url": "https://www.rocknrollbride.com/", "location": "UK",
        "rss_url": "https://feeds2.feedburner.com/rocknrollbride"
    },
    {
        "outlet": "Disneyrollergirl", "url": "https://disneyrollergirl.net/", "location": "UK",
        "rss_url": "https://disneyrollergirl.net/feed/"
    },
    {
        "outlet": "SilverSpoon London", "url": "https://silverspoonlondon.co.uk/", "location": "London",
        "rss_url": "https://silverspoonlondon.co.uk/feed/"
    },
    {
        "outlet": "UK Fundraising Blog", "url": "https://fundraising.co.uk/", "location": "UK",
        "rss_url": "https://fundraising.co.uk/category/blogs/feed/"
    },
    {
        "outlet": "The Anna Edit", "url": "https://www.theannaedit.com/", "location": "UK",
        "rss_url": "https://www.theannaedit.com/feed/"
    },
    {
        "outlet": "Healthy Magazine", "url": "https://www.healthy-magazine.co.uk/", "location": "UK",
        "rss_url": "https://www.healthy-magazine.co.uk/feed/"
    },
    {
        "outlet": "Everything Zany", "url": "https://everythingzany.com/", "location": "UK",
        "rss_url": "https://everythingzany.com/feed/"
    },
    {
        "outlet": "Lily Pebbles", "url": "https://lilypebbles.co.uk/", "location": "UK",
        "rss_url": "https://lilypebbles.co.uk/feed/"
    }
]


def get_existing_journalists():
    """Reads master and pending files for de-duplication."""
    journalists = set()
    for filename in [MASTER_LIST_FILE, PENDING_FILE]:
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and len(row) > 1:
                        journalists.add(f"{row[0]} {row[1]}".lower())
        except FileNotFoundError:
            pass
    return journalists

def get_blacklist_emails():
    """Reads the blacklist file and returns a set of invalid emails."""
    blacklist = set()
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                email = line.strip().lower()
                if email:
                    blacklist.add(email)
    except FileNotFoundError:
        pass
    return blacklist

def find_email_with_playwright(article_url, author_name):
    """Uses an OPTIMIZED headless browser to find a real email."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    found_email = None

    def block_unnecessary_resources(route):
        blocked_resource_types = ['image', 'stylesheet', 'font', 'media', 'csp_report']
        if route.request.resource_type in blocked_resource_types:
            route.abort()
        else:
            route.continue_()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.route('**/*', block_unnecessary_resources)

            log(f"  -> Visiting article (Optimized): {article_url}")
            page.goto(article_url, timeout=60000, wait_until='domcontentloaded') 

            author_link = page.get_by_text(author_name, exact=False).first
            if author_link and author_link.get_attribute('href'):
                author_page_url = author_link.get_attribute('href')

                if 'mailto:' in author_page_url:
                    log("  -> SUCCESS! Found a direct mailto: link.")
                    found_email = author_page_url.replace('mailto:', '').strip()
                    browser.close()
                    return found_email

                if author_page_url.startswith('/'):
                    base_url = '/'.join(article_url.split('/')[:3])
                    author_page_url = f"{base_url}{author_page_url}"
                
                log(f"  -> Found author page, navigating to: {author_page_url}")
                page.goto(author_page_url, timeout=60000, wait_until='domcontentloaded')

            page_content = page.locator('body').inner_text()
            match = re.search(email_pattern, page_content)
            
            if match:
                found_email = match.group(0)
            
            browser.close()
    except TimeoutError:
        log("  -> Page still timed out, even with optimization. Skipping this author.")
    except Exception as e:
        log(f"  -> An error occurred during headless browsing: {e}")
    
    return found_email

def parse_rss_for_leads(content):
    """Parses RSS feed to get a list of leads, splitting multiple authors."""
    leads = []
    soup = BeautifulSoup(content, 'xml')
    articles = soup.find_all('item')
    for article in articles:
        author_tag = article.find('dc:creator') or article.find('author')
        link_tag = article.find('link')
        title_tag = article.find('title')
        if not (author_tag and author_tag.string and link_tag and link_tag.string and title_tag and title_tag.string):
            continue
        author_string = author_tag.string.strip()
        author_names = re.split(r'\s*,\s*|\s+and\s+', author_string)
        
        article_link = link_tag.string.strip()
        article_title = title_tag.string.strip()
        
        for name in author_names:
            name = name.strip()
            if name:
                leads.append({'name': name, 'link': article_link, 'title': article_title})
    return leads

def write_results(filename, results_list, header):
    """Helper to write results, ensuring header exists."""
    if not results_list: return
    write_header = not os.path.exists(filename) or os.path.getsize(filename) == 0
    log(f"\nAppending {len(results_list)} entries to local file: {filename}.")
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header: writer.writerow(header)
        writer.writerows(results_list)

def main():
    log("--- Starting Journalist Monitor (UK Edition) ---")
    existing_journalists = get_existing_journalists()
    blacklist_emails = get_blacklist_emails()
    log(f"Loaded {len(existing_journalists)} existing journalists.")
    log(f"Loaded {len(blacklist_emails)} emails in the Blacklist filter.")

    new_verified_journalists = []
    new_pending_journalists = []
    HEADER = ['First_Name', 'Last_Name', 'Email', 'City', 'State', 'Country', 'phone', 'publications', 'title', 'topics', 'twitter', 'source_url']

    for outlet in OUTLET_SOURCES:
        if not outlet.get('rss_url'): continue
        log(f"\nChecking: {outlet['outlet']}")
        try:
            response = requests.get(outlet['rss_url'], headers=HEADERS, timeout=15)
            response.raise_for_status()
            leads = parse_rss_for_leads(response.content)
            for lead in leads:
                full_name = lead['name']
                if not full_name.strip() or full_name.lower() in existing_journalists:
                    continue
                name_parts = full_name.split()
                if not name_parts: continue
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                domain = outlet['url'].split('/')[2].replace('www.', '')
                email_guess = f"{first_name[0].lower()}.{last_name.lower().replace(' ', '')}@{domain}"
                if email_guess.lower() in blacklist_emails:
                    log(f"  -> Skipping author {full_name}: Guessed email is blacklisted.")
                    existing_journalists.add(full_name.lower())
                    continue
                log(f"\nFound new author: {full_name}. Searching for real email...")
                real_email = find_email_with_playwright(lead['link'], full_name)
                
                # 'topics' is blank, 'title' has the article title, 'source_url' has the link
                journalist_record = [
                    first_name, last_name, "N/A", outlet.get('location', ''), '', 'UK', '',
                    outlet['outlet'], lead['title'], '', '', lead['link']
                ]
                if real_email:
                    log(f"  -> SUCCESS! Found real email: {real_email}")
                    journalist_record[2] = real_email
                    new_verified_journalists.append(journalist_record)
                else:
                    log("  -> No public email found. Generating guess for API validation.")
                    journalist_record[2] = email_guess
                    new_pending_journalists.append(journalist_record)
                existing_journalists.add(full_name.lower())
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            log(f"-> Error fetching RSS for {outlet['outlet']}: {e}")

    if new_verified_journalists:
        write_results(MASTER_LIST_FILE, new_verified_journalists, HEADER)

    if new_pending_journalists:
        write_results(PENDING_FILE, new_pending_journalists, HEADER)
    
    if new_verified_journalists:
        log("\nConnecting to Google Sheets to sync new verified journalists...")
        # 1. Create an instance of the class
        client = sheets_client.GoogleSheetsClient()
        
        # 2. Get the worksheet by its name
        master_ws = client.get_worksheet("master_list_uk") 
        
        if master_ws:
            try:
                log(f"Uploading {len(new_verified_journalists)} new rows to 'master_list_uk' sheet...")
                # Added value_input_option for better formatting
                master_ws.append_rows(new_verified_journalists, value_input_option='USER_ENTERED')
                log("Google Sheets sync successful.")
            except Exception as e:
                log(f"Google Sheets sync failed: {e}")
    
    log("--- Monitor Finished ---")

if __name__ == "__main__":
    main()
