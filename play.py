import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import altair as alt
from groq import Groq

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(
    page_title="Dentsu Conversational Analytics",
    page_icon="https://img.icons8.com/ios11/16/000000/dashboard-gauge.png",
    layout="wide"
)

# Hide Streamlit branding and menu
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# STYLING
# -------------------------------
st.markdown("""
<style>
    .stSidebar {
        min-width: 336px;
    }
    .stSidebar .stHeading {
        color: #FAFAFA;
    }
    .stSidebar .stElementContainer {
        width: auto;
    }
    .stAppHeader {
        display: none;
    }
    .stMainBlockContainer div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] > div[data-testid="stButton"] {
        text-align: center;
    }
    .stMainBlockContainer div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] > div[data-testid="stButton"] button {
        color: #FAFAFA;
        border: 1px solid #FAFAFA33;
        transition: all 0.3s ease;
        background-color: #0E1117;
        width: fit-content;
    }
    .stMainBlockContainer div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] > div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:
    st.image("https://www.dentsu.com/assets/images/main-logo-alt.png", width=160)

    # Clear conversation button
    if st.button("🧹 Start New Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.header("Dentsu Conversational Analytics")
    st.markdown("""
    **How to use**
    - Type any question about campaign performance or strategy.
    - The assistant responds with quantified, data-driven insight.
    - Conversation context is remembered.
    """)
    
    st.divider()
    
    # Question history section
    st.subheader("📋 Recent Questions")
    
    if "question_history" not in st.session_state:
        st.session_state.question_history = []
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_questions = [q for q in st.session_state.question_history if q["date"] == today]
    yesterday_questions = [q for q in st.session_state.question_history if q["date"] == yesterday]
    
    if today_questions:
        st.markdown("**Today**")
        for q in reversed(today_questions[-5:]):  # Show last 5
            if st.button(q["text"][:50] + "..." if len(q["text"]) > 50 else q["text"], 
                        key=f"today_{q['timestamp']}",
                        use_container_width=True):
                st.session_state.rerun_question = q["text"]
                st.rerun()
    
    if yesterday_questions:
        st.markdown("**Yesterday**")
        for q in reversed(yesterday_questions[-5:]):  # Show last 5
            if st.button(q["text"][:50] + "..." if len(q["text"]) > 50 else q["text"], 
                        key=f"yesterday_{q['timestamp']}",
                        use_container_width=True):
                st.session_state.rerun_question = q["text"]
                st.rerun()

# -------------------------------
# HEADER
# -------------------------------
st.markdown("""
<div>
    <h1 style="text-align: center; font-size: 64px;">
        <span style="color: #FAFAFA; text-shadow: 0 0 4px rgba(216, 237, 255, 0.16), 0 2px 20px rgba(164, 214, 255, 0.36);">dentsu</span>
        <span style="background: radial-gradient(909.23% 218.25% at -4.5% 144.64%, #80D5FF 0%, #79AAFA 44.5%, #C4ADFF 100%); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Conversational Analytics</span>
    </h1>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# GROQ SETUP
# -------------------------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY. Add it to your environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# -------------------------------
# SYSTEM PROMPT
# -------------------------------
system_prompt = """
You are the ANZ Conversational Analytics tool — a senior strategist delivering enterprise-level marketing intelligence to C-suite stakeholders.Your role is to synthesize performance across all channels, formats, funnel layers, and audience segments and deliver quantified, executive-ready insights that reflect fiscal year context and strategic impact.
Use new zealand spelling and context. 
**CRITICAL: You have access to real data. Do NOT invent hypothetical data.**
- The dataframe `df` contains actual campaign performance across all 6 campaigns, 7 publishers, and 52 weeks
- Every claim MUST reference real metrics from this data
- If asked about something the data doesn't contain, say "Data insufficient" — do NOT generate hypothetical examples

**Current Dataset Context**
- FY2025: April 2024 - March 2025 (Week 1 = Early April, Week 52 = Late March)
- Total Annual Investment: $300-500 million across 6 campaigns
- Publishers: Meta, Google, YouTube, TikTok, LinkedIn, TVNZ, NZ Herald
- 7 Publishers, 6 Campaigns, 52 Weeks, 3 Funnel Layers, 4 Formats

Always reference specific campaigns. If the query doesn't specify campaigns, pick 2-3 relevant examples.

**6 Campaigns & Objectives:**
1. Home Loans ($80M, Weeks 1-26, 25-44): Drive consideration + enquiries. Channels: TVNZ, YouTube, Meta, Search, NZ Herald. Funnel: Consideration. Barrier: complexity of mortgage process + upfront costs.
2. Business Banking ($65M, Year-round, 35-54): Acquire SME customers. Channels: LinkedIn, Search, NZ Herald, YouTube. Funnel: Consideration. Barrier: skepticism about fintech; need proof of track record.
3. KiwiSaver ($55M, Weeks 1-26, 18-54): Drive enrollments during tax season. Channels: TVNZ, YouTube, Meta, Search, NZ Herald. Funnel: Consideration. Barrier: financial literacy + tax confusion.
4. Personal Banking ($45M, Year-round, 25-54): Drive account switching. Channels: Meta, Search, YouTube, NZ Herald. Funnel: Conversion. Barrier: loyalty to existing bank + perception of switching friction.
5. Airpoints Visa ($25M, Weeks 35-40, 18-35): Acquire younger customers post-Kiwibank switch. Channels: Meta, Search, TikTok, NZ Herald. Funnel: Conversion. Barrier: rewards comparison across products; emotional attachment to Kiwibank brand.
6. goMoney App ($15M, Weeks 1-26, 18-44): Drive downloads + activation. Channels: Meta, Search, TikTok, YouTube, TVNZ. Funnel: Conversion. Barrier: digital literacy + willingness to switch from incumbent banking app.

**Audience Demographics & Decision Drivers:**
- 25-34 (First Home Buyers): Value digital convenience + clarity. Decision driver: desire to own home; motivated by life stage. Respond to: comparative information, trust signals, urgency (first-time opportunity).
- 35-44 (Mortgage Refinancers): Established, higher income, value trust. Decision driver: potential savings. Respond to: premium environments (TVNZ), authority voices, detailed comparisons.
- 45-54 (Wealth Builders/SME Owners): Peak earning, investment-focused, skeptical of fintech. Decision driver: ROI + control. Respond to: professional channels (LinkedIn), data-driven proof, track record.
- 18-35 (Young Professionals/Digital-First): Mobile-first, social proof-driven. Decision driver: rewards + convenience. Respond to: peer recommendations, authentic content, instant gratification (TikTok, Meta).

**Publisher ROAS Multipliers:** Search 1.4x, Meta 1.0x, YouTube 1.05x, TikTok 0.95x, LinkedIn 0.9x, TVNZ 0.85x, NZ Herald 0.75x
**Format ROAS Multipliers:** Carousel 1.2x, Video 1.15x, Interactive 1.1x, Static 0.85x, Radio 0.75x
**Demographic ROAS Multipliers:** Wealth Builders 1.15x, Mortgage Refinancers 1.1x, Young Professionals 1.08x, First Home Buyers 1.05x, Pre-retirees 0.95x

**Seasonality:** Q1 (Weeks 1-12) 1.25x [Tax time, KiwiSaver peak, home buying], Q2 (13-26) 0.85x [Winter lull], Q3 (27-39) 1.15x [Year-end push], Q4 (40-52) 1.05x [Summer lull recovery]

**Response Format:**

1. **Executive Summary** (1-2 sentences)
   - State specific finding + campaign(s) + business impact
   - Example: "Home Loans underleverage Search by 60% despite 1.4x ROAS multiplier—$3.2M recoverable margin in Q1 because first-home buyers actively compare mortgage rates on Search."

2. **Performance Insight** (3-4 paragraphs)
   - Use template: "[Campaign] underperforms [Publisher] because [audience barrier]. [Demographic] needs [format/channel] because [psychological driver]. Data shows [metric] = [value], indicating [root cause]."
   - Example: "Home Loans underperforms TVNZ relative to Search because first-home buyers in Consideration actively compare rates (intent signal), not seeking upper-funnel awareness. However, Mortgage Refinancers (35-44) need TVNZ's premium environment because they require trust-building for $500K+ decisions; Search's transactional tone doesn't build confidence for existing-customer retention."
   - Compare like-for-like only (Video vs Video, Consideration vs Consideration)
   - Always explain the causal chain, not just the metric

3. **Recommendations** (2-3 bullets with full structure)
   - Format: a) Campaign(s), b) Change, c) Why (barrier + fit), d) Impact (quantified), e) Trade-off
   - Example: "Home Loans → Shift 15% TVNZ spend ($2.1M) to Search Carousel in Q1 (weeks 1-12). Rationale: First-home buyers in Consideration actively compare mortgages on Search (1.4x ROAS baseline vs TVNZ 0.85x); Carousel format drives 1.2x additional lift by showing 4 loan product angles. Impact: CPA improves $31→$24 (22% efficiency), ROAS +0.4x. Preserve $6.7M TVNZ for Mortgage Refinancers (35-44) who need trust-building environment. Result: Home Loans portfolio ROAS moves 3.2→3.6."

**If query doesn't specify campaigns:**
Pick 2-3 relevant ones. Example: "Home Loans and Business Banking both sit in Consideration. Home Loans underleverage Search because first-home buyers actively compare rates (intent signal). Business Banking underleverage LinkedIn because SME owners research on Google (vendor reviews) not LinkedIn—LinkedIn skews professional networking, not procurement research. KiwiSaver should maintain TVNZ because tax-time awareness (Feb-Jun) requires reach across older demographics (45-54) who trust premium TV environment."

**Investment Scenario Planning:**
- Current: $285M baseline
- $100M: Cut awareness. Focus Conversion (Personal Banking, Airpoints, goMoney) on Search + Meta. Home Loans → Search + YouTube only. Business Banking → Search only. Remove TVNZ, Herald, LinkedIn. Expected ROAS: 3.8-4.2 (portfolio squeeze, reach collapse).
- $200M: Split Consideration/Conversion. Home Loans + KiwiSaver → Search + Meta (Q1 seasonality). Business Banking → Search + YouTube (year-round). Airpoints + goMoney → Meta + TikTok (high-ROI Conversion). Cut TVNZ, reduce LinkedIn. Expected ROAS: 3.4-3.6.
- $300M: Full portfolio with Awareness. Scale Home Loans + KiwiSaver across all channels (TVNZ + Herald for reach). LinkedIn for Business Banking (SME targeting). Airpoints + goMoney → full channel mix. Expected ROAS: 2.8-3.2 (reach dilution, lower average ROAS but volume trade-off).

**BAN THESE PHRASES:**
- "enables/enable precise tracking," "cost efficiency," "dynamic testing," "unique capabilities"
- "drives engagement" (unless: "drives engagement because Carousel shows 4 angles, reducing decision friction")
- "Comparative analysis shows," "highlights the importance," "it's important to note"
- "Performance variance across channels" (state specific variance + why)
- "Amplify high-performing channels," "Optimize targeting" (vague, non-causal)

**CRITICAL: No chart descriptions, visualization references, or placeholder text. Text analysis only. Use NZ spelling.**
"""

# -------------------------------
# CHAT MEMORY
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": system_prompt}]

# -------------------------------
# SAMPLE DATA
# -------------------------------
@st.cache_data(ttl=3600)
def generate_data():
    fy_year = 2025
    
    # Campaign specifications
    campaigns = {
        "ANZ Home Loans": {
            "spend_annual": 80_000_000,
            "channels": ["TVNZ", "YouTube", "Meta", "Search", "NZ Herald"],
            "funnel": "Consideration",
            "demo": ["First Home Buyers (25-34)", "Mortgage Refinancers (35-44)"],
            "weeks": list(range(1, 27))  # Feb-Jun (weeks 1-26 roughly)
        },
        "ANZ Business Banking": {
            "spend_annual": 65_000_000,
            "channels": ["LinkedIn", "Search", "NZ Herald", "YouTube"],
            "funnel": "Consideration",
            "demo": ["Wealth Builders (45-54)"],
            "weeks": list(range(1, 53))  # Year-round
        },
        "ANZ KiwiSaver": {
            "spend_annual": 55_000_000,
            "channels": ["TVNZ", "YouTube", "Meta", "Search", "NZ Herald"],
            "funnel": "Consideration",
            "demo": ["First Home Buyers (25-34)", "Mortgage Refinancers (35-44)", "Wealth Builders (45-54)", "Pre-retirees (55+)"],
            "weeks": list(range(1, 27))  # Feb-Jun
        },
        "ANZ Personal Banking": {
            "spend_annual": 45_000_000,
            "channels": ["Meta", "Search", "YouTube", "NZ Herald"],
            "funnel": "Conversion",
            "demo": ["First Home Buyers (25-34)", "Mortgage Refinancers (35-44)", "Wealth Builders (45-54)"],
            "weeks": list(range(1, 53))  # Year-round
        },
        "ANZ Airpoints Visa": {
            "spend_annual": 25_000_000,
            "channels": ["Meta", "Search", "TikTok", "NZ Herald"],
            "funnel": "Conversion",
            "demo": ["Young Professionals (25-34)"],
            "weeks": list(range(35, 41))  # Sep-Oct (weeks 35-40 roughly)
        },
        "ANZ goMoney App": {
            "spend_annual": 15_000_000,
            "channels": ["Meta", "Search", "TikTok", "YouTube", "TVNZ"],
            "funnel": "Conversion",
            "demo": ["Young Professionals (25-34)"],
            "weeks": list(range(1, 27))  # Apr-Jun (weeks 1-26)
        }
    }
    
    strategies = ["Retargeting", "Brand Lift", "Product Launch", "Offer Promotion"]
    formats = ["Video", "Static", "Carousel", "Interactive", "Radio"]
    creative_messaging = ["Value-led", "Urgency-led", "Emotional", "Informational"]
    behav_segments = ["In-Market Researchers", "Decision-Ready", "Loyal Members"]
    
    # Publisher-specific ROAS multipliers
    publisher_roas_adjust = {
        "Search": 1.4,
        "Meta": 1.0,
        "YouTube": 1.05,
        "TikTok": 0.95,
        "LinkedIn": 0.9,
        "TVNZ": 0.85,
        "NZ Herald": 0.75
    }
    
    # Format-specific ROAS multipliers
    format_roas_adjust = {
        "Video": 1.15,
        "Carousel": 1.20,
        "Static": 0.85,
        "Interactive": 1.10,
        "Radio": 0.75
    }
    
    # Demographic ROAS multipliers
    demo_roas_adjust = {
        "First Home Buyers (25-34)": 1.05,
        "Mortgage Refinancers (35-44)": 1.10,
        "Wealth Builders (45-54)": 1.15,
        "Young Professionals (25-34)": 1.08,
        "Pre-retirees (55+)": 0.95
    }
    
    # Publisher-specific CPA multipliers
    publisher_cpa_adjust = {
        "Search": 0.75,
        "Meta": 1.0,
        "YouTube": 1.1,
        "TikTok": 1.05,
        "LinkedIn": 1.25,
        "TVNZ": 1.15,
        "NZ Herald": 1.3
    }
    
    # Format-specific CPA multipliers
    format_cpa_adjust = {
        "Video": 0.95,
        "Carousel": 0.90,
        "Static": 1.20,
        "Interactive": 0.98,
        "Radio": 1.45
    }
    
    # Behavioral segment CPA base
    cpa_base_lookup = {
        "In-Market Researchers": 45,
        "Decision-Ready": 28,
        "Loyal Members": 18
    }
    
    # CTR by format
    ctr_lookup = {
        "Video": 2.8,
        "Carousel": 3.2,
        "Static": 1.2,
        "Interactive": 2.5,
        "Radio": 0.6
    }
    
    # CPM adjustments
    cpm_adjust = {
        "Video": 6,
        "Carousel": 5,
        "Static": 4,
        "Interactive": 6,
        "Radio": 3
    }
    
    # ROAS base by funnel
    roas_base_lookup = {
        "Awareness": 2.0,
        "Consideration": 3.5,
        "Conversion": 5.0
    }
    
    rows = []
    row_id = 0
    
    # Generate data per campaign
    for campaign_name, campaign_spec in campaigns.items():
        weekly_spend = campaign_spec["spend_annual"] / len(campaign_spec["weeks"])
        
        for week in campaign_spec["weeks"]:
            # Seasonal multiplier
            if 1 <= week <= 12:
                seasonal_mult = 1.25
            elif 13 <= week <= 26:
                seasonal_mult = 0.85
            elif 27 <= week <= 39:
                seasonal_mult = 1.15
            else:
                seasonal_mult = 1.05
            
            # Generate 4 rows per week (rotate through channels, formats, audiences)
            for iteration in range(4):
                channel = campaign_spec["channels"][iteration % len(campaign_spec["channels"])]
                format = formats[iteration % len(formats)]
                strategy = strategies[iteration % len(strategies)]
                demo = campaign_spec["demo"][iteration % len(campaign_spec["demo"])]
                behav = behav_segments[iteration % len(behav_segments)]
                creative = creative_messaging[iteration % len(creative_messaging)]
                
                spend = (weekly_spend / 4) * seasonal_mult
                
                # Calculate metrics
                ctr = ctr_lookup[format]
                pub_mult = publisher_roas_adjust.get(channel, 1.0)
                fmt_mult = format_roas_adjust.get(format, 1.0)
                demo_mult = demo_roas_adjust.get(demo, 1.0)
                roas_base = roas_base_lookup[campaign_spec["funnel"]]
                roas = max(1.2, (roas_base * pub_mult * fmt_mult * demo_mult) - (spend / 2_000_000))
                
                cpa_base = cpa_base_lookup[behav]
                pub_mult_cpa = publisher_cpa_adjust.get(channel, 1.0)
                fmt_mult_cpa = format_cpa_adjust.get(format, 1.0)
                cpa = round(cpa_base * pub_mult_cpa * fmt_mult_cpa, 2)
                
                impressions = int(spend / cpm_adjust[format] * 1000)
                clicks = int(impressions * (ctr / 100))
                conversions = int(clicks * (0.03 + np.random.rand() * 0.05))
                revenue = spend * roas
                
                # Viewability
                viewability_rate = round(np.random.uniform(0.55, 0.85), 3)
                measurable_impressions = int(impressions * 0.95)
                
                # Traffic & Engagement
                website_sessions = int(clicks * np.random.uniform(0.7, 0.95))
                time_on_site = round(np.random.uniform(1.5, 8.5), 1)
                pages_per_session = round(np.random.uniform(1.2, 5.5), 2)
                bounce_rate = round(np.random.uniform(0.25, 0.75), 3)
                
                # Social Engagement
                if channel in ["Meta", "TikTok", "LinkedIn"]:
                    social_likes = int(impressions * np.random.uniform(0.001, 0.008))
                    social_shares = int(impressions * np.random.uniform(0.0002, 0.002))
                    social_comments = int(impressions * np.random.uniform(0.0001, 0.001))
                else:
                    social_likes = 0
                    social_shares = 0
                    social_comments = 0
                
                # Revenue breakdown
                website_sales = int(revenue * 0.45)
                ecommerce_sales = int(revenue * 0.35)
                affiliate_revenue = int(revenue * 0.15)
                other_revenue = int(revenue * 0.05)
                
                # CX Metrics
                form_submissions = int(conversions * 0.6)
                lead_generation = int(conversions * 0.3)
                signups = int(conversions * 0.1)
                
                # CPA derivatives
                cost_per_lead = round(spend / max(1, lead_generation), 2) if lead_generation > 0 else spend
                cost_per_signup = round(spend / max(1, signups), 2) if signups > 0 else spend
                conversion_rate_pct = round((conversions / max(1, clicks)) * 100, 2)
                
                # Radio specific
                if format == "Radio" and channel in ["TVNZ", "NZ Herald"]:
                    tarps = round(min(100, 30 + (week % 20)), 1)
                    reach = round(tarps / 1.5, 1)
                    frequency = round(tarps / reach, 1)
                    spot_count = int(spend / 500)
                    station = ["ZM", "The Edge", "Newstalk ZB", "Hauraki", "Coast"][row_id % 5]
                else:
                    tarps = None
                    reach = None
                    frequency = None
                    spot_count = None
                    station = None
                
                rows.append({
                    "FY Year": fy_year,
                    "Week": week,
                    "Campaign": campaign_name,
                    "Publisher": channel,
                    "Strategy": strategy,
                    "Funnel Layer": campaign_spec["funnel"],
                    "Format": format,
                    "Creative Messaging": creative,
                    "Audience Segment (Demographic)": demo,
                    "Audience Segment (Behavioral)": behav,
                    "Spend ($)": spend,
                    "ROAS": roas,
                    "CTR (%)": ctr,
                    "CPA ($)": cpa,
                    "Impressions": impressions,
                    "Clicks": clicks,
                    "Conversions": conversions,
                    "Conversion Rate (%)": conversion_rate_pct,
                    "Revenue ($)": revenue,
                    "Website Sales ($)": website_sales,
                    "E-Commerce Sales ($)": ecommerce_sales,
                    "Affiliate Revenue ($)": affiliate_revenue,
                    "Other Revenue ($)": other_revenue,
                    "Form Submissions": form_submissions,
                    "Leads Generated": lead_generation,
                    "Sign-Ups": signups,
                    "Cost Per Lead ($)": cost_per_lead,
                    "Cost Per Sign-Up ($)": cost_per_signup,
                    "Viewability (%)": viewability_rate,
                    "Measurable Impressions": measurable_impressions,
                    "Website Sessions": website_sessions,
                    "Time on Site (min)": time_on_site,
                    "Pages Per Session": pages_per_session,
                    "Bounce Rate (%)": bounce_rate,
                    "Social Likes": social_likes,
                    "Social Shares": social_shares,
                    "Social Comments": social_comments,
                    "TARPs": tarps,
                    "Reach (%)": reach,
                    "Frequency": frequency,
                    "Spot Count": spot_count,
                    "Station": station
                })
                row_id += 1
    
    return pd.DataFrame(rows)

df = generate_data()

# Add Channel Type mapping
def map_channel_type(publisher):
    if publisher in ['Meta', 'TikTok', 'LinkedIn']:
        return 'Social'
    elif publisher in ['NZ Herald', 'TVNZ']:
        return 'Display'
    elif publisher == 'Search':
        return 'Search'
    elif publisher == 'YouTube':
        return 'Video'
    else:
        return 'Other'

df['Channel'] = df['Publisher'].apply(map_channel_type)

# -------------------------------
# DYNAMIC CHART GENERATION
# -------------------------------
def clean_output(text):
    """Remove formatting artifacts and chart placeholders from AI output"""
    import re
    # Remove [Insert Chart X: ...] patterns
    text = re.sub(r'\[Insert Chart \d+:.*?\]', '', text, flags=re.DOTALL)
    # Remove <Chart: ...> patterns
    text = re.sub(r'<Chart:.*?>', '', text, flags=re.DOTALL)
    
    # Clean up broken spacing in numbers/currency (fixes italics issue)
    text = re.sub(r'(\d)([a-z])', r'\1 \2', text)  # "$285million" → "$285 million"
    text = re.sub(r'(\w)\s{2,}(\w)', r'\1 \2', text)  # Multiple spaces → single
    
    # Remove any lingering chart references
    lines = text.split('\n')
    cleaned_lines = [line for line in lines if not line.strip().startswith('<Chart') and not line.strip().startswith('[Insert Chart')]
    return '\n'.join(cleaned_lines).strip()

def generate_dynamic_chart(user_query, df):
    """Generate a chart based on what the user is asking about"""
    query_lower = user_query.lower()
    
    # Channel mix / investment / budget allocation questions
    if any(word in query_lower for word in ['channel mix', 'investment', '$100m', '$200m', '$300m', 'optimal', 'allocation']):
        data = df.groupby('Channel').agg({
            'ROAS': 'mean',
            'Spend ($)': 'sum',
            'Revenue ($)': 'sum'
        }).reset_index().sort_values('ROAS', ascending=False).head(10)
        
        chart = alt.Chart(data).mark_bar(color='#8b5cf6').encode(
            x=alt.X('Channel:N', sort='-y'),
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Channel', alt.Tooltip('ROAS:Q', format='.2f'), alt.Tooltip('Spend ($):Q', format='$,.0f')]
        ).properties(width=800, height=400, title='Channel Performance by ROAS').interactive()
        
        return chart
    
    # ROI and CPA by format
    elif any(word in query_lower for word in ['roi', 'highest roi', 'cpa', 'format']):
        data = df.groupby('Format').agg({
            'ROAS': 'mean',
            'CPA ($)': 'mean',
            'Revenue ($)': 'sum'
        }).reset_index().sort_values('ROAS', ascending=False)
        
        base = alt.Chart(data).encode(x='Format:N')
        
        roas_chart = base.mark_bar(color='#10b981').encode(
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Format', alt.Tooltip('ROAS:Q', format='.2f'), alt.Tooltip('CPA ($):Q', format='$,.2f')]
        )
        
        cpa_line = base.mark_line(point=True, color='#ef4444', size=3).encode(
            y=alt.Y('CPA ($):Q', title='CPA ($)', axis=alt.Axis(orient='right')),
            tooltip=['Format', alt.Tooltip('CPA ($):Q', format='$,.2f')]
        )
        
        return alt.layer(roas_chart, cpa_line).resolve_scale(y='independent').properties(
            width=800, height=400, title='Format Performance: ROAS vs CPA'
        ).interactive()
    
    # Click-to-conversion rates by channel/publisher
    elif any(word in query_lower for word in ['click', 'conversion rate', 'click-to-conversion', 'strongest']):
        data = df.groupby('Channel').agg({
            'Conversion Rate (%)': 'mean',
            'CTR (%)': 'mean',
            'Conversions': 'sum'
        }).reset_index().sort_values('Conversion Rate (%)', ascending=False).head(10)
        
        chart = alt.Chart(data).mark_bar(color='#3b82f6').encode(
            x=alt.X('Channel:N', sort='-y'),
            y=alt.Y('Conversion Rate (%):Q', title='Conversion Rate (%)'),
            tooltip=['Channel', alt.Tooltip('Conversion Rate (%):Q', format='.2f'), alt.Tooltip('CTR (%):Q', format='.2f')]
        ).properties(width=800, height=400, title='Channels by Conversion Rate').interactive()
        
        return chart
    
    # Churn analysis by month
    elif any(word in query_lower for word in ['churn', 'month', 'highest churn', 'internal', 'external', 'driver']):
        df_copy = df.copy()
        df_copy['Month'] = ((df_copy['Week'] - 1) // 4) + 1
        data = df_copy.groupby('Month').agg({
            'Conversions': 'sum',
            'Spend ($)': 'sum',
            'ROAS': 'mean',
            'CPA ($)': 'mean'
        }).reset_index()
        
        # Calculate churn proxy (inverse of conversions normalized)
        data['Churn Index'] = 100 - (data['Conversions'] / data['Conversions'].max() * 100)
        
        chart = alt.Chart(data).mark_line(point=True, color='#ef4444', size=3).encode(
            x=alt.X('Month:Q', title='Month'),
            y=alt.Y('Churn Index:Q', title='Churn Index'),
            tooltip=['Month', alt.Tooltip('Churn Index:Q', format='.1f'), alt.Tooltip('Conversions:Q', format=',.0f')]
        ).properties(width=800, height=400, title='Churn Index by Month').interactive()
        
        return chart
    
    # Video vs Static engagement
    elif any(word in query_lower for word in ['video', 'static', 'engagement', 'higher engagement']):
        data = df[df['Format'].isin(['Video', 'Static'])].groupby('Format').agg({
            'CTR (%)': 'mean',
            'Time on Site (min)': 'mean',
            'Pages Per Session': 'mean',
            'Social Likes': 'sum',
            'Social Shares': 'sum'
        }).reset_index()
        
        chart = alt.Chart(data).mark_bar(color='#06b6d4').encode(
            x='Format:N',
            y=alt.Y('CTR (%):Q', title='Average CTR (%)'),
            tooltip=['Format', alt.Tooltip('CTR (%):Q', format='.2f'), alt.Tooltip('Time on Site (min):Q', format='.1f')]
        ).properties(width=800, height=400, title='Video vs Static: Engagement Metrics').interactive()
        
        return chart
    
    # Audience segment performance
    elif any(word in query_lower for word in ['audience', 'segment', 'underperforming', 'demographic', 'behavioral']):
        data = df.groupby('Audience Segment (Demographic)').agg({
            'ROAS': 'mean',
            'CPA ($)': 'mean'
        }).reset_index()
        
        base = alt.Chart(data).encode(x='Audience Segment (Demographic):N')
        
        roas_chart = base.mark_bar(color='#00d4ff').encode(
            y=alt.Y('ROAS:Q', title='ROAS'),
            tooltip=['Audience Segment (Demographic)', alt.Tooltip('ROAS:Q', format='.2f')]
        )
        
        cpa_line = base.mark_line(point=True, color='#ef4444', size=3).encode(
            y=alt.Y('CPA ($):Q', title='CPA ($)', axis=alt.Axis(orient='right')),
            tooltip=['Audience Segment (Demographic)', alt.Tooltip('CPA ($):Q', format='$,.2f')]
        )
        
        return alt.layer(roas_chart, cpa_line).resolve_scale(y='independent').properties(
            width=800, height=400, title='Audience Segment Performance'
        ).interactive()
    
    # Social vs Display ROAS drivers
    elif any(word in query_lower for word in ['social', 'display', 'roas', 'driving']):
        social_publishers = ['Meta', 'TikTok', 'LinkedIn']
        display_publishers = ['NZ Herald', 'TVNZ']
        
        df_copy = df.copy()
        df_copy['Channel Type'] = df_copy['Publisher'].apply(
            lambda x: 'Social' if x in social_publishers else ('Display' if x in display_publishers else 'Other')
        )
        
        data = df_copy[df_copy['Channel Type'].isin(['Social', 'Display'])].groupby('Channel Type').agg({
            'ROAS': 'mean',
            'CTR (%)': 'mean',
            'Conversion Rate (%)': 'mean',
            'Revenue ($)': 'sum'
        }).reset_index()
        
        chart = alt.Chart(data).mark_bar(color='#ec4899').encode(
            x='Channel Type:N',
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Channel Type', alt.Tooltip('ROAS:Q', format='.2f'), alt.Tooltip('CTR (%):Q', format='.2f')]
        ).properties(width=800, height=400, title='Social vs Display: ROAS Comparison').interactive()
        
        return chart
    
    # Default fallback
    else:
        data = df.groupby('Channel').agg({
            'ROAS': 'mean'
        }).reset_index().sort_values('ROAS', ascending=False).head(10)
        
        chart = alt.Chart(data).mark_bar(color='#00d4ff').encode(
            x=alt.X('Channel:N', sort='-y'),
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Channel', alt.Tooltip('ROAS:Q', format='.2f')]
        ).properties(width=800, height=400, title='Channel Performance by ROAS').interactive()
        
        return chart

# -------------------------------
# MAIN LAYOUT
# -------------------------------

# Share button in top right
col_title, col_share = st.columns([6, 1])
with col_title:
    st.title("")
with col_share:
    current_url = "https://dentsusolutions.com/"  # Update with your actual deployed URL
    if st.button("🔗 Share", use_container_width=True):
        st.code(current_url, language=None)
        st.success("Link ready to share!")

# DISPLAY PREVIOUS MESSAGES
for msg in st.session_state.chat_history:
    if msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])

# Check if rerunning from history
preset_input = None
if "rerun_question" in st.session_state:
    preset_input = st.session_state.rerun_question
    del st.session_state.rerun_question

# Initialize chat started flag
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

# Quick Questions (above chat input) - line by line in rectangular form
# Only show if chat hasn't started
if not st.session_state.chat_started:
    st.markdown("### 💡 Quick Questions")
    preset_questions = [
        "💰 Recommend optimal channel mixes for $100M, $200M, and $300M investment levels.",
        "📊 Determine which formats delivered the highest ROI.",
        "🎯 Evaluate channels & publishers with the strongest click-to-conversion rates.",
        "📉 Highlight months with the highest churn and distinguish internal vs. external drivers.",
        "🎥 Is Video or Static driving higher engagement?",
        "👥 Which audience segment is underperforming?",
        "📱 What's driving ROAS on Social vs Display?"
    ]

    # Create centered container for questions
    st.markdown('<div class="question-container">', unsafe_allow_html=True)
    for question in preset_questions:
        col = st.container()
        with col:
            if st.button(question, use_container_width=True, key=f"preset_{question}"):
                preset_input = question
                st.session_state.chat_started = True
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # Show questions in bottom left when chat has started
    with st.sidebar:
        st.divider()
        st.subheader("💡 Quick Questions")
        preset_questions = [
            "💰 Recommend optimal channel mixes for $100M, $200M, and $300M investment levels.",
            "📊 Determine which formats delivered the highest ROI.",
            "🎯 Evaluate channels & publishers with the strongest click-to-conversion rates.",
            "📉 Highlight months with the highest churn and distinguish internal vs. external drivers.",
            "🎥 Is Video or Static driving higher engagement?",
            "👥 Which audience segment is underperforming?",
            "📱 What's driving ROAS on Social vs Display?"
        ]
        
        for question in preset_questions:
            if st.button(question, use_container_width=True, key=f"sidebar_preset_{question}"):
                preset_input = question

# CHAT INPUT
user_input = st.chat_input("Select a prompt above or type your custom prompt here")

# Use preset input if a button was clicked
if preset_input:
    user_input = preset_input

if user_input:
    # Add to question history
    if "question_history" not in st.session_state:
        st.session_state.question_history = []
    
    st.session_state.question_history.append({
        "text": user_input,
        "date": datetime.now().date(),
        "timestamp": datetime.now().isoformat()
    })
    
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analysing performance..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=st.session_state.chat_history
                )
                output = response.choices[0].message.content
                cleaned_output = clean_output(output)
                st.markdown(cleaned_output)
                
                chart = generate_dynamic_chart(user_input, df)
                st.altair_chart(chart, use_container_width=True)
                
                st.session_state.chat_history.append({"role": "assistant", "content": cleaned_output})
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str or "rate limit" in error_str or "429" in error_str:
                    st.warning("⚠️ Too many messages sent. Please wait a moment and try again.")
                else:
                    st.error(f"Error from Groq API: {e}")

# -------------------------------
# LEGAL DISCLAIMER
# -------------------------------
st.markdown("---")
st.markdown("""
<div style="background-color: #481d00; margin-bottom: 32px; padding: 16px; font-size: 14px; border-radius: 8px;">
    <p style="margin: 0;">Legal Disclaimer — The insights and visualisations generated by this tool are for informational purposes only and should not be considered financial, legal, or business advice.</p>
</div>
""", unsafe_allow_html=True)
