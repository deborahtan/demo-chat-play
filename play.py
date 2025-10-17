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

# Hide Streamlit toolbar and footer
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stDecoration"] {visibility: hidden;}
[data-testid="stStatusWidget"] {visibility: hidden;}
.viewerBadge_container {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:
    st.image("https://www.dentsu.com/assets/images/main-logo-alt.png", width=160)
    st.header("Dentsu Conversational Analytics")
    st.markdown("""
    **How to use**
    - Type any question about campaign performance or strategy.
    - The assistant responds with quantified, data-driven insight.
    - Conversation context is remembered.
    """)
    
    # Clear conversation button
    if st.button("🧹 Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()
    
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
# GROQ SETUP
# -------------------------------
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY. Add it to your environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# -------------------------------
# SYSTEM PROMPT
# -------------------------------
system_prompt = """
You are the Dentsu Intelligence Assistant — a senior strategist delivering enterprise-level marketing intelligence to C-suite stakeholders across Media, Marketing, CRM, Loyalty, and Finance.

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
    
    if any(word in query_lower for word in ['audience', 'demographic', 'behavioral', 'segment']):
        data = df.groupby('Audience Segment (Demographic)').agg({
            'ROAS': 'mean',
            'CPA ($)': 'mean'
        }).reset_index()
        
        roas_chart = alt.Chart(data).mark_line(point=True, color='#00d4ff', size=3).encode(
            x='Audience Segment (Demographic):N',
            y=alt.Y('ROAS:Q', title='ROAS'),
            tooltip=['Audience Segment (Demographic)', alt.Tooltip('ROAS:Q', format='.2f')]
        )
        
        cpa_chart = alt.Chart(data).mark_line(point=True, color='#ef4444', size=3).encode(
            x='Audience Segment (Demographic):N',
            y=alt.Y('CPA ($):Q', title='CPA ($)', axis=alt.Axis(orient='right'))
        )
        
        return alt.layer(roas_chart, cpa_chart).resolve_scale(y='independent').properties(
            width=800, height=400
        ).interactive()
    
    elif any(word in query_lower for word in ['strategy', 'retargeting', 'brand lift', 'launch', 'promotion']):
        data = df.groupby('Strategy').agg({
            'ROAS': 'mean',
            'Revenue ($)': 'sum'
        }).reset_index()
        
        chart = alt.Chart(data).mark_bar(color='#8b5cf6').encode(
            x='Strategy:N',
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Strategy', alt.Tooltip('ROAS:Q', format='.2f')]
        ).properties(width=800, height=400).interactive()
        
        return chart
    
    elif any(word in query_lower for word in ['creative', 'messaging', 'value-led', 'urgency', 'emotional']):
        data = df.groupby('Creative Messaging').agg({
            'ROAS': 'mean',
            'CTR (%)': 'mean'
        }).reset_index()
        
        chart = alt.Chart(data).mark_bar(color='#10b981').encode(
            x='Creative Messaging:N',
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Creative Messaging', alt.Tooltip('ROAS:Q', format='.2f')]
        ).properties(width=800, height=400).interactive()
        
        return chart
    
    elif any(word in query_lower for word in ['spend', 'budget', 'allocation', 'cost']):
        data = df.groupby('Publisher')['Spend ($)'].sum().reset_index().sort_values('Spend ($)', ascending=False).head(10)
        
        chart = alt.Chart(data).mark_bar(color='#f59e0b').encode(
            x=alt.X('Publisher:N', sort='-y'),
            y=alt.Y('Spend ($):Q', title='Total Spend'),
            tooltip=['Publisher', alt.Tooltip('Spend ($):Q', format='$,.0f')]
        ).properties(width=800, height=400).interactive()
        
        return chart
    
    elif any(word in query_lower for word in ['format', 'video', 'static', 'carousel', 'interactive', 'radio']):
        data = df.groupby('Format').agg({
            'ROAS': 'mean',
            'CTR (%)': 'mean'
        }).reset_index()
        
        chart = alt.Chart(data).mark_bar(color='#06b6d4').encode(
            x='Format:N',
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Format', alt.Tooltip('ROAS:Q', format='.2f'), alt.Tooltip('CTR (%):Q', format='.2f')]
        ).properties(width=800, height=400).interactive()
        
        return chart
    
    elif any(word in query_lower for word in ['funnel', 'awareness', 'consideration', 'conversion']):
        data = df.groupby('Funnel Layer').agg({
            'ROAS': 'mean',
            'Revenue ($)': 'sum'
        }).reset_index()
        
        chart = alt.Chart(data).mark_bar(color='#ec4899').encode(
            x='Funnel Layer:N',
            y=alt.Y('ROAS:Q', title='Average ROAS'),
            tooltip=['Funnel Layer', alt.Tooltip('ROAS:Q', format='.2f')]
        ).properties(width=800, height=400).interactive()
        
        return chart
    
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
            width=800, height=400
        ).interactive()

# -------------------------------
# MAIN LAYOUT
# -------------------------------
col_main, col_preset = st.columns([3, 1], gap="large")

with col_main:
    # DISPLAY PREVIOUS MESSAGES
    for msg in st.session_state.chat_history:
        if msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
        elif msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])

    # CHAT INPUT
    user_input = st.chat_input("Ask about performance, ROI, or recommendations...")
    
    # Check if rerunning from history
    if "rerun_question" in st.session_state:
        user_input = st.session_state.rerun_question
        del st.session_state.rerun_question

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
            with st.spinner("Analyzing performance..."):
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

with col_preset:
    st.subheader("💡 Quick Questions")
    
    preset_questions = [
        "How is 18-35 performing vs older segments?",
        "Which channel has the best CPA this period?",
        "Is Video or Static driving higher engagement?",
        "What's the Consideration layer momentum?",
        "How are Digital channels performing week-over-week?",
        "Which audience segment is underperforming?",
        "What's driving ROAS on Social vs Display?",
        "Should we increase or decrease TV spend?"
    ]
    
    for question in preset_questions:
        if st.button(question, use_container_width=True, key=f"preset_{question}"):
            st.session_state.rerun_question = question
            st.rerun()

# -------------------------------
# LEGAL DISCLAIMER
# -------------------------------
st.markdown("---")
st.markdown(
    "Legal Disclaimer — The insights and visualizations generated by this tool are for informational purposes only "
    "and should not be considered financial, legal, or business advice."
)
