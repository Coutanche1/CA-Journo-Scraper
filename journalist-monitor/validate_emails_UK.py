#!/usr/bin/env python3
import csv
import quickemailverification
import time
from datetime import datetime
import signal
import os
import sheets_client

# --- HELPER FUNCTION ---
def log(message, end='\n'):
    """Prints a message with a timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", end=end)

# --- CONFIGURATION (UK) ---
MASTER_LIST_FILE = 'master_list_uk.csv'
PENDING_FILE = 'pending_verification_uk.csv'
BLACKLIST_FILE = 'blacklist_emails.txt'
API_KEY = os.getenv('EMAIL_VERIFY_KEY')
if not API_KEY:
    log("CRITICAL ERROR: EMAIL_VERIFY_KEY environment variable not set.")
    exit()CREDITS_TO_USE = 100

# --- TIMEOUT HANDLER for API calls ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("API call timed out")

# Set the signal handler for the alarm signal (works on Linux)
signal.signal(signal.SIGALRM, timeout_handler)

def main():
    log("--- Starting Pending Email Validator (UK Edition) ---")
    
    try:
        client = quickemailverification.Client(API_KEY)
        verifier = client.quickemailverification()
    except Exception as e:
        log(f"Failed to initialize API client: {e}")
        return

    try:
        with open(PENDING_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            pending_rows = list(reader)
    except (FileNotFoundError, StopIteration):
        log("Pending verification file is empty or not found. Nothing to do.")
        return
        
    if not pending_rows:
        log("Pending verification file is empty. Nothing to do.")
        return

    log(f"Found {len(pending_rows)} journalists in the pending queue.")
    
    rows_to_process = pending_rows[:CREDITS_TO_USE]
    remaining_rows = pending_rows[CREDITS_TO_USE:]
    
    validated_rows = []
    api_calls = 0

    for row in rows_to_process:
        if len(row) < 3:
            continue
            
        email_to_check = row[2]
        full_name = f"{row[0]} {row[1]}"
        log(f"Verifying {full_name}: {email_to_check}...", end='')
        
        signal.alarm(15)
        try:
            response = verifier.verify(email_to_check)
            api_calls += 1
            result = response.body.get('result')
            
            if result == 'valid':
                print(" VALID ✅")
                validated_rows.append(row)
            else:
                print(f" INVALID ({result}) ❌. Blacklisting email.")
                with open(BLACKLIST_FILE, 'a', encoding='utf-8') as f_out:
                    f_out.write(email_to_check + '\n')
            time.sleep(1)
        except (TimeoutError, Exception) as e:
            print(f" API ERROR/TIMEOUT: {e}. Row returned to queue.")
            remaining_rows.insert(0, row)
            continue
        finally:
            signal.alarm(0)

    # --- LOCAL FILE WRITING ---
    if validated_rows:
        log(f"\nFound {len(validated_rows)} VALID emails. Appending to local UK master list.")
        write_header = not os.path.exists(MASTER_LIST_FILE) or os.path.getsize(MASTER_LIST_FILE) == 0
        with open(MASTER_LIST_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(header)
            writer.writerows(validated_rows)

    # --- GOOGLE SHEETS SYNC (UK) ---
    if validated_rows:
        log("\nConnecting to Google Sheets to sync newly validated journalists...")
                
        # 1. Create an instance of the class
        client = sheets_client.GoogleSheetsClient()
        
        # 2. Get the worksheet by its name
        master_ws = client.get_worksheet("master_list_uk") # <-- Calls the correct function

        if master_ws:
            try:
                log(f"Uploading {len(validated_rows)} new rows to 'master_list_uk' sheet...")
                # Added value_input_option for better formatting
                master_ws.append_rows(validated_rows, value_input_option='USER_ENTERED')
                log("Google Sheets sync successful.")
            except Exception as e:
                log(f"Google Sheets sync failed: {e}")
        else:
            log("Skipping Google Sheets sync due to connection failure.")

    # Overwrite the pending file with the remaining rows
    log(f"\nUpdating pending queue. {len(remaining_rows)} journalists remaining.")
    with open(PENDING_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(remaining_rows)
        
    log(f"\n--- Validator Finished. API calls made: {api_calls} ---")

if __name__ == "__main__":
    main()
