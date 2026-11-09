"""
POCKET WATCHING AI - CORE ESTIMATION RULES
Based on the blueprint methodology
"""

# STEP 1: INCOME STREAMS BY ENTITY TYPE
INCOME_STREAMS = {
    "musician": [
        "streaming_royalties",
        "physical_sales",
        "touring",
        "merchandise",
        "features_collabs",
        "publishing_songwriting",
        "brand_endorsements",
        "acting_media",
        "business_ventures"
    ],
    "athlete": [
        "salary_contract",
        "signing_bonus",
        "endorsements",
        "performance_bonuses",
        "appearance_fees",
        "business_investments",
        "real_estate",
        "media_deals"
    ],
    "youtuber_influencer": [
        "ad_revenue",
        "sponsorships",
        "merchandise",
        "affiliate_marketing",
        "memberships_patreon",
        "licensing_syndication",
        "public_appearances"
    ],
    "actor": [
        "film_tv_salary",
        "residuals_royalties",
        "endorsements",
        "production_equity",
        "streaming_deals"
    ],
    "public_figure": [
        "book_deals",
        "speaking_engagements",
        "investments_stocks",
        "real_estate",
        "business_ownership"
    ]
}

# STEP 2: OWNERSHIP & DEAL STRUCTURE
OWNERSHIP_RULES = {
    "musician": {
        "owns_masters_publishing": "Keeps 80-90% of streaming revenue",
        "owns_masters_only": "Keeps 70-85% of gross",
        "major_label_standard": "Gets 15-20% of master revenue",
        "deal_360": "Label takes 10-20% of ALL revenue streams",
        "independent": "Keeps 70-90% of merch/vinyl profits"
    },
    "athlete": {
        "guaranteed_contract": "Money is locked in",
        "incentive_based": "Only paid if performance targets met",
        "agent_fees": "10-15% typically"
    },
    "youtuber": {
        "owns_channel": "Keeps 100% of ad revenue",
        "network_deal": "Network takes 10-30% cut",
        "rpm_varies": "Depends on niche and audience"
    },
    "actor": {
        "backend_points": "Percentage of movie profits",
        "production_equity": "Ownership in production company",
        "union_residuals": "SAG-AFTRA residual payments"
    }
}

# STEP 4: LIABILITY INDICATORS
RED_FLAGS = [
    "gambling_debts",
    "legal_fees_lawsuits",
    "child_support_alimony",
    "tax_debts_irs",
    "renting_luxury_items",
    "pawning_assets",
    "constant_social_media_flexing"
]

GREEN_FLAGS = [
    "owns_masters_publishing",
    "owns_real_estate",
    "owns_businesses",
    "stock_market_investments",
    "low_profile_lifestyle",
    "long_term_brand_building"
]

# STEP 5: HIDDEN ASSET VALUATION
HIDDEN_ASSETS = {
    "music_catalog": "Annual net royalties × 15-20x",
    "business_equity": "DJ Vlad: VladTV = $30-50M",
    "stock_investments": "Nas: Coinbase early = $40M+",
    "real_estate": "Jay-Z/Beyonce: $300M+ in property"
}

# STEP 6: TAXES & FEES
TEAM_FEES = {
    "management": 0.10,
    "lawyers": 0.05,
    "business_managers": 0.05
}

TAX_RATES = {
    "federal_top": 0.37,
    "state_avg": 0.05,
    "fica": 0.0765,
    "total_effective": 0.45
}

# STEP 7: OUTPUT FORMAT
OUTPUT_FORMAT = {
    "name": "string",
    "primary_income_streams": "list",
    "ownership_status": "string",
    "estimated_annual_income": "range",
    "estimated_asset_breakdown": "dict",
    "estimated_liabilities": "range",
    "estimated_net_worth_range": "low/mid/high",
    "reasoning": "text"
}

# STEP 8: GOLDEN RULES
GOLDEN_RULES = [
    "Ownership > Income",
    "Gross ≠ Net",
    "Quiet wealth > Loud flexing",
    "Hidden assets matter",
    "Regional payouts matter",
    "Spending habits matter",
    "Always use ranges",
    "Public data only",
    "Use hedging language",
    "Think like a forensic accountant, not a gossip blog"
]

# NET WORTH FORMULA
def calculate_net_worth(gross_income, team_fees_pct, tax_rate, assets, liabilities):
    """
    Gross Income - Team Fees = Pre-Tax Income
    Pre-Tax Income - Taxes = Post-Tax Income
    Post-Tax Income + Assets - Liabilities = Net Worth
    """
    team_fees = gross_income * team_fees_pct
    pre_tax_income = gross_income - team_fees
    taxes = pre_tax_income * tax_rate
    post_tax_income = pre_tax_income - taxes
    net_worth = post_tax_income + assets - liabilities
    
    return {
        'gross_income': gross_income,
        'team_fees': team_fees,
        'pre_tax_income': pre_tax_income,
        'taxes': taxes,
        'post_tax_income': post_tax_income,
        'net_worth': net_worth
    }