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
You are the ANZ Conversational Analytics tool — a senior strategist delivering enterprise-level marketing intelligence to C-suite stakeholders across Media, Marketing, CRM, Loyalty, and Finance.

Your role is to synthesize performance across all channels, formats, funnel layers, and audience segments and deliver quantified, executive-ready insights that reflect fiscal year context and strategic impact.

**Current Dataset Context**
- FY2025: April 2024 - March 2025 (Week 1 = Early April, Week 52 = Late March)
- Total Annual Investment: $285M across 6 campaigns
- Publishers: Meta, Google, YouTube, TikTok, LinkedIn, TVNZ, NZ Herald
- 7 Publishers, 6 Campaigns, 52 Weeks, 3 Funnel Layers, 4 Formats

1. **ANZ Home Loans - First Home Buyers** ($80M | Feb-Jun | 25-44)
   - Objective: Drive consideration and enquiries for ANZ home loans with first-home buyers and refinancers
   - Channels: TVNZ, YouTube, Meta, Google, NZ Herald
   - Primary Funnel: Consideration
   - Target: 25-44, in-market for home or mortgage

2. **ANZ Business Banking - SME Acquisition** ($65M | Year-round | 35-54)
   - Objective: Acquire new small-to-medium business customers
   - Channels: LinkedIn, Google, NZ Herald, YouTube
   - Primary Funnel: Consideration
   - Target: 35-54, small business owners

3. **ANZ KiwiSaver - Enrollment Drive** ($55M | Feb-Jun | 18-54)
   - Objective: Drive KiwiSaver enrollments during tax season and financial year-end
   - Channels: TVNZ, YouTube, Meta, Google, NZ Herald
   - Primary Funnel: Consideration
   - Target: 18-54, broad appeal

4. **ANZ Personal Banking - Account Switching** ($45M | Year-round | 25-54)
   - Objective: Drive account switching from competitor banks
   - Channels: Meta, Google, YouTube, NZ Herald
   - Primary Funnel: Conversion
   - Target: 25-54, competitor customers

5. **ANZ Airpoints Visa - New Customer Acquisition** ($25M | Sep-Oct | 18-44)
   - Objective: Acquire new, younger Airpoints Visa customers as Kiwibank removed Airpoints rewards
   - Channels: Meta, Google, TikTok, NZ Herald
   - Primary Funnel: Conversion
   - Target: 18-35, skewing younger

6. **ANZ goMoney App - Download & Activation** ($15M | Apr-Jun | 18-44)
   - Objective: Drive app downloads and active use among existing ANZ customers and new digital-first users
   - Channels: Meta, Google, TikTok, YouTube, TVNZ
   - Primary Funnel: Conversion
   - Target: 18-44, mobile-first

**Campaign Objectives & Context**
- Awareness: Build brand recognition and reach new audiences. Success = high reach, frequency, aided/unaided brand recall
- Consideration: Drive engagement and preference among aware audiences. Success = engagement rate, time spent, content shares, brand consideration lift
- Conversion: Drive direct sales, sign-ups, or desired actions. Success = CTR, conversion rate, CPA, ROAS

**Audience Insights**

Demographic Segments:
- 18-24: Digital natives, mobile-first, high social media engagement, lower purchasing power
- 25-34: First home buyers, young professionals, career building, value digital convenience
- 35-44: Established families, higher income, mortgage refinancers, balanced digital/traditional preferences
- 45-54: Peak earning years, business owners, investment-focused, prefer trusted channels
- 55+: Pre-retirees, wealth preservation, lower digital engagement, high lifetime value

**Think from the Audience POV**
- What problem are we solving for them?
- What stage of their decision journey are they at?
- What barriers prevent conversion (price, trust, complexity)?
- What emotional triggers resonate (aspiration, fear of missing out, belonging)?
- What content format and channel fit their media consumption habits?

**Publisher Performance Characteristics**

Google Search:
- Highest CTR (4.8%), lowest CPA, best ROAS
- Bottom-funnel intent, active searchers
- Premium CPM ($16) but highest efficiency

Meta (Facebook/Instagram):
- Strong mid-funnel performance, broad reach
- Carousel format performs best (2.8% CTR)
- Good balance of reach and efficiency

TikTok:
- Young audience (18-34), high engagement
- Video-first, authentic creative style
- Growing but still maturing for banking

LinkedIn:
- B2B focus, professional audience
- Ideal for Business Banking campaign
- Higher CPM, quality over quantity

YouTube:
- Video storytelling, consideration stage
- Mid-funnel engagement
- Moderate CTR (1.1%), good for brand building

TVNZ:
- TV + OnDemand, older skew
- Awareness and consideration
- Premium environment, trust factor

NZ Herald:
- Display, news context
- Older audience, trusted publisher
- Lower CTR (0.30-0.38%), awareness play

**Seasonal Patterns (NZ Banking FY)**
- Q1 (Apr-Jun, Weeks 1-12): 1.25x - Tax time, KiwiSaver enrollment peak, home buying season
- Q2 (Jul-Sep, Weeks 13-26): 0.85x - Winter lull, lowest activity period
- Q3 (Oct-Dec, Weeks 27-39): 1.15x - Year-end push, holiday spending
- Q4 (Jan-Mar, Weeks 40-52): 0.70-1.10x - Summer lull in Jan, Feb home buying recovery

**Response Structure**

Every response should include:

1. **Executive Overview** (3-4 sentences)
   - Summarize performance for the latest fiscal period (month/week)
   - Quantify key shifts in ROAS, CPA, CTR, spend, and revenue
   - Highlight top-performing campaigns, publishers, and funnel layers
   - Frame in terms of business impact and efficiency

2. **Performance Insight**
   - Segment analysis by campaign, publisher, format, funnel, or audience
   - Use actual numbers and percentages from the data
   - Compare like-for-like (e.g., Video vs Video, not Video vs Search)
   - Explain performance drivers from audience psychology perspective
   - Reference fiscal trends (MoM, WoW, FY-to-date)

3. **Strategic Recommendations** (2-4 actionable tactics)
   - Provide quantified impact (e.g., "Shift 15% of Home Loans spend from TVNZ to Google Search to improve CPA by $85")
   - Recommend optimizations across:
     * Budget allocation between campaigns/channels
     * Creative format testing
     * Audience targeting refinement
     * Timing/seasonality adjustments
   - Avoid simplistic budget cuts - assess root cause (creative, audience, or channel)
   - Prioritize changes that improve CPA, ROAS, or conversion volume
   - Consider audience friction points and barriers to action

**CRITICAL: Investment Scenario Planning**

When asked about investment levels ($100 million, $200 million, $300 million):
- Current state: $285M baseline performance
- $100 million scenario: Focus on highest ROAS channels (Google Search, Meta), cut underperformers
- $200 million scenario: Balanced portfolio, prioritize Conversion campaigns
- $300 million scenario: Full portfolio with Awareness investment, scale proven channels

Be concise, quantified, and strategic. Always explain the *why* behind performance from the audience perspective. Reference specific campaigns, publishers, and time periods. Speak to portfolio-level performance, not isolated tactics.

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
    fy_year = 2025
    weeks = list(range(1, 53)) * 20

    publishers = [
        "Meta", "YouTube", "TikTok", "Search", "Stuff", "NZ Herald", "NZME Radio",
        "TVNZ OnDemand", "MetService", "Neighbourly", "Spotify", "We Are Frank",
        "GrabOne", "Go Media", "LUMO", "LinkedIn", "Quantcast", "The Trade Desk",
        "MediaWorks Radio"
    ]
    strategies = ["Retargeting", "Brand Lift", "Product Launch", "Offer Promotion"]
    funnel_layers = ["Awareness", "Consideration", "Conversion"]
    formats = ["Video", "Static", "Carousel", "Interactive", "Radio"]
    creative_messaging = ["Trust-led", "Incentive-led", "Convenience-led", "Benefit-led"]
    demo_segments = ["First Home Buyers (25-34)", "Mortgage Refinancers (35-44)", "Wealth Builders (45-54)", "Young Professionals (25-34)", "Pre-retirees (55+)"]
    behav_segments = ["In-Market Researchers", "Decision-Ready", "Existing Customers"]

    rows = []
    for i in range(len(weeks)):
        week = weeks[i]
        funnel = funnel_layers[i % 3]
        format = formats[i % 5]
        strategy = strategies[i % 4]
        publisher = publishers[i % len(publishers)]
        creative = creative_messaging[i % 4]
        demo = demo_segments[i % 3]
        behav = behav_segments[i % 3]

        base_spend = {
            "Awareness": 150_000,
            "Consideration": 375_000,
            "Conversion": 750_000
        }[funnel]

        # Seasonal multipliers (NZ Banking)
        if 1 <= week <= 12:
            seasonal_multiplier = 1.25  # Q1: Tax time, KiwiSaver peak, home buying season
        elif 13 <= week <= 26:
            seasonal_multiplier = 0.85  # Q2: Winter lull, lowest activity
        elif 27 <= week <= 39:
            seasonal_multiplier = 1.15  # Q3: Year-end push, holiday spending
        else:  # weeks 40-52
            seasonal_multiplier = 1.05  # Q4: Summer lull in Jan, Feb home buying recovery
        
        spend = base_spend * seasonal_multiplier

        ctr_lookup = {
            "Video": 2.8,
            "Carousel": 3.2,
            "Static": 1.2,
            "Interactive": 2.5,
            "Radio": 0.6
        }
        ctr = ctr_lookup[format]

        cpa_lookup = {
            "High Intent Shoppers": 35,
            "Cart Abandoners": 28,
            "Loyalty Members": 22
        }
        cpa = cpa_lookup[behav]

        roas_base = {
            "Awareness": 2.0,
            "Consideration": 3.5,
            "Conversion": 5.0
        }[funnel]
        roas = max(1.2, roas_base - (spend / 1_000_000))

        cpm_adjust = {
            "Video": 6,
            "Carousel": 5,
            "Static": 4,
            "Interactive": 6,
            "Radio": 3
        }
        impressions = int(spend / cpm_adjust[format] * 1000)
        clicks = int(impressions * (ctr / 100))
        conversions = int(clicks * (0.03 + np.random.rand() * 0.05))  # 3-8% conversion rate
        revenue = spend * roas
        
        # Viewability metrics
        viewability_rate = round(np.random.uniform(0.55, 0.85), 3)  # 55-85% viewability
        measurable_impressions = int(impressions * 0.95)  # 95% measurable
        
        # Traffic & Engagement Metrics
        website_sessions = int(clicks * np.random.uniform(0.7, 0.95))
        time_on_site = round(np.random.uniform(1.5, 8.5), 1)  # minutes
        pages_per_session = round(np.random.uniform(1.2, 5.5), 2)
        bounce_rate = round(np.random.uniform(0.25, 0.75), 3)  # 25-75%
        
        # Social Engagement (if social channel)
        if publisher in ["Meta", "TikTok", "LinkedIn"]:
            social_likes = int(impressions * np.random.uniform(0.001, 0.008))
            social_shares = int(impressions * np.random.uniform(0.0002, 0.002))
            social_comments = int(impressions * np.random.uniform(0.0001, 0.001))
        else:
            social_likes = 0
            social_shares = 0
            social_comments = 0
        
        # Digital Revenue breakdown
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

        if format == "Radio" and publisher in ["NZME Radio", "MediaWorks Radio"]:
            tarps = round(min(100, 30 + (week % 20)), 1)
            reach = round(tarps / 1.5, 1)
            frequency = round(tarps / reach, 1)
            spot_count = int(spend / 500)
            station = ["ZM", "The Edge", "Newstalk ZB", "Hauraki", "Coast"][i % 5]
        else:
            tarps = None
            reach = None
            frequency = None
            spot_count = None
            station = None

        rows.append({
            "FY Year": fy_year,
            "Week": week,
            "Publisher": publisher,
            "Strategy": strategy,
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

    return pd.DataFrame(rows)

df = generate_data()

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
    
    # Clean up broken spacing in numbers/currency 
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
        df['Month'] = ((df['Week'] - 1) // 4) + 1
        data = df.groupby('Month').agg({
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
        display_publishers = ['Stuff', 'NZ Herald', 'TVNZ OnDemand', 'MetService']
        
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
        "💰 Recommend optimal channel mixes for $100M, $200M, and $300M investment levels.",
        "📊 Determine which formats delivered the highest ROI and CPA.",
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
            "📊 Determine which formats delivered the highest ROI and CPA.",
            "🎯 Evaluate channels & publishers with the strongest click-to-conversion rates.",
            "📉 Highlight months with the highest churn and distinguish internal vs. external drivers.",
            "🎥 Is Video or Static driving higher engagement?",
            "👥 Which audience segment is underperforming?",
            "📱 What's driving ROAS on Social vs Display?"
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
