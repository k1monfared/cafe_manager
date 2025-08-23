#!/usr/bin/env python3
"""
Google Drive Integration for Cafe Supply Manager
Allows users to connect their Google Drive and automatically sync Google Sheets files
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import io
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    print("⚠️  Google APIs not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

class GoogleDriveIntegration:
    def __init__(self, credentials_file="google_credentials.json", token_file="google_token.pickle"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file'
        ]
        self.service = None
        self.credentials = None
        
        # File mappings for cafe manager
        self.file_mappings = {
            'inventory': 'current_inventory.csv',
            'usage': 'daily_usage.csv',
            'orders': 'order_history.csv',
            'suppliers': 'suppliers.csv'
        }
    
    def setup_credentials(self) -> Tuple[bool, str]:
        """Set up Google Drive credentials"""
        if not GOOGLE_APIS_AVAILABLE:
            return False, "Google APIs not installed. Please run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        
        # Check if we have valid credentials
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
                if creds and creds.valid:
                    self.credentials = creds
                    return True, "Already authenticated"
        
        # If we have stored credentials, try to refresh them
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        self.credentials = creds
                        return True, "Credentials refreshed"
                    except Exception as e:
                        print(f"Error refreshing credentials: {e}")
        
        # Need to authenticate
        if not os.path.exists(self.credentials_file):
            return False, f"Credentials file not found: {self.credentials_file}. Please follow setup instructions."
        
        # Run the OAuth flow
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.scopes
            )
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            self.credentials = creds
            return True, "Authentication successful"
            
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"
    
    def get_service(self):
        """Get Google Drive service"""
        if not self.credentials:
            success, message = self.setup_credentials()
            if not success:
                return None
        
        if not self.service:
            self.service = build('drive', 'v3', credentials=self.credentials)
        
        return self.service
    
    def list_spreadsheets(self) -> Tuple[bool, List[Dict]]:
        """List all Google Sheets in the user's drive"""
        try:
            service = self.get_service()
            if not service:
                return False, []
            
            # Search for Google Sheets files
            results = service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                pageSize=50,
                fields="nextPageToken, files(id, name, modifiedTime, webViewLink)"
            ).execute()
            
            items = results.get('files', [])
            
            # Format the results
            formatted_items = []
            for item in items:
                formatted_items.append({
                    'id': item['id'],
                    'name': item['name'],
                    'modified': item.get('modifiedTime', ''),
                    'url': item.get('webViewLink', ''),
                    'type': 'spreadsheet'
                })
            
            return True, formatted_items
            
        except HttpError as error:
            return False, f"An error occurred: {error}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def download_sheet_as_csv(self, file_id: str, sheet_name: str = None) -> Tuple[bool, str, str]:
        """Download a Google Sheet as CSV"""
        try:
            service = self.get_service()
            if not service:
                return False, "", "Could not connect to Google Drive"
            
            # Export as CSV
            request = service.files().export_media(
                fileId=file_id,
                mimeType='text/csv'
            )
            
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            
            while done is False:
                status, done = downloader.next_chunk()
            
            # Get the CSV content
            csv_content = file.getvalue().decode('utf-8')
            
            # Get file info for naming
            file_info = service.files().get(fileId=file_id).execute()
            filename = file_info.get('name', 'downloaded_sheet')
            
            return True, csv_content, filename
            
        except HttpError as error:
            return False, "", f"Download failed: {error}"
        except Exception as e:
            return False, "", f"Unexpected error: {str(e)}"
    
    def save_csv_content(self, csv_content: str, file_type: str) -> Tuple[bool, str]:
        """Save CSV content to the appropriate file"""
        try:
            if file_type not in self.file_mappings:
                return False, f"Invalid file type: {file_type}"
            
            filename = self.file_mappings[file_type]
            filepath = os.path.join('google_sheets_data', filename)
            
            # Ensure directory exists
            os.makedirs('google_sheets_data', exist_ok=True)
            
            # Write the CSV content
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)
            
            return True, f"Saved {filename} successfully"
            
        except Exception as e:
            return False, f"Error saving file: {str(e)}"
    
    def sync_from_drive_links(self, drive_links: Dict[str, str]) -> Dict[str, bool]:
        """Sync multiple files from Google Drive links"""
        results = {}
        
        for file_type, drive_url in drive_links.items():
            try:
                # Extract file ID from Google Sheets URL
                file_id = self.extract_file_id_from_url(drive_url)
                if not file_id:
                    results[file_type] = False
                    continue
                
                # Download the sheet
                success, csv_content, filename = self.download_sheet_as_csv(file_id)
                if not success:
                    results[file_type] = False
                    continue
                
                # Save the content
                save_success, message = self.save_csv_content(csv_content, file_type)
                results[file_type] = save_success
                
            except Exception as e:
                print(f"Error syncing {file_type}: {e}")
                results[file_type] = False
        
        return results
    
    def extract_file_id_from_url(self, url: str) -> Optional[str]:
        """Extract Google Sheets file ID from various URL formats"""
        import re
        
        # Common Google Sheets URL patterns
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'^([a-zA-Z0-9-_]+)$'  # Just the ID itself
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_sheet_info(self, file_id: str) -> Tuple[bool, Dict]:
        """Get information about a Google Sheet"""
        try:
            service = self.get_service()
            if not service:
                return False, {}
            
            file_info = service.files().get(fileId=file_id).execute()
            
            return True, {
                'name': file_info.get('name', ''),
                'id': file_info.get('id', ''),
                'modified': file_info.get('modifiedTime', ''),
                'url': file_info.get('webViewLink', ''),
                'size': file_info.get('size', '0')
            }
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the Google Drive connection"""
        try:
            service = self.get_service()
            if not service:
                return False, "Could not connect to Google Drive"
            
            # Try to list a few files
            results = service.files().list(pageSize=1).execute()
            
            return True, "Connection successful"
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

def create_credentials_template():
    """Create a template for Google Drive credentials"""
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('google_credentials_template.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    return """
📋 Google Drive Setup Instructions:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing project
3. Enable Google Drive API:
   - Go to APIs & Services > Library
   - Search for "Google Drive API" 
   - Click Enable
4. Create credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file
5. Rename the downloaded file to "google_credentials.json"
6. Place it in your cafe_manager folder
7. Restart the application

The file should look like the template created: google_credentials_template.json
"""

def main():
    print("🔗 Google Drive Integration Setup")
    print("=" * 50)
    
    if not GOOGLE_APIS_AVAILABLE:
        print("❌ Google APIs not installed")
        print("📦 Please run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return
    
    # Create credentials template
    instructions = create_credentials_template()
    
    drive = GoogleDriveIntegration()
    
    # Check if credentials exist
    if not os.path.exists(drive.credentials_file):
        print("❌ Google credentials not found")
        print(instructions)
        return
    
    # Test authentication
    success, message = drive.setup_credentials()
    print(f"🔐 Authentication: {message}")
    
    if success:
        # Test connection
        conn_success, conn_message = drive.test_connection()
        print(f"🔗 Connection: {conn_message}")
        
        if conn_success:
            # List some spreadsheets
            list_success, sheets = drive.list_spreadsheets()
            if list_success:
                print(f"📊 Found {len(sheets)} Google Sheets in your drive")
                for sheet in sheets[:5]:  # Show first 5
                    print(f"   • {sheet['name']}")
            else:
                print(f"❌ Could not list sheets: {sheets}")

if __name__ == "__main__":
    main()