# CA-Journo-Scraper
J A N K Y

- Pulls journalists from a number of Canadian outlets using "monitor.py"

- Creates a local file - "master_list.csv" for those with a found email, also creates "pending_verification.csv" for Journalists the script guessed the email for.
^ Auto runs as a cron job at 4am CET

- Manual running of validate_emails.py within the venv uses an email validation service with 100 credits per day, either validating (and moving to the master list) or failing (moving to blacklist.txt

After the local changed are made, everything is pushed to Google Sheets
