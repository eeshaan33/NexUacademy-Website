import os
from typing import List, Dict, Optional
import logging
from datetime import datetime

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logging.warning("Google Sheets API not available. Install google-api-python-client")

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """
    Manages Google Sheets integration for YouTube link management.
    """
    
    def __init__(self):
        self.sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        self.service = None
        
        if GOOGLE_SHEETS_AVAILABLE and self.sheet_id:
            self._initialize_service()
    
    def _initialize_service(self):
        """
        Initialize Google Sheets API service.
        """
        try:
            # Try to get credentials from environment
            creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            
            if creds_json:
                import json
                creds_dict = json.loads(creds_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                # Fallback to service account file
                creds_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'credentials.json')
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            self.service = None
    
    def create_sheet(self, questions: List[Dict]) -> Optional[str]:
        """
        Create a new Google Sheet with questions data.
        Returns the Sheet URL if successful.
        """
        if not self.service:
            logger.error("Google Sheets service not available")
            return None
        
        try:
            # Create new spreadsheet
            spreadsheet = {
                'properties': {
                    'title': f'JEE PYQ YouTube Links - {datetime.now().strftime("%Y-%m-%d")}'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'JEE PYQ YouTube Links',
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        }
                    },
                    {
                        'properties': {
                            'title': 'Instructions'
                        }
                    }
                ]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            sheet_id = result['spreadsheetId']
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            
            # Populate with data
            self._populate_sheet(sheet_id, questions)
            self._add_instructions(sheet_id)
            
            logger.info(f"Created Google Sheet: {sheet_url}")
            return sheet_url
            
        except HttpError as e:
            logger.error(f"Failed to create Google Sheet: {e}")
            return None
    
    def _populate_sheet(self, sheet_id: str, questions: List[Dict]):
        """
        Populate sheet with questions data.
        """
        # Prepare header
        headers = [
            "Row ID", "Question Number", "Exam Type", "Year", "Subject",
            "Chapter", "Topic", "Question Preview", "YouTube URL",
            "Timestamp (seconds)", "Last Updated"
        ]
        
        # Prepare data rows
        rows = [headers]
        for i, q in enumerate(questions, 1):
            row_id = f"Q{str(i).zfill(3)}"
            preview = q.get('questionText', '')[:50] + "..."
            
            row = [
                row_id,
                q.get('questionNumber', i),
                q.get('examType', 'JEE_Main'),
                q.get('year', 2024),
                q.get('subject', 'Chemistry'),
                q.get('chapter', ''),
                q.get('topic', ''),
                preview,
                "",  # YouTube URL (empty for now)
                0,   # Timestamp (empty for now)
                ""   # Last Updated
            ]
            rows.append(row)
        
        # Write to sheet
        body = {'values': rows}
        self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='JEE PYQ YouTube Links!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Populated sheet with {len(questions)} questions")
    
    def _add_instructions(self, sheet_id: str):
        """
        Add instructions to the Instructions sheet.
        """
        instructions = [
            ["HOW TO ADD YOUTUBE SOLUTION LINKS:"],
            [""],
            ["1. Find the Row ID of the question (e.g., Q001)"],
            ["2. Paste the YouTube video URL in the 'YouTube URL' column"],
            ["   Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            [""],
            ["3. Add the timestamp (in seconds) where solution starts"],
            ["   Example: If solution starts at 2:15, enter 135"],
            ["   (2 minutes × 60 + 15 seconds = 135)"],
            [""],
            ["4. Save the sheet (Ctrl+S or auto-saves)"],
            [""],
            ["5. Wait 30 seconds - changes will sync to website automatically"],
            [""],
            ["6. Check website to confirm 'View Solution' button works"],
            [""],
            ["TIPS:"],
            ["- YouTube URL format: https://www.youtube.com/watch?v=VIDEO_ID"],
            ["- Find timestamp: Pause video, right-click → 'Copy video URL at current time'"],
            ["- This gives you URL with &t=XXXs automatically"],
            [""],
            ["TROUBLESHOOTING:"],
            ["- If link doesn't work, check URL format"],
            ["- Timestamp must be in seconds (not MM:SS)"],
            ["- Changes sync every 30 seconds, so wait a bit"]
        ]
        
        body = {'values': instructions}
        self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Instructions!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def sync_youtube_links(self, db) -> int:
        """
        Sync YouTube links from Google Sheet to database.
        Returns number of questions updated.
        """
        if not self.service or not self.sheet_id:
            return 0
        
        try:
            # Read data from sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='JEE PYQ YouTube Links!A2:K1000'  # Skip header
            ).execute()
            
            rows = result.get('values', [])
            updated_count = 0
            
            for row in rows:
                if len(row) < 9:
                    continue
                
                row_id = row[0]
                youtube_url = row[8] if len(row) > 8 else ""
                timestamp = row[9] if len(row) > 9 else 0
                
                if youtube_url and youtube_url.strip():
                    # Update database
                    result = db.questions.update_one(
                        {"googleSheetRowId": row_id},
                        {
                            "$set": {
                                "solutionYoutubeUrl": youtube_url.strip(),
                                "solutionTimestamp": int(timestamp) if timestamp else 0,
                                "updatedAt": datetime.now()
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Synced {updated_count} YouTube links from Google Sheet")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to sync YouTube links: {e}")
            return 0
