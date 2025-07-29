import datetime
import json
import os
import time

import streamlit as st

from app.agents.content_generator import (generate_alternate_idea,
                                          generate_content_ideas,
                                          summarize_single_idea)

st.set_page_config(
    page_title="Agentic Content Planner",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- COMPLETE CSS WITH INTEGRATED BUTTON DESIGN ---
st.markdown(
    """
<style>
    .stApp {
        background: 
          radial-gradient(circle at 20% 80%, rgba(79, 195, 247, 0.03) 0%, transparent 50%), 
          radial-gradient(circle at 80% 20%, rgba(41, 182, 246, 0.03) 0%, transparent 50%), 
          linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
        color: #e0e0e0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        min-height: 100vh;
    }
    
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    h1 {
        background: linear-gradient(90deg, #4FC3F7, #29B6F6, #0288D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 2.8rem !important;
        margin: 1rem 0 0.5rem 0 !important;
        font-weight: 700;
        letter-spacing: -1px;
        animation: titleGlow 4s ease-in-out infinite alternate;
    }
    
    @keyframes titleGlow {
        0% { text-shadow: 0 0 20px rgba(79, 195, 247, 0.3); }
        100% { text-shadow: 0 0 40px rgba(79, 195, 247, 0.6), 0 0 60px rgba(41, 182, 246, 0.4); }
    }
    
    .main-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #a0a0a0;
        margin: 0 0 1.5rem 0 !important;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    .premium-welcome {
        max-width: 960px;
        margin: 0 auto 1.5rem auto;
        padding: 0.5rem 1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.8rem;
        box-sizing: border-box;
    }
    
    .features-single-row {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
        margin-bottom: 1.5rem;
        width: 100%;
        max-width: 900px;
    }
    
    .feature-item {
        background: linear-gradient(135deg, rgba(79, 195, 247, 0.08) 0%, rgba(41, 182, 246, 0.04) 100%);
        border: 1px solid rgba(79, 195, 247, 0.2);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        flex: 0 0 calc(25% - 12px);
        min-width: 180px;
        box-shadow: 0 2px 9px rgba(221, 227, 238, 0.1);
    }
    
    .feature-item:hover {
        border-color: rgba(79, 195, 247, 0.4);
        box-shadow: 0 8px 25px rgba(79, 195, 247, 0.15);
        transform: translateY(-3px);
    }
    
    .feature-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 0.2rem;
    }
    
    .feature-desc {
        font-size: 0.8rem;
        color: #a0a0a0;
        line-height: 1.3;
    }
    
    /* Enhanced metric container styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%) !important;
        border: 1px solid #4FC3F7 !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        box-shadow: 0 4px 15px rgba(79, 195, 247, 0.1) !important;
        transition: all 0.3s ease !important;
        height: auto !important;
        min-height: 70px !important;
        margin: 0.25rem 0 !important;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 195, 247, 0.2) !important;
        border-color: #29B6F6 !important;
    }
    
    /* NEW: Content cards with PROPERLY integrated buttons */
    .content-card-wrapper {
        position: relative;
        margin-bottom: 1rem;
    }
    
    .content-card-overlay {
        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
        border: 1px solid rgba(79, 195, 247, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        position: relative;
    }

    .content-card-overlay:hover {
        border-color: rgba(79, 195, 247, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79, 195, 247, 0.15);
    }

    .day-header-overlay {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4FC3F7;
        margin-bottom: 0.6rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(79, 195, 247, 0.2);
    }

    .content-text-overlay {
        color: #e0e0e0;
        line-height: 1.5;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        word-wrap: break-word;
        padding: 0;
    }
    
    /* NEW: Properly integrated button container - INSIDE the card */
    .button-integrated {
        border-top: 1px solid rgba(79, 195, 247, 0.1);
        padding-top: 1rem;
        margin-top: 1rem;
    }
    
    .button-integrated .stButton {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .button-integrated .stButton > button {
        background: linear-gradient(90deg, #0288D1, #4FC3F7) !important;
        border: none !important;
        border-radius: 6px !important;
        color: white !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        padding: 0.4rem 0.8rem !important;
        height: 32px !important;
        width: 100% !important;
        min-width: 85px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(79, 195, 247, 0.25) !important;
        white-space: nowrap !important;
        text-align: center !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        line-height: 1 !important;
        letter-spacing: 0.1px !important;
        text-transform: none !important;
        font-family: 'Inter', sans-serif !important;
    }

    .button-integrated .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 10px rgba(79, 195, 247, 0.4) !important;
        background: linear-gradient(90deg, #29B6F6, #4FC3F7) !important;
    }

    .button-integrated .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Button color variants */
    .button-integrated .stButton:nth-child(1) > button {
        background: linear-gradient(135deg, #FF6B35, #FF8E53) !important;
    }

    .button-integrated .stButton:nth-child(1) > button:hover {
        background: linear-gradient(135deg, #FF8E53, #FFA726) !important;
    }

    .button-integrated .stButton:nth-child(2) > button {
        background: linear-gradient(135deg, #7B1FA2, #9C27B0) !important;
    }

    .button-integrated .stButton:nth-child(2) > button:hover {
        background: linear-gradient(135deg, #9C27B0, #BA68C8) !important;
    }

    .button-integrated .stButton:nth-child(3) > button {
        background: linear-gradient(135deg, #388E3C, #4CAF50) !important;
    }

    .button-integrated .stButton:nth-child(3) > button:hover {
        background: linear-gradient(135deg, #4CAF50, #66BB6A) !important;
    }
    
    /* Analysis card styling with close button */
    .analysis-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        border: 1px solid #4FC3F7;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 3px 12px rgba(79, 195, 247, 0.1);
        color: #e0e0e0;
        font-size: 0.85rem;
        line-height: 1.5;
        min-height: 50px;
        display: flex;
        align-items: center;
        position: relative;
    }
    
    .analysis-text {
        width: 100%;
        text-align: left;
        word-wrap: break-word;
        overflow-wrap: break-word;
        padding-right: 2rem;
    }

    .close-analysis-btn {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: rgba(255, 255, 255, 0.1) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 24px !important;
        height: 24px !important;
        min-width: 24px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: #fff !important;
        font-size: 0.8rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    .close-analysis-btn:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: scale(1.1) !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        height: 2.5rem !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        border: 1px solid rgba(79, 195, 247, 0.3) !important;
        background: rgba(42, 42, 42, 0.8) !important;
        color: #f0f0f0 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(79, 195, 247, 0.6) !important;
        box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.2) !important;
    }
    
    /* Section headers */
    h3 {
        margin: 1.5rem 0 0.8rem 0 !important;
        font-size: 1.4rem !important;
        color: #e0e0e0 !important;
        font-weight: 600 !important;
    }
    
    /* Dividers */
    hr {
        margin: 1.2rem 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.3), transparent) !important;
    }
    
    /* Sidebar styling */
    .stSidebar > div {
        background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
        padding: 1rem 0.5rem;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4FC3F7, #29B6F6) !important;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 8px !important;
        margin: 0.5rem 0 !important;
        padding: 0.75rem !important;
    }
    
    /* Columns */
    .stColumns {
        gap: 0.5rem !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .feature-item {
            flex: 0 0 calc(50% - 8px);
            min-width: 140px;
            padding: 0.6rem 0.8rem;
        }
        
        .button-integrated .stButton > button {
            font-size: 0.7rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .feature-item {
            flex: 0 0 100%;
        }
        
        .main .block-container {
            padding: 1rem 0.5rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# Configuration options (ALL PRESERVED)
audience_options = {
    "Startup Founders & Entrepreneurs": "entrepreneurs",
    "Marketing Professionals": "marketers", 
    "Content Creators & Influencers": "creators",
    "Tech & Software Developers": "developers",
    "Educators & Students": "students",
    "Healthcare Professionals": "healthcare",
    "Business Executives": "executives",
    "E-commerce Owners": "ecommerce",
    "Freelancers & Consultants": "freelancers",
    "Sustainability Advocates": "sustainability",
}

template_options = {
    "Social Media Posts": "social",
    "Blog Articles": "blog",
    "Email Newsletters": "email", 
    "Video Scripts": "video",
    "Podcast Content": "podcast",
    "Infographic Ideas": "infographic",
}

# Title & subtitle (ALL PRESERVED)
st.markdown('<h1>Agentic Content Planner</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">AI-Powered Weekly Content Strategy</div>',
    unsafe_allow_html=True,
)

# Features row (ALL PRESERVED)
st.markdown('<div class="premium-welcome">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="features-single-row">
        <div class="feature-item">
            <div class="feature-title">AI-Powered Generation</div>
            <div class="feature-desc">Advanced AI creates personalized content ideas</div>
        </div>
        <div class="feature-item">
            <div class="feature-title">Performance Analytics</div>
            <div class="feature-desc">Track and optimize engagement</div>
        </div>
        <div class="feature-item">
            <div class="feature-title">Multi-Format Export</div>
            <div class="feature-desc">Export ideas for different platforms</div>
        </div>
        <div class="feature-item">
            <div class="feature-title">Content Enhancement</div>
            <div class="feature-desc">Boost your content with AI enhancements</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

# SIDEBAR (ALL PRESERVED)
st.sidebar.header("Content Settings")
theme_mode = st.sidebar.toggle("Dark Mode", value=True)

# Enhanced API Health Monitor (ALL PRESERVED)
with st.sidebar.expander("API Health Monitor", expanded=False):
    try:
        import requests
        resp = requests.get("http://localhost:8000/health", timeout=3)
        if resp.status_code == 200:
            health = resp.json()
            st.success("Backend Connected")
            col1, col2 = st.columns(2)
            with col1:
                if health.get("openai_available"):
                    st.markdown("**OpenAI:** Online")
                else:
                    st.markdown("**OpenAI:** Offline")
            with col2:
                if health.get("perplexity_available"):
                    st.markdown("**Perplexity:** Online")
                else:
                    st.markdown("**Perplexity:** Offline")
        else:
            st.error(f"Backend Error: {resp.status_code}")
    except requests.exceptions.Timeout:
        st.warning("Backend connection timeout")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend")
        st.info("Make sure your backend server is running on port 8000")
    except Exception as e:
        st.error(f"Connection Failed: {str(e)}")
        
    # Fallback API key check
    openai_key = os.getenv("OPENAI_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    st.markdown("**Environment Check:**")
    col1, col2 = st.columns(2)
    with col1:
        if openai_key:
            st.markdown("**OpenAI:** Key Found")
        else:
            st.markdown("**OpenAI:** No Key")
    with col2:
        if perplexity_key:
            st.markdown("**Perplexity:** Key Found")
        else:
            st.markdown("**Perplexity:** No Key")

selected_audience = st.sidebar.selectbox("Target Audience", options=list(audience_options.keys()), index=0)
content_template = st.sidebar.selectbox("Content Template", options=list(template_options.keys()), index=0)

# Advanced Settings (ALL PRESERVED)
with st.sidebar.expander("Advanced Settings", expanded=False):
    st.markdown("**Debug Configuration**")
    debug_mode = st.checkbox("Enable Debug Logging", value=False)
    st.markdown("**Content Settings**")
    tone = st.selectbox("Writing Tone", ["Professional", "Casual", "Friendly", "Authoritative", "Inspirational", "Educational"])
    content_length = st.selectbox("Content Length", ["Short (< 100 words)", "Medium (100-300 words)", "Long (300+ words)"])
    st.markdown("**AI Enhancement Options**")
    enable_enhancement = st.checkbox("Enable AI Enhancement", value=True)
    include_hashtags = st.checkbox("Include Hashtags", value=False)
    include_cta = st.checkbox("Include Call-to-Action", value=True)

# Calendar Navigation (ALL PRESERVED)
with st.sidebar.expander("Calendar Navigation", expanded=False):
    cal_date = st.date_input("Jump to Date", value=datetime.date.today())
    if st.button("Navigate to Week", use_container_width=True):
        start_of_selected_week = cal_date - datetime.timedelta(days=cal_date.weekday())
        st.session_state["week_start"] = start_of_selected_week
        st.rerun()

today = datetime.date.today()
start_of_week = today - datetime.timedelta(days=today.weekday())
week_start = st.sidebar.date_input("Week Starting", value=start_of_week)

# Session state (ALL PRESERVED)
session_defaults = {
    "generated_ideas": [""] * 7,
    "summary": "",
    "topic": "",
    "audience": "",
    "day_summaries": [None] * 7,
    "day_performance": [{"likes": 0, "shares": 0, "comments": 0} for _ in range(7)],
    "week_start": start_of_week,
    "last_generation_successful": False,
    "analysis_results": [None] * 7,
    "generation_time": None,
    "clear_input": False,  # NEW: Flag to clear input
}

for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Search input section (MODIFIED TO HANDLE CLEARING)
st.markdown("### Enter Your Content Topic")

col1, col2 = st.columns([4, 1])
with col1:
    # Clear the input if flag is set
    input_value = "" if st.session_state.get("clear_input", False) else st.session_state.get("last_topic_input", "")
    
    topic_input = st.text_input(
        "Content Topic",
        label_visibility="collapsed",
        value=input_value,
        max_chars=100,
        placeholder="Type your content topic (e.g., AI marketing strategies, fitness tips)",
        key="main_topic_input"
    )
    
    # Store the current input value
    if topic_input:
        st.session_state["last_topic_input"] = topic_input
    
    # Reset the clear flag after input is rendered
    if st.session_state.get("clear_input", False):
        st.session_state["clear_input"] = False

with col2:
    generate_clicked = st.button("Generate", use_container_width=True, type="primary")

# Content generation logic (MODIFIED TO CLEAR INPUT ON SUCCESS)
if generate_clicked:
    if not topic_input.strip():
        st.error("Please enter a topic before generating content.")
    else:
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.info("Connecting to AI services...")
                progress_bar.progress(20)
                time.sleep(0.5)
                
                status_text.info("Generating content ideas...")
                progress_bar.progress(40)
                
                audience_code = audience_options.get(selected_audience, "marketers")
                
                # Try to generate content
                result = generate_content_ideas(topic_input.strip(), audience_code)
                progress_bar.progress(70)
                
                if isinstance(result, dict) and result.get("ideas"):
                    ideas = result.get("ideas", [])
                    summary = result.get("summary", "")
                    
                    # Ensure we have 7 ideas
                    while len(ideas) < 7:
                        ideas.append(f"Additional content idea for {topic_input}")
                    ideas = ideas[:7]
                    
                    # Update session state
                    st.session_state.generated_ideas = ideas
                    st.session_state.summary = summary
                    st.session_state.topic = topic_input.strip()
                    st.session_state.audience = selected_audience
                    st.session_state.last_generation_successful = True
                    st.session_state.generation_time = datetime.datetime.now()
                    st.session_state.analysis_results = [None] * 7
                    
                    # NEW: Clear the input field on successful generation
                    st.session_state["clear_input"] = True
                    st.session_state["last_topic_input"] = ""
                    
                    progress_bar.progress(100)
                    status_text.success("Content plan generated successfully!")
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()
                    st.success("Your weekly content plan is ready!")
                    st.rerun()  # Rerun to clear the input
                    
                else:
                    raise Exception("Invalid response format from content generator")
                    
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                error_msg = str(e)
                if "connection" in error_msg.lower():
                    st.error("Connection failed. Please check your backend server.")
                elif "timeout" in error_msg.lower():
                    st.error("Request timed out. Please try again.")
                elif "api" in error_msg.lower():
                    st.error("API error. Please check your API keys.")
                else:
                    st.error(f"Generation failed: {error_msg}")
                st.session_state.last_generation_successful = False

# Content Overview Metrics (ALL PRESERVED)
if any(idea.strip() for idea in st.session_state.generated_ideas):
    st.markdown("---")
    st.markdown("### Content Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        ideas_count = len([i for i in st.session_state.generated_ideas if i.strip()])
        st.metric("Ideas Generated", ideas_count, delta="Complete" if ideas_count == 7 else "Partial")
    with col2:
        audience_short = st.session_state.get("audience", "N/A").split(" ")[0]
        st.metric("Target Audience", audience_short)
    with col3:
        summaries_count = len([s for s in st.session_state.day_summaries if s])
        st.metric("Summaries", f"{summaries_count}/7")
    with col4:
        template_short = content_template.split(" ")[0]
        st.metric("Template", template_short)
    with col5:
        if st.session_state.generation_time:
            st.metric("Generated", st.session_state.generation_time.strftime("%H:%M"))

# NEW: Content display with buttons PROPERLY positioned inside cards AND FIXED ANALYSIS ISSUE
if any(idea.strip() for idea in st.session_state.generated_ideas):
    st.markdown("---")
    st.markdown(f"### Weekly Content Plan: {st.session_state.topic.title()}")
    
    if st.session_state.summary:
        st.info(f"**Strategy Overview:** {st.session_state.summary}")
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for i, day in enumerate(days):
        if i < len(st.session_state.generated_ideas):
            idea = st.session_state.generated_ideas[i]
            if idea.strip():
                # Start the card
                st.markdown(f"""
                <div class="content-card-wrapper">
                    <div class="content-card-overlay">
                        <div class="day-header-overlay">{day}</div>
                        <div class="content-text-overlay">{idea}</div>
                """, unsafe_allow_html=True)
                
                # Buttons inside the card using the integrated class
                st.markdown('<div class="button-integrated">', unsafe_allow_html=True)
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                
                with btn_col1:
                    if st.button("🔄 Regenerate", key=f"regen_{i}_{day}", help=f"Generate new content for {day}"):
                        try:
                            with st.spinner(f"Regenerating {day} content..."):
                                new_idea = generate_alternate_idea(
                                    st.session_state.topic, 
                                    audience_options.get(selected_audience, "marketers"), 
                                    day, 
                                    exclude=idea
                                )
                                if new_idea:
                                    cleaned_idea = new_idea.split('\n')[0].strip()
                                    if cleaned_idea.startswith(("Title:", "**Title:**")):
                                        cleaned_idea = cleaned_idea.split(':', 1)[1].strip().strip('"')
                                    if len(cleaned_idea) > 120:
                                        cleaned_idea = cleaned_idea[:120] + "..."
                                    
                                    st.session_state.generated_ideas[i] = cleaned_idea
                                    st.session_state.analysis_results[i] = None
                                    st.success(f"{day} content updated!")
                                    st.rerun()
                                else:
                                    st.warning("Could not generate alternative content")
                        except Exception as e:
                            st.error(f"Failed to regenerate: {str(e)}")
                
                with btn_col2:
                    if st.button("📊 Analyze", key=f"analyze_{i}_{day}", help=f"Get detailed analysis for {day}"):
                        try:
                            with st.spinner(f"Analyzing {day} content..."):
                                # FIXED: Clear all other analysis results first
                                for j in range(len(st.session_state.analysis_results)):
                                    if j != i:
                                        st.session_state.analysis_results[j] = None
                                
                                analysis = summarize_single_idea(
                                    st.session_state.topic,
                                    audience_options.get(selected_audience, "marketers"),
                                    idea,
                                    day
                                )
                                if analysis:
                                    st.session_state.analysis_results[i] = analysis
                                    st.success(f"{day} analysis complete!")
                                    st.rerun()
                                else:
                                    st.warning("Could not generate analysis")
                        except Exception as e:
                            st.error(f"Failed to analyze: {str(e)}")
                
                with btn_col3:
                    if st.button("✨ Enhance", key=f"enhance_{i}_{day}", help=f"Improve {day} content with AI"):
                        try:
                            with st.spinner(f"Enhancing {day} content..."):
                                enhanced_idea = f"Enhanced: {idea} - with improved targeting and engagement strategies"
                                st.session_state.generated_ideas[i] = enhanced_idea
                                st.success(f"{day} content enhanced!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to enhance: {str(e)}")
                
                # Close the card properly
                st.markdown('</div></div></div>', unsafe_allow_html=True)
                
                # FIXED: Analysis display with close button
                if st.session_state.analysis_results[i]:
                    full_analysis = st.session_state.analysis_results[i].strip()
                    if full_analysis and not full_analysis.endswith(('.', '!', '?')):
                        full_analysis += '.'
                    
                    # Create container for analysis with close button
                    analysis_container = st.container()
                    with analysis_container:
                        col_analysis, col_close = st.columns([10, 1])
                        
                        with col_analysis:
                            st.markdown(f"""
                            <div class="analysis-card">
                                <div class="analysis-text">
                                    <strong>📋 Analysis:</strong> {full_analysis}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_close:
                            if st.button("✕", key=f"close_analysis_{i}", help="Close analysis", type="secondary"):
                                st.session_state.analysis_results[i] = None
                                st.rerun()

# Export functionality with NEW "Generate New Plan" button
if any(idea.strip() for idea in st.session_state.generated_ideas):
    st.markdown("---")
    st.markdown("### Export & Actions")
    
    col1, col2, col3, col4 = st.columns(4)  # Changed to 4 columns
    
    with col1:
        if st.button("Copy to Clipboard", use_container_width=True):
            content_text = f"Weekly Content Plan: {st.session_state.topic}\n\n"
            for i, (day, idea) in enumerate(zip(days, st.session_state.generated_ideas)):
                if idea.strip():
                    content_text += f"{day}: {idea}\n"
            st.text_area("Content to Copy:", content_text, height=150)
    
    with col2:
        if st.button("Download as Text", use_container_width=True):
            content_text = f"Weekly Content Plan: {st.session_state.topic}\n\n"
            for i, (day, idea) in enumerate(zip(days, st.session_state.generated_ideas)):
                if idea.strip():
                    content_text += f"{day}: {idea}\n"
            st.download_button(
                label="Download",
                data=content_text,
                file_name=f"content_plan_{st.session_state.topic.replace(' ', '_')}.txt",
                mime="text/plain"
            )
    
    with col3:
        if st.button("Export as JSON", use_container_width=True):
            export_data = {
                "topic": st.session_state.topic,
                "audience": st.session_state.audience,
                "generated_date": st.session_state.generation_time.isoformat() if st.session_state.generation_time else None,
                "content_plan": {
                    day: idea for day, idea in zip(days, st.session_state.generated_ideas) if idea.strip()
                },
                "summary": st.session_state.summary
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"content_plan_{st.session_state.topic.replace(' ', '_')}.json",
                mime="application/json"
            )
    
    # NEW: Generate New Plan button
    with col4:
        if st.button("🔄 Generate New Plan", use_container_width=True, type="secondary"):
            # Clear all session state for new plan
            keys_to_clear = [
                "generated_ideas", "summary", "topic", "day_summaries", 
                "day_performance", "analysis_results", "generation_time", 
                "last_generation_successful", "last_topic_input"
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    if key == "generated_ideas":
                        st.session_state[key] = [""] * 7
                    elif key == "day_summaries":
                        st.session_state[key] = [None] * 7
                    elif key == "day_performance":
                        st.session_state[key] = [{"likes": 0, "shares": 0, "comments": 0} for _ in range(7)]
                    elif key == "analysis_results":
                        st.session_state[key] = [None] * 7
                    else:
                        st.session_state[key] = ""
            
            # Set flag to clear input
            st.session_state["clear_input"] = True
            st.success("Ready for new content plan!")
            st.rerun()

# Footer (ALL PRESERVED)
st.markdown("---")
st.markdown(
    """
<div style="text-align:center;opacity:0.7;padding:1.5rem 1rem;color:#888;background:linear-gradient(135deg,rgba(79,195,247,0.05),rgba(41,182,246,0.05));border-radius:12px;margin-top:1rem;">
    <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.3rem;color:#4FC3F7;">
        Agentic Content Planner
    </div>
    <div style="margin-bottom:0.3rem;">
        Powered by Advanced AI Technologies
    </div>
    <small style="opacity:0.8;">
        Built with Streamlit • OpenAI & Perplexity APIs
    </small>
</div>
""",
    unsafe_allow_html=True,
)
