"""
CALCULATION ENGINES
===================
- FullEngine: full breakdown for known people (from database)
- PatternEstimatorV2: estimate unknown people via similarity matching
- RefinementEngine: apply user facts to adjust estimates
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ============================================================
# FULL ENGINE
# ============================================================
from config.heuristics import OWNERSHIP_SPLITS, CATALOG_VALUATION, TOURING, YOUTUBE_ECONOMICS
from config.estimation_rules import TEAM_FEES, TAX_RATES


class FullEngine:
    """Complete wealth calculation engine with auto-inference"""

    def __init__(self):
        self.manual_db = self._load_manual_knowledge()
        self.enhanced_db = self._enhance_all_people()

    def _load_manual_knowledge(self):
        filepath = 'data/manual_estimates/manual_knowledge.json'
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('people', [])
        print(f"WARNING: Manual knowledge file not found at {filepath}")
        return []

    def _infer_deal_type(self, person):
        label = person.get('label_situation', '').lower()
        if any(word in label for word in ['owns', 'own', 'independent', 'studioz', 'records']):
            return 'independent_ownership'
        elif 'distribution' in label:
            return 'distribution_deal'
        elif '360' in label:
            return 'deal_360'
        elif any(word in label for word in ['major', 'def jam', 'interscope', 'atlantic', 'republic']):
            return 'major_label'
        else:
            return 'unknown'

    def _infer_touring_status(self, person):
        entity_type = person.get('entity_type', 'unknown')
        nw_mid = person.get('manual_net_worth', [0, 0, 0])[1]
        if entity_type in ['rapper', 'musician']:
            if nw_mid > 100000000:
                return 'active_arena'
            elif nw_mid > 10000000:
                return 'active_theater'
            elif nw_mid > 1000000:
                return 'active_club'
            else:
                return 'inactive'
        elif entity_type == 'producer':
            return 'dj_sets_only'
        else:
            return 'not_applicable'

    def _infer_streaming_power(self, person):
        nw_mid = person.get('manual_net_worth', [0, 0, 0])[1]
        if nw_mid > 100000000:
            return 'high'
        elif nw_mid > 10000000:
            return 'mid'
        elif nw_mid > 1000000:
            return 'low_mid'
        else:
            return 'low'

    def _infer_career_stage(self, person):
        entity_type = person.get('entity_type', 'unknown')
        nw_mid = person.get('manual_net_worth', [0, 0, 0])[1]
        if entity_type in ['rapper', 'musician']:
            if nw_mid > 500000000:
                return 'legacy_icon'
            elif nw_mid > 100000000:
                return 'peak'
            elif nw_mid > 10000000:
                return 'established'
            else:
                return 'rising'
        elif entity_type == 'producer':
            if nw_mid > 50000000:
                return 'legendary'
            elif nw_mid > 10000000:
                return 'established'
            else:
                return 'working'
        else:
            return 'active'

    def _infer_ownership_tier(self, person):
        owns_masters = person.get('owns_masters', False)
        owns_publishing = person.get('owns_publishing', False)
        label = person.get('label_situation', '').lower()

        has_label_empire = any(
            word in label
            for word in ['roc nation', 'dreamville', 'ovo', 'aftermath',
                         'bad boy', 'mass appeal', 'freebandz', 'griselda',
                         'backwoodz', 'alc records']
        )

        if owns_masters and owns_publishing and has_label_empire:
            return 'owns_everything'
        elif owns_masters and owns_publishing:
            return 'owns_most'
        elif owns_masters or owns_publishing:
            return 'partial_ownership'
        elif owns_publishing:
            return 'publishing_only'
        else:
            return 'no_ownership'

    def _enhance_person(self, person):
        enhanced = person.copy()
        enhanced['deal_type_inferred'] = self._infer_deal_type(person)
        enhanced['touring_status_inferred'] = self._infer_touring_status(person)
        enhanced['streaming_power_inferred'] = self._infer_streaming_power(person)
        enhanced['career_stage_inferred'] = self._infer_career_stage(person)
        enhanced['ownership_tier_inferred'] = self._infer_ownership_tier(person)
        return enhanced

    def _enhance_all_people(self):
        return [self._enhance_person(person) for person in self.manual_db]

    def _get_ownership_percentage(self, tier):
        tier_pct = {
            'owns_everything': 0.85,
            'owns_most': 0.75,
            'partial_ownership': 0.50,
            'publishing_only': 0.20,
            'no_ownership': 0.15
        }
        return tier_pct.get(tier, 0.20)

    def _estimate_annual_income(self, person):
        entity_type = person.get('entity_type', 'unknown')
        nw_mid = person.get('manual_net_worth', [0, 0, 0])[1]
        career_stage = person.get('career_stage_inferred', 'active')

        income_ratios = {
            'rapper': {
                'legacy_icon': 0.06,
                'peak': 0.08,
                'established': 0.10,
                'rising': 0.12
            },
            'producer': {
                'legendary': 0.08,
                'established': 0.15,
                'working': 0.20
            },
            'media_personality': {
                'active': 0.20,
                'established': 0.25
            },
            'boxer': {
                'active': 0.25,
                'retired': 0.10
            }
        }

        type_ratios = income_ratios.get(entity_type, {'active': 0.10})
        ratio = type_ratios.get(career_stage, 0.10)
        annual_gross = nw_mid * ratio

        min_incomes = {
            'producer': 150000,
            'rapper': 50000,
            'media_personality': 50000,
            'boxer': 100000
        }
        min_income = min_incomes.get(entity_type, 50000)
        return max(annual_gross, min_income)

    def _split_income_by_type(self, annual_gross, entity_type, touring_status):
        if entity_type == 'rapper':
            streaming = annual_gross * 0.30
            touring = annual_gross * 0.40 if touring_status.startswith('active') else annual_gross * 0.10
            merch = annual_gross * 0.15
            other = annual_gross * 0.15
        elif entity_type == 'producer':
            streaming = annual_gross * 0.40
            touring = annual_gross * 0.10
            merch = annual_gross * 0.10
            other = annual_gross * 0.40
        elif entity_type == 'media_personality':
            streaming = annual_gross * 0.50
            touring = 0
            merch = annual_gross * 0.20
            other = annual_gross * 0.30
        elif entity_type == 'boxer':
            streaming = 0
            touring = 0
            merch = annual_gross * 0.10
            other = annual_gross * 0.90
        else:
            streaming = annual_gross * 0.40
            touring = annual_gross * 0.30
            merch = annual_gross * 0.15
            other = annual_gross * 0.15

        return {
            'streaming': streaming,
            'touring': touring,
            'merch': merch,
            'other': other
        }

    def _estimate_catalog_value(self, streaming_income, ownership_tier, entity_type):
        if entity_type not in ['rapper', 'producer']:
            return 0
        if ownership_tier in ['owns_everything', 'owns_most']:
            catalog_multiple = 15
        elif ownership_tier == 'partial_ownership':
            catalog_multiple = 5
        else:
            catalog_multiple = 3
        return streaming_income * catalog_multiple

    def calculate_full_breakdown(self, person_name):
        person = None
        name_normalized = person_name.lower().replace(' ', '').replace('-', '').replace('.', '')

        for p in self.enhanced_db:
            p_normalized = p['name'].lower().replace(' ', '').replace('-', '').replace('.', '')
            if p_normalized in name_normalized or name_normalized in p_normalized:
                person = p
                break

        if not person:
            return {'error': f'{person_name} not found in database'}

        nw_range = person['manual_net_worth']
        entity_type = person['entity_type']
        ownership_tier = person['ownership_tier_inferred']
        touring_status = person['touring_status_inferred']
        career_stage = person['career_stage_inferred']
        key_assets = person.get('key_assets', {})

        annual_gross = self._estimate_annual_income(person)
        annual_net = annual_gross * 0.55
        ownership_pct = self._get_ownership_percentage(ownership_tier)

        income_split = self._split_income_by_type(annual_gross, entity_type, touring_status)

        total_known_assets = sum(key_assets.values())
        catalog_value = self._estimate_catalog_value(
            income_split['streaming'], ownership_tier, entity_type
        )

        nw_mid = nw_range[1]
        estimated_other_assets = max(0, nw_mid - total_known_assets)

        breakdown = {
            'name': person['name'],
            'entity_type': entity_type,
            'ownership_tier': ownership_tier,
            'ownership_percentage': f"{ownership_pct*100:.0f}%",
            'deal_type': person['deal_type_inferred'],
            'touring_status': touring_status,
            'streaming_power': person['streaming_power_inferred'],
            'career_stage': career_stage,
            'net_worth_range': {
                'low': nw_range[0],
                'mid': nw_range[1],
                'high': nw_range[2]
            },
            'income_analysis': {
                'estimated_annual_gross': annual_gross,
                'estimated_annual_net': annual_net,
                'streaming_estimate': income_split['streaming'],
                'touring_estimate': income_split['touring'],
                'merch_estimate': income_split['merch'],
                'other_income': income_split['other']
            },
            'asset_breakdown': {
                'known_assets': key_assets,
                'total_known_assets': total_known_assets,
                'catalog_value_estimated': catalog_value,
                'estimated_other_assets': estimated_other_assets,
                'note': 'All values included in net worth. No double counting.'
            },
            'ownership_status': {
                'owns_masters': person.get('owns_masters', False),
                'owns_publishing': person.get('owns_publishing', False)
            },
            'label_situation': person.get('label_situation', 'Unknown'),
            'notes': person.get('notes', ''),
            'confidence_score': person.get('confidence', 7)
        }
        return breakdown

    def generate_reasoning(self, breakdown):
        if 'error' in breakdown:
            return breakdown['error']

        return f"""
        {breakdown['name']} ({breakdown['entity_type']}):

        Ownership & Deal Structure:
        - Ownership Tier: {breakdown['ownership_tier']}
        - Keeps: {breakdown['ownership_percentage']} of revenue
        - Deal Type: {breakdown['deal_type']}
        - Touring: {breakdown['touring_status']}
        - Career Stage: {breakdown['career_stage']}

        Income Analysis (Annual):
        - Gross: ${breakdown['income_analysis']['estimated_annual_gross']/1000000:.2f}M
        - Streaming: ${breakdown['income_analysis']['streaming_estimate']/1000000:.2f}M
        - Touring: ${breakdown['income_analysis']['touring_estimate']/1000000:.2f}M
        - Merch: ${breakdown['income_analysis']['merch_estimate']/1000000:.2f}M
        - Other: ${breakdown['income_analysis']['other_income']/1000000:.2f}M

        Assets (Included in Net Worth):
        - Known Assets: ${breakdown['asset_breakdown']['total_known_assets']/1000000:.1f}M
        - Catalog Value: ${breakdown['asset_breakdown']['catalog_value_estimated']/1000000:.1f}M

        Net Worth: ${breakdown['net_worth_range']['low']/1000000:.1f}M - ${breakdown['net_worth_range']['high']/1000000:.1f}M
        Most Likely: ${breakdown['net_worth_range']['mid']/1000000:.1f}M

        Note: Estimates based on public data and domain heuristics.
        """

    def generate_explanation(self, breakdown):
        if 'error' in breakdown:
            return breakdown['error']

        name = breakdown.get('name', 'This person')
        entity_type = breakdown.get('entity_type', 'unknown')
        ownership = breakdown.get('ownership_tier', 'unknown')
        stage = breakdown.get('career_stage', 'unknown')
        income = breakdown.get('income_analysis', {})
        assets = breakdown.get('asset_breakdown', {})
        nw = breakdown.get('net_worth_range', {})
        ownership_status = breakdown.get('ownership_status', {})

        lines = []
        lines.append(f"### Why {name} is estimated at ${nw.get('mid', 0)/1e6:.0f}M")
        lines.append("")

        annual = income.get('estimated_annual_gross', 0)
        if annual > 0:
            lines.append(f"**Annual income:** ~${annual/1e6:.1f}M per year gross")
            lines.append("")
            lines.append("Breakdown:")
            lines.append(f"- Streaming: ${income.get('streaming_estimate', 0)/1e6:.1f}M")
            lines.append(f"- Touring: ${income.get('touring_estimate', 0)/1e6:.1f}M")
            lines.append(f"- Merch: ${income.get('merch_estimate', 0)/1e6:.1f}M")
            lines.append(f"- Other: ${income.get('other_income', 0)/1e6:.1f}M")
            lines.append("")

        ownership_text = {
            'owns_everything': "Keeps ~85% of revenue (owns masters + publishing + label)",
            'owns_most': "Keeps ~75% of revenue (owns masters + publishing)",
            'partial_ownership': "Keeps ~50% of revenue (partial master ownership)",
            'publishing_only': "Keeps ~20% of revenue (publishing only)",
            'no_ownership': "Keeps ~15% of revenue (standard label deal)"
        }
        lines.append(f"**Ownership:** {ownership_text.get(ownership, ownership)}")
        lines.append("")

        lines.append("**Key factors:**")
        if ownership_status.get('owns_masters'):
            lines.append("- ✅ Owns masters (major wealth driver)")
        else:
            lines.append("- ⚠️ Does not own masters (limits long-term catalog value)")

        if ownership_status.get('owns_publishing'):
            lines.append("- ✅ Owns publishing (extra royalty stream)")

        label = breakdown.get('label_situation', '')
        if label and label != 'Unknown':
            lines.append(f"- Label situation: {label}")
        lines.append("")

        known = assets.get('total_known_assets', 0)
        catalog = assets.get('catalog_value_estimated', 0)
        if known > 0 or catalog > 0:
            lines.append("**Assets:**")
            if known > 0:
                lines.append(f"- Known assets: ${known/1e6:.1f}M")
            if catalog > 0:
                lines.append(f"- Catalog value: ${catalog/1e6:.1f}M")
            lines.append("")

        lines.append(f"**Career stage:** {stage}")
        lines.append("")

        notes = breakdown.get('notes', '')
        if notes:
            lines.append(f"**Notes:** {notes}")
            lines.append("")

        lines.append(f"**Estimated range:** \\${nw.get('low', 0)/1e6:.0f}M – \\${nw.get('high', 0)/1e6:.0f}M")
        lines.append("")
        lines.append("*Estimates based on public data and industry heuristics. Not financial advice.*")

        return "\n".join(lines)


# ============================================================
# PATTERN ESTIMATOR V2
# ============================================================
class PatternEstimatorV2:
    """
    Estimates unknown people by finding similar database entries.

    Approach:
    - Uses REAL YouTube subscriber/view counts (log-scale)
    - Computes similarity on log-scale subs + views
    - Weights DB people by similarity, averages their net worth
    - Applies ownership adjustment (default 0.5 = neutral, not worst-case)
    """

    def __init__(self):
        self.manual_db = self._load_manual_knowledge()
        self.ownership_tiers = {
            "owns_everything": 1.0,
            "owns_most": 0.6,
            "partial_ownership": 0.4,
            "publishing_only": 0.2,
            "no_ownership": 0.15,
        }

    def _load_manual_knowledge(self):
        filepath = 'data/manual_estimates/manual_knowledge.json'
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data.get('people', [])
        print(f"WARNING: Manual knowledge file not found at {filepath}")
        return []

    def get_people_by_type(self, entity_type):
        return [p for p in self.manual_db if p.get('entity_type') == entity_type]

    def _youtube_proxy_for_db_person(self, db_person):
        nw_mid = db_person.get('manual_net_worth', [0, 0, 0])[1]
        et = db_person.get('entity_type', 'unknown')

        subs_per_million = {
            'rapper': 60000,
            'singer': 60000,
            'producer': 20000,
            'media_personality': 100000,
            'boxer': 5000,
        }.get(et, 40000)

        est_subs = max(1000, nw_mid * subs_per_million / 1_000_000)
        est_views = est_subs * 500
        return est_subs, est_views

    def calculate_similarity(self, youtube_data, db_person):
        import math

        subs1 = max(1, youtube_data.get('subscribers', 0))
        views1 = max(1, youtube_data.get('total_views', 0))

        est_subs, est_views = self._youtube_proxy_for_db_person(db_person)
        subs2 = max(1, est_subs)
        views2 = max(1, est_views)

        subs_diff = abs(math.log10(subs1) - math.log10(subs2))
        views_diff = abs(math.log10(views1) - math.log10(views2))

        subs_similarity = max(0, 1 - subs_diff / 3)
        views_similarity = max(0, 1 - views_diff / 3)

        ownership_bonus = 0.1 if db_person.get('owns_masters') else 0.0

        similarity = (subs_similarity * 0.4) + (views_similarity * 0.5) + ownership_bonus
        return min(1.0, similarity), subs2, views2

    def estimate_new_person(self, name, youtube_data, entity_type=None, ownership_hint=None):
        if not entity_type:
            entity_type = self._detect_entity_type(youtube_data)

        people_of_type = self.get_people_by_type(entity_type)

        scored = []
        for person in people_of_type:
            sim, _, _ = self.calculate_similarity(youtube_data, person)
            scored.append({'person': person, 'similarity': sim})

        scored.sort(key=lambda x: x['similarity'], reverse=True)
        top = scored[:5]
        top = [s for s in top if s['similarity'] > 0.05]

        if not top:
            return {
                'error': 'No similar people found',
                'name': name,
                'entity_type': entity_type,
            }

        total_sim = sum(s['similarity'] for s in top)
        if total_sim == 0:
            return {
                'error': 'No meaningful similarity',
                'name': name,
                'entity_type': entity_type,
            }

        weighted_low = sum(s['person']['manual_net_worth'][0] * s['similarity'] / total_sim for s in top)
        weighted_mid = sum(s['person']['manual_net_worth'][1] * s['similarity'] / total_sim for s in top)
        weighted_high = sum(s['person']['manual_net_worth'][2] * s['similarity'] / total_sim for s in top)

        top_db_person = top[0]['person']
        est_subs_top, _ = self._youtube_proxy_for_db_person(top_db_person)
        actual_subs = youtube_data.get('subscribers', 0)
        if est_subs_top > 0 and actual_subs > 0:
            raw_ratio = actual_subs / est_subs_top
            subs_ratio = max(0.5, min(raw_ratio, 2.0))
        else:
            subs_ratio = 1.0

        weighted_low *= subs_ratio
        weighted_mid *= subs_ratio
        weighted_high *= subs_ratio

        if ownership_hint and ownership_hint in self.ownership_tiers:
            ownership_multiplier = self.ownership_tiers[ownership_hint]
        else:
            ownership_multiplier = 0.5

        weighted_low *= ownership_multiplier
        weighted_mid *= ownership_multiplier
        weighted_high *= ownership_multiplier

        best_similarity = top[0]['similarity']
        confidence = min(int(best_similarity * 8) + 1, 7)

        return {
            'name': name,
            'entity_type': entity_type,
            'net_worth_range': {
                'low': weighted_low,
                'mid': weighted_mid,
                'high': weighted_high,
            },
            'confidence_score': confidence,
            'similar_people': [
                {
                    'name': s['person']['name'],
                    'similarity': f"{s['similarity']*100:.0f}%",
                    'their_net_worth': s['person']['manual_net_worth'],
                }
                for s in top
            ],
            'ownership_tier_applied': ownership_hint or 'unknown_neutral',
            'note': 'Pattern-based estimate using top 5 similarity matches',
        }

    def estimate_or_lookup(self, name, youtube_data, entity_type=None, ownership_hint=None):
        name_normalized = name.lower().replace(' ', '').replace('-', '').replace('.', '')

        for person in self.manual_db:
            person_normalized = person['name'].lower().replace(' ', '').replace('-', '').replace('.', '')
            if person_normalized in name_normalized or name_normalized in person_normalized:
                return {
                    'source': 'manual_database',
                    'name': person['name'],
                    'entity_type': person['entity_type'],
                    'net_worth_range': {
                        'low': person['manual_net_worth'][0],
                        'mid': person['manual_net_worth'][1],
                        'high': person['manual_net_worth'][2]
                    },
                    'confidence_score': person.get('confidence', 8),
                    'ownership_status': {
                        'owns_masters': person.get('owns_masters', False),
                        'owns_publishing': person.get('owns_publishing', False)
                    }
                }

        result = self.estimate_new_person(name, youtube_data, entity_type, ownership_hint)
        result['source'] = 'pattern_estimation'
        return result

    def _detect_entity_type(self, youtube_data):
        subs = youtube_data.get('subscribers', 0)
        if subs > 5000000:
            return 'rapper'
        elif subs > 1000000:
            return 'media_personality'
        elif subs > 100000:
            return 'producer'
        else:
            return 'rapper'


# ============================================================
# REFINEMENT ENGINE
# ============================================================
TOURING_TIERS = {
    "stadium_legend": {"tier": "Stadium/Legend", "avg_gross_per_show": 3500000,
                       "artist_net_percentage": 0.40, "annual_shows": 25,
                       "examples": ["Jay-Z", "Drake", "Kendrick Lamar", "Eminem"],
                       "annual_tour_income": 35000000},
    "arena_superstar": {"tier": "Arena Superstar", "avg_gross_per_show": 1500000,
                        "artist_net_percentage": 0.38, "annual_shows": 50,
                        "examples": ["J. Cole", "Future", "Lil Baby", "21 Savage"],
                        "annual_tour_income": 28500000},
    "theater_mid_tier": {"tier": "Theater/Mid-Tier", "avg_gross_per_show": 250000,
                         "artist_net_percentage": 0.40, "annual_shows": 60,
                         "examples": ["Freddie Gibbs", "Pusha T", "Benny The Butcher", "Rapsody"],
                         "annual_tour_income": 6000000},
    "club_independent": {"tier": "Club/Independent", "avg_gross_per_show": 35000,
                         "artist_net_percentage": 0.45, "annual_shows": 80,
                         "examples": ["Billy Woods", "ELUCID", "IDK", "Rome Streetz"],
                         "annual_tour_income": 1260000},
    "festival_circuit": {"tier": "Festival Circuit", "avg_gross_per_show": 500000,
                         "artist_net_percentage": 0.85, "annual_shows": 15,
                         "examples": ["Anderson .Paak", "SZA", "Denzel Curry"],
                         "annual_tour_income": 6375000}
}

PUBLIC_TOUR_GROSSES = {
    "Drake": {"tour_name": "It's All A Blur Tour", "total_gross": 320000000,
              "shows": 72, "avg_per_show": 4444444, "artist_net_estimate": 128000000},
    "Beyonce": {"tour_name": "Renaissance Tour", "total_gross": 579000000,
                "shows": 56, "avg_per_show": 10339286, "artist_net_estimate": 231600000},
    "Taylor Swift": {"tour_name": "Eras Tour", "total_gross": 1040000000,
                     "shows": 60, "avg_per_show": 17333333, "artist_net_estimate": 416000000},
    "Kendrick Lamar": {"tour_name": "Big Steppers Tour", "total_gross": 110000000,
                       "shows": 73, "avg_per_show": 1506849, "artist_net_estimate": 44000000},
    "Lil Baby": {"tour_name": "It's Only Us Tour", "total_gross": 45000000,
                 "shows": 32, "avg_per_show": 1406250, "artist_net_estimate": 18000000},
    "J. Cole": {"tour_name": "The Off-Season Tour", "total_gross": 75000000,
                "shows": 35, "avg_per_show": 2142857, "artist_net_estimate": 30000000}
}


class RefinementEngine:
    def __init__(self, knowledge_path: str = "data/manual_estimates/manual_knowledge.json"):
        self.knowledge_path = knowledge_path
        self.load_knowledge()
        self.load_user_facts()

        self.adjustment_factors = {
            "owns_masters": {"multiplier": 1.15, "category": "ownership", "impact": "HIGH",
                             "reason": "Owning masters means keeping 80-90% of revenue vs 15-20% for major label deals."},
            "does_not_own_masters": {"multiplier": 0.85, "category": "ownership", "impact": "HIGH",
                                     "reason": "Not owning masters means only receiving 15-20% of music revenue."},
            "owns_publishing": {"multiplier": 1.08, "category": "ownership", "impact": "MODERATE",
                                "reason": "Publishing rights generate separate songwriting royalties."},
            "does_not_own_publishing": {"multiplier": 0.92, "category": "ownership", "impact": "MODERATE",
                                        "reason": "Without publishing, missing songwriting royalties."},
            "owns_masters_and_publishing": {"multiplier": 1.20, "category": "ownership", "impact": "HIGH",
                                            "reason": "Owning both means keeping 90%+ of music revenue."},
            "tours_constantly": {"multiplier": 1.08, "category": "touring", "impact": "MODERATE",
                                 "reason": "Consistent touring adds incremental income."},
            "rarely_tours": {"multiplier": 0.92, "category": "touring", "impact": "MODERATE",
                             "reason": "Limited touring means missing some income."},
            "stadium_tours": {"multiplier": 1.12, "category": "touring", "impact": "HIGH",
                              "reason": "Stadium tours gross $3M-$5M per show."},
            "arena_tours": {"multiplier": 1.08, "category": "touring", "impact": "MODERATE",
                            "reason": "Arena tours gross $1M-$2M per show."},
            "theater_club_tours": {"multiplier": 1.03, "category": "touring", "impact": "LOW",
                                   "reason": "Theater/club tours gross $50K-$500K per show."},
            "festival_circuit": {"multiplier": 1.05, "category": "touring", "impact": "LOW",
                                 "reason": "Festival bookings pay flat fees."},
            "no_touring": {"multiplier": 0.90, "category": "touring", "impact": "MODERATE",
                           "reason": "No touring means relying on streaming/catalog."},
            "massive_streaming": {"multiplier": 1.10, "category": "streaming", "impact": "MODERATE",
                                  "reason": "High streaming generates steady passive income."},
            "low_streaming": {"multiplier": 0.90, "category": "streaming", "impact": "MODERATE",
                              "reason": "Low streaming means limited passive income."},
            "owns_business": {"multiplier": 1.10, "category": "business", "impact": "MODERATE",
                              "reason": "Business ownership provides additional revenue streams."},
            "owns_label": {"multiplier": 1.08, "category": "business", "impact": "MODERATE",
                           "reason": "Label ownership collects % from other artists."},
            "major_endorsement_deal": {"multiplier": 1.08, "category": "business", "impact": "MODERATE",
                                       "reason": "Major brand deals can add $5M-$50M+."},
            "smart_investments": {"multiplier": 1.05, "category": "business", "impact": "LOW",
                                  "reason": "Smart investments compound over time."},
            "bad_spending_habits": {"multiplier": 0.85, "category": "spending", "impact": "MODERATE",
                                    "reason": "Bad spending habits drain wealth. Hood rich ≠ wealthy."},
            "good_spending_habits": {"multiplier": 1.05, "category": "spending", "impact": "LOW",
                                     "reason": "Frugal spending preserves wealth."},
            "heavy_gambling": {"multiplier": 0.88, "category": "spending", "impact": "MODERATE",
                               "reason": "Heavy gambling losses reduce net worth."},
            "flashy_lifestyle": {"multiplier": 0.92, "category": "spending", "impact": "LOW",
                                 "reason": "Flashy lifestyle often masks lower actual net worth."},
            "multiple_baby_mamas": {"multiplier": 0.95, "category": "spending", "impact": "LOW",
                                    "reason": "Child support reduces disposable wealth."},
            "legal_issues": {"multiplier": 0.88, "category": "legal", "impact": "MODERATE",
                             "reason": "Legal issues drain wealth through fees."},
            "tax_problems": {"multiplier": 0.80, "category": "legal", "impact": "HIGH",
                             "reason": "Tax problems can result in massive IRS bills."},
            "bankruptcy_history": {"multiplier": 0.75, "category": "legal", "impact": "HIGH",
                                   "reason": "Bankruptcy indicates poor financial management."},
            "clear_legal_record": {"multiplier": 1.05, "category": "legal", "impact": "LOW",
                                   "reason": "Clean legal record allows maximum earnings."},
            "owns_real_estate": {"multiplier": 1.08, "category": "assets", "impact": "MODERATE",
                                 "reason": "Real estate appreciates over time."},
            "owns_expensive_assets": {"multiplier": 1.05, "category": "assets", "impact": "LOW",
                                      "reason": "Expensive assets hold some value."},
            "no_significant_assets": {"multiplier": 0.85, "category": "assets", "impact": "MODERATE",
                                      "reason": "No assets means wealth isn't preserved."},
            "hidden_assets": {"multiplier": 1.12, "category": "assets", "impact": "MODERATE",
                              "reason": "Hidden assets indicate wealth shielded from view."},
            "independent_artist": {"multiplier": 1.12, "category": "industry", "impact": "MODERATE",
                                   "reason": "Independents keep 70-90% of revenue."},
            "major_label_deal": {"multiplier": 0.88, "category": "industry", "impact": "MODERATE",
                                 "reason": "Major labels take 80-85% of revenue."},
            "owns_digital_platform": {"multiplier": 1.08, "category": "industry", "impact": "MODERATE",
                                      "reason": "Platform ownership generates direct revenue."},
            "legacy_catalog": {"multiplier": 1.10, "category": "career", "impact": "MODERATE",
                               "reason": "Legacy catalog generates royalties for decades."},
            "inactive_career": {"multiplier": 0.90, "category": "career", "impact": "MODERATE",
                                "reason": "Inactive career means no new income streams."},
            "new_money": {"multiplier": 0.92, "category": "wealth_type", "impact": "LOW",
                          "reason": "New money often gets spent quickly."},
            "old_money_stable": {"multiplier": 1.08, "category": "wealth_type", "impact": "MODERATE",
                                 "reason": "Long-term stable wealth indicates good management."}
        }

    def load_knowledge(self):
        try:
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.people = data.get("people", [])
        except FileNotFoundError:
            self.people = []
            print(f"Knowledge file not found: {self.knowledge_path}")

    def load_user_facts(self):
        facts_path = "data/user_facts.json"
        try:
            with open(facts_path, 'r', encoding='utf-8') as f:
                self.user_facts = json.load(f)
        except FileNotFoundError:
            self.user_facts = {}

    def save_user_facts(self):
        facts_path = "data/user_facts.json"
        os.makedirs(os.path.dirname(facts_path), exist_ok=True)
        with open(facts_path, 'w', encoding='utf-8') as f:
            json.dump(self.user_facts, f, indent=2, ensure_ascii=False)

    def find_person(self, name: str) -> Optional[Dict]:
        name_lower = name.lower().strip()
        for person in self.people:
            if person.get("name", "").lower() == name_lower:
                return person
        for person in self.people:
            person_name = person.get("name", "").lower()
            if name_lower in person_name or person_name in name_lower:
                return person
        return None

    def get_base_estimate(self, person: Dict) -> Tuple[float, float, float]:
        net_worth = person.get("manual_net_worth", [])
        if len(net_worth) >= 3:
            return net_worth[0], net_worth[1], net_worth[2]
        elif len(net_worth) == 2:
            mid = (net_worth[0] + net_worth[1]) / 2
            return net_worth[0], mid, net_worth[1]
        else:
            return 1000000, 5000000, 10000000

    def apply_adjustments(self, base: Tuple[float, float, float], facts: List[str]) -> Tuple[Tuple[float, float, float], List[Dict]]:
        low, mid, high = base
        adjustments_applied = []
        category_adjustments = {}
        total_multiplier = 1.0

        for fact in facts:
            fact_key = fact.lower().strip().replace(" ", "_")
            for key, adjustment in self.adjustment_factors.items():
                if fact_key in key or key in fact_key:
                    category = adjustment["category"]
                    if category not in category_adjustments:
                        category_adjustments[category] = {
                            "multiplier": adjustment["multiplier"],
                            "fact": fact,
                            "key": key,
                            "reason": adjustment["reason"],
                            "impact": adjustment["impact"]
                        }
                    else:
                        current = category_adjustments[category]
                        current_deviation = abs(1.0 - current["multiplier"])
                        new_deviation = abs(1.0 - adjustment["multiplier"])
                        if new_deviation > current_deviation:
                            category_adjustments[category] = {
                                "multiplier": adjustment["multiplier"],
                                "fact": fact,
                                "key": key,
                                "reason": adjustment["reason"],
                                "impact": adjustment["impact"]
                            }
                    break

        for category, adj in category_adjustments.items():
            total_multiplier *= adj["multiplier"]
            adjustments_applied.append({
                "fact": adj["fact"],
                "key": adj["key"],
                "multiplier": adj["multiplier"],
                "reason": adj["reason"],
                "category": category,
                "impact": adj["impact"]
            })

        total_multiplier = max(0.85, min(1.15, total_multiplier))
        new_low = low * total_multiplier
        new_mid = mid * total_multiplier
        new_high = high * total_multiplier
        return (new_low, new_mid, new_high), adjustments_applied

    def format_currency(self, amount: float) -> str:
        if amount < 0:
            return f"-${abs(amount):,.0f}"
        elif amount >= 1_000_000_000:
            return f"${amount/1_000_000_000:.2f}B"
        elif amount >= 1_000_000:
            return f"${amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.0f}K"
        else:
            return f"${amount:,.0f}"

    def get_touring_estimate(self, name: str) -> Dict:
        person = self.find_person(name)
        if not person:
            return {"success": False, "message": f"Couldn't find '{name}'"}
        if name in PUBLIC_TOUR_GROSSES:
            tour_data = PUBLIC_TOUR_GROSSES[name]
            return {
                "success": True,
                "name": name,
                "tour_name": tour_data["tour_name"],
                "total_gross": tour_data["total_gross"],
                "shows": tour_data["shows"],
                "avg_per_show": tour_data["avg_per_show"],
                "artist_net_estimate": tour_data["artist_net_estimate"],
                "source": "Public tour data 2023-2024"
            }
        for tier_key, tier_data in TOURING_TIERS.items():
            if name in tier_data["examples"]:
                return {
                    "success": True,
                    "name": name,
                    "tier": tier_data["tier"],
                    "avg_gross_per_show": tier_data["avg_gross_per_show"],
                    "annual_shows": tier_data["annual_shows"],
                    "artist_net_percentage": tier_data["artist_net_percentage"],
                    "estimated_annual_tour_income": tier_data["annual_tour_income"],
                    "source": f"Estimated based on {tier_data['tier']} tier"
                }
        return {"success": False, "message": f"No touring data available for {name}"}

    def get_touring_breakdown(self, gross_box_office: float) -> Dict:
        return {
            "gross_box_office": gross_box_office,
            "venue_production_costs": gross_box_office * 0.30,
            "promoter_cut": gross_box_office * 0.12,
            "management_legal": gross_box_office * 0.18,
            "artist_net": gross_box_office * 0.40,
            "merch_estimate": gross_box_office * 0.20,
            "vip_estimate": gross_box_office * 0.12 if gross_box_office > 50000000 else 0
        }

    def get_estimate(self, name: str, user_facts: Optional[List[str]] = None) -> Dict:
        person = self.find_person(name)
        if not person:
            return {
                "success": False,
                "message": f"Couldn't find '{name}' in database.",
                "name": name,
                "estimate": None,
                "reasoning": "Person not found in knowledge base",
                "adjustments": []
            }

        actual_name = person.get("name", name)
        base_low, base_mid, base_high = self.get_base_estimate(person)
        saved_facts = self.user_facts.get(actual_name, [])
        all_facts = saved_facts + (user_facts or [])
        adjusted_estimate, adjustments = self.apply_adjustments(
            (base_low, base_mid, base_high),
            all_facts
        )

        reasoning_parts = []
        reasoning_parts.append(f"Base estimate: {self.format_currency(base_low)} - {self.format_currency(base_high)}")
        if person.get("owns_masters"):
            reasoning_parts.append("✓ Owns masters (positive for long-term wealth)")
        else:
            reasoning_parts.append("✗ Does not own masters (limits long-term catalog value)")
        if person.get("owns_publishing"):
            reasoning_parts.append("✓ Owns publishing (additional royalty stream)")
        if person.get("label_situation"):
            reasoning_parts.append(f"Label: {person['label_situation']}")
        if person.get("key_assets"):
            assets_str = ", ".join([f"{k.replace('_', ' ').title()}: {self.format_currency(v)}" for k, v in person["key_assets"].items()])
            reasoning_parts.append(f"Key assets: {assets_str}")

        touring = self.get_touring_estimate(actual_name)
        if touring["success"]:
            if "tour_name" in touring:
                reasoning_parts.append(f"Recent tour: {touring['tour_name']} (Gross: {self.format_currency(touring['total_gross'])})")
            elif "tier" in touring:
                reasoning_parts.append(f"Touring tier: {touring['tier']}")

        if adjustments:
            reasoning_parts.append("\nADJUSTMENTS APPLIED:")
            for adj in adjustments:
                direction = "↑" if adj["multiplier"] > 1 else "↓"
                impact = f"[{adj['impact']}]" if "impact" in adj else ""
                reasoning_parts.append(f"{direction} {adj['fact']} {impact}: {adj['reason']}")

        if person.get("notes"):
            reasoning_parts.append(f"\nNotes: {person['notes']}")

        if user_facts:
            if actual_name not in self.user_facts:
                self.user_facts[actual_name] = []
            self.user_facts[actual_name].extend(user_facts)
            self.save_user_facts()

        confidence = person.get("confidence", 5)
        confidence_text = {
            9: "Very High", 8: "High", 7: "Moderate-High",
            6: "Moderate", 5: "Medium", 4: "Low-Moderate"
        }.get(confidence, "Unknown")

        return {
            "success": True,
            "name": actual_name,
            "base_estimate": (base_low, base_mid, base_high),
            "adjusted_estimate": adjusted_estimate,
            "low": adjusted_estimate[0],
            "mid": adjusted_estimate[1],
            "high": adjusted_estimate[2],
            "confidence": confidence_text,
            "reasoning": "\n".join(reasoning_parts),
            "adjustments": adjustments,
            "ownership_status": person.get("owns_masters", False),
            "entity_type": person.get("entity_type", "unknown")
        }

    def quick_estimate(self, name: str, user_facts: Optional[List[str]] = None) -> str:
        result = self.get_estimate(name, user_facts)
        if not result["success"]:
            return result["message"]
        low, mid, high = result["low"], result["mid"], result["high"]
        response = f"📊 {result['name']} Estimated Net Worth:\n"
        response += f"Range: {self.format_currency(low)} - {self.format_currency(high)}\n"
        response += f"Mid-point: {self.format_currency(mid)}\n"
        response += f"Confidence: {result['confidence']}\n\n"
        response += "🔍 REASONING:\n"
        response += result["reasoning"]
        response += "\n\n⚠️ These are estimates based on available public data and industry heuristics."
        return response