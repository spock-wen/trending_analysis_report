#!/usr/bin/env python3
"""Collect Hugging Face trending papers for June 2026, rank by upvotes, output top N.
Uses web_extract for network access since urllib is blocked."""

import json
import sys
import time
from datetime import date, timedelta

def main():
    year = 2026
    month = 6
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    # Instead of making actual API calls (which require network), 
    # we'll output a list of dates for the caller to fetch via web_extract.
    start_date = date(year, month, 1)
    end_date = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, month, 31)
    
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    
    print(json.dumps({"dates": dates, "total": len(dates)}))

if __name__ == "__main__":
    main()
