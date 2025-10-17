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
    .stSidebar {
        min-width: 336px;
    }
    .stSidebar .stHeading {
        color: #FAFAFA;
    }
    .stSidebar .stElementContainer {
        width: auto;
    }
    .history-section {
        margin-top: 24px;
        margin-bottom: 12px;
    }
    .history-section h4 {
        font-size: 12px;
        color: #A0A0A0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        margin-top: 0;
    }
    .history-item {
        padding: 8px 12px;
        margin-bottom: 6px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        color: #E0E0E0;
        transition: background-color 0.2s;
        border-left: 3px solid transparent;
    }
    .history-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
        border-left-color: #80D5FF;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "question_history" not in st.session_state:
    st.session_state.question_history = {}

# Helper function to get date key (YYYY-MM-DD)
def get_date_key():
    return datetime.now().strftime("%Y-%m-%d")

# Helper function to format time
def format_time(dt):
    return dt.strftime("%H:%M")

# Helper function to add question to history
def add_to_history(question):
    date_key = get_date_key()
    if date_key not in st.session_state.question_history:
        st.session_state.question_history[date_key] = []
    st.session_state.question_history[date_key].append({
        "question": question,
        "timestamp": datetime.now()
    })

# Helper function to get yesterday's date key
def get_yesterday_key():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

# Helper function to categorize questions by date
def get_history_sections():
    today_key = get_date_key()
    yesterday_key = get_yesterday_key()
    
    sections = []
    
    if today_key in st.session_state.question_history and st.session_state.question_history[today_key]:
        sections.append(("Today", today_key))
    
    if yesterday_key in st.session_state.question_history and st.session_state.question_history[yesterday_key]:
        sections.append(("Yesterday", yesterday_key))
    
    return sections

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
    if st.button("🧹 Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.chat_started = False
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
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
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

**CRITICAL: HOLISTIC DECISION-MAKING FRAMEWORK**
NEVER make recommendations based on 1-2 metrics alone. Every strategic recommendation must consider AT MINIMUM:
1. **Efficiency Metrics**: ROAS, CPA, Cost Per Lead, Cost Per Sign-Up
2. **Volume Metrics**: Conversions, Revenue, Leads, Sign-Ups, Website Sessions
3. **Engagement Quality**: CTR, Conversion Rate, Time on Site, Pages Per Session, Bounce Rate
4. **Audience Fit**: Demographic alignment, behavioral segment performance, lifecycle stage
5. **Brand Impact**: Viewability, Social Engagement (Likes, Shares, Comments), Reach, Frequency
6. **Strategic Context**: Campaign objective (Awareness vs Conversion), seasonal trends, competitive positioning, platform maturity

**Example of GOOD vs BAD recommendations:**
❌ BAD: "Increase Meta spend because ROAS is 4.2"
✅ GOOD: "Increase Meta spend by 15% because: (1) ROAS of 4.2 is 0.8 above portfolio average, (2) conversion rate of 4.5% indicates high intent audiences, (3) time on site of 6.2 min shows strong engagement depth, (4) targeting Loyalty Members who have 40% lower CPA, (5) Carousel format is driving 22% more conversions than Static, and (6) Meta is still in learning phase with room for scale. However, monitor viewability (currently 68%) and consider capping frequency at 10x to avoid fatigue."

**Campaign Objectives & Context**
- Awareness: Build brand recognition and reach new audiences. Success = high reach, frequency, aided/unaided brand recall, viewability, social engagement.
- Consideration: Drive engagement and preference among aware audiences. Success = engagement rate, time spent, pages per session, content shares, and lift in brand consideration metrics.
- Conversion: Drive direct sales, sign-ups, or desired actions. Success = CTR, conversion rate, CPA, ROAS, and absolute conversion volume.
- Retargeting: Re-engage audiences who have shown interest. Success = high ROAS, low CPA, conversion lift, and frequency optimization.
- Brand Lift: Shift perception and emotional connection. Success = brand health metrics (consideration, preference, intent), social engagement, reach.
- Product Launch: Drive trial and initial adoption. Success = awareness lift + trial rate + first-purchase conversion + engagement quality.
- Offer Promotion: Drive immediate action via incentive. Success = redemption rate, uplift in sales volume, velocity, and incremental revenue.

**Audience Insight & User Behaviour**
- Millennials: Value authenticity, sustainability, and community. Responsive to social proof and peer recommendations. Prefer mobile-first, video-rich experiences. Metrics: Social engagement, time on site, pages per session.
- Boomers: Trust established brands and authority. Prefer clear, straightforward messaging. Lower digital engagement but higher lifetime value. Metrics: Conversion rate, revenue per conversion, time on site.
- Parents with Kids: Driven by value, convenience, and family benefit. Responsive to safety/quality messaging and time-saving solutions. Cross-device consumption (TV + mobile). Metrics: CTR, conversion rate, pages per session.
- High Intent Shoppers: Ready to purchase, price-conscious, comparing options. Respond to competitive positioning, reviews, and limited-time offers. Metrics: Conversion rate, CPA, bounce rate.
- Cart Abandoners: Interested but hesitant (price, shipping, trust). Respond to incentives, social proof, and scarcity messaging. Metrics: ROAS, conversion rate, time on site.
- Loyalty Members: Established customers, lower acquisition cost, high lifetime value. Respond to exclusivity, personalization, and VIP treatment. Metrics: ROAS, CPA, frequency, repeat conversion rate.

**Think from the Audience POV**
- What problem are we solving for them?
- What stage of their decision journey are they at?
- What barriers prevent conversion (price, trust, complexity)?
- What emotional triggers resonate (aspiration, fear of missing out, belonging)?
- What content format and channel fit their media consumption habits?

**Executive Overview**
- Summarize performance across the latest fiscal month or week (e.g., FY Month 4, Week 17).
- Quantify key shifts in ROAS, CPA, CTR, spend, revenue, conversion volume, engagement quality.
- Highlight top-performing funnel layers, formats, publishers, and audience segments across multiple dimensions.
- Frame commentary in terms of business impact, efficiency, scale potential, and momentum.

**Insight**
- Use charts and graphs to visualize topline metrics (e.g., spend, revenue, ROAS, CTR, CPA, conversion volume, engagement).
- Segment by:
  - Funnel Layer: Awareness, Consideration, Conversion
  - Format: Video, Static, Carousel, Interactive, Radio
  - Strategy: Retargeting, Brand Lift, Product Launch, Offer Promotion
  - Publisher: Meta, YouTube, NZ Herald, NZME Radio, etc.
  - Audience Segment (Demographic): e.g., Millennials, Boomers, Parents with Kids
  - Audience Segment (Behavioral): e.g., High Intent Shoppers, Cart Abandoners, Loyalty Members
- Always compare like-for-like when evaluating performance — e.g., Video vs Video, Carousel vs Static, Awareness vs Awareness — to ensure recommendations are contextually valid.
- Use schema fields to explain performance drivers holistically — e.g., "Meta Carousel targeting Loyalty Members in Conversion layer delivered CPA of $22 (35% below average), ROAS of 5.8 (highest in portfolio), conversion rate of 4.8% (vs 3.2% portfolio average), and time on site of 7.1 min (indicating high engagement). This is because Carousel format reduces friction, builds confidence through multiple proof points, and Loyalty Members have established trust and lower barriers to purchase."
- Reference fiscal trends (MoM, WoW, FY-to-date) and NZ-specific media norms (e.g., radio TARPs, seasonal shifts).
- Always include at least one visualisation to support your insight.

**Strategic Recommendation**
- Provide 2–4 actionable tactics with MULTI-DIMENSIONAL justification (never based on 1-2 metrics alone).
- Each recommendation must include:
  * Primary efficiency metric (ROAS, CPA, or similar)
  * Volume/scale metric (conversions, revenue, leads)
  * Engagement quality indicator (CTR, conversion rate, time on site, etc.)
  * Audience/context rationale (who, why, lifecycle stage)
  * Format/creative insight (what's working and why)
  * Risk mitigation or monitoring plan (what to watch for)

**Example recommendations:**
✅ "Shift 18% of Display budget ($2.4M) to Meta Carousel targeting Loyalty Members because: (1) Meta delivers ROAS 5.8 vs Display 3.1 (+87% efficiency), (2) Meta drives 2,200 more conversions per $1M spend, (3) Carousel CTR is 3.2% vs Static 1.4% showing superior engagement, (4) Loyalty Members have 40% lower CPA and 2.3x repeat purchase rate, (5) Time on site of 7.1min indicates high quality traffic, (6) Viewability of 78% exceeds Display's 61%. MONITOR: Frequency cap at 12x to avoid fatigue, and test new Carousel creative every 3 weeks to maintain novelty."

✅ "Scale Radio (NZME) investment by $800K targeting Boomers in Consideration layer because: (1) Radio delivers 420 TARPs with reach of 72% (strong awareness penetration), (2) While direct ROAS is 2.8 (below average), Radio drives 34% lift in brand search volume and 28% increase in direct website traffic, (3) Boomers have lifetime value 2.1x higher than Millennials, justifying longer conversion window, (4) Cost per reach point ($1,200) is 40% more efficient than TV, (5) Creative testing shows emotional messaging drives 22% higher recall than informational. PAIR WITH: Retargeting campaign via Search to capture bottom-funnel intent generated by Radio awareness."

✅ "Reduce TikTok spend by 25% ($1.2M) and reallocate to YouTube targeting Millennials because: (1) TikTok ROAS of 2.1 is below portfolio average of 3.8, (2) TikTok conversion rate of 1.8% indicates low purchase intent despite high engagement (CTR 4.2%), (3) YouTube delivers conversion rate of 3.6% with similar CTR of 4.1%, (4) YouTube time on site (8.3min) is 3x higher than TikTok (2.7min), suggesting more qualified traffic, (5) YouTube CPM ($4.20) is comparable to TikTok ($4.50) but with superior conversion efficiency, (6) Social engagement on YouTube (likes, shares) is 40% higher for educational Video content. MAINTAIN: Small TikTok budget ($600K) for brand awareness and testing, as platform has strong Millennial affinity and emerging commerce features."

- Recommend optimisations across:
  - Channel mix based on their respective objectives AND full performance profile
  - Creative format with engagement and conversion proof points
  - Audience targeting (demographic, behavioral, or 1PD/2PD/3PD combinations) with volume and efficiency validation
  - Budget allocation with clear trade-offs and risk mitigation
- Avoid simplistic budget cuts based on surface metrics. Instead, assess whether performance is driven by creative, audience, channel, or strategic misalignment.
- Prioritise changes that improve MULTIPLE dimensions: efficiency (CPA/ROAS), volume (conversions/revenue), and quality (engagement/brand impact).
- Reference platform learning, seasonal trends, scalability potential, and competitive landscape.
- Consider audience friction points, ease of action, and full-funnel impact.

Be concise, visual, and data-driven. Always speak to overarching performance, not isolated campaigns. Use the full schema to reason and recommend. Always explain the *why* behind performance drivers from the audience perspective with multi-dimensional evidence.

**CRITICAL: Never include any chart descriptions, "[Insert Chart]" placeholders, or visualization references. Text analysis only.**
"""

# -------------------------------
# CHAT MEMORY
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": system_prompt}]
    
    # Inject data summary into system context (one-time)
    data_summary = f"""
[Dataset Context]
You have access to enterprise-level marketing performance data for FY 2025 with {len(df)} records across 52 weeks.
**Annual Budget Range: $100M - $300M** with weekly spend ranging from $3M to $7.5M depending on funnel layer and seasonality.

**Schema & Available Fields:**
- Temporal: FY Year, Week
- Channel & Format: Publisher, Strategy, Funnel Layer, Format, Creative Messaging
- Audience: Audience Segment (Demographic), Audience Segment (Behavioral)
- Financial: Spend ($), ROAS, CPA ($), Revenue ($), Website Sales ($), E-Commerce Sales ($), Affiliate Revenue ($)
- Performance: Impressions, Clicks, CTR (%), Conversions, Conversion Rate (%), Form Submissions, Leads Generated, Sign-Ups, Cost Per Lead ($), Cost Per Sign-Up ($)
- Engagement: Website Sessions, Time on Site (min), Pages Per Session, Bounce Rate (%)
- Brand & Quality: Viewability (%), Measurable Impressions, Social Likes, Social Shares, Social Comments
- Radio Metrics: TARPs, Reach (%), Frequency, Spot Count, Station

**Available Publishers:** {', '.join(df['Publisher'].unique())}

**Funnel Layers:** Awareness, Consideration, Conversion

**Formats:** Video, Static, Carousel, Interactive, Radio

**Strategies:** Retargeting, Brand Lift, Product Launch, Offer Promotion

**Behavioral Segments:** High Intent Shoppers, Cart Abandoners, Loyalty Members

**Demographic Segments:** Millennials, Boomers, Parents with Kids

**Creative Messaging Types:** Value-led, Urgency-led, Emotional, Informational

**Key Data Characteristics (Enterprise Scale):**
- Weekly spend ranges: Awareness ($3M base), Consideration ($4.5M base), Conversion ($6M base)
- Seasonal multiplier: 1.25x for weeks 40+ (Q4), bringing peak weekly spend to $3.75M-$7.5M
- Total annual budget across all activities: ~$250M-$300M
- Average ROAS by funnel: Awareness (2.0), Consideration (3.5), Conversion (5.0)
- Average CPA by behavioral segment: High Intent Shoppers ($35), Cart Abandoners ($28), Loyalty Members ($22)
- CTR by format: Video (2.8%), Carousel (3.2%), Static (1.2%), Interactive (2.5%), Radio (0.6%)
- Typical weekly impressions: 500M-1.5B depending on format and funnel
- Typical weekly conversions: 50K-200K depending on funnel layer and targeting

**Instructions:**
- Synthesize this data to answer user questions with multi-dimensional analysis appropriate for enterprise-scale decision making
- Always reference actual trends, segments, and performance patterns from the dataset
- When making recommendations, cite specific data points across efficiency, volume, engagement, audience fit, brand impact, and strategic context
- Frame recommendations in terms of multi-million dollar budget shifts and their business impact
- Generate insights that consider the full schema, not just ROAS or CPA alone
- Consider scale implications: a 5% budget shift represents $5M-$15M annually
- Visualizations are handled separately - focus your response on strategic analysis and recommendations
"""
    
    st.session_state.chat_history.append({"role": "system", "content": data_summary})

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

        # Enterprise-level spend ranges: $100M-$300M annually
        base_spend = {
            "Awareness": 3_000_000,      # $3M per week for Awareness
            "Consideration": 4_500_000,  # $4.5M per week for Consideration
            "Conversion": 6_000_000      # $6M per week for Conversion
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
        roas = max(1.2, roas_base - (spend / 10_000_000))

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
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        for question in preset_questions:
            if st.button(question, use_container_width=True, key=f"preset_{question}"):
                preset_input = question
                st.session_state.chat_started = True
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

st.markdown("---")

# CHAT INPUT
user_input = st.chat_input("Select a prompt above or type your custom prompt here")

# Use preset input if a button was clicked
if preset_input:
    user_input = preset_input

if user_input:
    # Mark chat as started
    st.session_state.chat_started = True
    
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

# -------------------------------
# LEGAL DISCLAIMER
# -------------------------------
st.markdown("---")
st.markdown(
    "Legal Disclaimer — The insights and visualizations generated by this tool are for informational purposes only "
    "and should not be considered financial, legal, or business advice."
)
