#!/usr/bin/env python3
"""
API Logging Test Script
Direct test of Korean Investment API logging functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brokers.korea_investment.ki_api import KoreaInvestAPI
from config.config import CONFIG

def test_api_logging():
    """Test the Korean Investment API logging functionality"""
    print("=== API Logging Test ===")
    
    # Initialize the API client
    api = KoreaInvestAPI(CONFIG)
    
    print(f"Testing account balance API call...")
    
    # Make a real API call that should trigger logging
    try:
        total_value, positions_df = api.get_acct_balance()
        print(f"API call completed successfully!")
        print(f"Total value: {total_value}")
        print(f"Positions: {len(positions_df)} records")
        
        # Check if log files were created
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.startswith("API_")]
            print(f"\nAPI log files found: {log_files}")
            
            if log_files:
                # Show contents of the most recent log file
                latest_log = max(log_files)
                log_path = os.path.join(logs_dir, latest_log)
                print(f"\nContents of {latest_log}:")
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content[:2000] + "..." if len(content) > 2000 else content)
            else:
                print("No API log files were created!")
        else:
            print("Logs directory doesn't exist!")
            
    except Exception as e:
        print(f"API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_logging()