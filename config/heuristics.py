"""
POCKET WATCHING AI: CORE HEURISTICS
Music industry specific rates and rules
"""

# 1. STREAMING PAYOUT RATES (Per Stream, USD)
STREAMING_RATES = {
    "spotify_premium_us_uk": {"low": 0.004, "high": 0.006},
    "spotify_premium_cee": {"low": 0.0015, "high": 0.003},
    "apple_music_us_uk": {"low": 0.007, "high": 0.008},
    "apple_music_cee": {"low": 0.004, "high": 0.006},
    "youtube_music_premium_us_uk": {"low": 0.007, "high": 0.014},
    "youtube_music_premium_cee": {"low": 0.004, "high": 0.007},
    "youtube_standard_ads": {"low": 0.001, "high": 0.002},
    "spotify_ad_supported": {"low": 0.001, "high": 0.002},
    "global_blended_average": 0.0045
}

# 2. OWNERSHIP SPLITS (Percentage artist keeps)
OWNERSHIP_SPLITS = {
    "owns_masters_and_publishing": {"low": 0.80, "high": 0.90},
    "owns_masters_splits_publishing": {"low": 0.70, "high": 0.85},
    "major_label_standard": {"low": 0.15, "high": 0.20},
    "deal_360": {
        "master_revenue": {"low": 0.15, "high": 0.20},
        "touring_take": {"low": 0.10, "high": 0.20},
        "merch_take": {"low": 0.10, "high": 0.20},
        "endorsement_take": {"low": 0.10, "high": 0.20}
    }
}

# 3. CATALOG VALUATION MULTIPLES
CATALOG_VALUATION = {
    "multiple_range": {"low": 15, "high": 20},
    "note": "Annual net royalties × multiple = catalog value",
    "no_ownership_value": 0
}

# 4. TOURING & LIVE SHOWS
TOURING = {
    "arena_gross_per_night": {"low": 1500000, "high": 2500000},
    "stadium_gross_per_night": {"low": 10000000, "high": 15000000},
    "artist_net_percentage": {"low": 0.35, "high": 0.45},
    "vip_upgrade_percentage": 0.05,
    "vip_extra_revenue_range": {"low": 500000, "high": 2000000},
    "merch_purchase_percentage": 0.30,
    "merch_spend_range": {"low": 50, "high": 100},
    "merch_profit_margin": 0.50
}

# 5. PHYSICAL MEDIA
PHYSICAL_MEDIA = {
    "independent_colored_vinyl_appreciation": {"low": 5, "high": 10},
    "major_label_black_vinyl_resale_max": {"low": 50, "high": 100},
    "d2c_artist_profit_percentage": {"low": 0.70, "high": 0.90},
    "major_label_artist_merch_percentage": {"low": 0.10, "high": 0.20}
}

# 6. COPYRIGHT TERMINATION (35-Year Rule)
COPYRIGHT_TERMINATION = {
    "rule": "Artists can reclaim masters 35 years after release",
    "key_dates": {
        "Nas - Illmatic": 2029,
        "Nas - It Was Written": 2031,
        "Nas - Stillmatic": 2036,
        "Wu-Tang - Enter the Wu-Tang": 2028,
        "Slick Rick - Great Adventures": "Already past 35 years"
    },
    "impact": "Reclaiming masters massively increases net worth"
}

# 7. REGIONAL WEALTH MULTIPLIERS
REGIONAL_MULTIPLIERS = {
    "us_uk_canada_australia": {"value": 5, "note": "5-10x more valuable fan"},
    "central_europe_premium": {"low": 0.005, "high": 0.007},
    "brazil_premium": {"low": 0.001, "high": 0.003},
    "developing_markets": {"value": 1, "note": "Base value"}
}

# 8. WEALTH INDICATORS
WEALTH_INDICATORS = {
    "wealthy_signals": [
        "owns_masters",
        "owns_real_estate",
        "owns_stocks",
        "owns_businesses",
        "multiple_revenue_streams"
    ],
    "rich_but_not_wealthy_signals": [
        "high_income",
        "high_spending",
        "no_ownership",
        "renting_assets",
        "flashy_lifestyle"
    ],
    "broke_signals": [
        "renting_cars",
        "pawning_jewelry",
        "evictions",
        "negative_net_worth",
        "loud_flexing_on_social_media"
    ],
    "key_insight": "Loud flexing often correlates with low liquid cash"
}

# 9. YOUTUBE ECONOMICS
YOUTUBE_ECONOMICS = {
    "rpm_hiphop_commentary": {"low": 4, "high": 8},
    "rpm_entertainment_vlogs": {"low": 2, "high": 5},
    "rpm_finance_business": {"low": 10, "high": 20},
    "sponsorship_per_dedicated_read": {"low": 1500, "high": 3000},
    "membership_price_range": {"low": 5, "high": 10},
    "guest_split_percentage": {"low": 0.40, "high": 0.50}
}

# 10. QUICK ESTIMATION FUNCTION
def quick_estimate(total_streams, ownership_percentage, blend_rate=None):
    """Quick net worth estimation"""
    if blend_rate is None:
        blend_rate = STREAMING_RATES["global_blended_average"]
    
    annual_income = total_streams * blend_rate * ownership_percentage
    
    if ownership_percentage > 0.5:
        catalog_multiple = 15
    else:
        catalog_multiple = 0
    
    catalog_value = annual_income * catalog_multiple
    estimated_net_worth = catalog_value
    
    return {
        "annual_income": annual_income,
        "catalog_value": catalog_value,
        "estimated_net_worth": estimated_net_worth,
        "assumptions": {
            "blend_rate": blend_rate,
            "ownership_percentage": ownership_percentage,
            "catalog_multiple": catalog_multiple
        }
    }

# ARTIST TYPE CLASSIFICATIONS
ARTIST_TYPES = {
    "wealthy": {
        "description": "Owns masters + real estate + stocks",
        "examples": ["J. Cole", "Jay-Z", "Nas"],
        "net_worth_range": [50000000, 2500000000]
    },
    "rich_not_wealthy": {
        "description": "High income + high spending + no ownership",
        "examples": ["Many mainstream rappers"],
        "net_worth_range": [5000000, 30000000]
    },
    "broke": {
        "description": "Renting cars, pawning jewelry, evictions",
        "examples": ["Papoose"],
        "net_worth_range": [-500000, 1000000]
    }
}