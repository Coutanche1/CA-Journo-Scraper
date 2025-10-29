#!/usr/bin/env python3
import gspread
import os
from gspread.exceptions import SpreadsheetNotFound, APIError

# Get the absolute path of the directory where this script is located
# This is crucial for cron jobs
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, 'credentials.json')

GOOGLE_SHEET_NAME = os.getenv('JOURNALIST_SHEET_NAME')
class GoogleSheetsClient:
    """
    A dedicated class to handle all Google Sheets connections.
    """
    def __init__(self):
        """
        Authenticates and opens the spreadsheet upon creation.
        """
        self.spreadsheet = None
        try:
            print(f"Authenticating with Google Sheets using {CREDENTIALS_FILE}...")
            gc = gspread.service_account(filename=CREDENTIALS_FILE)
            self.spreadsheet = gc.open(GOOGLE_SHEET_NAME)
            print(f"Successfully opened spreadsheet: '{GOOGLE_SHEET_NAME}'")
        
        except FileNotFoundError:
            print(f"!!! CRITICAL ERROR: 'credentials.json' not found.")
            print(f"    Make sure it is in the same directory: {SCRIPT_DIR}")
        except SpreadsheetNotFound:
            print(f"!!! CRITICAL ERROR: Google Sheet not found.")
            print(f"    Make sure the name is *exactly*: '{GOOGLE_SHEET_NAME}'")
        except APIError as e:
            print(f"!!! CRITICAL ERROR: Google API Error.")
            print(f"    Share the sheet with your 'client_email' from 'credentials.json' as an 'Editor'.")
            print(f"    Full error details: {e}")
        except Exception as e:
            print(f"!!! CRITICAL ERROR: Could not open Google Sheet.")
            print(f"    Error Type: {type(e).__name__}: {e}")

    def get_worksheet(self, sheet_name):
        """
        Gets a specific worksheet (tab) by its name.
        Returns the worksheet object or None if not found or if auth failed.
        """
        if not self.spreadsheet:
            print(f"  > Cannot get worksheet, spreadsheet was not loaded.")
            return None
        
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            print(f"  > Successfully accessed worksheet: '{sheet_name}'")
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            print(f"  > !!! ERROR: Worksheet named '{sheet_name}' not found in the document.")
            return None
        except Exception as e:
            print(f"  > !!! ERROR: Could not get worksheet '{sheet_name}'.")
            print(f"    Error Type: {type(e).__name__}: {e}")
            return None