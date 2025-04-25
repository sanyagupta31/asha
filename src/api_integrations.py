import os
import requests
from typing import List, Dict

def fetch_live_jobs(query: str, location: str = "") -> List[Dict]:
    """
    Fetch real-time jobs from Adzuna API.
    Returns a list of job dicts.
    """
    base_url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
    params = {
        "app_id": os.getenv("ADZUNA_APP_ID"),
        "app_key": os.getenv("ADZUNA_APP_KEY"),
        "what": query,
        "results_per_page": 5
    }
    if location:
        params["where"] = location

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"Adzuna API error: {str(e)}")
        return []

def fetch_live_events(query: str = "women career", city: str = "", size: int = 3) -> List[Dict]:
    """
    Fetch live events from Ticketmaster Discovery API.
    Returns a list of event dicts.
    """
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        print("Ticketmaster API key is missing in .env")
        return []

    base_url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "keyword": query,
        "size": size,
        "sort": "date,asc"
    }
    if city:
        params["city"] = city

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        events = data.get("_embedded", {}).get("events", [])
        result = []
        for event in events:
            # Venue extraction (handle multiple venues or missing)
            venue = "Venue not specified"
            if "_embedded" in event and "venues" in event["_embedded"]:
                venues = event["_embedded"]["venues"]
                if isinstance(venues, list) and len(venues) > 0:
                    venue = venues[0].get("name", venue)
            # Description: prefer 'info', fallback to 'pleaseNote'
            description = event.get("info", "") or event.get("pleaseNote", "")
            result.append({
                "name": event.get("name", "Untitled Event"),
                "description": description,
                "start": event.get("dates", {}).get("start", {}).get("localDate", "Date not available"),
                "url": event.get("url", ""),
                "venue": venue
            })
        return result
    except Exception as e:
        print(f"Ticketmaster API error: {str(e)}")
        return []

if __name__ == "__main__":
    print("Testing Adzuna jobs API:")
    jobs = fetch_live_jobs("data analyst", "London")
    for job in jobs:
        print(f"{job.get('title')} at {job.get('company', {}).get('display_name', 'Unknown Company')} in {job.get('location', {}).get('display_name', 'Unknown')}")

    print("\nTesting Ticketmaster events API:")
    events = fetch_live_events("women in tech", city="New York")
    for event in events:
        print(f"{event['name']} at {event['venue']} on {event['start']}")
