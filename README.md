# Canadian Journalist Contact Scraper & Validator

This project is a set of Python scripts that automatically scrapes Canadian and UK news sites for journalist bylines. It attempts to find their email addresses, validates them using an API, and uploads the verified contacts to separate tabs in a Google Sheet.

## 🧰 What It Does

* **Scrapes Bylines:** Reads RSS feeds from dozens of news outlets (in `monitor.py` and `monitorUK.py`) to find new articles and author names.
* **Finds Emails:** Uses `playwright` (a headless browser) to visit the article link and search the page (or the author's bio page) for an email address.
* **Guesses Emails:** If no email is found, it generates a common email "guess" (e.g., `j.doe@domain.com`).
* **Separates Contacts:**
    * Found emails are added to `master_list.csv` / `master_list_uk.csv`.
    * Guessed emails are added to `pending_verification.csv` / `pending_verification_uk.csv`.
* **Validates Emails:** The `validate_emails.py` scripts run on the "pending" files, using an API to check if the guessed emails are valid.
* **Syncs to Cloud:** All newly verified contacts (both found and validated) are automatically appended to a Google Sheet.

---

## ⚙️ Setup and Installation

Follow these steps to get the project running on a new machine.

### 1. Clone the Repository

git clone [https://github.com/Coutanche1/CA-Journo-Scraper.git](https://github.com/Coutanche1/CA-Journo-Scraper.git)
cd CA-Journo-Scraper

### 2. Create a Virtual Environment
It's highly recommended to use a virtual environment to keep dependencies clean.

# Create the venv
python3 -m venv venv

# Activate it (on macOS/Linux)
source venv/bin/activate

### 3. Install Dependencies
# Install all the required Python libraries from requirements.txt.

pip install -r requirements.txt

### 4. Install Playwright Browsers
# The playwright library requires its own set of browser binaries. This command will download them.

playwright install

### 🔑 Configuration (Required)
# This project requires three secret items to function. These are NEVER stored in the repository (they are protected by .gitignore).

### 1. Google Cloud (GCP) for credentials.json
# This is the most complex step. You need a Google Cloud service account to allow the script to edit your Google Sheet.

Go to Google Cloud Console: console.cloud.google.com

Create a New Project: Call it "Journalist Scraper" or similar.

Enable APIs:

In the search bar, find and enable the Google Drive API.

In the search bar, find and enable the Google Sheets API.

Create Credentials:

Go to "APIs & Services" > "Credentials".

Click "+ Create Credentials" and select "Service Account".

Give it a name (e.g., "sheets-editor") and click "Done".

Generate a Key:

Find your new service account in the list and click on it.

Go to the "KEYS" tab.

Click "Add Key" > "Create new key".

Choose JSON and click "Create".

Save the Key:

A JSON file will be downloaded.

# Rename this file to credentials.json.

# Place this file in the root of your project folder (CA-Journo-Scraper/).

Share Your Google Sheet:

# Open your credentials.json file and find the client_email address. It will look like sheets-editor@your-project-id.iam.gserviceaccount.com.

## Open the Google Sheet you want the script to write to.

# 1 Click the "Share" button.

Paste the client_email into the share dialog and give it "Editor" permission.

# 2. Email Validation API Key
The validate_emails.py scripts require an API key from an email verification service (the code is set up for QuickEmailVerification, but any can be adapted).

This key is loaded from an environment variable.

# 3. Google Sheet Name
The sheets_client.py script also loads your sheet name from an environment variable.

How to Set Environment Variables
Before running the scripts, you must set these variables in your terminal.

On macOS/Linux:

# This key is used by validate_emails.py and validate_emails_UK.py
export EMAIL_VERIFY_KEY="your_quickemailverification_api_key_here"

# This sheet name is used by sheets_client.py
export JOURNALIST_SHEET_NAME="The-Name-of-Your-Google-Sheet"

(Note: You'll need to run these export commands every time you open a new terminal, or add them to your ~/.zprofile or ~/.bash_profile to make them permanent.)

### 🚀 How to Use the Scripts

Make sure your virtual environment is active (source venv/bin/activate) and your environment variables are set.

# To Scrape for New Journalists:

python3 monitor.py

## These scripts will scrape the RSS feeds, find/guess emails, and add them to the local .csv files. Any found emails (not guesses) will be synced to Google Sheets immediately.

# To Validate Guessed Emails:

python3 validate_emails.py

# These scripts will read the "pending" files, use your API credits to check the emails, and move any valid ones to the "master" list and sync them to Google Sheets.

### Automation
These scripts are designed to be run on a schedule using cron (on Linux/macOS) to fully automate your contact list building.
