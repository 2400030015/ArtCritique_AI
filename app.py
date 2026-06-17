import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import uuid
from datetime import datetime

# Import modules first to register them in sys.modules
import modules.database
import modules.color_analysis
import modules.composition_analysis
import modules.balance_analysis
import modules.style_detector
import modules.artwork_rating
import modules.color_theory
import modules.color_names
import modules.ai_feedback
import modules.pdf_report
import modules.similarity
import auth.database
import auth.login
import auth.signup
import auth.forgot_password

import sys
import importlib

# Force reload all modules to prevent Streamlit caching stale files in memory
for m in [
    modules.database,
    modules.color_analysis,
    modules.composition_analysis,
    modules.balance_analysis,
    modules.style_detector,
    modules.artwork_rating,
    modules.color_theory,
    modules.color_names,
    modules.ai_feedback,
    modules.pdf_report,
    modules.similarity,
    auth.database,
    auth.login,
    auth.signup,
    auth.forgot_password
]:
    importlib.reload(m)

# Now import the functions into app.py namespace
from modules.database import (
    db_init,
    save_analysis,
    save_report_path,
    get_artwork_history,
    get_artwork_detail,
    get_average_scores,
    get_score_trends,
    delete_artwork,
    get_db_connection
)
from modules.color_analysis import analyze_colors
from modules.composition_analysis import composition_score
from modules.balance_analysis import balance_score
from modules.style_detector import detect_style
from modules.artwork_rating import calculate_rating
from modules.color_theory import detect_color_theory
from modules.color_names import get_color_name
from modules.ai_feedback import generate_critique, get_fallback_critique
from modules.pdf_report import create_report
from modules.similarity import artwork_similarity
from auth import init_auth_db, show_login_page, show_signup_page, show_forgot_password_page

def cleanup_broken_records():
    """Detects broken image paths and deletes those records from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cleaned_count = 0
    try:
        cursor.execute("SELECT id, image_path FROM artworks")
        rows = cursor.fetchall()
        
        broken_ids = []
        for row in rows:
            art_id = row["id"]
            img_path = row["image_path"]
            if not img_path or not os.path.exists(img_path):
                broken_ids.append(art_id)
                
        if broken_ids:
            # Delete broken records. PRAGMA foreign_keys = ON automatically cascade-deletes children!
            cursor.executemany("DELETE FROM artworks WHERE id = ?", [(art_id,) for art_id in broken_ids])
            conn.commit()
            cleaned_count = len(broken_ids)
            print(f"Database cleanup: Removed {cleaned_count} records with missing images.")
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()
    return cleaned_count

# Initialize directory structures
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Initialize Database
db_init()
init_auth_db()
cleanup_broken_records()

# Page configurations
st.set_page_config(
    page_title="ArtCritique AI - Professional Art Feedback",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
styles_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(styles_path):
    with open(styles_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state initialization
# Session state initialization
if "active_artwork_id" not in st.session_state:
    st.session_state.active_artwork_id = None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# Authentication Routing
if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0F2027, #203A43, #2C5364) !important;
            background-attachment: fixed !important;
        }
        div[data-testid="stForm"] {
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    if st.session_state.auth_page == "login":
        show_login_page()
    elif st.session_state.auth_page == "signup":
        show_signup_page()
    elif st.session_state.auth_page == "forgot_password":
        show_forgot_password_page()
    st.stop()

# Helper to draw focal point on image
def get_image_with_focal_point(image_path, focal_point_coords):
    if not os.path.exists(image_path):
        return None
    try:
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        x, y = focal_point_coords
        
        # Calculate visual circle radius based on image dimensions
        r = max(min(img.width, img.height) // 35, 8)
        
        # Draw target ring
        draw.ellipse([x - r, y - r, x + r, y + r], outline="#E53935", width=4)
        draw.ellipse([x - r//2, y - r//2, x + r//2, y + r//2], outline="#FFEB3B", width=2)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill="#E53935")
        return img
    except Exception as e:
        print(f"Error drawing focal point: {e}")
        return None

# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
st.sidebar.markdown(
    f"""
    <div style='text-align: center; padding: 10px 0;'>
        <h1 style='color: #1E88E5; margin-bottom: 0;'>🎨 ArtCritique AI</h1>
        <p style='font-size: 0.85em; opacity: 0.7;'>Professional Art Feedback in Seconds</p>
        <div style='margin-top: 15px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 8px;'>
            <span style='font-size: 0.9em; opacity: 0.8;'>Artist Profile:</span><br/>
            <strong style='color: #1E88E5; font-size: 1.05em;'>{st.session_state.user_name}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()

if st.sidebar.button("🚪 Log Out", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = ""
    st.session_state.user_email = ""
    st.session_state.active_artwork_id = None
    st.session_state.auth_page = "login"
    st.rerun()

st.sidebar.divider()

menu = st.sidebar.selectbox(
    "Navigation Menu",
    ["Dashboard Overview", "Analyze Artwork", "Artwork Comparison", "Project Info"]
)

# Sidebar summary stats
averages = get_average_scores(user_id=st.session_state.user_id)
st.sidebar.markdown("### User Statistics")
st.sidebar.metric("Total Uploads", averages["total_uploads"])
st.sidebar.metric("Average Aesthetic Score", f"{averages['avg_aesthetic']}/100")

# If details view is active, force navigation override to show artwork details
if st.session_state.active_artwork_id is not None:
    current_page = "Artwork Details"
else:
    current_page = menu

# =====================================================
# ARTWORK DETAILS PAGE (DETAILED ANALYSIS VIEW)
# =====================================================
if current_page == "Artwork Details":
    artwork_id = st.session_state.active_artwork_id
    detail = get_artwork_detail(artwork_id)
    
    if not detail:
        st.error("Artwork details not found.")
        st.session_state.active_artwork_id = None
        st.rerun()
        
    st.markdown(f"## 📊 Analysis Report: {detail['title']}")
    
    # Back button
    if st.button("← Back to Dashboard", key="back_btn"):
        st.session_state.active_artwork_id = None
        st.rerun()
        
    st.divider()
    
    metrics = detail["metrics"]
    feedback = detail["feedback"]
    
    # Verdict badge
    verdict = metrics.get("verdict", "Intermediate")
    verdict_badge_class = f"badge-{verdict.lower()}"
    st.markdown(
        f"""
        <div style='margin-bottom: 20px;'>
            <span class='badge {verdict_badge_class}' style='font-size: 1.1em; padding: 6px 16px;'>{verdict} Skill Classification</span>
            <span style='margin-left: 15px; font-weight: bold; font-size: 1.1em;'>Overall Rating: {calculate_rating(metrics.get("composition_score",0), metrics.get("color_score",0), metrics.get("contrast_score",0), metrics.get("aesthetic_score",0))}/10</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Row 1: Metrics Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Composition Score", f"{int(metrics.get('composition_score', 0))}/100")
    c2.metric("Color Harmony Score", f"{int(metrics.get('color_score', 0))}/100")
    c3.metric("Contrast Score", f"{int(metrics.get('contrast_score', 0))}/100")
    c4.metric("Aesthetic Score (AI)", f"{int(metrics.get('aesthetic_score', 0))}/100")
    c5.metric("Visual Balance", f"{int(metrics.get('balance_score', 0))}%")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Row 2: Image and Radar Chart
    col_img, col_chart = st.columns([1, 1])
    
    with col_img:
        st.markdown("### 🖼 Focal Point Projection")
        focal_coords = (metrics.get("focal_point_x", 0), metrics.get("focal_point_y", 0))
        image_path = detail["image_path"]
        
        # Verify the file actually exists on disk before drawing or calling st.image
        if image_path and os.path.exists(image_path):
            if focal_coords != (0, 0):
                marked_img = get_image_with_focal_point(image_path, focal_coords)
                if marked_img:
                    st.image(marked_img, use_container_width=True, caption="Detected Focal Point (Red Target)")
                else:
                    st.image(image_path, use_container_width=True, caption=detail["title"])
            else:
                st.image(image_path, use_container_width=True, caption=detail["title"])
        else:
            st.warning("Artwork image file not found on disk.")
            
    with col_chart:
        st.markdown("### 📊 Skill Radar Chart")
        
        # Plotly Radar Chart
        radar_df = pd.DataFrame(dict(
            r=[
                metrics.get("composition_score", 0),
                metrics.get("color_score", 0),
                metrics.get("contrast_score", 0),
                metrics.get("aesthetic_score", 0),
                metrics.get("balance_score", 0),
                metrics.get("symmetry_score", 0)
            ],
            theta=['Composition', 'Color Harmony', 'Contrast', 'Aesthetic Score', 'Visual Balance', 'Symmetry']
        ))
        
        fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
        fig.update_traces(fill='toself', line_color='#1E88E5', line_width=2.5)
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # Row 3: Color Palette Analysis
    st.markdown("### 🎨 Dominant Color Palette")
    # Redetect colors or display them. Let's recalculate or pull from details.
    # In database.py, dominant colors aren't stored as lists but we can get them by recalculating,
    # or by storing colors in database? Wait! In database.py we did:
    # "ai_feedback: style_percentages". We didn't save colors list, but we can compute analyze_colors(img) instantly!
    # Recalculating is very fast (takes milliseconds) and allows dynamic interactive Plotly charts!
    img = cv2.imread(detail["image_path"])
    if img is not None:
        colors_result = analyze_colors(img)
        palette_cols = st.columns(5)
        for idx, color in enumerate(colors_result["colors"]):
            rgb = (color[0], color[1], color[2])
            hex_val = '#%02x%02x%02x' % rgb
            color_name = get_color_name(rgb)
            percentage = colors_result["percentages"][idx]
            
            palette_cols[idx].markdown(
                f"""
                <div style="
                    height:80px;
                    background:{hex_val};
                    border-radius:12px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                    margin-bottom: 8px;
                "></div>
                <div style='text-align: center; font-size: 0.85em;'>
                    <b>{color_name}</b><br/>
                    <code style='font-size: 0.8em;'>{hex_val.upper()}</code><br/>
                    <span style='color: #1E88E5; font-weight: bold;'>{percentage}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        st.markdown("<br/>", unsafe_allow_html=True)
        # Pie chart and color distribution
        c_pie, c_info = st.columns([1.5, 1])
        with c_pie:
            df_pie = pd.DataFrame({
                "Color": [get_color_name(c) for c in colors_result["colors"]],
                "Percentage": colors_result["percentages"],
                "Hex": ['#%02x%02x%02x' % (c[0], c[1], c[2]) for c in colors_result["colors"]]
            })
            fig_pie = px.pie(
                df_pie, 
                names="Color", 
                values="Percentage", 
                color="Hex",
                color_discrete_map={row["Hex"]: row["Hex"] for _, row in df_pie.iterrows()}
            )
            fig_pie.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c_info:
            theory = detect_color_theory(colors_result["colors"])
            st.markdown(
                f"""
                <div class='premium-card' style='margin-top: 15px;'>
                    <h4 style='margin-top:0;'>🎨 Color Theory & Harmony</h4>
                    <p><b>Harmony Scheme:</b> {theory['scheme']}</p>
                    <p><b>Color Compliance:</b> {theory['score']}/100</p>
                    <p><b>Warm/Cool Balance:</b> {colors_result['warm_cool_ratio']}% Warm Colors / {round(100 - colors_result['warm_cool_ratio'], 1)}% Cool Colors</p>
                    <p><b>Saturation Intensity:</b> {colors_result['saturation']}% average saturation</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    st.divider()

    # Row 4: AI Critique & Insights
    st.markdown("### 💡 AI Critique Engine")
    
    col_crit, col_road = st.columns([1, 1])
    
    with col_crit:
        st.markdown("#### ✦ Critique Breakdown")
        
        st.success("✔ **Strengths**")
        for s in feedback.get("strengths", []):
            st.markdown(f"- {s}")
            
        st.warning("⚠ **Areas for Improvement**")
        for w in feedback.get("weaknesses", []):
            st.markdown(f"- {w}")
            
        st.info("💡 **Actionable Suggestions**")
        for sug in feedback.get("suggestions", []):
            st.markdown(f"- {sug}")
            
    with col_road:
        st.markdown("#### ✦ Technical Roadmap")
        
        st.markdown("📦 **Immediate Fixes**")
        for fix in feedback.get("roadmap_immediate", []):
            st.markdown(f"- {fix}")
            
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("⏳ **Long-Term Skill Development**")
        for item in feedback.get("roadmap_longterm", []):
            st.markdown(f"- {item}")
            
    st.markdown("#### ✦ Professional Review")
    st.info(feedback.get("insights", "No review insights found."))

    st.divider()
    
    # Row 5: Action Button (PDF Download)
    st.markdown("### 📄 Export Critique Report")
    
    # Read generated PDF
    pdf_path = detail.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            st.download_button(
                label="⬇ Download Professional PDF Report",
                data=pdf_bytes,
                file_name=f"{detail['title'].replace(' ', '_')}_Critique_Report.pdf",
                mime="application/pdf"
            )
    else:
        # Re-generate PDF on the fly if missing
        st.warning("PDF report file is missing locally. Generating a new report...")
        new_pdf_path = f"reports/report_{artwork_id}.pdf"
        try:
            create_report(new_pdf_path, detail)
            save_report_path(artwork_id, new_pdf_path)
            
            with open(new_pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="⬇ Download Professional PDF Report",
                    data=pdf_bytes,
                    file_name=f"{detail['title'].replace(' ', '_')}_Critique_Report.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Failed to generate PDF Report: {e}")

# =====================================================
# PAGE 1: DASHBOARD OVERVIEW
# =====================================================
elif current_page == "Dashboard Overview":
    st.markdown("## 📊 Artist Analytics Dashboard")
    st.markdown("Track your learning curve, average skills progress, and historical uploads.")
    st.divider()

    # Get dashboard stats
    stats = get_average_scores(user_id=st.session_state.user_id)
    
    if stats["total_uploads"] == 0:
        st.info("👋 Welcome! You haven't analyzed any artworks yet. Go to the **Analyze Artwork** tab to get started.")
    else:
        # KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Uploads", stats["total_uploads"])
        c2.metric("Avg Composition", f"{stats['avg_composition']}/100")
        c3.metric("Avg Color Harmony", f"{stats['avg_color']}/100")
        c4.metric("Avg Contrast", f"{stats['avg_contrast']}/100")
        c5.metric("Avg Aesthetic Appeal", f"{stats['avg_aesthetic']}/100")
        
        st.divider()
        
        # Chronological line charts (Trends)
        st.markdown("### 📈 Visual Skill Progression Trends")
        trends = get_score_trends(user_id=st.session_state.user_id)
        
        if len(trends) > 1:
            df_trends = pd.DataFrame(trends)
            df_trends["created_at"] = pd.to_datetime(df_trends["created_at"])
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_trends["created_at"], y=df_trends["composition_score"], name="Composition", line=dict(color='#FF5722', width=2)))
            fig_trend.add_trace(go.Scatter(x=df_trends["created_at"], y=df_trends["color_score"], name="Color Harmony", line=dict(color='#4CAF50', width=2)))
            fig_trend.add_trace(go.Scatter(x=df_trends["created_at"], y=df_trends["contrast_score"], name="Contrast", line=dict(color='#FFEB3B', width=2)))
            fig_trend.add_trace(go.Scatter(x=df_trends["created_at"], y=df_trends["aesthetic_score"], name="Aesthetic Score", line=dict(color='#2196F3', width=2)))
            
            fig_trend.update_layout(
                xaxis_title="Timeline",
                yaxis_title="Scores",
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("💡 Keep uploading more artworks! A trend line chart will appear here once you have at least 2 analysis records.")
            
        st.divider()
        
        # History Gallery Grid
        st.markdown("### 🎨 Historical Artwork Gallery")
        history = get_artwork_history(user_id=st.session_state.user_id)
        
        cols_per_row = 4
        rows_count = (len(history) + cols_per_row - 1) // cols_per_row
        
        for r in range(rows_count):
            row_cols = st.columns(cols_per_row)
            for c in range(cols_per_row):
                idx = r * cols_per_row + c
                if idx < len(history):
                    art = history[idx]
                    
                    with row_cols[c]:
                        # Wrap card
                        verdict = art.get("verdict", "Intermediate")
                        badge_class = f"badge-{verdict.lower()}"
                        
                        st.markdown(
                            f"""
                            <div class='premium-card' style='padding: 10px;'>
                                <div style='text-align: center;'>
                                    <span class='badge {badge_class}' style='font-size:0.75em;'>{verdict}</span>
                                </div>
                                <h4 style='text-align: center; margin: 8px 0 2px 0;'>{art['title']}</h4>
                                <p style='text-align: center; font-size:0.8em; color:#78909C; margin:0 0 8px 0;'>{art['created_at'][:10]} | {art['style']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        img_path = art["image_path"]
                        if img_path and os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                        else:
                            st.warning("Image file missing from disk.")
                        
                        col_view, col_del = st.columns([2, 1])
                        
                        if col_view.button("View Report", key=f"view_{art['id']}"):
                            st.session_state.active_artwork_id = art["id"]
                            st.rerun()
                            
                        if col_del.button("🗑 Delete", key=f"del_{art['id']}"):
                            delete_artwork(art["id"])
                            st.toast(f"Deleted {art['title']}")
                            st.rerun()

# =====================================================
# PAGE 2: ANALYZE ARTWORK
# =====================================================
elif current_page == "Analyze Artwork":
    st.markdown("## 🚀 Analyze New Artwork")
    st.markdown("Upload your image (painting, sketch, digital drawing) to get low-level visual metrics and detailed AI critiques.")
    st.divider()

    uploaded_file = st.file_uploader(
        "Drag and drop artwork here (Max 20MB)",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file is not None:
        # Check size constraints
        if uploaded_file.size > 20 * 1024 * 1024:
            st.error("File size exceeds 20MB. Please upload a smaller image.")
        else:
            col1, col2 = st.columns([1, 1.2])
            
            with col1:
                st.markdown("### Image Preview")
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)
                
            with col2:
                st.markdown("### Artwork Details")
                art_title = st.text_input("Artwork Title", placeholder="e.g. Whispers of Autumn", value="")
                
                # Check for empty title
                if not art_title.strip():
                    art_title = f"Artwork {datetime.now().strftime('%Y%m%d%H%M')}"
                
                st.write("")
                if st.button("🚀 Run AI Art Critique Analysis"):
                    
                    import time
                    t_start = time.time()
                    
                    with st.status("Running Art Critique Analysis...") as status:
                        
                        # Stage 1: Image preparation / upload
                        status.text("Preparing image upload...")
                        t_prep_start = time.time()
                        img_array = np.array(image)
                        if len(img_array.shape) == 3:
                            if img_array.shape[2] == 4:
                                img_array = img_array[:, :, :3]
                            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        elif len(img_array.shape) == 2:
                            img_cv = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                        else:
                            img_cv = np.zeros((400, 400, 3), dtype=np.uint8)
                        t_prep = time.time() - t_prep_start
                        
                        # Stage 2: Composition Analysis
                        status.text("Running composition analysis...")
                        t_comp_start = time.time()
                        comp_res = composition_score(img_cv)
                        t_comp = time.time() - t_comp_start
                        
                        # Stage 3: Balance Analysis
                        status.text("Running balance analysis...")
                        t_bal_start = time.time()
                        bal_res = balance_score(img_cv)
                        t_bal = time.time() - t_bal_start
                        
                        # Stage 4: Color Analysis
                        status.text("Running color analysis...")
                        t_color_start = time.time()
                        colors_res = analyze_colors(img_cv)
                        t_color = time.time() - t_color_start
                        
                        # Stage 5: Color Theory Detection
                        status.text("Running color theory detection...")
                        t_theory_start = time.time()
                        harmony_res = detect_color_theory(colors_res["colors"])
                        t_theory = time.time() - t_theory_start
                        
                        # Defensive validation and debug logging (Requirement 5 & 6)
                        if not isinstance(comp_res, dict):
                            raise ValueError(
                                f"Expected dict from composition analysis, got {type(comp_res)}"
                            )
                            
                        balance_res = bal_res
                        color_res = colors_res
                        theory_res = harmony_res
                        
                        st.write("Composition:", comp_res)
                        st.write("Balance:", balance_res)
                        st.write("Color:", color_res)
                        st.write("Theory:", theory_res)
                        
                        metrics = {
                            "composition_score": comp_res["composition_score"],
                            "color_score": harmony_res["score"],
                            "contrast_score": colors_res["contrast"] * 100.0 / 127.0, # normalized
                            "symmetry_score": comp_res["symmetry_score"],
                            "balance_score": bal_res["balance_score"],
                            "focal_point_x": comp_res["focal_point"][0],
                            "focal_point_y": comp_res["focal_point"][1]
                        }

                        # Stage 6: Call Gemini AI critique (Requirement 2, 3, 4, 7)
                        status.text("Generating AI critique...")
                        t_gemini_start = time.time()
                        feedback_res = None
                        try:
                            feedback_res = generate_critique(image, timeout=30)
                        except Exception as e:
                            st.error(f"Gemini Error: {e}")
                            err_msg = str(e)
                            if "Raw response:" in err_msg:
                                raw_resp = err_msg.split("Raw response:", 1)[1]
                                st.markdown("### Raw Gemini Response")
                                st.code(raw_resp.strip(), language="json")
                            # Continues analysis using fallback critique (Requirement 7)
                            feedback_res = get_fallback_critique()
                        t_gemini = time.time() - t_gemini_start
                        
                        # Stage 7: Save file locally & DB save
                        status.text("Saving results...")
                        t_db_start = time.time()
                        unique_id = str(uuid.uuid4())[:8]
                        filename = f"uploads/art_{unique_id}.png"
                        image.save(filename, format="PNG")
                        
                        artwork_id = save_analysis(
                            user_id=st.session_state.user_id,
                            title=art_title,
                            image_path=filename,
                            metrics=metrics,
                            feedback=feedback_res
                        )
                        t_db = time.time() - t_db_start
                        
                        # Stage 8: Generate PDF report
                        status.text("Generating PDF report...")
                        t_pdf_start = time.time()
                        pdf_path = f"reports/report_{artwork_id}.pdf"
                        full_detail = get_artwork_detail(artwork_id)
                        create_report(pdf_path, full_detail)
                        
                        # Update report path in db
                        save_report_path(artwork_id, pdf_path)
                        t_pdf = time.time() - t_pdf_start
                        
                        t_total = time.time() - t_start
                        
                        status.update(label="Analysis Complete!", state="complete", expanded=False)
                        
                    # Display timing logs (Requirement 8)
                    st.markdown("### ⏱ Execution Times")
                    st.write(f"Composition: {t_comp:.1f} sec")
                    st.write(f"Color Analysis: {t_color:.1f} sec")
                    st.write(f"Gemini: {t_gemini:.1f} sec")
                    st.write(f"Total: {t_total:.1f} sec")
                    
                    st.markdown("#### Detailed Timing Breakdown")
                    st.write(f"Image Preparation: {t_prep:.3f} sec")
                    st.write(f"Composition Analysis: {t_comp:.3f} sec")
                    st.write(f"Balance Analysis: {t_bal:.3f} sec")
                    st.write(f"Color Analysis: {t_color:.3f} sec")
                    st.write(f"Color Theory Detection: {t_theory:.3f} sec")
                    st.write(f"Gemini API Call: {t_gemini:.3f} sec")
                    st.write(f"Database Save: {t_db:.3f} sec")
                    st.write(f"PDF Report Generation: {t_pdf:.3f} sec")
                    
                    st.session_state.active_artwork_id = artwork_id
                    st.success("Analysis complete! Click below to view the detailed report.")
                    if st.button("📊 View Report Dashboard", key="view_report_btn"):
                        st.rerun()

# =====================================================
# PAGE 3: ARTWORK COMPARISON
# =====================================================
elif current_page == "Artwork Comparison":
    st.markdown("## 🆚 Artwork Side-by-Side Comparison")
    st.markdown("Upload two different artworks to compare composition, color harmony, and visual similarity.")
    st.divider()

    c_upload1, c_upload2 = st.columns(2)
    
    with c_upload1:
        st.subheader("Artwork 1")
        file1 = st.file_uploader("Upload first image", type=["jpg", "png", "webp"], key="comp1")
        
    with c_upload2:
        st.subheader("Artwork 2")
        file2 = st.file_uploader("Upload second image", type=["jpg", "png", "webp"], key="comp2")

    if file1 and file2:
        img1 = Image.open(file1)
        img2 = Image.open(file2)
        
        # Display side-by-side previews
        c_preview1, c_preview2 = st.columns(2)
        with c_preview1:
            st.image(img1, use_container_width=True, caption="Artwork 1")
        with c_preview2:
            st.image(img2, use_container_width=True, caption="Artwork 2")
            
        st.divider()
        
        if st.button("🆚 Execute Similarity & Style Comparison"):
            with st.spinner("Analyzing and comparing pixels..."):
                # Convert PIL to OpenCV BGR
                cv_img1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)
                cv_img2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)
                
                # Run metrics
                comp1 = composition_score(cv_img1)
                comp2 = composition_score(cv_img2)
                
                colors1 = analyze_colors(cv_img1)
                colors2 = analyze_colors(cv_img2)
                
                harmony1 = detect_color_theory(colors1["colors"])
                harmony2 = detect_color_theory(colors2["colors"])
                
                bal1 = balance_score(cv_img1)
                bal2 = balance_score(cv_img2)
                
                # Defensive validation and debug logging for comparison
                st.write("DEBUG composition 1 result:", comp1)
                st.write("DEBUG composition 2 result:", comp2)
                if not isinstance(comp1, dict):
                    raise ValueError(f"Expected dict from composition analysis 1, got {type(comp1)}")
                if not isinstance(comp2, dict):
                    raise ValueError(f"Expected dict from composition analysis 2, got {type(comp2)}")
                
                # Similarity mapping
                sim_score = artwork_similarity(cv_img1, cv_img2)
                
                # Render results in table
                st.markdown(f"### 📊 Comparison Metrics (Visual Similarity: `{sim_score}%`)")
                
                comparison_df = pd.DataFrame({
                    "Metric": [
                        "Composition Alignment", 
                        "Color Harmony", 
                        "Visual Balance", 
                        "Symmetry Score",
                        "Average Brightness", 
                        "Average Saturation",
                        "Contrast Index"
                    ],
                    "Artwork 1 Value": [
                        f"{comp1['composition_score']}/100",
                        f"{harmony1['score']}/100 ({harmony1['scheme']})",
                        f"{bal1['balance_score']}%",
                        f"{comp1['symmetry_score']}%",
                        f"{colors1['brightness']}/255",
                        f"{colors1['saturation']}%",
                        f"{colors1['contrast']}"
                    ],
                    "Artwork 2 Value": [
                        f"{comp2['composition_score']}/100",
                        f"{harmony2['score']}/100 ({harmony2['scheme']})",
                        f"{bal2['balance_score']}%",
                        f"{comp2['symmetry_score']}%",
                        f"{colors2['brightness']}/255",
                        f"{colors2['saturation']}%",
                        f"{colors2['contrast']}"
                    ]
                })
                
                st.table(comparison_df)
                
                # Summarized Verdict
                st.markdown("#### ✦ Summary Critique")
                if comp1['composition_score'] > comp2['composition_score']:
                    st.write("- **Artwork 1** displays a stronger grid alignment and focal structure.")
                else:
                    st.write("- **Artwork 2** displays a stronger grid alignment and focal structure.")
                    
                if harmony1['score'] > harmony2['score']:
                    st.write(f"- **Artwork 1** shows higher compliance to color harmony theory ({harmony1['scheme']}).")
                else:
                    st.write(f"- **Artwork 2** shows higher compliance to color harmony theory ({harmony2['scheme']}).")

# =====================================================
# PAGE 4: PROJECT INFO
# =====================================================
else:
    st.markdown("## 📘 Project Information")
    st.markdown("### ArtCritique AI - B.Tech Major Project")
    st.divider()

    st.markdown(
        """
        <div class='premium-card'>
            <h4>⚙ Architecture Overview</h4>
            <p>This system integrates computer vision techniques with large multimodal model capability to automate technical critiques of artwork. Key components:</p>
            <ul>
                <li><b>Computer Vision Layer:</b> Analyzes Rule of Thirds alignment, horizontal/vertical symmetry, visual weight balance, dominant color extraction (via KMeans), and color harmony schemes (HSV circular analysis).</li>
                <li><b>Generative AI Layer:</b> Leverages Google Gemini 2.5 Flash for professional feedback text formatting, aesthetic appraisal, and technical roadmap building.</li>
                <li><b>Data & Storage Layer:</b> Uses a SQLite database storing user records, artwork upload pointers, raw metrics, and AI textual feedback.</li>
                <li><b>PDF Engine:</b> ReportLab script drawing layout grids, canvas headers/footers, dynamic pagination, and embedding high-definition matplotlib radar charts.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div class='premium-card'>
            <h4>🛠 Technologies Utilized</h4>
            <ul>
                <li><b>Language:</b> Python 3.10</li>
                <li><b>Frontend:</b> Streamlit 1.58</li>
                <li><b>Image Processing:</b> OpenCV, NumPy, Pillow, Scikit-Learn</li>
                <li><b>Generative AI:</b> google-generativeai API (Gemini 2.5 Flash)</li>
                <li><b>Charts & Plotting:</b> Plotly, Matplotlib</li>
                <li><b>PDF Builder:</b> ReportLab Platypus</li>
                <li><b>Database:</b> SQLite3</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )