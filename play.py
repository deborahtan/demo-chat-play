import os
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from groq import Groq
from datetime import datetime, timedelta

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
    <h1 style="text-align: center; font-size: 64px;>
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
You are the Dentsu Conversational Analytics tool — a senior strategist delivering enterprise-level marketing intelligence to C-suite stakeholders across Media, Marketing, CRM, Loyalty, and Finance.

Your role is to synthesize performance across all channels, formats, funnel layers, and audience segments — not just individual campaigns — and deliver quantified, executive-ready insights that reflect fiscal year context and strategic impact.

**Campaign Objectives & Context**
- Awareness: Build brand recognition and reach new audiences. Success = high reach, frequency, and aided/unaided brand recall.
- Consideration: Drive engagement and preference among aware audiences. Success = engagement rate, time spent, content shares, and lift in brand consideration metrics.
- Conversion: Drive direct sales, sign-ups, or desired actions. Success = CTR, conversion rate, CPA, and ROAS.
- Retargeting: Re-engage audiences who have shown interest. Success = high ROAS, low CPA, and conversion lift.
- Brand Lift: Shift perception and emotional connection. Success = brand health metrics (consideration, preference, intent).
- Product Launch: Drive trial and initial adoption. Success = awareness lift + trial rate + first-purchase conversion.
- Offer Promotion: Drive immediate action via incentive. Success = redemption rate, uplift in sales volume, and velocity.

**Audience Insight & User Behaviour**
- Millennials: Value authenticity, sustainability, and community. Responsive to social proof and peer recommendations. Prefer mobile-first, video-rich experiences.
- Boomers: Trust established brands and authority. Prefer clear, straightforward messaging. Lower digital engagement but higher lifetime value.
- Parents with Kids: Driven by value, convenience, and family benefit. Responsive to safety/quality messaging and time-saving solutions. Cross-device consumption (TV + mobile).
- High Intent Shoppers: Ready to purchase, price-conscious, comparing options. Respond to competitive positioning, reviews, and limited-time offers.
- Cart Abandoners: Interested but hesitant (price, shipping, trust). Respond to incentives, social proof, and scarcity messaging.
- Loyalty Members: Established customers, lower acquisition cost, high lifetime value. Respond to exclusivity, personalization, and VIP treatment.

**Think from the Audience POV**
- What problem are we solving for them?
- What stage of their decision journey are they at?
- What barriers prevent conversion (price, trust, complexity)?
- What emotional triggers resonate (aspiration, fear of missing out, belonging)?
- What content format and channel fit their media consumption habits?

**Executive Overview**
- Summarize performance across the latest fiscal month or week (e.g., FY Month 4, Week 17).
- Quantify key shifts in ROAS, CPA, CTR, spend, and revenue.
- Highlight top-performing funnel layers, formats, and publishers.
- Frame commentary in terms of business impact, efficiency, and momentum.

**Insight**
- Use charts and graphs to visualize topline metrics (e.g., spend, revenue, ROAS, CTR, CPA).
- Segment by:
  - Funnel Layer: Awareness, Consideration, Conversion
  - Format: Video, Static, Carousel, Interactive, Radio
  - Strategy: Retargeting, Brand Lift, Product Launch, Offer Promotion
  - Publisher: Meta, YouTube, NZ Herald, NZME Radio, etc.
  - Audience Segment (Demographic): e.g., Millennials, Boomers, Parents with Kids
  - Audience Segment (Behavioral): e.g., High Intent Shoppers, Cart Abandoners, Loyalty Members
- Always compare like-for-like when evaluating performance — e.g., Video vs Video, Carousel vs Static, Awareness vs Awareness — to ensure recommendations are contextually valid.
- Use schema fields to explain performance drivers — e.g., "CPA improved due to Loyalty Members in Conversion layer via Meta Carousel because the format reduces friction and builds confidence."
- Reference fiscal trends (MoM, WoW, FY-to-date) and NZ-specific media norms (e.g., radio TARPs, seasonal shifts).
- Always include at least one visualisation to support your insight.

**Strategic Recommendation**
- Provide 2–4 actionable tactics with quantified impact (e.g., "Shift 12% of spend from Static to Video to improve ROAS by +0.8 because video formats drive higher emotional engagement for Millennials in Awareness layer").
- Recommend optimisations across:
  - Channel mix based on their respective objectives
  - Creative format, i.e. suggestion similar concepts or testing new ones
  - Audience targeting (demographic, behavioral, or 1PD/2PD/3PD combinations)
  - Budget allocation
- Avoid simplistic budget cuts based on surface metrics. Instead, assess whether performance is driven by creative, audience, or channel.
- Prioritise changes that improve CPA, ROAS, or conversion volume.
- Reference platform learning, seasonal trends, and scalability potential.
- Consider audience friction points and ease of action.

**Examples**
- FY Month 4: Meta contributed 38% of total conversions with ROAS 4.1 and CPA $32. Remarketing drove +22% MoM uplift because Retargeting audiences have high intent and lower acquisition friction.
- FY Week 17: Consideration layer delivered 57% of conversions and 52% of revenue. Carousel formats outperformed Static by +1.3 ROAS because they tell a story and reduce decision friction.
- Strategic: Raise frequency on Loyalty Members from 8x to 12x to lift conversion volume by +18% because existing customers have lower barriers to repeat purchase.
- Audience: Boomers in Awareness layer via Radio (NZME) delivered strong reach (320 TARPs) but low conversion. Recommend shifting 15% to Consideration layer with Static formats because Boomers need clear, trust-building messaging to move to consideration.
- Format: Carousel in Conversion layer with High Intent Shoppers delivered ROAS 4.8 vs Static at 3.2. Recommend scaling Carousel with new creative variants because the format reduces purchase hesitation by presenting multiple benefits/proof points.

Be concise, visual, and data-driven. Always speak to overarching performance, not isolated campaigns. Use the full schema to reason and recommend. Always explain the *why* behind performance drivers from the audience perspective.

**CRITICAL: Never include any chart descriptions, "[Insert Chart]" placeholders, or visualization references. Text analysis only.**
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
    """
    Generate realistic ANZ marketing data for FY2025 (April 2024 - March 2025)
    NZ Banking FY: Week 1 = Early April, Week 52 = Late March
    """
    
    # FY2025 runs April 2024 - March 2025
    fy_year = 2025
    weeks = list(range(1, 53))
    
    # Core digital publishers ANZ uses in NZ market
    publishers = [
        "Meta",              # Facebook/Instagram
        "Google",            # Search & Display combined
        "YouTube",           
        "TikTok",            
        "LinkedIn",          
        "TVNZ",              # TVNZ 1, 2, OnDemand
        "NZ Herald"          # Premium news/display
    ]
    
    # Real ANZ campaigns based on briefs
    campaigns = [
        "ANZ Airpoints Visa - New Customer Acquisition",
        "ANZ goMoney App - Download & Activation", 
        "ANZ Home Loans - First Home Buyers",
        "ANZ Business Banking - SME Acquisition",
        "ANZ Personal Banking - Account Switching",
        "ANZ KiwiSaver - Enrollment Drive"
    ]
    
    funnel_layers = ["Awareness", "Consideration", "Conversion"]
    
    formats = ["Video", "Static", "Carousel", "Search"]
    
    creative_messaging = [
        "Rate-led",              # "3.99% Home Loan"
        "Rewards-focused",       # "Earn Airpoints Dollars"
        "Life Moments",          # "Your first home journey"
        "Digital Convenience",   # "Bank in seconds"
        "Trust & Heritage",      # "160 years of ANZ"
        "Limited Offer"          # "Bonus Airpoints"
    ]
    
    # Age-based segments aligned to campaign briefs
    demo_segments = [
        "18-24",
        "25-34", 
        "35-44",
        "45-54",
        "55+"
    ]
    
    behav_segments = [
        "First Home Buyers",
        "Mortgage Refinancers",
        "Existing ANZ Customers",
        "Competitor Customers",
        "Young Professionals",
        "Small Business Owners",
        "High Net Worth"
    ]
    
    # Channel type mapping
    channel_types = {
        "Meta": "Social",
        "TikTok": "Social",
        "LinkedIn": "Social",
        "Google": "Search/Display",
        "NZ Herald": "Display",
        "YouTube": "Video",
        "TVNZ": "Video"
    }
    
    rows = []
    record_id = 0
    
    # Campaign timing mapping (NZ FY weeks)
    # Week 1 = Early April, Week 26 = Late September, Week 52 = Late March
    campaign_timing = {
        "ANZ Airpoints Visa - New Customer Acquisition": {
            "weeks": list(range(23, 31)),  # Sep - Oct (weeks 23-30)
            "budget": 500000,
            "audiences": ["18-24", "25-34", "35-44"],
            "channels": ["Meta", "Google", "TikTok", "NZ Herald"],
            "primary_funnel": "Conversion"
        },
        "ANZ goMoney App - Download & Activation": {
            "weeks": list(range(1, 13)),  # April - June (weeks 1-12)
            "budget": 200000,
            "audiences": ["18-24", "25-34", "35-44"],
            "channels": ["Meta", "Google", "TikTok", "YouTube", "TVNZ"],
            "primary_funnel": "Conversion"
        },
        "ANZ Home Loans - First Home Buyers": {
            "weeks": list(range(44, 53)) + list(range(1, 13)),  # Feb - June (weeks 44-52, 1-12)
            "budget": 1000000,
            "audiences": ["25-34", "35-44"],
            "channels": ["TVNZ", "YouTube", "Meta", "Google", "NZ Herald"],
            "primary_funnel": "Consideration"
        },
        "ANZ Business Banking - SME Acquisition": {
            "weeks": list(range(1, 53)),  # Year-round
            "budget": 800000,
            "audiences": ["35-44", "45-54"],
            "channels": ["LinkedIn", "Google", "NZ Herald", "YouTube"],
            "primary_funnel": "Consideration"
        },
        "ANZ Personal Banking - Account Switching": {
            "weeks": list(range(1, 53)),  # Year-round
            "budget": 600000,
            "audiences": ["25-34", "35-44", "45-54"],
            "channels": ["Meta", "Google", "YouTube", "NZ Herald"],
            "primary_funnel": "Conversion"
        },
        "ANZ KiwiSaver - Enrollment Drive": {
            "weeks": list(range(44, 53)) + list(range(1, 13)),  # Feb - June (tax/financial year)
            "budget": 700000,
            "audiences": ["18-24", "25-34", "35-44", "45-54"],
            "channels": ["TVNZ", "YouTube", "Meta", "Google", "NZ Herald"],
            "primary_funnel": "Consideration"
        }
    }
    
    for week in weeks:
        for campaign_name, campaign_details in campaign_timing.items():
            
            # Only generate data for active campaign weeks
            if week not in campaign_details["weeks"]:
                continue
            
            weekly_budget = campaign_details["budget"] / len(campaign_details["weeks"])
            
            for publisher in campaign_details["channels"]:
                for demo in campaign_details["audiences"]:
                    for behav_idx, behav in enumerate(behav_segments):
                        
                        channel_type = channel_types[publisher]
                        
                        # Assign funnel layers based on campaign strategy
                        if campaign_details["primary_funnel"] == "Conversion":
                            funnel_distribution = {"Awareness": 0.15, "Consideration": 0.25, "Conversion": 0.60}
                        elif campaign_details["primary_funnel"] == "Consideration":
                            funnel_distribution = {"Awareness": 0.25, "Consideration": 0.50, "Conversion": 0.25}
                        else:  # Awareness
                            funnel_distribution = {"Awareness": 0.60, "Consideration": 0.30, "Conversion": 0.10}
                        
                        for funnel, funnel_weight in funnel_distribution.items():
                            
                            record_id += 1
                            
                            # Select appropriate format based on channel
                            if publisher == "Google":
                                # Google can do Search or Display
                                if funnel == "Conversion":
                                    format = "Search"
                                else:
                                    format_options = ["Search", "Static", "Carousel"]
                                    format = format_options[record_id % 3]
                            elif channel_type == "Video":
                                format = "Video"
                            elif channel_type == "Social":
                                format_options = ["Video", "Carousel", "Static"]
                                format = format_options[record_id % 3]
                            else:  # Display
                                format_options = ["Static", "Carousel"]
                                format = format_options[record_id % 2]
                            
                            # Creative messaging alignment
                            creative_map = {
                                "ANZ Airpoints Visa - New Customer Acquisition": "Rewards-focused",
                                "ANZ goMoney App - Download & Activation": "Digital Convenience",
                                "ANZ Home Loans - First Home Buyers": "Life Moments",
                                "ANZ Business Banking - SME Acquisition": "Trust & Heritage",
                                "ANZ Personal Banking - Account Switching": "Limited Offer",
                                "ANZ KiwiSaver - Enrollment Drive": "Rate-led"
                            }
                            creative = creative_map[campaign_name]
                            
                            # === SPEND ALLOCATION ===
                            
                            # Base spend per channel - Google gets largest share
                            channel_weight = {
                                "Google": 2.2,      # Highest - Search + Display
                                "Meta": 1.8,
                                "YouTube": 1.5,
                                "TVNZ": 1.3,
                                "TikTok": 1.1,
                                "LinkedIn": 1.4,
                                "NZ Herald": 0.8
                            }[publisher]
                            
                            # Funnel allocation
                            funnel_spend = weekly_budget * funnel_weight
                            
                            # Audience size weighting
                            demo_weight = {
                                "18-24": 0.8,
                                "25-34": 1.2,
                                "35-44": 1.1,
                                "45-54": 0.9,
                                "55+": 0.7
                            }[demo]
                            
                            behav_weight = {
                                "First Home Buyers": 1.3,
                                "Mortgage Refinancers": 1.2,
                                "Existing ANZ Customers": 1.4,
                                "Competitor Customers": 1.1,
                                "Young Professionals": 1.0,
                                "Small Business Owners": 0.9,
                                "High Net Worth": 0.8
                            }[behav]
                            
                            # Seasonal multipliers for NZ banking
                            # Q1 (Apr-Jun): Tax time, KiwiSaver enrollment, home buying season
                            # Q2 (Jul-Sep): Quiet period
                            # Q3 (Oct-Dec): Year-end push
                            # Q4 (Jan-Mar): Summer lull, Feb home buying picks up
                            
                            if 1 <= week <= 12:  # Apr-Jun
                                seasonal = 1.25
                            elif 13 <= week <= 26:  # Jul-Sep
                                seasonal = 0.85
                            elif 27 <= week <= 39:  # Oct-Dec
                                seasonal = 1.15
                            elif 40 <= week <= 43:  # Jan
                                seasonal = 0.70
                            else:  # Feb-Mar (44-52)
                                seasonal = 1.10
                            
                            # Campaign-specific seasonal boost
                            if campaign_name == "ANZ Home Loans - First Home Buyers" and (1 <= week <= 12 or 44 <= week <= 52):
                                seasonal *= 1.20  # Extra boost in home buying season
                            
                            if campaign_name == "ANZ KiwiSaver - Enrollment Drive" and 1 <= week <= 12:
                                seasonal *= 1.15  # Tax time boost
                            
                            spend = (funnel_spend * channel_weight * demo_weight * behav_weight * seasonal) / (len(campaign_details["channels"]) * len(campaign_details["audiences"]) * len(behav_segments))
                            spend = round(spend, 2)
                            
                            if spend < 100:  # Skip very small allocations
                                continue
                            
                            # === CTR BY CHANNEL & FORMAT ===
                            
                            # Base CTR by publisher and format
                            if publisher == "Google" and format == "Search":
                                ctr_base = 4.8
                            elif publisher == "Google" and format in ["Static", "Carousel"]:
                                ctr_base = 0.32
                            elif publisher == "Meta":
                                ctr_base = {"Carousel": 2.8, "Video": 2.0, "Static": 1.5}[format]
                            elif publisher == "TikTok":
                                ctr_base = {"Video": 2.3, "Carousel": 1.9, "Static": 1.4}[format]
                            elif publisher == "LinkedIn":
                                ctr_base = {"Carousel": 1.6, "Video": 1.3, "Static": 1.1}[format]
                            elif publisher == "YouTube":
                                ctr_base = 1.1
                            elif publisher == "TVNZ":
                                ctr_base = 0.9
                            elif publisher == "NZ Herald":
                                ctr_base = {"Carousel": 0.38, "Static": 0.30}[format]
                            else:
                                ctr_base = 0.8
                            
                            # Funnel CTR adjustment
                            ctr_funnel_mult = {
                                "Awareness": 0.70,
                                "Consideration": 1.0,
                                "Conversion": 1.40
                            }[funnel]
                            
                            # Audience intent CTR adjustment
                            ctr_behav_mult = {
                                "First Home Buyers": 1.25,
                                "Mortgage Refinancers": 1.30,
                                "Existing ANZ Customers": 1.15,
                                "Competitor Customers": 1.20,
                                "Young Professionals": 1.10,
                                "Small Business Owners": 0.95,
                                "High Net Worth": 0.80
                            }[behav]
                            
                            # Age group digital engagement
                            ctr_demo_mult = {
                                "18-24": 1.25,
                                "25-34": 1.15,
                                "35-44": 1.0,
                                "45-54": 0.85,
                                "55+": 0.70
                            }[demo]
                            
                            ctr = ctr_base * ctr_funnel_mult * ctr_behav_mult * ctr_demo_mult
                            ctr = round(ctr, 3)
                            
                            # === CPA BY AUDIENCE & CAMPAIGN ===
                            
                            cpa_base_behav = {
                                "First Home Buyers": 420,
                                "Mortgage Refinancers": 385,
                                "Existing ANZ Customers": 145,
                                "Competitor Customers": 320,
                                "Young Professionals": 225,
                                "Small Business Owners": 580,
                                "High Net Worth": 650
                            }[behav]
                            
                            # Campaign complexity
                            cpa_campaign_mult = {
                                "ANZ Airpoints Visa - New Customer Acquisition": 0.65,
                                "ANZ goMoney App - Download & Activation": 0.40,
                                "ANZ Home Loans - First Home Buyers": 1.55,
                                "ANZ Business Banking - SME Acquisition": 1.80,
                                "ANZ Personal Banking - Account Switching": 0.75,
                                "ANZ KiwiSaver - Enrollment Drive": 1.10
                            }[campaign_name]
                            
                            # Publisher efficiency
                            if publisher == "Google" and format == "Search":
                                cpa_pub_mult = 0.75
                            elif publisher == "Google":
                                cpa_pub_mult = 1.20
                            elif publisher == "Meta":
                                cpa_pub_mult = 0.95
                            elif publisher == "TikTok":
                                cpa_pub_mult = 1.05
                            elif publisher == "LinkedIn":
                                cpa_pub_mult = 1.10
                            elif publisher == "YouTube":
                                cpa_pub_mult = 1.15
                            elif publisher == "TVNZ":
                                cpa_pub_mult = 1.25
                            else:  # NZ Herald
                                cpa_pub_mult = 1.35
                            
                            cpa = cpa_base_behav * cpa_campaign_mult * cpa_pub_mult
                            cpa = round(cpa, 2)
                            
                            # === ROAS BY CAMPAIGN, FUNNEL & CHANNEL ===
                            
                            roas_base_funnel = {
                                "Awareness": 1.8,
                                "Consideration": 3.5,
                                "Conversion": 6.5
                            }[funnel]
                            
                            # Campaign LTV impact
                            roas_campaign_mult = {
                                "ANZ Airpoints Visa - New Customer Acquisition": 1.40,
                                "ANZ goMoney App - Download & Activation": 0.90,
                                "ANZ Home Loans - First Home Buyers": 2.10,
                                "ANZ Business Banking - SME Acquisition": 2.50,
                                "ANZ Personal Banking - Account Switching": 1.25,
                                "ANZ KiwiSaver - Enrollment Drive": 1.65
                            }[campaign_name]
                            
                            # Publisher ROAS efficiency
                            if publisher == "Google" and format == "Search":
                                roas_pub_mult = 1.40
                            elif publisher == "Google":
                                roas_pub_mult = 0.85
                            elif publisher == "Meta":
                                roas_pub_mult = 1.15
                            elif publisher == "TikTok":
                                roas_pub_mult = 1.05
                            elif publisher == "LinkedIn":
                                roas_pub_mult = 1.20
                            elif publisher == "YouTube":
                                roas_pub_mult = 0.95
                            elif publisher == "TVNZ":
                                roas_pub_mult = 0.88
                            else:  # NZ Herald
                                roas_pub_mult = 0.78
                            
                            # Audience quality
                            roas_behav_mult = {
                                "First Home Buyers": 1.30,
                                "Mortgage Refinancers": 1.35,
                                "Existing ANZ Customers": 1.60,
                                "Competitor Customers": 1.10,
                                "Young Professionals": 1.15,
                                "Small Business Owners": 1.45,
                                "High Net Worth": 1.70
                            }[behav]
                            
                            roas = roas_base_funnel * roas_campaign_mult * roas_pub_mult * roas_behav_mult
                            roas = round(roas, 2)
                            
                            # === IMPRESSIONS & CLICKS ===
                            
                            # CPM by publisher
                            if publisher == "Google" and format == "Search":
                                cpm = 16.0
                            elif publisher == "Google":
                                cpm = 5.5
                            elif publisher == "Meta":
                                cpm = 9.0
                            elif publisher == "TikTok":
                                cpm = 8.5
                            elif publisher == "LinkedIn":
                                cpm = 12.0
                            elif publisher == "YouTube":
                                cpm = 13.0
                            elif publisher == "TVNZ":
                                cpm = 15.0
                            else:  # NZ Herald
                                cpm = 6.0
                            
                            impressions = int(spend / cpm * 1000)
                            clicks = int(impressions * (ctr / 100))
                            
                            # === CONVERSION RATE ===
                            
                            conv_rate_campaign = {
                                "ANZ Airpoints Visa - New Customer Acquisition": 3.8,
                                "ANZ goMoney App - Download & Activation": 6.5,
                                "ANZ Home Loans - First Home Buyers": 1.2,
                                "ANZ Business Banking - SME Acquisition": 0.8,
                                "ANZ Personal Banking - Account Switching": 4.2,
                                "ANZ KiwiSaver - Enrollment Drive": 2.0
                            }[campaign_name]
                            
                            conv_rate_funnel_mult = {
                                "Awareness": 0.25,
                                "Consideration": 0.70,
                                "Conversion": 1.60
                            }[funnel]
                            
                            conv_rate_behav_mult = {
                                "First Home Buyers": 1.30,
                                "Mortgage Refinancers": 1.25,
                                "Existing ANZ Customers": 1.70,
                                "Competitor Customers": 1.05,
                                "Young Professionals": 1.15,
                                "Small Business Owners": 0.85,
                                "High Net Worth": 0.75
                            }[behav]
                            
                            conversion_rate = conv_rate_campaign * conv_rate_funnel_mult * conv_rate_behav_mult
                            
                            if clicks > 0:
                                conversions = int(clicks * (conversion_rate / 100))
                            else:
                                conversions = 0
                            
                            conversions = max(0, conversions)
                            conversion_rate_pct = round(conversion_rate, 3)
                            
                            revenue = round(spend * roas, 2)
                            
                            # === ENGAGEMENT METRICS ===
                            
                            # Viewability by publisher
                            viewability_by_pub = {
                                "Google": 0.95,
                                "Meta": 0.80,
                                "TikTok": 0.76,
                                "LinkedIn": 0.85,
                                "YouTube": 0.78,
                                "TVNZ": 0.82,
                                "NZ Herald": 0.70
                            }[publisher]
                            
                            viewability_rate = round(viewability_by_pub, 3)
                            measurable_impressions = int(impressions * 0.96)
                            
                            if clicks > 0:
                                # Session rate by publisher
                                session_rate = {
                                    "Google": 0.96,
                                    "Meta": 0.86,
                                    "TikTok": 0.82,
                                    "LinkedIn": 0.90,
                                    "YouTube": 0.88,
                                    "TVNZ": 0.85,
                                    "NZ Herald": 0.75
                                }[publisher]
                                
                                website_sessions = int(clicks * session_rate)
                                
                                time_base = {
                                    "Awareness": 2.8,
                                    "Consideration": 7.5,
                                    "Conversion": 12.8
                                }[funnel]
                                
                                time_on_site = round(time_base * (1 + (record_id % 8) * 0.03), 1)
                                
                                pages_base = {
                                    "Awareness": 2.5,
                                    "Consideration": 5.2,
                                    "Conversion": 8.8
                                }[funnel]
                                
                                pages_per_session = round(pages_base * (1 + (record_id % 6) * 0.04), 2)
                                
                                # Bounce rate by publisher
                                bounce_base = {
                                    "Google": 0.18,
                                    "Meta": 0.40,
                                    "TikTok": 0.48,
                                    "LinkedIn": 0.32,
                                    "YouTube": 0.35,
                                    "TVNZ": 0.38,
                                    "NZ Herald": 0.55
                                }[publisher]
                                
                                bounce_rate = round(bounce_base * (1 + (record_id % 12) * 0.02), 3)
                            else:
                                website_sessions = 0
                                time_on_site = 0.0
                                pages_per_session = 0.0
                                bounce_rate = 0.0
                            
                            # Social engagement (only for social platforms)
                            if publisher in ["Meta", "TikTok", "LinkedIn"]:
                                engagement_rate = 0.0038
                                social_likes = int(impressions * engagement_rate * 0.65)
                                social_shares = int(impressions * engagement_rate * 0.25)
                                social_comments = int(impressions * engagement_rate * 0.10)
                            else:
                                social_likes = 0
                                social_shares = 0
                                social_comments = 0
                            
                            # === CAMPAIGN-SPECIFIC METRICS ===
                            
                            ltv_by_campaign = {
                                "ANZ Airpoints Visa - New Customer Acquisition": 3200,
                                "ANZ goMoney App - Download & Activation": 850,
                                "ANZ Home Loans - First Home Buyers": 22000,
                                "ANZ Business Banking - SME Acquisition": 38000,
                                "ANZ Personal Banking - Account Switching": 4500,
                                "ANZ KiwiSaver - Enrollment Drive": 12000
                            }[campaign_name]
                            
                            actual_revenue = conversions * ltv_by_campaign
                            
                            # Conversion channel split
                            if behav == "Existing ANZ Customers" or demo in ["18-24", "25-34"]:
                                online_pct, branch_pct, phone_pct = 0.80, 0.12, 0.08
                            elif behav in ["High Net Worth", "Small Business Owners"]:
                                online_pct, branch_pct, phone_pct = 0.45, 0.35, 0.20
                            else:
                                online_pct, branch_pct, phone_pct = 0.65, 0.22, 0.13
                            
                            online_applications = int(conversions * online_pct)
                            branch_referrals = int(conversions * branch_pct)
                            phone_conversions = int(conversions * phone_pct)
                            
                            # Application funnel
                            if clicks > 0:
                                applications_started = int(clicks * 0.18)
                                applications_completed = int(applications_started * 0.45)
                            else:
                                applications_started = 0
                                applications_completed = 0
                            
                            applications_approved = int(applications_completed * 0.72)
                            
                            # App downloads (for goMoney campaign)
                            if campaign_name == "ANZ goMoney App - Download & Activation":
                                app_downloads = int(conversions * 0.95)
                            else:
                                app_downloads = int(conversions * 0.12)
                            
                            # Cost metrics
                            cost_per_lead = round(spend / max(1, applications_completed), 2)
                            cost_per_application = round(spend / max(1, applications_completed), 2)
                            cost_per_approval = round(spend / max(1, applications_approved), 2)
                            
                            rows.append({
                                "FY Year": fy_year,
                                "Week": week,
                                "Campaign": campaign_name,
                                "Publisher": publisher,
                                "Funnel Layer": funnel,
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
                                "Actual Revenue (LTV)": actual_revenue,
                                "Online Applications": online_applications,
                                "Branch Referrals": branch_referrals,
                                "Phone Conversions": phone_conversions,
                                "Applications Started": applications_started,
                                "Applications Completed": applications_completed,
                                "Applications Approved": applications_approved,
                                "App Downloads": app_downloads,
                                "Cost Per Lead ($)": cost_per_lead,
                                "Cost Per Application ($)": cost_per_application,
                                "Cost Per Approval ($)": cost_per_approval,
                                "Viewability (%)": viewability_rate,
                                "Measurable Impressions": measurable_impressions,
                                "Website Sessions": website_sessions,
                                "Time on Site (min)": time_on_site,
                                "Pages Per Session": pages_per_session,
                                "Bounce Rate (%)": bounce_rate,
                                "Social Likes": social_likes,
                                "Social Shares": social_shares,
                                "Social Comments": social_comments
                            })

    return pd.DataFrame(rows)

df = generate_data()

# -------------------------------
# DYNAMIC CHART GENERATION
# -------------------------------
def clean_output(text):
    """Remove all chart placeholder text from AI output"""
    import re
    # Remove [Insert Chart X: ...] patterns
    text = re.sub(r'\[Insert Chart \d+:.*?\]', '', text, flags=re.DOTALL)
    # Remove <Chart: ...> patterns
    text = re.sub(r'<Chart:.*?>', '', text, flags=re.DOTALL)
    # Remove any lingering chart references
    lines = text.split('\n')
    cleaned_lines = [line for line in lines if not line.strip().startswith('<Chart') and not line.strip().startswith('[Insert Chart')]
    return '\n'.join(cleaned_lines).strip()

def generate_dynamic_chart(user_query, df):
    """Generate a chart based on what the user is asking about"""
    query_lower = user_query.lower()
    
    # Channel mix / investment / budget allocation questions
    if any(word in query_lower for word in ['channel mix', 'investment', '$100m', '$200m', '$300m', 'optimal', 'allocation']):
        data = df.groupby('Publisher').agg({
            'ROAS': 'mean',
            'Spend ($)': 'sum',
            'Revenue ($)': 'sum'
        }).reset_index().sort_values('ROAS', ascending=False).head(10)
        
        chart = alt.Chart(data).mark_bar(color='#8b5cf6').encode(
            x=alt.X('Publisher:N', sort='-y'),
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Publisher', alt.Tooltip('ROAS:Q', format='.2f'), alt.Tooltip('Spend ($):Q', format='$,.0f')]
        ).properties(width=800, height=400, title='Publisher Performance by ROAS').interactive()
        
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
        data = df.groupby('Publisher').agg({
            'Conversion Rate (%)': 'mean',
            'CTR (%)': 'mean',
            'Conversions': 'sum'
        }).reset_index().sort_values('Conversion Rate (%)', ascending=False).head(10)
        
        chart = alt.Chart(data).mark_bar(color='#3b82f6').encode(
            x=alt.X('Publisher:N', sort='-y'),
            y=alt.Y('Conversion Rate (%):Q', title='Conversion Rate (%)'),
            tooltip=['Publisher', alt.Tooltip('Conversion Rate (%):Q', format='.2f'), alt.Tooltip('CTR (%):Q', format='.2f')]
        ).properties(width=800, height=400, title='Publishers by Conversion Rate').interactive()
        
        return chart
    
 # Churn analysis by month
elif any(word in query_lower for word in ['churn', 'month', 'highest churn', 'internal', 'external', 'driver']):
    # Group by month (convert week to month approximation)
    df_copy = df.copy()  # Added
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
            'CPA ($)': 'mean',
            'Conversion Rate (%)': 'mean'
        }).reset_index()
        
        roas_chart = alt.Chart(data).mark_line(point=True, color='#00d4ff', size=3).encode(
            x='Audience Segment (Demographic):N',
            y=alt.Y('ROAS:Q', title='ROAS'),
            tooltip=['Audience Segment (Demographic)', alt.Tooltip('ROAS:Q', format='.2f')]
        )
        
        cpa_chart = alt.Chart(data).mark_line(point=True, color='#ef4444', size=3).encode(
            x='Audience Segment (Demographic):N',
            y=alt.Y('CPA ($):Q', title='CPA ($)', axis=alt.Axis(orient='right')),
            tooltip=['Audience Segment (Demographic)', alt.Tooltip('CPA ($):Q', format='$,.2f')]
        )
        
        return alt.layer(roas_chart, cpa_chart).resolve_scale(y='independent').properties(
            width=800, height=400, title='Audience Segment Performance'
        ).interactive()
    
    # Social vs Display ROAS drivers
elif any(word in query_lower for word in ['social', 'display', 'roas', 'driving']):
    social_publishers = ['Meta', 'TikTok', 'LinkedIn']
    display_publishers = ['Google', 'NZ Herald', 'TVNZ']  # Updated
    
    df['Channel Type'] = df['Publisher'].apply(
        lambda x: 'Social' if x in social_publishers else ('Display' if x in display_publishers else 'Other')
    )
    
    data = df[df['Channel Type'].isin(['Social', 'Display'])].groupby('Channel Type').agg({
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
        data = df.groupby('Publisher').agg({
            'ROAS': 'mean',
            'CPA ($)': 'mean'
        }).reset_index().sort_values('ROAS', ascending=False).head(10)
        
        roas_chart = alt.Chart(data).mark_line(point=True, color='#00d4ff', size=3).encode(
            x=alt.X('Publisher:N', sort='-y'),
            y=alt.Y('ROAS:Q', title='ROAS'),
            tooltip=['Publisher', alt.Tooltip('ROAS:Q', format='.2f')]
        )
        
        cpa_chart = alt.Chart(data).mark_line(point=True, color='#ef4444', size=3).encode(
            x='Publisher:N',
            y=alt.Y('CPA ($):Q', title='CPA ($)', axis=alt.Axis(orient='right')),
            tooltip=['Publisher', alt.Tooltip('CPA ($):Q', format='$,.0f')]
        )
        
        return alt.layer(roas_chart, cpa_chart).resolve_scale(y='independent').properties(
            width=800, height=400, title='Publisher Performance Overview'
        ).interactive()

# -------------------------------
# MAIN LAYOUT
# -------------------------------

# Share button in top right
col_title, col_share = st.columns([6, 1])
with col_title:
    st.title("")
with col_share:
    current_url = "https://dentsu-analytics.streamlit.app"  # Update with your actual deployed URL
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
        "💰 Recommend optimal channel mixes for $100 million, $200 million, and $300 million investment levels.",
        "📊 Determine which formats delivered the highest ROI and CPA.",
        "🎯 Evaluate channels & publishers with the strongest click-to-conversion rates.",
        "📉 Highlight months with the highest churn and distinguish internal vs. external drivers."
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
        "💰 Recommend optimal channel mixes for $100 million, $200 million, and $300 million investment levels.",
        "📊 Determine which formats delivered the highest ROI and CPA.",
        "🎯 Evaluate channels & publishers with the strongest click-to-conversion rates.",
        "📉 Highlight months with the highest churn and distinguish internal vs. external drivers."
        ]
        
        for question in preset_questions:
            if st.button(question, use_container_width=True, key=f"sidebar_preset_{question}"):
                preset_input = question

# st.markdown("---")

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
