import os
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from groq import Groq

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(
    page_title="Dentsu Intelligence Assistant",
    page_icon="https://img.icons8.com/ios11/16/000000/dashboard-gauge.png",
    layout="wide"
)

# -------------------------------
# STYLING
# -------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #000;
    color: #fff;
}
h1,h2,h3,h4,h5,h6 {font-weight:600;color:#fff;}
[data-testid="stSidebar"] {
    background-color:#000;
    color:#fff;
}
[data-testid="stSidebar"] button {
    background-color:#fff !important;
    color:#000 !important;
    border-radius:6px;
    font-weight:600;
}
.answer-card {
    background-color:#2e2e2e;
    border-radius:12px;
    padding:20px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:
    st.image("https://www.dentsu.com/assets/images/main-logo-alt.png", width=160)
    st.header("Executive Chat")
    st.markdown("""
    **How to use**
    - Type any question about campaign performance or strategy.
    - The assistant responds with quantified, data-driven insight.
    - Conversation context is remembered.
    """)
    if st.button("🧹 Clear Conversation"):
        st.session_state.chat_history = []
        st.experimental_rerun()

# -------------------------------
# GROQ SETUP
# -------------------------------
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY. Add it to your environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

system_prompt = """
You are the Dentsu Intelligence Assistant — a senior strategist delivering enterprise-level marketing intelligence to C-suite stakeholders across Media, Marketing, CRM, Loyalty, and Finance.

Your role is to synthesize performance across all channels, formats, funnel layers, and audience segments — not just individual campaigns — and deliver quantified, executive-ready insights that reflect fiscal year context and strategic impact.

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
- Use schema fields to explain performance drivers — e.g., “CPA improved due to Loyalty Members in Conversion layer via Meta Carousel.”
- Reference fiscal trends (MoM, WoW, FY-to-date) and NZ-specific media norms (e.g., radio TARPs, seasonal shifts).
- Always include at least one visualisation to support your insight.

**Strategic Recommendation**
- Provide 2–4 actionable tactics with quantified impact (e.g., “Shift 12% of spend from Static to Video to improve ROAS by +0.8”).
- Recommend optimisations across:
  - Channel mix based on their respective objectives
  - Creative format, i.e. suggestion similar concepts or testing new ones
  - Audience targeting (demographic, behavioral, or 1PD/2PD/3PD combinations)
  - Budget allocation
- Avoid simplistic budget cuts based on surface metrics. Instead, assess whether performance is driven by creative, audience, or channel.
- Prioritise changes that improve CPA, ROAS, or conversion volume.
- Reference platform learning, seasonal trends, and scalability potential.

**Examples**
- FY Month 4: Meta contributed 38% of total conversions with ROAS 4.1 and CPA $32. Remarketing drove +22% MoM uplift.
- FY Week 17: Consideration layer delivered 57% of conversions and 52% of revenue. Carousel formats outperformed Static by +1.3 ROAS.
- Strategic: Raise frequency on Loyalty Members from 8x to 12x to lift conversion volume by +18%.
- Audience: Boomers in Awareness layer via Radio (NZME) delivered strong reach (320 TARPs) but low conversion. Recommend shifting 15% to Consideration layer with Static formats.
- Format: Carousel in Conversion layer with High Intent Shoppers delivered ROAS 4.8 vs Static at 3.2. Recommend scaling Carousel with new creative variants.

Be concise, visual, and data-driven. Always speak to overarching performance, not isolated campaigns. Use the full schema to reason and recommend.
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
    creative_messaging = ["Value-led", "Urgency-led", "Emotional", "Informational"]
    demo_segments = ["Millennials", "Boomers", "Parents with Kids"]
    behav_segments = ["High Intent Shoppers", "Cart Abandoners", "Loyalty Members"]

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
            "Awareness": 100_000,
            "Consideration": 250_000,
            "Conversion": 500_000
        }[funnel]

        seasonal_multiplier = 1.25 if week >= 40 else 1.0
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
        revenue = spend * roas

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
            "Revenue ($)": revenue,
            "TARPs": tarps,
            "Reach (%)": reach,
            "Frequency": frequency,
            "Spot Count": spot_count,
            "Station": station
        })

    return pd.DataFrame(rows)

df = generate_data()

# -------------------------------
# CHART GENERATION FUNCTIONS
# -------------------------------
def generate_roas_cpa_chart():
    """Generate ROAS and CPA comparison chart by publisher"""
    data = df.groupby('Publisher').agg({
        'ROAS': 'mean',
        'CPA ($)': 'mean'
    }).reset_index().head(10)
    
    # Normalize CPA to same scale as ROAS for visualization
    data['CPA_normalized'] = data['CPA ($)'] / 10
    
    roas_chart = alt.Chart(data).mark_bar(color='#00d4ff').encode(
        x=alt.X('Publisher:N', sort='-y'),
        y=alt.Y('ROAS:Q', title='ROAS'),
    ).properties(width=700, height=300, title='Average ROAS by Publisher')
    
    return roas_chart

def generate_format_performance_chart():
    """Generate performance by format"""
    data = df.groupby('Format').agg({
        'ROAS': 'mean',
        'CTR (%)': 'mean',
        'Spend ($)': 'sum'
    }).reset_index()
    
    chart = alt.Chart(data).mark_bar(color='#0099ff').encode(
        x=alt.X('Format:N'),
        y=alt.Y('ROAS:Q', title='Average ROAS'),
    ).properties(width=600, height=300, title='Performance by Format')
    
    return chart

def generate_funnel_chart():
    """Generate performance by funnel layer"""
    data = df.groupby('Funnel Layer').agg({
        'ROAS': 'mean',
        'Revenue ($)': 'sum',
        'Spend ($)': 'sum'
    }).reset_index()
    
    chart = alt.Chart(data).mark_bar(color='#10b981').encode(
        x=alt.X('Funnel Layer:N'),
        y=alt.Y('ROAS:Q', title='Average ROAS'),
    ).properties(width=600, height=300, title='Performance by Funnel Layer')
    
    return chart

def generate_spend_by_publisher():
    """Generate spend distribution by publisher"""
    data = df.groupby('Publisher')['Spend ($)'].sum().reset_index().sort_values('Spend ($)', ascending=False).head(10)
    
    chart = alt.Chart(data).mark_bar(color='#8b5cf6').encode(
        x=alt.X('Publisher:N', sort='-y'),
        y=alt.Y('Spend ($):Q', title='Total Spend'),
    ).properties(width=700, height=300, title='Top 10 Publishers by Spend')
    
    return chart

# -------------------------------
# DISPLAY PREVIOUS MESSAGES
# -------------------------------
for msg in st.session_state.chat_history:
    if msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])

# -------------------------------
# CHAT INPUT
# -------------------------------
user_input = st.chat_input("Ask about performance, ROI, or recommendations...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing performance..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=st.session_state.chat_history
                )
                output = response.choices[0].message.content
                st.markdown(output)
                
                # Display relevant charts based on user query
                if any(keyword in user_input.lower() for keyword in ['roas', 'cpa', 'publisher', 'channel']):
                    st.altair_chart(generate_roas_cpa_chart(), use_container_width=True)
                elif any(keyword in user_input.lower() for keyword in ['format', 'video', 'static', 'carousel']):
                    st.altair_chart(generate_format_performance_chart(), use_container_width=True)
                elif any(keyword in user_input.lower() for keyword in ['funnel', 'awareness', 'consideration', 'conversion']):
                    st.altair_chart(generate_funnel_chart(), use_container_width=True)
                elif any(keyword in user_input.lower() for keyword in ['spend', 'budget', 'allocation']):
                    st.altair_chart(generate_spend_by_publisher(), use_container_width=True)
                else:
                    # Default chart if no specific keyword matches
                    st.altair_chart(generate_roas_cpa_chart(), use_container_width=True)
                
                st.session_state.chat_history.append({"role": "assistant", "content": output})
            except Exception as e:
                st.error(f"Error from Groq API: {e}")

# -------------------------------
# LEGAL DISCLAIMER
# -------------------------------
st.markdown("---")
st.markdown(
    "Legal Disclaimer — The insights and visualizations generated by this tool are for informational purposes only "
    "and should not be considered financial, legal, or business advice."
)
