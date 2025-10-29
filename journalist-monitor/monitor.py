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
MASTER_LIST_FILE = 'master_journalist_list.csv'
PENDING_FILE = 'pending_verification.csv'
BLACKLIST_FILE = 'blacklist_emails.txt'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}
OUTLET_SOURCES = [
    # National
    {
        "outlet": "The Globe and Mail", "url": "https://www.theglobeandmail.com/", "location": "National",
        "rss_url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/?outputType=xml"
    },
    {
        "outlet": "National Post", "url": "https://nationalpost.com/", "location": "National",
        "rss_url": "https://nationalpost.com/feed"
    },
    {
        "outlet": "The Walrus", "url": "https://thewalrus.ca/", "location": "National",
        "rss_url": "https://thewalrus.ca/feed/"
    },
    {
        "outlet": "BNN Bloomberg", "url": "https://www.bnnbloomberg.ca/", "location": "National",
        "rss_url": "https://www.bnnbloomberg.ca/rss/news/bnn-s-top-stories-1.1044434"
    },
    {
        "outlet": "Canada's National Observer", "url": "https://www.nationalobserver.com/", "location": "National",
        "rss_url": "https://www.nationalobserver.com/front/rss"
    },
    {
        "outlet": "Canadaland", "url": "https://www.canadaland.com/", "location": "National",
        "rss_url": "https://www.canadaland.com/feed/"
    },
    {
        "outlet": "The Hill Times", "url": "https://www.hilltimes.com/", "location": "National (Ottawa)",
        "rss_url": "https://www.hilltimes.com/feed/"
    },
    # British Columbia
    {
        "outlet": "The Vancouver Sun", "url": "https://vancouversun.com/", "location": "British Columbia",
        "rss_url": "https://vancouversun.com/feed"
    },
    {
        "outlet": "The Tyee", "url": "https://thetyee.ca/", "location": "British Columbia",
        "rss_url": "https://thetyee.ca/rss2.xml"
    },
    {
        "outlet": "Vancouver Is Awesome", "url": "https://www.vancouverisawesome.com/", "location": "British Columbia",
        "rss_url": "https://www.vancouverisawesome.com/rss"
    },
    {
        "outlet": "Castanet (Most Recent)", "url": "https://www.castanet.net/", "location": "British Columbia",
        "rss_url": "https://www.castanet.net/rss/mostrecent.xml"
    },
    {
        "outlet": "Castanet (Top Headlines)", "url": "https://www.castanet.net/", "location": "British Columbia",
        "rss_url": "https://www.castanet.net/rss/topheadlines.xml"
    },
    # Alberta
    {
        "outlet": "Calgary Herald", "url": "https://calgaryherald.com/", "location": "Alberta",
        "rss_url": "https://calgaryherald.com/feed"
    },
    {
        "outlet": "Edmonton Journal", "url": "https://edmontonjournal.com/", "location": "Alberta",
        "rss_url": "https://edmontonjournal.com/feed"
    },
    # Saskatchewan & Manitoba
    {
        "outlet": "Regina Leader-Post", "url": "https://leaderpost.com/", "location": "Saskatchewan",
        "rss_url": "https://leaderpost.com/feed"
    },
    {
        "outlet": "Saskatoon StarPhoenix", "url": "https://thestarphoenix.com/", "location": "Saskatchewan",
        "rss_url": "https://thestarphoenix.com/feed"
    },
    {
        "outlet": "Winnipeg Free Press", "url": "https://www.winnipegfreepress.com/", "location": "Manitoba",
        "rss_url": "https://www.winnipegfreepress.com/rss/?path=%2F"
    },
    # Ontario
    {
        "outlet": "Toronto Star", "url": "https://www.thestar.com/", "location": "Ontario",
        "rss_url": "https://www.thestar.com/feed/"
    },
    {
        "outlet": "Ottawa Citizen", "url": "https://ottawacitizen.com/", "location": "Ontario",
        "rss_url": "https://ottawacitizen.com/feed"
    },
    {
        "outlet": "The Hamilton Spectator", "url": "https://www.thespec.com/", "location": "Ontario",
        "rss_url": "https://www.thespec.com/rss/"
    },
    {
        "outlet": "TVO (TVOntario)", "url": "https://www.tvo.org/", "location": "Ontario",
        "rss_url": "https://www.tvo.org/rss/articles/all"
    },
    {
        "outlet": "Guelph Today", "url": "https://www.guelphtoday.com/", "location": "Ontario",
        "rss_url": "https://www.guelphtoday.com/rss"
    },
    # Quebec
    {
        "outlet": "La Presse", "url": "https://www.lapresse.ca/", "location": "Quebec",
        "rss_url": "https://www.lapresse.ca/actualites/rss"
    },
    {
        "outlet": "Montreal Gazette", "url": "https://montrealgazette.com/", "location": "Quebec",
        "rss_url": "https://montrealgazette.com/feed"
    },
    # Atlantic Canada
    {
        "outlet": "SaltWire Network", "url": "https://www.saltwire.com/", "location": "Atlantic Canada",
        "rss_url": "https://www.saltwire.com/feed/"
    },
    # The North
    {
        "outlet": "Cabin Radio", "url": "https://cabinradio.ca/", "location": "Northwest Territories",
        "rss_url": "https://cabinradio.ca/feed/"
    },
    {
        "outlet": "Nunatsiaq News", "url": "https://nunatsiaq.com/", "location": "Nunavut / Nunavik",
        "rss_url": "https://nunatsiaq.com/feed/"
    }
]

def get_existing_journalists():
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
        """Intercepts network requests and blocks non-essential ones."""
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
    log("--- Starting Journalist Monitor (Local with Cloud Sync) ---")
    existing_journalists = get_existing_journalists()
    blacklist_emails = get_blacklist_emails()
    log(f"Loaded {len(existing_journalists)} existing journalists.")
    log(f"Loaded {len(blacklist_emails)} emails in the Blacklist filter.")

    new_verified_journalists = []
    new_pending_journalists = []
    HEADER = ['First_Name', 'Last_Name', 'Email', 'City', 'State', 'Country', 'phone', 'publications', 'title', 'topics', 'twitter', 'link']
    
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
                
                journalist_record = [
                    first_name, last_name, "N/A", '', outlet.get('location', ''), 'Canada', '',
                    outlet['outlet'], lead['title'], lead['link'], ''
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
    # 1. Create an instance of the class first
        client = sheets_client.GoogleSheetsClient()

    # 2. Call the correct method on that instance
        master_ws = client.get_worksheet("master_list")
        if master_ws:
            try:
                log(f"Uploading {len(new_verified_journalists)} new rows to 'master_list' sheet...")
                master_ws.append_rows(new_verified_journalists)
                log("Google Sheets sync successful.")
            except Exception as e:
                log(f"Google Sheets sync failed: {e}")
        else:
            log("Skipping Google Sheets sync due to connection failure.")
    
    log("--- Monitor Finished ---")

if __name__ == "__main__":
    main()
