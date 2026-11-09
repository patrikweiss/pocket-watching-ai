"""
POCKET WATCHING AI - DASHBOARD
===============================
Streamlit web app with:
- Search any artist
- Base estimate (database first, then REAL YouTube + pattern matching)
- Full breakdown (income, assets, ownership)
- "Why this estimate?" explanation
- Interactive refinement (user adds facts, estimate adjusts)
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.engines import FullEngine, PatternEstimatorV2, RefinementEngine
from src.data_collection import get_channel_data


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Pocket Watching AI",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Pocket Watching AI")
st.subheader("Net Worth Estimation with Interactive Refinement")


# ============================================================
# LOAD ENGINES (cached so they don't reload on every interaction)
# ============================================================
@st.cache_resource
def load_engines():
    return FullEngine(), PatternEstimatorV2(), RefinementEngine()


full_engine, pattern_engine, refinement_engine = load_engines()


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def format_money(amount):
    """Format a dollar amount nicely (e.g., $1.2B, $45M, $500K)"""
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.0f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.0f}K"
    else:
        return f"${amount:,.0f}"


@st.cache_data(ttl=3600)  # Cache YouTube results for 1 hour to avoid API spam
def fetch_youtube_data(name):
    """Fetch real YouTube channel data for an artist"""
    try:
        data = get_channel_data(name)
        if data and data.get('subscribers', 0) > 0:
            return {
                'subscribers': data.get('subscribers', 0),
                'total_views': data.get('total_views', 0),
                'total_videos': data.get('total_videos', 0),
                'channel_name': data.get('name', name)
            }
    except Exception as e:
        print(f"YouTube fetch error for '{name}': {e}")
    return None


def get_base_estimate(name):
    """
    Try database first, then pattern estimation with REAL YouTube data.
    Returns (low, mid, high, source, result_dict, youtube_data_used)
    """
    # Step 1: Database lookup (known people)
    result = full_engine.calculate_full_breakdown(name)

    if 'error' not in result and result.get('net_worth_range'):
        nw = result['net_worth_range']
        return nw['low'], nw['mid'], nw['high'], 'database', result, None

    # Step 2: Fetch real YouTube data for unknown people
    youtube_data = fetch_youtube_data(name)

    if youtube_data:
        source_tag = 'pattern_real'
    else:
        # Fallback placeholder (only if YouTube lookup totally fails)
        youtube_data = {
            'subscribers': 1000000,
            'total_views': 500000000,
            'total_videos': 100,
            'channel_name': name
        }
        source_tag = 'pattern_placeholder'

    # Step 3: Pattern estimation
    pattern_result = pattern_engine.estimate_or_lookup(
        name, youtube_data, entity_type=None
    )

    if 'net_worth_range' in pattern_result:
        nw = pattern_result['net_worth_range']
        return nw['low'], nw['mid'], nw['high'], source_tag, pattern_result, youtube_data

    # Nothing worked
    return None, None, None, 'not_found', None, None


# ============================================================
# MAIN UI
# ============================================================
name = st.text_input(
    "Enter a name:",
    placeholder="e.g., J. Cole, DJ Vlad, Drake, Lil Durk"
)

if name:
    # Get base estimate
    base_low, base_mid, base_high, source, base_result, yt_data = get_base_estimate(name)

    if source == 'not_found':
        st.error(f"Could not find or estimate '{name}'.")

    else:
        # ---- Source indicator ----
        if source == 'database':
            st.success(f"✅ Found in database ({len(full_engine.manual_db)} people)")
        elif source == 'pattern_real':
            st.info("🔍 Not in database — using REAL YouTube data + pattern matching")
        elif source == 'pattern_placeholder':
            st.warning("⚠️ Not in database, YouTube lookup failed — estimate is rough")
        else:
            st.warning("⚠️ Using pattern estimation")

        # ---- Base estimate display ----
        st.markdown("### 📊 Base Estimate")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Low", format_money(base_low))
        with col2:
            st.metric("Most Likely", format_money(base_mid))
        with col3:
            st.metric("High", format_money(base_high))

        # ============================================================
        # DATABASE ENTRY SECTIONS
        # ============================================================
        if source == 'database':

            # ---- Full Breakdown Expander ----
            with st.expander("📈 Full Breakdown (Income, Assets, Ownership)"):
                left, right = st.columns(2)

                with left:
                    st.markdown("**Income (Annual)**")
                    income = base_result.get('income_analysis', {})
                    if income:
                        st.write(f"Gross: {format_money(income.get('estimated_annual_gross', 0))}")
                        st.write(f"Streaming: {format_money(income.get('streaming_estimate', 0))}")
                        st.write(f"Touring: {format_money(income.get('touring_estimate', 0))}")
                        st.write(f"Merch: {format_money(income.get('merch_estimate', 0))}")
                        st.write(f"Other: {format_money(income.get('other_income', 0))}")

                    st.markdown("**Ownership**")
                    st.write(f"Tier: {base_result.get('ownership_tier', 'N/A')}")
                    st.write(f"Keeps: {base_result.get('ownership_percentage', 'N/A')}")
                    st.write(f"Deal: {base_result.get('deal_type', 'N/A')}")

                with right:
                    st.markdown("**Assets**")
                    assets = base_result.get('asset_breakdown', {})
                    if assets:
                        st.write(f"Known: {format_money(assets.get('total_known_assets', 0))}")
                        st.write(f"Catalog: {format_money(assets.get('catalog_value_estimated', 0))}")

                    st.markdown("**Career**")
                    st.write(f"Stage: {base_result.get('career_stage', 'N/A')}")
                    st.write(f"Confidence: {base_result.get('confidence_score', 'N/A')}/10")
                    st.write(f"Entity: {base_result.get('entity_type', 'N/A')}")

            # ---- "Why This Estimate?" Expander ----
            with st.expander("❓ Why this estimate? (Explanation)"):
                explanation = full_engine.generate_explanation(base_result)
                st.markdown(explanation)

        # ============================================================
        # PATTERN ESTIMATION SECTIONS (unknown people)
        # ============================================================
        elif source in ['pattern_real', 'pattern_placeholder', 'pattern']:

            # ---- YouTube Data Used ----
            if yt_data:
                with st.expander("📊 YouTube Data Used", expanded=True):
                    if source == 'pattern_real':
                        st.markdown(f"**Channel:** {yt_data.get('channel_name', name)}")
                    else:
                        st.markdown("**⚠️ Placeholder data (YouTube lookup failed)**")

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Subscribers", f"{yt_data.get('subscribers', 0):,}")
                    with col_b:
                        st.metric("Total Views", f"{yt_data.get('total_views', 0):,}")
                    with col_c:
                        st.metric("Videos", f"{yt_data.get('total_videos', 0):,}")

            # ---- Similar People ----
            with st.expander("🔍 Similar People (used for estimation)"):
                if 'similar_people' in base_result:
                    for sp in base_result['similar_people']:
                        st.write(f"- **{sp['name']}** ({sp['similarity']} similar)")
                else:
                    st.info("No similar people found in database")

        # ============================================================
        # INTERACTIVE REFINEMENT SECTION (both database + pattern)
        # ============================================================
        st.markdown("---")
        st.markdown("### 🔧 Refine This Estimate")
        st.write(
            "Add facts you know about this person. The estimate will adjust accordingly. "
            "Try things like: `owns masters`, `tours constantly`, `bad spending habits`, "
            "`legal issues`, `owns business`"
        )

        facts_input = st.text_area(
            "Your knowledge:",
            placeholder="owns masters, tours constantly, bad spending habits",
            key=f"facts_{name}"
        )

        # When user types facts, apply refinements live
        if facts_input and facts_input.strip():
            # Parse facts (split by comma)
            facts = [f.strip() for f in facts_input.split(',') if f.strip()]

            # Apply refinements
            base_tuple = (base_low, base_mid, base_high)
            adjusted, adjustments = refinement_engine.apply_adjustments(base_tuple, facts)

            adj_low, adj_mid, adj_high = adjusted

            # ---- Adjusted estimate display ----
            st.markdown("### ✨ Adjusted Estimate")

            col1, col2, col3 = st.columns(3)
            with col1:
                delta_low = adj_low - base_low
                st.metric("Low", format_money(adj_low), delta=format_money(delta_low))
            with col2:
                delta_mid = adj_mid - base_mid
                st.metric("Most Likely", format_money(adj_mid), delta=format_money(delta_mid))
            with col3:
                delta_high = adj_high - base_high
                st.metric("High", format_money(adj_high), delta=format_money(delta_high))

            # ---- Adjustments breakdown ----
            if adjustments:
                st.markdown("#### 📋 Adjustments Applied")

                for adj in adjustments:
                    direction = "⬆️" if adj['multiplier'] > 1 else "⬇️"
                    impact = adj.get('impact', 'MODERATE')

                    with st.container():
                        header = f"{direction} **{adj['fact']}** ({adj['multiplier']}x) — {impact}"
                        st.markdown(header)
                        st.caption(adj['reason'])
                        st.markdown("")
            else:
                st.info("No matching facts found. Try different keywords.")

            # ---- Total change summary ----
            total_change = adj_mid - base_mid
            total_pct = (total_change / base_mid * 100) if base_mid > 0 else 0
            sign = "+" if total_change >= 0 else ""

            st.markdown("---")
            st.markdown(
                f"**Net change:** {sign}{format_money(total_change)} "
                f"({sign}{total_pct:.0f}%)"
            )

        # ---- Disclaimer ----
        st.markdown("---")
        st.caption(
            "⚠️ Estimates are based on publicly available data and industry heuristics. "
            "Not financial advice. Actual figures may vary significantly."
        )

else:
    st.info("👆 Type a name to see the estimate. Then add facts to refine it.")


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### About")
    st.write(
        "Estimates net worth for rappers, producers, athletes, and media personalities "
        "using real data + industry heuristics + your knowledge."
    )

    st.markdown("### How It Works")
    st.write("1. Search a name")
    st.write("2. Get base estimate (database or real YouTube + pattern match)")
    st.write("3. Read the 'Why this estimate?' explanation")
    st.write("4. Add facts you know to refine")

    st.markdown("### Try These Facts")
    st.write("- owns masters")
    st.write("- tours constantly")
    st.write("- bad spending habits")
    st.write("- legal issues")
    st.write("- owns business")
    st.write("- smart investments")

    st.markdown("### Try These Names")
    st.write("- J. Cole")
    st.write("- DJ Vlad")
    st.write("- Drake")
    st.write("- Lil Baby")
    st.write("- Lil Durk (test real YouTube data)")