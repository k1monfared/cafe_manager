#!/usr/bin/env python3
"""
Automatic Sync Scheduler for Google Drive Integration
Allows users to set up automatic syncing of their Google Sheets
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from .google_drive_integration import GoogleDriveIntegration
from .sheets_sync import SheetsSync

class SyncScheduler:
    def __init__(self, config_file="sync_config.json"):
        self.config_file = config_file
        self.google_drive = GoogleDriveIntegration()
        self.sheets_sync = SheetsSync()
        self.sync_thread = None
        self.stop_sync = False
        self.last_sync_results = {}
        self.sync_config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load sync configuration"""
        default_config = {
            "enabled": False,
            "sync_interval_hours": 24,  # Sync once per day
            "auto_sync_files": {},      # {file_type: google_drive_url}
            "last_sync_time": None,
            "notification_email": None,
            "sync_on_startup": False
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Error loading sync config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save sync configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.sync_config, f, indent=2)
        except Exception as e:
            print(f"Error saving sync config: {e}")
    
    def set_auto_sync_files(self, file_urls: Dict[str, str]):
        """Set the Google Drive URLs for automatic syncing"""
        self.sync_config["auto_sync_files"] = file_urls
        self.save_config()
    
    def enable_auto_sync(self, interval_hours: int = 24):
        """Enable automatic syncing"""
        self.sync_config["enabled"] = True
        self.sync_config["sync_interval_hours"] = interval_hours
        self.save_config()
        self.start_sync_thread()
    
    def disable_auto_sync(self):
        """Disable automatic syncing"""
        self.sync_config["enabled"] = False
        self.save_config()
        self.stop_sync_thread()
    
    def start_sync_thread(self):
        """Start the background sync thread"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.stop_sync = False
        self.sync_thread = threading.Thread(target=self._sync_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        print("✅ Auto-sync thread started")
    
    def stop_sync_thread(self):
        """Stop the background sync thread"""
        self.stop_sync = True
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("✅ Auto-sync thread stopped")
    
    def _sync_loop(self):
        """Background sync loop"""
        while not self.stop_sync:
            if self.sync_config["enabled"] and self.sync_config["auto_sync_files"]:
                if self._should_sync():
                    print("🔄 Starting automatic sync...")
                    results = self.perform_sync()
                    self.last_sync_results = results
                    self.sync_config["last_sync_time"] = datetime.now().isoformat()
                    self.save_config()
                    print(f"✅ Automatic sync completed: {results}")
            
            # Sleep for 1 hour before checking again
            for _ in range(3600):  # 3600 seconds = 1 hour
                if self.stop_sync:
                    break
                time.sleep(1)
    
    def _should_sync(self) -> bool:
        """Check if it's time to sync"""
        if not self.sync_config["last_sync_time"]:
            return True  # First sync
        
        try:
            last_sync = datetime.fromisoformat(self.sync_config["last_sync_time"])
            hours_since_sync = (datetime.now() - last_sync).total_seconds() / 3600
            return hours_since_sync >= self.sync_config["sync_interval_hours"]
        except:
            return True  # If we can't parse the time, sync anyway
    
    def perform_sync(self) -> Dict:
        """Perform the actual sync operation"""
        try:
            # Download from Google Drive
            download_results = self.google_drive.sync_from_drive_links(
                self.sync_config["auto_sync_files"]
            )
            
            # Convert to JSON format
            sync_results = self.sheets_sync.sync_from_sheets()
            
            return {
                "success": any(download_results.values()) and any(sync_results.values()),
                "download_results": download_results,
                "sync_results": sync_results,
                "timestamp": datetime.now().isoformat(),
                "files_synced": [f for f, success in sync_results.items() if success]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def manual_sync(self) -> Dict:
        """Perform a manual sync (same as automatic but doesn't update schedule)"""
        return self.perform_sync()
    
    def get_sync_status(self) -> Dict:
        """Get current sync status and configuration"""
        next_sync = None
        if self.sync_config["enabled"] and self.sync_config["last_sync_time"]:
            try:
                last_sync = datetime.fromisoformat(self.sync_config["last_sync_time"])
                next_sync = last_sync + timedelta(hours=self.sync_config["sync_interval_hours"])
            except:
                pass
        
        return {
            "enabled": self.sync_config["enabled"],
            "interval_hours": self.sync_config["sync_interval_hours"],
            "connected_files": list(self.sync_config["auto_sync_files"].keys()),
            "last_sync_time": self.sync_config["last_sync_time"],
            "next_sync_time": next_sync.isoformat() if next_sync else None,
            "last_sync_results": self.last_sync_results,
            "thread_running": self.sync_thread and self.sync_thread.is_alive()
        }
    
    def test_sync_connection(self) -> Dict:
        """Test if Google Drive connection is working"""
        try:
            success, message = self.google_drive.test_connection()
            return {
                "success": success,
                "message": message,
                "files_configured": len(self.sync_config["auto_sync_files"])
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "files_configured": 0
            }

# Global scheduler instance
_scheduler = None

def get_scheduler() -> SyncScheduler:
    """Get the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SyncScheduler()
    return _scheduler

def main():
    """Demo the sync scheduler"""
    print("⏰ Google Drive Sync Scheduler")
    print("=" * 50)
    
    scheduler = SyncScheduler()
    
    # Test connection
    print("🔗 Testing Google Drive connection...")
    test_result = scheduler.test_sync_connection()
    print(f"   {test_result}")
    
    # Show current status
    status = scheduler.get_sync_status()
    print(f"\n📊 Current Status:")
    print(f"   Enabled: {status['enabled']}")
    print(f"   Interval: {status['interval_hours']} hours")
    print(f"   Connected files: {status['connected_files']}")
    print(f"   Last sync: {status['last_sync_time']}")
    print(f"   Thread running: {status['thread_running']}")
    
    if not test_result["success"]:
        print("\n❌ Google Drive connection failed")
        print("   Set up Google Drive integration first")
        return
    
    # Example: Set up auto-sync (commented out for demo)
    # scheduler.set_auto_sync_files({
    #     "inventory": "https://docs.google.com/spreadsheets/d/YOUR_INVENTORY_ID",
    #     "usage": "https://docs.google.com/spreadsheets/d/YOUR_USAGE_ID"
    # })
    # scheduler.enable_auto_sync(interval_hours=6)  # Sync every 6 hours
    
    print("\n💡 To enable auto-sync:")
    print("   1. Set up your Google Drive files")
    print("   2. Call scheduler.set_auto_sync_files(file_urls)")
    print("   3. Call scheduler.enable_auto_sync(interval_hours=24)")

if __name__ == "__main__":
    main()