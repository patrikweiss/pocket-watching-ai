"""
DATA COLLECTION
===============
- YouTube: channel stats, revenue estimation (filters Topic channels)
- Deezer: fan counts, albums, top tracks
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')


# ============================================================
# YOUTUBE
# ============================================================
# Load API keys from .env
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')


# ============================================================
# MAIN FUNCTION: Get channel data
# ============================================================
def get_channel_data(channel_name):
    """
    Search YouTube for a channel by name and return its stats.

    Strategy:
    1. Fetch top 10 search results
    2. Filter out "Topic" channels (auto-generated music channels)
    3. From remaining candidates, pick the one with the most subscribers
    4. Give a bonus to exact-name matches (e.g., "Lil Durk" vs "Lil Durk Official")

    Returns dict with name, subscribers, views, videos — or None if not found.
    """
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY missing from .env")
        return None

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # ---- Step 1: Search (get 10 results instead of 1) ----
    try:
        search_response = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id,snippet',
            maxResults=10
        ).execute()
    except Exception as e:
        print(f"  YouTube search error: {e}")
        return None

    if not search_response.get('items'):
        print(f"  No results for '{channel_name}'")
        return None

    # ---- Step 2: Filter out Topic channels ----
    candidates = [
        item for item in search_response['items']
        if ' - Topic' not in item['snippet']['title']
    ]

    if not candidates:
        print(f"  Only Topic channels found for '{channel_name}'")
        return None

    # ---- Step 3: Fetch stats for each candidate, pick best ----
    best = None
    best_score = -1

    for item in candidates:
        channel_id = item['id']['channelId']
        title = item['snippet']['title']

        try:
            stats_response = youtube.channels().list(
                id=channel_id,
                part='statistics,snippet'
            ).execute()

            if not stats_response.get('items'):
                continue

            stats = stats_response['items'][0]['statistics']
            subs = int(stats.get('subscriberCount', 0))

            # Exact match gets a 1.5x score bonus
            is_exact = title.lower().strip() == channel_name.lower().strip()
            score = subs * (1.5 if is_exact else 1.0)

            if score > best_score:
                best_score = score
                best = {
                    'channel_id': channel_id,
                    'title': title,
                    'stats': stats,
                    'snippet': stats_response['items'][0]['snippet']
                }
        except Exception:
            continue

    if not best:
        return None

    # ---- Step 4: Return clean channel data ----
    return {
        'name': best['title'],
        'channel_id': best['channel_id'],
        'description': best['snippet'].get('description', '')[:200],
        'subscribers': int(best['stats'].get('subscriberCount', 0)),
        'total_views': int(best['stats'].get('viewCount', 0)),
        'total_videos': int(best['stats'].get('videoCount', 0)),
        'created_at': best['snippet'].get('publishedAt', ''),
        'country': best['snippet'].get('country', 'Unknown'),
        'collected_at': datetime.now().isoformat()
    }


# ============================================================
# REVENUE ESTIMATION
# ============================================================
def estimate_youtube_revenue(channel_data):
    """Estimate YouTube revenue using industry heuristics."""
    total_views = channel_data['total_views']

    # RPM range for hip-hop content
    rpm_low, rpm_high = 4, 8

    # Lifetime revenue
    lifetime_low = (total_views / 1000) * rpm_low
    lifetime_high = (total_views / 1000) * rpm_high

    # Monthly views (~3% of lifetime is recent activity)
    monthly_views = total_views * 0.03
    monthly_low = (monthly_views / 1000) * rpm_low
    monthly_high = (monthly_views / 1000) * rpm_high

    return {
        'total_revenue_low': lifetime_low,
        'total_revenue_high': lifetime_high,
        'monthly_views_estimated': monthly_views,
        'monthly_revenue_low': monthly_low,
        'monthly_revenue_high': monthly_high,
        'rpm_range_used': [rpm_low, rpm_high]
    }


# ============================================================
# SAVE
# ============================================================
def save_channel_data(channel_data, revenue_estimate):
    """Save channel data + revenue estimate to JSON file."""
    if not channel_data:
        return None

    full_data = {
        'channel': channel_data,
        'revenue_estimates': revenue_estimate,
        'saved_at': datetime.now().isoformat()
    }

    filename = channel_data['name'].lower().replace(' ', '_').replace('/', '_')
    filepath = f"data/raw/youtube_{filename}_{datetime.now().strftime('%Y%m%d')}.json"

    os.makedirs('data/raw', exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=2)

    return filepath


# ============================================================
# TEST / STANDALONE RUN
# ============================================================


# ============================================================
# DEEZER
# ============================================================
# Known correct Deezer IDs (avoids fake/duplicate profiles with same name)
KNOWN_DEEZER_IDS = {
    "Drake": 246791,
    "Westside Gunn": 8323782,
    "J. Cole": 339209,
    "Kendrick Lamar": 525046,
    "Billy Woods": 254849,
    "Kanye West": 15885,
    "Jay-Z": 13628,
    "Nas": 13619,
    "Eminem": 13,
    "Future": 2308081,
    "21 Savage": 11319122,
    "Lil Baby": 15072132,
    "Travis Scott": 1052322,
    "Tyler, The Creator": 1692564,
    "NBA YoungBoy": 12582250,
}


class DeezerCollector:
    """Collects artist data from Deezer's free public API"""

    def __init__(self):
        self.base_url = "https://api.deezer.com"
        print("✓ Deezer collector ready (no key needed)")

    def search_artist(self, name):
        """Search for an artist by name (fallback if no known ID)"""
        try:
            response = requests.get(
                f"{self.base_url}/search/artist",
                params={'q': name, 'limit': 5},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    # Return the one with most fans (usually the real one)
                    sorted_artists = sorted(
                        data['data'],
                        key=lambda x: x.get('nb_fan', 0),
                        reverse=True
                    )
                    return sorted_artists[0]
        except Exception as e:
            print(f"  Search error: {e}")
        return None

    def get_artist_data(self, name, artist_id=None):
        """Get artist data - uses known ID if available, otherwise searches"""
        print(f"\nSearching Deezer for: {name}")

        # Use known ID if we have one (reliable)
        if artist_id is None:
            artist_id = KNOWN_DEEZER_IDS.get(name)

        if artist_id:
            print(f"  Using known ID: {artist_id}")
        else:
            artist = self.search_artist(name)
            if not artist:
                print(f"  ✗ Not found")
                return None
            artist_id = artist['id']
            print(f"  Found via search: {artist_id}")

        try:
            # Full artist info
            response = requests.get(
                f"{self.base_url}/artist/{artist_id}",
                timeout=10
            )
            if response.status_code != 200:
                return None
            full_info = response.json()

            # Top tracks
            top_response = requests.get(
                f"{self.base_url}/artist/{artist_id}/top",
                params={'limit': 5},
                timeout=10
            )
            top_tracks = top_response.json().get('data', []) if top_response.status_code == 200 else []

            artist_data = {
                'name': full_info.get('name', name),
                'deezer_id': artist_id,
                'fans': full_info.get('nb_fan', 0),
                'albums': full_info.get('nb_album', 0),
                'top_tracks': [
                    {'title': t.get('title', ''), 'rank': t.get('rank', 0)}
                    for t in top_tracks
                ],
                'url': full_info.get('link', ''),
                'collected_at': datetime.now().isoformat()
            }
            return artist_data

        except Exception as e:
            print(f"  Error: {e}")
            return None

    def save_artist_data(self, artist_data):
        """Save to JSON file"""
        if not artist_data:
            return None
        filename = artist_data['name'].lower().replace(' ', '_').replace('/', '_')
        filepath = f"data/raw/deezer_{filename}_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs('data/raw', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(artist_data, f, indent=2)
        print(f"  ✓ Saved to {filepath}")
        return filepath


def test():
    """Test with some artists"""
    collector = DeezerCollector()
    test_artists = ["J. Cole", "Kendrick Lamar", "Drake", "Billy Woods", "Westside Gunn"]

    for artist_name in test_artists:
        data = collector.get_artist_data(artist_name)
        if data:
            print(f"\n  🎵 {data['name']}")
            print(f"     Fans: {data['fans']:,}")
            print(f"     Albums: {data['albums']}")
            print(f"     URL: {data['url']}")
            collector.save_artist_data(data)
        time.sleep(0.5)

    print("\n✅ Deezer collection complete!")


