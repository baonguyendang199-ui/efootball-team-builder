# app.py – Efootball Team Builder (Google Sheets version)
import os
import shutil
import time
from pathlib import Path
from datetime import datetime
import re
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
import streamlit as st
import json
from google.oauth2.service_account import Credentials
import gspread
import numpy as np
from scipy.optimize import linear_sum_assignment

st.set_page_config(
    page_title="Efootball Team Builder",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_THEME = {
    "primary": "#7C3AED",
    "secondary": "#F97316",
    "accent": "#22D3EE",
    "bg_gradient": "linear-gradient(135deg, #030712 0%, #0F172A 55%, #1E1B4B 100%)",
    "surface": "rgba(15,23,42,0.85)",
    "card": "rgba(15,23,42,0.75)",
    "border": "rgba(255,255,255,0.08)",
    "text": "#E2E8F0",
    "muted": "#94A3B8"
}
SHOW_APP_HERO = False


def inject_modern_ui_theme():
    """Inject modern UI tokens, typography and component styling (Compact Version)."""
    theme = APP_THEME
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
        
        :root {{
            --epic-grad: linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
            --potw-grad: linear-gradient(135deg, #d946ef 0%, #9333ea 100%);
            --std-grad: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            --card-bg: rgba(15,23,42,0.95);
        }}

        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            background: {theme["bg_gradient"]};
            color: {theme["text"]};
        }}

        /* --- COMPACT EFOOTBALL CARD STYLES --- */
        .e-card {{
            position: relative;
            width: 100%;
            /* GIẢM CHIỀU CAO TỪ 280px -> 200px */
            height: 200px !important; 
            border-radius: 8px; /* Bo góc nhỏ hơn xíu */
            overflow: hidden;
            transition: all 0.2s ease-out;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1);
            background: var(--card-bg);
            cursor: pointer;
        }}
        
        .e-card:hover {{
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 16px rgba(0,0,0,0.6);
            border-color: rgba(255,255,255,0.3);
            z-index: 10;
        }}

        /* Rarity Borders - Mỏng hơn (3px) */
        .e-card.epic {{ border-bottom: 3px solid #FFD700; }}
        .e-card.potw {{ border-bottom: 3px solid #d946ef; }}
        .e-card.std {{ border-bottom: 3px solid #3b82f6; }}

        .e-card .card-header {{
            position: relative;
            height: 35px; /* Giảm từ 60px -> 35px */
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 8px;
            background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, transparent 100%);
            z-index: 2;
        }}

        .e-card .rating-box {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 800;
            font-size: 1.1rem; /* Giảm từ 1.4rem */
            line-height: 1;
            text-shadow: 1px 1px 0px rgba(0,0,0,0.8);
        }}
        
        .e-card.epic .rating-box {{ color: #FFD700; }}
        .e-card.potw .rating-box {{ color: #ff8df5; }}
        .e-card.std .rating-box {{ color: #93c5fd; }}

        .e-card .position-box {{
            font-size: 0.7rem; /* Giảm font */
            font-weight: 700;
            background: rgba(0,0,0,0.6);
            padding: 1px 4px;
            border-radius: 3px;
            color: #fff;
        }}

        .e-card .player-img {{
            width: 100%;
            height: 110px; /* Giảm từ 140px */
            object-fit: contain;
            margin-top: -15px; /* Đẩy ảnh lên cao hơn */
            position: relative;
            z-index: 1;
            filter: drop-shadow(0 3px 3px rgba(0,0,0,0.5));
        }}

        .e-card .card-info {{
            padding: 6px 8px; /* Padding gọn hơn */
            background: rgba(10, 15, 30, 0.9); /* Màu nền đậm hơn để dễ đọc */
            border-top: 1px solid rgba(255,255,255,0.05);
            position: absolute;
            bottom: 0;
            width: 100%;
            height: 55px; /* Cố định chiều cao phần info */
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .e-card .player-name {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 700;
            font-size: 0.85rem; /* Giảm từ 0.95rem */
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center;
            margin-bottom: 2px;
            color: white;
        }}

        .e-card .sub-info {{
            display: flex;
            justify-content: space-between;
            font-size: 0.65rem; /* Font rất nhỏ cho thông tin phụ */
            color: #94a3b8;
            align-items: center;
        }}

        /* Shine Effect - Giữ nguyên nhưng chỉnh speed */
        .shine {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
            background-size: 200% 100%;
            animation: shine 5s infinite linear;
            pointer-events: none;
            z-index: 5;
        }}
        @keyframes shine {{ 0% {{background-position: 100% 0}} 100% {{background-position: -100% 0}} }}

        /* --- STREAMLIT OVERRIDES --- */
        div.stButton > button {{
            border-radius: 4px;
            font-size: 0.8rem;
            padding: 0.25rem 0.5rem;
        }}
        
        </style>
        """,
        unsafe_allow_html=True
    )

def render_efootball_card_html(player_data, width="100%", highlight_metric=None):
    """
    Tạo HTML Card - FIX TRIỆT ĐỂ LỖI CODE BLOCK DO THỤT DÒNG.
    """
    import re
    
    p_name = player_data.get('Player', 'Unknown')
    rating = player_data.get('Rating', 0)
    pos = player_data.get('Position', '?')
    p_type = str(player_data.get('Player Type', 'NON-EPIC')).upper()
    action = str(player_data.get('Action', '')).upper()
    
    # --- XỬ LÝ ẢNH ---
    img_url = "https://pesdb.net/assets/img/card/f0.png"
    pid = str(player_data.get('Player ID', '')).strip()
    if not pid or pid == "0" or pid == "":
        purl = str(player_data.get('Player URL', '')).strip()
        match = re.search(r"id=(\d+)", purl) or re.search(r"(\d{5,})", purl)
        if match: pid = match.group(1)
    if pid and pid.isdigit():
        img_url = f"https://pesdb.net/assets/img/card/f{pid}.png"
    custom_img = str(player_data.get('Image', '')).strip()
    if custom_img and custom_img.startswith('http'):
        img_url = custom_img

    # --- MÀU SẮC ---
    card_class = "std"
    bg_gradient = "linear-gradient(180deg, #172554 0%, #020617 100%)" 
    stat_color = "#38bdf8" # Cyan
    
    if "POTW" in p_type or "TRENDING" in p_type:
        card_class = "potw"
        bg_gradient = "linear-gradient(180deg, #581c87 0%, #2e1065 100%)" 
        stat_color = "#e879f9" # Pink
    elif "EPIC" in p_type and "NON" not in p_type:
        card_class = "epic"
        bg_gradient = "linear-gradient(180deg, #713f12 0%, #451a03 100%)" 
        stat_color = "#fbbf24" # Gold

    club = player_data.get('Club', '')
    
    # --- LOGIC ACTION BADGE ---
    top_badge_html = ""
    if "BÁN" in action:
        top_badge_html = f'<div style="position:absolute; top:35px; right:5px; background:#ef4444; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:4px; z-index:4; box-shadow:0 1px 3px rgba(0,0,0,0.5); transform: rotate(5deg);">BÁN</div>'
    elif "GIỮ" in action:
        top_badge_html = f'<div style="position:absolute; top:35px; right:5px; background:#22c55e; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:4px; z-index:4; box-shadow:0 1px 3px rgba(0,0,0,0.5); transform: rotate(-5deg);">GIỮ</div>'
    
    # --- LOGIC METRIC TAG (QUAN TRỌNG: VIẾT TRÊN 1 DÒNG) ---
    metric_val = ""
    metric_label = ""
    
    if highlight_metric:
        try:
            if highlight_metric == 'BMI':
                h = float(player_data.get('Height', 0)) / 100.0
                w = float(player_data.get('Weight', 0))
                if h > 0: 
                    bmi = w/(h**2)
                    metric_val = f"{bmi:.1f}"
                    metric_label = "BMI"
            elif highlight_metric == 'Height':
                metric_val = f"{player_data.get('Height', '-')} cm"
            elif highlight_metric == 'Weight':
                metric_val = f"{player_data.get('Weight', '-')} kg"
            elif highlight_metric == 'Age':
                metric_val = f"{player_data.get('Age', '-')} tuổi"
        except:
            pass
            
    metric_html = ""
    if metric_val:
        # LƯU Ý: Đoạn này phải viết liền 1 dòng, không được xuống dòng
        label_html = f"<span style='color:#94a3b8; font-weight:500; margin-right:4px'>{metric_label}:</span>" if metric_label else ""
        metric_html = f'<div style="position: absolute; bottom: 58px; left: 50%; transform: translateX(-50%); background: rgba(15, 23, 42, 0.95); color: {stat_color}; font-size: 10px; font-weight: 700; padding: 2px 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); z-index: 20; white-space: nowrap; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; align-items: center;">{label_html}<span>{metric_val}</span></div>'

    # --- HTML CARD TỔNG (CŨNG PHẢI 1 DÒNG) ---
    html = f"""<div class="e-card {card_class}" style="background: {bg_gradient}; width: {width};" title="{p_name} | {rating}">{metric_html}{top_badge_html}<div class="shine"></div><div class="card-header"><div class="rating-box">{rating}</div><div class="position-box">{pos}</div></div><img src="{img_url}" class="player-img" onerror="this.src='https://pesdb.net/assets/img/card/f0.png'"><div class="card-info"><div class="player-name">{p_name}</div><div class="sub-info"><span style="opacity:0.9; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; max-width: 70%;">{club}</span><span>{str(player_data.get('Nation', ''))[:3].upper()}</span></div></div></div>"""
    
    return html

@st.dialog("Hồ sơ cầu thủ", width="large")
def show_player_modal(row):
    """
    Giao diện Scouting Profile - Phiên bản Fix lỗi hiển thị Code Text.
    Lưu ý: Các dòng HTML bên trong f-string phải viết sát lề trái.
    """
    # --- 1. CHUẨN BỊ DỮ LIỆU ---
    p_name = row.get('Player', 'Unknown')
    rating = row.get('Rating', 0)
    pos = row.get('Position', '?')
    style = row.get('Position Style', 'N/A')
    p_type = str(row.get('Player Type', 'Standard')).upper()
    club = row.get('Club', 'Unknown Club')
    nation = row.get('Nation', 'Unknown Nation')
    
    action = str(row.get('Action', 'N/A')).upper()
    reasons = str(row.get('Reasons', 'Chưa có phân tích'))
    
    img_url = row.get('Player URL', '') 
    pid = str(row.get('Player ID', '')).strip()
    if not pid and img_url:
        m = re.search(r"(\d{14,})", str(img_url))
        pid = m.group(1) if m else ""
    real_img = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else "https://pesdb.net/assets/img/card/f0.png"

    # Theme Config
    if "POTW" in p_type or "TRENDING" in p_type:
        accent_color = "#D946EF"
        badge_bg = "linear-gradient(135deg, #701a75 0%, #D946EF 100%)"
        shadow_color = "rgba(217, 70, 239, 0.4)"
    elif "EPIC" in p_type and "NON" not in p_type:
        accent_color = "#F59E0B"
        badge_bg = "linear-gradient(135deg, #78350f 0%, #F59E0B 100%)"
        shadow_color = "rgba(245, 158, 11, 0.4)"
    else:
        accent_color = "#3B82F6"
        badge_bg = "linear-gradient(135deg, #1e3a8a 0%, #3B82F6 100%)"
        shadow_color = "rgba(59, 130, 246, 0.4)"

    def render_stat_bar(label, value_text, max_score=4):
        val = str(value_text).upper()
        score = 1
        if any(x in val for x in ['VERY HIGH', 'REGULARLY', 'UNWAVERING']): score = 4
        elif any(x in val for x in ['HIGH', 'OCCASIONALLY', 'STANDARD']): score = 3
        elif any(x in val for x in ['MEDIUM', 'RARELY']): score = 2
        
        bars = ""
        for i in range(1, max_score + 1):
            bg = accent_color if i <= score else "rgba(255,255,255,0.1)"
            bars += f'<div style="flex:1; height:4px; background:{bg}; border-radius:2px; margin-right:2px;"></div>'
        
        # HTML này phải viết thành 1 dòng hoặc sát lề
        return f"""<div style="margin-bottom: 8px;"><div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:2px; color:#cbd5e1;"><span>{label}</span><span style="color:{accent_color}; font-weight:600">{value_text}</span></div><div style="display:flex; width:100%;">{bars}</div></div>"""

    # --- 2. XỬ LÝ SKILLS ---
    base_skills = [s.strip() for s in str(row.get('Skills','')).split(',') if s.strip()]
    added_skills = [s.strip() for s in str(row.get('Added Skills','')).split(',') if s.strip()]
    skills_html = ""
    for s in base_skills: skills_html += f'<span class="pf-skill">{s}</span>'
    for s in added_skills: skills_html += f'<span class="pf-skill added" title="Added Skill">+{s}</span>'
    if not skills_html: skills_html = '<span style="color:#64748b; font-style:italic;">Chưa có kỹ năng</span>'

    # --- 3. REASONS BLOCK ---
    action_bg = "rgba(34, 197, 94, 0.2)" if "GIỮ" in action else "rgba(239, 68, 68, 0.2)"
    action_border = "#22c55e" if "GIỮ" in action else "#ef4444"
    action_text = "#4ade80" if "GIỮ" in action else "#f87171"

    reasons_html = ""
    if action != "N/A" and action != "":
        # HTML viết sát lề trái
        reasons_html = f"""<div style="margin: 0 20px 10px 20px; padding: 12px; background: {action_bg}; border: 1px solid {action_border}; border-radius: 8px; display: flex; align-items: flex-start; gap: 10px;"><div style="font-weight: 800; font-size: 1.1rem; color: {action_text}; white-space: nowrap;">{action}</div><div style="font-size: 0.9rem; color: #e2e8f0; border-left: 1px solid rgba(255,255,255,0.2); padding-left: 10px; line-height: 1.4;"><div style="font-weight:600; font-size:0.75rem; color:#94a3b8; text-transform:uppercase; margin-bottom:2px;">PHÂN TÍCH CHIẾN LƯỢC</div>{reasons}</div></div>"""

    # --- 4. HTML TỔNG (QUAN TRỌNG: VIẾT SÁT LỀ TRÁI, KHÔNG THỤT ĐẦU DÒNG) ---
    html_content = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
.profile-container {{ font-family: 'Space Grotesk', sans-serif; background: linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 1) 100%); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; overflow: hidden; box-shadow: 0 0 40px rgba(0,0,0,0.5); color: white; margin-bottom: 10px; }}
.pf-hero {{ position: relative; height: 140px; background: radial-gradient(circle at top right, {shadow_color}, transparent 60%); display: flex; align-items: flex-end; padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
.pf-img-wrapper {{ width: 110px; height: 110px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-right: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); backdrop-filter: blur(4px); }}
.pf-img {{ width: 100%; height: 100%; object-fit: contain; transform: scale(1.1); }}
.pf-header-info {{ flex-grow: 1; }}
.pf-name {{ font-size: 2rem; font-weight: 700; line-height: 1.1; margin-bottom: 5px; text-transform: uppercase; letter-spacing: -0.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
.pf-badges {{ display: flex; gap: 8px; align-items: center; }}
.pf-badge {{ font-size: 0.75rem; padding: 4px 8px; border-radius: 4px; font-weight: 600; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.1); }}
.pf-rating {{ background: {badge_bg}; color: white; border: none; box-shadow: 0 0 10px {shadow_color}; }}
.pf-grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; padding: 20px; }}
.pf-section-title {{ font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
.stat-item {{ background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; }}
.stat-label {{ font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; }}
.stat-val {{ font-size: 1.1rem; font-weight: 600; color: white; }}
.skill-container {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.pf-skill {{ font-size: 0.8rem; padding: 4px 10px; border-radius: 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #e2e8f0; transition: all 0.2s; }}
.pf-skill:hover {{ background: {accent_color}33; border-color: {accent_color}; color: white; }}
.pf-skill.added {{ border-left: 3px solid #4ade80; background: rgba(74, 222, 128, 0.1); }}
</style>
<div class="profile-container">
<div class="pf-hero">
<div class="pf-img-wrapper"><img src="{real_img}" class="pf-img"></div>
<div class="pf-header-info">
<div class="pf-badges" style="margin-bottom:8px;">
<span class="pf-badge pf-rating">{rating}</span>
<span class="pf-badge">{pos}</span>
<span class="pf-badge" style="color:{accent_color}; border-color:{accent_color}">{p_type}</span>
</div>
<div class="pf-name">{p_name}</div>
<div style="font-size: 0.9rem; color: #cbd5e1;">{club} <span style="margin:0 5px; color:#64748b">•</span> {nation}</div>
</div>
</div>
{reasons_html}
<div class="pf-grid">
<div>
<div class="pf-section-title">Thông số vật lý</div>
<div class="stat-grid" style="margin-bottom: 20px;">
<div class="stat-item"><div class="stat-label">Chiều cao</div><div class="stat-val">{row.get('Height','-')} <small style="font-size:0.7em; color:#64748b">cm</small></div></div>
<div class="stat-item"><div class="stat-label">Cân nặng</div><div class="stat-val">{row.get('Weight','-')} <small style="font-size:0.7em; color:#64748b">kg</small></div></div>
<div class="stat-item"><div class="stat-label">Tuổi</div><div class="stat-val">{row.get('Age','-')}</div></div>
<div class="stat-item"><div class="stat-label">Chân thuận</div><div class="stat-val">{row.get('Foot','-')}</div></div>
</div>
<div class="pf-section-title">Kỹ thuật & Phong độ</div>
<div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 8px;">
{render_stat_bar("Weak Foot Usage", row.get('Weak Foot Usage', '-'))}
{render_stat_bar("Weak Foot Accuracy", row.get('Weak Foot Accuracy', '-'))}
{render_stat_bar("Form / Condition", row.get('Form', '-'))}
{render_stat_bar("Injury Resistance", row.get('Injury Resistance', '-'), max_score=3)}
</div>
</div>
<div>
<div class="pf-section-title">Phong cách thi đấu</div>
<div style="margin-bottom:20px; font-weight:600; font-size:1.1rem; color:{accent_color}">{style}</div>
<div class="pf-section-title">Danh sách kỹ năng</div>
<div class="skill-container">{skills_html}</div>
<div style="margin-top:25px; padding:12px; background:rgba(59, 130, 246, 0.1); border-radius:8px; border-left:3px solid {accent_color};">
<div style="font-size:0.75rem; color:#94a3b8; margin-bottom:4px;">REGION / LEAGUE</div>
<div style="font-size:0.9rem; font-weight:500;">{row.get('League','-')}</div>
<div style="font-size:0.8rem; color:#cbd5e1;">{row.get('Region','-')}</div>
</div>
</div>
</div>
</div>
"""
    st.markdown(html_content, unsafe_allow_html=True)

    # Footer Actions
    st.write("")
    c1, c2 = st.columns([1, 4])
    with c1:
        if row.get('Player URL'):
            st.link_button("🌐 PESDB Link", row.get('Player URL'), use_container_width=True)
    with c2:
        pass


def render_app_hero(df: pd.DataFrame):
    """Render the hero banner with live metrics."""
    if df is None:
        df = pd.DataFrame()
    total_players = int(df['Player'].count()) if 'Player' in df.columns else len(df)
    avg_rating = float(df['Rating'].mean()) if 'Rating' in df.columns and not df.empty else 0.0
    avg_rating_display = f"{avg_rating:.1f}" if avg_rating else "0.0"
    unique_clubs = int(df['Club'].nunique()) if 'Club' in df.columns else 0
    unique_leagues = int(df['League'].nunique()) if 'League' in df.columns else 0
    epic_count = int(df['Player Type'].astype(str).str.upper().eq('EPIC').sum()) if 'Player Type' in df.columns else 0
    potw_count = int(df['Player Type'].astype(str).str.upper().eq('POTW').sum()) if 'Player Type' in df.columns else 0
    epic_share = f"{(epic_count / total_players * 100):.0f}%" if total_players else "0%"
    top_positions = []
    if 'Position' in df.columns and not df.empty:
        top_positions = df['Position'].dropna().astype(str).value_counts().head(2).index.tolist()
    top_positions_text = " & ".join(top_positions) if top_positions else "Đa dạng vị trí"
    last_sync = datetime.now().strftime("%d/%m/%Y • %H:%M")
    
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-copy">
                <div class="hero-eyebrow">UI Refresh • {last_sync}</div>
                <h1>Control Center cho Efootball Team Builder</h1>
                <p class="hero-desc">
                    Thiết kế mới áp dụng nguyên tắc user-centric, visual hierarchy, 
                    khả năng tiếp cận WCAG và hỗ trợ AI cho quy trình build squad, 
                    giúp trải nghiệm nhanh hơn, nhất quán trên mọi thiết bị.
                </p>
                <div class="hero-tags">
                    <span class="pill">Responsive Grid</span>
                    <span class="pill">Design Tokens</span>
                    <span class="pill">Accessibility 2.2</span>
                    <span class="pill">AI Assist</span>
                </div>
            </div>
            <div class="hero-stats">
                <div class="stat-card">
                    <span>Tổng cầu thủ</span>
                    <strong>{total_players}</strong>
                    <small>{unique_clubs} clubs • {unique_leagues} leagues</small>
                </div>
                <div class="stat-card">
                    <span>Rating trung bình</span>
                    <strong>{avg_rating_display}</strong>
                    <small>Top vị trí: {top_positions_text}</small>
                </div>
                <div class="stat-card">
                    <span>EPIC share</span>
                    <strong>{epic_share}</strong>
                    <small>{epic_count} EPIC • {potw_count} POTW</small>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def apply_plotly_theme(fig):
    """Apply transparent background + typography to Plotly charts so they match the app theme."""
    theme = APP_THEME
    
    def extract_title(obj):
        if not obj:
            return ""
        if isinstance(obj, str):
            return obj
        text = getattr(obj, "text", None)
        if text is not None:
            return text
        return ""
    
    x_title = extract_title(getattr(getattr(fig.layout, "xaxis", None), "title", None))
    y_title = extract_title(getattr(getattr(fig.layout, "yaxis", None), "title", None))
    figure_title = extract_title(getattr(fig.layout, "title", None))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color=theme["text"]),
        margin=dict(l=40, r=30, t=60, b=50),
        legend=dict(font=dict(color=theme["text"])),
        title=dict(
            text=figure_title,
            font=dict(family="Space Grotesk, Inter, sans-serif", color=theme["text"])
        )
    )
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.08)',
        zerolinecolor='rgba(255,255,255,0.15)',
        linecolor='rgba(255,255,255,0.2)',
        tickfont=dict(color=theme["muted"]),
        title=dict(text=x_title, font=dict(color=theme["muted"]))
    )
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.08)',
        zerolinecolor='rgba(255,255,255,0.15)',
        linecolor='rgba(255,255,255,0.2)',
        tickfont=dict(color=theme["muted"]),
        title=dict(text=y_title, font=dict(color=theme["muted"]))
    )
    return fig

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def get_gsheet_connection():
    """Kết nối tới Google Sheets"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    
    client = gspread.authorize(credentials)
    return client

def load_data_from_gsheet():
    """Đọc dữ liệu từ Google Sheets"""
    try:
        client = get_gsheet_connection()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Ensure required columns (THÊM Secondary Positions VÀO ĐÂY)
        required_cols = [
            "Player", "Rating", "Position", "Position Style", "Player Type",
            "Nation", "Club", "League",
            "Region", "Height", "Weight", "Age", "Foot",
            "Weak Foot Usage", "Weak Foot Accuracy", "Form", "Injury Resistance",
            "Player URL", "Player ID", "Skills", "Added Skills", "Secondary Positions"
        ]
        for col in required_cols:
            if col not in df.columns:
                if col == "Rating":
                    df[col] = 0
                else:
                    df[col] = ""
        
        # Clean data
        df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce').fillna(0).astype(int)
        df = df[df["Rating"] > 0].copy()
        
        # Làm sạch dữ liệu (THÊM Secondary Positions VÀO ĐÂY)
        for col in [
            "Player", "Position", "Position Style", "Player Type",
            "Nation", "Club", "League",
            "Region", "Height", "Weight", "Age", "Foot",
            "Weak Foot Usage", "Weak Foot Accuracy", "Form", "Injury Resistance",
            "Player URL", "Player ID", "Skills", "Added Skills", "Secondary Positions"
        ]:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).replace(['nan', 'None', 'NaN', '<NA>'], '').str.strip()
        
        if "Player Type" in df.columns:
            df["Player Type"] = df["Player Type"].apply(normalize_player_type)
        else:
            df["Player Type"] = 'NON-EPIC'
        
        df["Epic_Priority"] = df["Player Type"].apply(lambda x: 0 if x == "EPIC" else 1)

        # Fix lỗi vị trí
        if 'Position' in df.columns:
            df['Position'] = df['Position'].astype(str).str.upper().str.strip()

        df = calculate_top23_count(df)
        
        return df
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc dữ liệu: {e}")
        return pd.DataFrame()

def save_data_to_gsheet(df):
    """Lưu dữ liệu lên Google Sheets"""
    try:
        # Check if dataframe is empty
        if df.empty:
            st.error("⚠️ Không thể lưu: DataFrame trống!")
            return False
            
        client = get_gsheet_connection()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        
        # Remove Epic_Priority column before saving
        df_save = df.drop(columns=['Epic_Priority'], errors='ignore').copy()
        
        # CRITICAL: Replace NaN/inf values with empty string or 0
        # This prevents JSON error when saving to Google Sheets
        df_save = df_save.fillna('')  # Fill NaN with empty string
        
        # Replace inf values if any
        df_save = df_save.replace([float('inf'), float('-inf')], '')
        
        # Check again after cleaning
        if df_save.empty:
            st.error("⚠️ Không thể lưu: DataFrame trống sau khi xử lý!")
            return False
        
        # Clear and update
        sheet.clear()
        sheet.update([df_save.columns.values.tolist()] + df_save.values.tolist())
        return True
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu dữ liệu: {e}")
        # Don't clear sheet if there's an error!
        return False

# --- SKILLS PRIORITY SYSTEM ---
POSITION_SKILLS_PRIORITY = {
    "CF": [
        "First-time Shot", "Acrobatic Finishing", "Long-Range Curler", 
        "Long Range Shooting", "Outside Curler", "Heading", 
        "Aerial Superiority", "One-touch Pass", "Through Passing",
        "Weighted Pass", "Fighting Spirit", "Cut Behind & Turn",
        "Sole Control", "Heel Trick", "Track Back"
    ],
    "SS": [
        "One-touch Pass", "Through Passing", "First-time Shot",
        "Acrobatic Finishing", "Fighting Spirit", "Outside Curler",
        "Long Range Shooting", "Weighted Pass", "Sole Control",
        "Long-Range Curler", "Cut Behind & Turn", "Double Touch",
        "Pinpoint Crossing", "Heel Trick", "Super Sub"
    ],
    "LWF": [
        "Pinpoint Crossing", "One-touch Pass", "Through Passing",
        "Weighted Pass", "Outside Curler", "Fighting Spirit",
        "Sole Control", "Long-Range Curler", "Long Range Shooting",
        "Cut Behind & Turn", "First-time Shot", "Heel Trick",
        "Double Touch", "Acrobatic Finishing", "Super Sub"
    ],
    "RWF": [
        "Pinpoint Crossing", "One-touch Pass", "Through Passing",
        "Weighted Pass", "Outside Curler", "Fighting Spirit",
        "Sole Control", "Long-Range Curler", "Long Range Shooting",
        "Cut Behind & Turn", "First-time Shot", "Heel Trick",
        "Double Touch", "Acrobatic Finishing", "Super Sub"
    ],
    "AMF": [
        "One-touch Pass", "Through Passing", "Weighted Pass",
        "Long-Range Curler", "Fighting Spirit", "First-time Shot",
        "Long Range Shooting", "Outside Curler", "Pinpoint Crossing",
        "Cut Behind & Turn", "Sole Control", "Heel Trick",
        "Acrobatic Finishing", "Double Touch", "Low Lofted Pass"
    ],
    "CMF": [
        "One-touch Pass", "Through Passing", "Interception",
        "Weighted Pass", "Fighting Spirit", "Track Back",
        "Sole Control", "Cut Behind & Turn", "Pinpoint Crossing","Outside Curler", "Heel Trick", "Low Lofted Pass",
        "Blocker", "Long Range Shooting", "Double Touch"
    ],
    "DMF": [
        "Interception", "Blocker", "One-touch Pass",
        "Through Passing", "Weighted Pass", "Man Marking",
        "Fighting Spirit", "Sole Control", "Aerial Superiority",
        "Sliding Tackle", "Heading", "Low Lofted Pass",
        "Cut Behind & Turn", "Outside Curler", "Acrobatic Clearance"
    ],
    "LMF": [
        "Pinpoint Crossing", "One-touch Pass", "Through Passing",
        "Fighting Spirit", "Cut Behind & Turn", "Weighted Pass",
        "Outside Curler", "Long-Range Curler", "Sole Control",
        "Heel Trick", "Track Back", "Long Range Shooting",
        "First-time Shot", "Acrobatic Finishing", "Double Touch"
    ],
    "RMF": [
        "Pinpoint Crossing", "One-touch Pass", "Through Passing",
        "Fighting Spirit", "Cut Behind & Turn", "Weighted Pass",
        "Outside Curler", "Long-Range Curler", "Sole Control",
        "Heel Trick", "Track Back", "Long Range Shooting",
        "First-time Shot", "Acrobatic Finishing", "Double Touch"
    ],
    "LB": [
        "Track Back", "Blocker", "Interception",
        "Man Marking", "Pinpoint Crossing", "Fighting Spirit",
        "Sliding Tackle", "Acrobatic Clearance", "Aerial Superiority",
        "One-touch Pass", "Through Passing", "Weighted Pass",
        "Outside Curler", "Sole Control", "Low Lofted Pass"
    ],
    "RB": [
        "Track Back", "Blocker", "Interception",
        "Man Marking", "Pinpoint Crossing", "Fighting Spirit",
        "Sliding Tackle", "Acrobatic Clearance", "Aerial Superiority",
        "One-touch Pass", "Through Passing", "Weighted Pass",
        "Outside Curler", "Sole Control", "Low Lofted Pass"
    ],
    "CB": [
        "Interception", "Blocker", "Man Marking",
        "Aerial Superiority", "Heading", "Sliding Tackle",
        "Acrobatic Clearance", "Fighting Spirit", "One-touch Pass",
        "Through Passing", "Weighted Pass", "Low Lofted Pass",
        "Sole Control", "Outside Curler", "Track Back"
    ],
    "GK": [
        "GK Low Punt", "GK High Punt", "GK Long Throw",
        "GK Penalty Saver", "Fighting Spirit", "Low Lofted Pass",
        "One-touch Pass", "Through Passing", "Weighted Pass",
        "Outside Curler", "Sole Control", "Heel Trick",
        "Captaincy"
    ]
}

def normalize_skill_name(skill: str) -> str:
    """Chuẩn hóa tên skill để so sánh - loại bỏ mọi whitespace thừa"""
    normalized = re.sub(r'\s+', ' ', str(skill).strip())
    return normalized.lower()

def normalize_player_type(value: str) -> str:
    """Chuẩn hóa Player Type về POTW / EPIC / NON-EPIC (case-insensitive)."""
    text = str(value).strip().upper()
    if not text:
        return 'NON-EPIC'
    
    canonical_map = {
        'POTW': 'POTW',
        'TRENDING': 'POTW',
        'EPIC': 'EPIC',
        'LEGENDARY': 'EPIC',
        'LEGEND': 'EPIC',
        'NON-EPIC': 'NON-EPIC',
        'NON EPIC': 'NON-EPIC',
        'NON_EPIC': 'NON-EPIC',
    }
    if text in canonical_map:
        return canonical_map[text]
    
    # Ưu tiên nhận diện POTW trước
    if 'TRENDING' in text or 'POTW' in text:
        return 'POTW'
    
    # Sau đó ưu tiên nhận diện các biến thể Non-Epic
    if 'HIGHLIGHT' in text or 'FEATURED' in text or 'STANDARD' in text:
        return 'NON-EPIC'
    if 'NON' in text and 'EPIC' in text:
        return 'NON-EPIC'
    
    if 'LEGENDARY' in text or 'LEGEND' in text:
        return 'EPIC'
    
    if 'EPIC' in text:
        return 'EPIC'
    
    return 'NON-EPIC'

def get_all_skills(base_skills: str, added_skills: str) -> list:
    """Kết hợp skills gốc và skills đã thêm thành một list"""
    all_skills = []
    
    if base_skills and base_skills.strip():
        all_skills.extend([s.strip() for s in base_skills.split(',') if s.strip()])
    
    if added_skills and added_skills.strip():
        all_skills.extend([s.strip() for s in added_skills.split(',') if s.strip()])
    
    return all_skills

def get_recommended_skills(position: str, base_skills: str, added_skills: str, max_total_skills: int = 15) -> list:
    """Trả về danh sách skills được đề xuất cho một vị trí"""
    if position not in POSITION_SKILLS_PRIORITY:
        return []
    
    all_current_skills = get_all_skills(base_skills, added_skills)
    current_skills_normalized = [normalize_skill_name(s) for s in all_current_skills]
    
    current_count = len(all_current_skills)
    remaining_slots = max_total_skills - current_count
    
    if remaining_slots <= 0:
        return []
    
    priority_skills = POSITION_SKILLS_PRIORITY[position]
    missing_skills = [s for s in priority_skills 
                     if normalize_skill_name(s) not in current_skills_normalized]
    
    return missing_skills[:remaining_slots]

def get_player_rank(df, row, group_by, max_size=23):
    """Trả về rank của 1 cầu thủ trong group (Club/Nation/League) theo Top 23."""
    value = row.get(group_by, "")
    if not value:
        return None
    
    group_df = df[df[group_by].astype(str) == str(value)].copy()
    if group_df.empty:
        return None
    
    # Với Nation/League: loại trùng tên, giữ thẻ tốt nhất
    if group_by in ['Nation', 'League']:
        group_df = group_df.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
        group_df = group_df.drop_duplicates(subset=['Player'], keep='first')

    # Xác định các tiêu chí sắp xếp
    sort_keys = ['Rating', 'Epic_Priority']
    sort_asc = [False, True]
    
    # THÊM TIÊU CHÍ ƯU TIÊN MỚI: Top23_Count (chỉ áp dụng cho Nation/League khi bị tie)
    if group_by in ['Nation', 'League'] and 'Top23_Count' in group_df.columns:
        sort_keys.append('Top23_Count')
        sort_asc.append(False) # False = Giảm dần
    
    # Sắp xếp theo các tiêu chí đã định
    group_df = group_df.sort_values(sort_keys, ascending=sort_asc).head(max_size)
    
    # Tìm vị trí của cầu thủ theo index gốc
    try:
        rank = group_df.index.get_loc(row.name) + 1
        return f"{rank}/{len(group_df)} {value}"
    except KeyError:
        return None

@st.cache_data(ttl=0)
def get_all_known_skills():
    """Get all unique skills from POSITION_SKILLS_PRIORITY"""
    all_skills = set()
    for skills_list in POSITION_SKILLS_PRIORITY.values():
        all_skills.update(skills_list)
    return sorted(list(all_skills))

def get_top23_indices(df: pd.DataFrame, group_by: str, max_size: int = 23) -> set:
    """Lấy index của Top 23 cầu thủ cho 1 nhóm (Nation/League/Club) - Logic tương tự build_top23_map nhưng chỉ lấy index."""
    top_indices = set()
    values = [v for v in df[group_by].dropna().astype(str).unique() if v.strip()]
    
    for value in values:
        gdf = df[df[group_by].astype(str) == value].copy()
        if gdf.empty:
            continue
            
        if group_by in ['Nation', 'League']:
            # Loại trùng tên, giữ thẻ tốt nhất
            gdf = gdf.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
            gdf = gdf.drop_duplicates(subset=['Player'], keep='first')
            
        # Sắp xếp cơ bản: Rating, Epic_Priority
        # **Lưu ý: Không dùng Top23_Count ở đây để tránh vòng lặp phụ thuộc**
        gdf = gdf.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(max_size)
        top_indices.update(gdf.index.tolist())
        
    return top_indices

def calculate_top23_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán số lần một cầu thủ thuộc Top 23 Club hoặc League (CHỈ TÍNH TARGET CLUBS/LEAGUES)
    Sử dụng để ưu tiên khi Nation/League Top 23 bị tie.
    """
    if 'Top23_Count' in df.columns:
        df = df.drop(columns=['Top23_Count'])
        
    # 1. Lấy danh sách index của Top 23 cho TẤT CẢ các team (dựa trên Rating)
    raw_club_top_indices = get_top23_indices(df, 'Club')
    raw_league_top_indices = get_top23_indices(df, 'League')
    
    # 2. Tạo cột Count mặc định là 0
    df['Top23_Count'] = 0
    
    # 3. CHỈ cộng điểm nếu:
    #    a) Cầu thủ nằm trong Top 23 của team đó (raw indices)
    #    b) Team đó nằm trong danh sách TARGET (Target list)
    
    # --- Xử lý Club ---
    # Kiểm tra xem Club của cầu thủ có trong TARGET_CLUBS không
    is_target_club = df['Club'].isin(target_clubs)
    # Kiểm tra xem cầu thủ có trong Top 23 Club không
    is_top23_club = df.index.isin(raw_club_top_indices)
    # Cộng 1 nếu thỏa mãn cả hai
    df.loc[is_target_club & is_top23_club, 'Top23_Count'] += 1
    
    # --- Xử lý League ---
    # Kiểm tra xem League của cầu thủ có trong TARGET_LEAGUES không
    is_target_league = df['League'].isin(target_leagues)
    # Kiểm tra xem cầu thủ có trong Top 23 League không
    is_top23_league = df.index.isin(raw_league_top_indices)
    # Cộng 1 nếu thỏa mãn cả hai
    df.loc[is_target_league & is_top23_league, 'Top23_Count'] += 1
    
    return df

# --- SKILL INVENTORY MANAGEMENT (Google Sheets) ---
@st.cache_data(ttl=10)
def get_inventory_from_gsheet():
    """Đọc skill inventory từ Google Sheets"""
    try:
        client = get_gsheet_connection()
        spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
        
        # Tìm hoặc tạo sheet "Skill_Inventory"
        try:
            sheet = spreadsheet.worksheet("Skill_Inventory")
        except:
            # Nếu chưa có sheet, tạo mới
            sheet = spreadsheet.add_worksheet(title="Skill_Inventory", rows=100, cols=2)
            sheet.update([["Skill Name", "Quantity"]])
            return {}
        
        data = sheet.get_all_records()
        
        if not data:
            return {}
        
        # Convert to dict
        inventory = {}
        for row in data:
            skill_name = str(row.get('Skill Name', '')).strip()
            quantity = row.get('Quantity', 0)
            
            if skill_name:
                try:
                    inventory[skill_name] = int(quantity)
                except:
                    inventory[skill_name] = 0
        
        return inventory
        
    except Exception as e:
        st.error(f"❌ Lỗi đọc inventory từ Google Sheets: {e}")
        return {}

def save_skill_inventory_to_gsheet(inventory):
    """Lưu skill inventory lên Google Sheets"""
    try:
        client = get_gsheet_connection()
        spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
        
        # Tìm hoặc tạo sheet
        try:
            sheet = spreadsheet.worksheet("Skill_Inventory")
        except:
            sheet = spreadsheet.add_worksheet(title="Skill_Inventory", rows=100, cols=2)
        
        # Prepare data
        rows = [["Skill Name", "Quantity"]]
        for skill_name, quantity in sorted(inventory.items()):
            if quantity > 0:  # Chỉ lưu skills có số lượng > 0
                rows.append([skill_name, int(quantity)])
        
        # Clear and update
        sheet.clear()
        sheet.update(rows)
        
        # Clear cache để load lại data mới
        st.cache_data.clear()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Lỗi lưu inventory: {e}")
        return False

# --- GK INVENTORY SYSTEM ---
GK_SKILLS_PRIORITY_LIST = [
    "GK Low Punt", "GK High Punt", "GK Long Throw", "GK Penalty Saver", 
    "Fighting Spirit", "Low Lofted Pass", "One-touch Pass", "Through Passing", 
    "Weighted Pass", "Outside Curler", "Sole Control", "Heel Trick", "Captaincy"
]

@st.cache_data(ttl=10)
def get_gk_inventory_from_gsheet():
    """Đọc kho skill GK riêng biệt"""
    try:
        client = get_gsheet_connection()
        spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
        
        try:
            sheet = spreadsheet.worksheet("GK_Inventory")
        except:
            # Nếu chưa có, tạo mới và KHỞI TẠO list skill mặc định = 0
            sheet = spreadsheet.add_worksheet(title="GK_Inventory", rows=50, cols=2)
            # Init data
            rows = [["Skill Name", "Quantity"]]
            for skill in GK_SKILLS_PRIORITY_LIST:
                rows.append([skill, 0])
            sheet.update(rows)
            return {k: 0 for k in GK_SKILLS_PRIORITY_LIST}
        
        data = sheet.get_all_records()
        inventory = {k: 0 for k in GK_SKILLS_PRIORITY_LIST} # Default 0
        
        for row in data:
            skill = str(row.get('Skill Name', '')).strip()
            qty = row.get('Quantity', 0)
            if skill: inventory[skill] = int(qty)
            
        return inventory
    except Exception as e:
        st.error(f"❌ Lỗi GK Inventory: {e}")
        return {}

def save_gk_inventory_to_gsheet(inventory):
    """Lưu kho GK"""
    try:
        client = get_gsheet_connection()
        spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
        try:
            sheet = spreadsheet.worksheet("GK_Inventory")
        except:
            sheet = spreadsheet.add_worksheet(title="GK_Inventory", rows=50, cols=2)
        
        rows = [["Skill Name", "Quantity"]]
        for skill, qty in inventory.items():
            rows.append([skill, int(qty)])
        
        sheet.clear()
        sheet.update(rows)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu GK Inventory: {e}")
        return False

def update_inventory_count(skill_name, delta, is_gk=False):
    """Hàm update thông minh: Tự chọn kho dựa vào is_gk"""
    try:
        if is_gk:
            inventory = get_gk_inventory_from_gsheet()
        else:
            inventory = get_inventory_from_gsheet()
            
        current = inventory.get(skill_name, 0)
        new_count = max(0, current + delta)
        inventory[skill_name] = new_count
        
        if is_gk:
            return save_gk_inventory_to_gsheet(inventory)
        else:
            return save_skill_inventory_to_gsheet(inventory)
    except Exception as e:
        st.error(f"⚠️ Lỗi cập nhật: {e}")
        return False

def get_inventory():
    """Get inventory (with cache)"""
    return get_inventory_from_gsheet()

# --- CONFIG ---
MAX_SQUAD_SIZE = 23

st.set_page_config(
    page_title="Efootball Team Builder",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Position mapping
POSITIONS = {
    "GK": "Goalkeeper",
    "CB": "Defender", "LB": "Defender", "RB": "Defender",
    "DMF": "Midfielder", "CMF": "Midfielder", "AMF": "Midfielder", 
    "LMF": "Midfielder", "RMF": "Midfielder",
    "LWF": "Forward", "RWF": "Forward", "SS": "Forward", "CF": "Forward"
}

POSITION_STYLES = ["Goalkeeper", "Defender", "Midfielder", "Forward"]

# Sort orders
POSITION_ORDER = {
    "GK": 1, "CB": 2, "LB": 3, "RB": 4,
    "DMF": 5, "CMF": 6, "AMF": 7, "LMF": 8, "RMF": 9,
    "LWF": 10, "RWF": 11, "SS": 12, "CF": 13
}

POSITION_STYLE_ORDER = {
    "Forward": 1,
    "Midfielder": 2,
    "Defender": 3,
    "Goalkeeper": 4,
}

# ==========================================
# 1. DANH SÁCH SƠ ĐỒ (LOGIC CHỌN NGƯỜI)
# ==========================================
FORMATIONS = {
    # 4 Hậu vệ
    "4-2-1-3 (Standard)":   ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "AMF", "LWF", "RWF", "CF"],
    "4-3-3 (Holding)":      ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "LWF", "RWF", "CF"],
    "4-3-3 (Attack)":       ["GK", "LB", "CB", "CB", "RB", "DMF", "AMF", "AMF", "LWF", "RWF", "CF"],
    "4-3-3 (False 9)":      ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "LWF", "RWF", "SS"],
    "4-2-3-1 (Wide)":       ["GK", "LB", "CB", "CB", "RB", "DMF", "DMF", "AMF", "LMF", "RMF", "CF"],
    "4-2-3-1 (Control)":    ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "AMF", "LWF", "RWF", "CF"],
    "4-2-3-1 (Flat)":       ["GK", "LB", "CB", "CB", "RB", "CMF", "CMF", "AMF", "LMF", "RMF", "CF"],
    "4-4-2 (Flat)":         ["GK", "LB", "CB", "CB", "RB", "LMF", "RMF", "CMF", "CMF", "CF", "CF"],
    "4-2-4 (Pressing)":     ["GK", "LB", "CB", "CB", "RB", "CMF", "CMF", "LWF", "RWF", "CF", "CF"],
    "4-2-4 (Pressing-Defensive)":     ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "LWF", "RWF", "CF", "CF"],
    "4-2-2-2 (Magic Box)":  ["GK", "LB", "CB", "CB", "RB", "DMF", "DMF", "AMF", "AMF", "CF", "CF"],
    "4-3-1-2 (Diamond)":    ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "AMF", "CF", "CF"],
    "4-1-2-3 (2 CF, 1 SS)": ["GK", "LB", "CB", "CB", "RB", "DMF", "AMF", "AMF", "SS", "CF", "CF"],
    "4-3-2-1 (Xmas Tree)":  ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "AMF", "AMF", "CF"],
    "4-1-4-1 (Solid Mid)":  ["GK", "LB", "CB", "CB", "RB", "DMF", "LMF", "RMF", "CMF", "CMF", "CF"],

    # 3 Hậu vệ
    "3-5-2 (Possession)":   ["GK", "CB", "CB", "CB", "LMF", "RMF", "DMF", "CMF", "AMF", "CF", "CF"],
    "3-4-3 (Standard)":     ["GK", "CB", "CB", "CB", "LMF", "RMF", "CMF", "CMF", "LWF", "RWF", "CF"],
    "3-4-3 (Defensive)":     ["GK", "CB", "CB", "CB", "LMF", "RMF", "DMF", "DMF", "LWF", "RWF", "CF"],
    "3-4-3 (Pressing)":     ["GK", "CB", "CB", "CB", "LMF", "RMF", "DMF", "CMF", "LWF", "RWF", "CF"],
    "3-4-1-2 (Classic)":    ["GK", "CB", "CB", "CB", "LMF", "RMF", "CMF", "CMF", "AMF", "CF", "CF"],
    "3-2-4-1 (Box Mid)":    ["GK", "CB", "CB", "CB", "DMF", "DMF", "AMF", "AMF", "LMF", "RMF", "CF"],
    "3-4-2-1 (Xabi Ball)":  ["GK", "CB", "CB", "CB", "LMF", "RMF", "CMF", "CMF", "AMF", "AMF", "CF"],

    # 5 Hậu vệ
    "5-4-1 (Low Block)":    ["GK", "LB", "CB", "CB", "CB", "RB", "LMF", "RMF", "DMF", "CMF", "CF"],
    "5-2-3 (Counter)":      ["GK", "LB", "CB", "CB", "CB", "RB", "DMF", "DMF", "LWF", "RWF", "CF"],
    "5-3-2 (Solid)":        ["GK", "LB", "CB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "CF", "CF"],
}

# ==========================================
# 2. TỌA ĐỘ HIỂN THỊ (PIXEL PERFECT) - ĐÃ CẬP NHẬT
# ==========================================
# Cấu trúc: (Top%, Left%)
# Top: Càng lớn càng gần đáy (Hậu vệ), Càng nhỏ càng gần đỉnh (Tiền đạo)
# Left: 0 (Trái) -> 50 (Giữa) -> 100 (Phải)

FORMATION_COORDS = {
    # --- 4 HẬU VỆ ---
    "4-2-1-3 (Standard)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), 
        (65, 40), (65, 60), # DMF & CMF ngang hàng nhau (Top 65)
        (45, 50),           # AMF chính giữa
        (25, 15), (25, 85), (15, 50)
    ],
    "4-3-3 (Holding)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (68, 50), (50, 30), (50, 70), (25, 15), (25, 85), (15, 50)
    ],
    "4-3-3 (Attack)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (68, 50), (40, 30), (40, 70), (25, 15), (25, 85), (15, 50)
    ],
    "4-3-3 (False 9)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (68, 50), (50, 30), (50, 70), (20, 15), (20, 85), (28, 50)
    ],
    "4-2-3-1 (Wide)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (65, 40), (65, 60), (45, 50), (35, 12), (35, 88), (15, 50)
    ],
    "4-2-3-1 (Control)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), 
        (65, 40), (65, 60), # Update: DMF (40) và CMF (60) ngang hàng nhau tại Top 65
        (45, 50),           # Update: AMF chính giữa
        (25, 20), (25, 80), (15, 50)
    ],
    "4-2-3-1 (Flat)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (60, 40), (60, 60), (45, 50), (35, 12), (35, 88), (15, 50)
    ],
    "4-4-2 (Flat)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (45, 10), (45, 90), (55, 35), (55, 65), (15, 35), (15, 65)
    ],
    "4-2-4 (Pressing)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (55, 35), (55, 65), (25, 10), (25, 90), (15, 35), (15, 65)
    ],
    "4-2-4 (Pressing-Defensive)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (55, 35), (55, 65), (25, 10), (25, 90), (15, 35), (15, 65)
    ],

    "4-2-2-2 (Magic Box)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (65, 35), (65, 65), (40, 25), (40, 75), (15, 35), (15, 65)
    ],
    "4-3-1-2 (Diamond)": [
        (92, 50), (78, 15), (82, 38), (82, 62), (78, 85), (68, 50), (50, 30), (50, 70), (35, 50), (15, 35), (15, 65)
    ],
    "4-1-2-3 (2 CF, 1 SS)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (65, 50), (40, 30), (40, 70), (25, 50), (15, 30), (15, 70)
    ],
    "4-3-2-1 (Xmas Tree)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (65, 50), (55, 30), (55, 70), (35, 35), (35, 65), (15, 50)
    ],
    "4-1-4-1 (Solid Mid)": [
        (92, 50), (78, 10), (82, 35), (82, 65), (78, 90), (68, 50), (45, 10), (45, 90), (50, 35), (50, 65), (15, 50)
    ],

    # --- 3 HẬU VỆ ---
    "3-5-2 (Possession)": [
        (92, 50), (80, 25), (82, 50), (80, 75), # GK, CBs
        (50, 8), (50, 92),                      # LMF, RMF
        (60, 40), (60, 60),                     # Update: DMF & CMF ngang hàng (Top 60), cân đối 2 bên
        (40, 50),                               # Update: AMF chính giữa (Top 40, Left 50)
        (15, 35), (15, 65)                      # CFs
    ],
    "3-4-3 (Standard)": [
        (92, 50), (80, 25), (82, 50), (80, 75), (50, 10), (50, 90), (60, 35), (60, 65), (25, 20), (25, 80), (15, 50)
    ],
    "3-4-3 (Pressing)": [
        (92, 50), (80, 25), (82, 50), (80, 75), (50, 10), (50, 90), (60, 35), (60, 65), (25, 20), (25, 80), (15, 50)
    ],
    "3-4-3 (Defensive)": [
        (92, 50), (80, 25), (82, 50), (80, 75), (50, 10), (50, 90), (60, 35), (60, 65), (25, 20), (25, 80), (15, 50)
    ],
    "3-4-1-2 (Classic)": [
        (92, 50), (80, 25), (82, 50), (80, 75), (50, 10), (50, 90), (60, 35), (60, 65), (40, 50), (15, 35), (15, 65)
    ],
    "3-2-4-1 (Box Mid)": [
        (92, 50), (80, 25), (82, 50), (80, 75), (65, 35), (65, 65), (35, 35), (35, 65), (40, 10), (40, 90), (15, 50)
    ],
    "3-4-2-1 (Xabi Ball)": [
        (92, 50), (80, 25), (82, 50), (80, 75), (50, 8), (50, 92), (65, 35), (65, 65), (30, 30), (30, 70), (15, 50)
    ],

    # --- 5 HẬU VỆ ---
    "5-4-1 (Low Block)": [
        (92, 50), (75, 10), (82, 28), (85, 50), (82, 72), (75, 90), (50, 10), (50, 90), (65, 50), (60, 40), (15, 50)
    ],
    "5-2-3 (Counter)": [
        (92, 50), (75, 10), (82, 28), (85, 50), (82, 72), (75, 90), (60, 35), (60, 65), (25, 15), (25, 85), (15, 50)
    ],
    "5-3-2 (Solid)": [
        (92, 50), (75, 10), (82, 28), (85, 50), (82, 72), (75, 90), (65, 50), (55, 30), (55, 70), (15, 35), (15, 65)
    ],
}

# ==========================================
# CẬP NHẬT LOGIC AUTO BUILD (BƯỚC 1)
# ==========================================

# 2. Hàm xử lý logic chọn cầu thủ (Đã nâng cấp)
# ==========================================
# CẬP NHẬT LOGIC: BEST XI + 12 SUBS (BƯỚC 1)
# ==========================================

# ==========================================
# CẬP NHẬT LOGIC: AUTO BUILD (FIX LỖI BMI/HEIGHT/WEIGHT)
# ==========================================

def auto_build_squad(df, formation_name, sort_mode='rating_desc', filter_col=None, filter_val=None):
    """
    Tự động xây dựng đội hình tối ưu.
    CẬP NHẬT: 
    1. Luật Anti-Spam CB ĐỘNG: 
       - Sơ đồ 2 CB đá chính -> Max 2 CB dự bị.
       - Sơ đồ 3 CB đá chính (3HV/5HV) -> Max 3 CB dự bị.
    2. Luật Strict Fit: Dự bị bắt buộc phải đá được 1 trong các vị trí của sơ đồ.
    """
    # 1. CHUẨN HÓA DỮ LIỆU
    pool_df = df.copy()
    
    def clean_and_to_num(val):
        if pd.isna(val) or str(val).strip() == "": return 0.0
        cleaned = re.sub(r'[^\d.]', '', str(val).replace(',', '.'))
        try: return float(cleaned)
        except ValueError: return 0.0

    if 'Height' in pool_df.columns: pool_df['Height_num'] = pool_df['Height'].apply(clean_and_to_num)
    else: pool_df['Height_num'] = 0.0
        
    if 'Weight' in pool_df.columns: pool_df['Weight_num'] = pool_df['Weight'].apply(clean_and_to_num)
    else: pool_df['Weight_num'] = 0.0
        
    if 'Age' in pool_df.columns: pool_df['Age_num'] = pool_df['Age'].apply(clean_and_to_num)
    else: pool_df['Age_num'] = 99.0
    
    if 'Secondary Positions' not in pool_df.columns: pool_df['Secondary Positions'] = ""
    else: pool_df['Secondary Positions'] = pool_df['Secondary Positions'].fillna("").astype(str).str.upper().str.strip()

    # 2. LỌC DỮ LIỆU
    if filter_col and filter_val and filter_val != "(Tất cả)":
        pool_df = pool_df[pool_df[filter_col].astype(str) == filter_val]
    if pool_df.empty: return []

    # Sắp xếp sơ bộ
    pool_df = pool_df.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
    pool_df = pool_df.drop_duplicates(subset=['Player'], keep='first')
    pool_df = pool_df.reset_index(drop=True)

    # --- LOGIC MỚI CHO UNITED NATIONS ---
    if sort_mode == 'united_nations':
        pool_df = pool_df.sort_values('Rating', ascending=False)
        gks = pool_df[pool_df['Position'] == 'GK']
        others = pool_df[pool_df['Position'] != 'GK']
        top_gks = gks.drop_duplicates(subset=['Nation'], keep='first').head(3)
        gk_nations = set(top_gks['Nation'].unique())
        others_filtered = others[~others['Nation'].isin(gk_nations)]
        others_unique = others_filtered.drop_duplicates(subset=['Nation'], keep='first')
        pool_df = pd.concat([top_gks, others_unique]).reset_index(drop=True)

    # 3. HỆ THỐNG TÍNH ĐIỂM (SCORING)
    ERROR_SCORE = -999999

    def calculate_score(row):
        rating_bonus = row['Rating'] / 100000.0 
        
        if sort_mode == 'rating_desc': 
            return row['Rating'] + (0.1 if row.get('Epic_Priority', 0) == 1 else 0)
        elif sort_mode == 'height_desc': return row['Height_num'] + rating_bonus
        elif sort_mode == 'height_asc': return (250 - row['Height_num']) + rating_bonus 
        elif sort_mode == 'weight_desc': return row['Weight_num'] + rating_bonus
        elif sort_mode == 'weight_asc': return (150 - row['Weight_num']) + rating_bonus
        elif sort_mode == 'age_desc': return row['Age_num'] + rating_bonus
        elif sort_mode == 'age_asc': return (100 - row['Age_num']) + rating_bonus
        elif 'bmi' in sort_mode:
            h_m = row['Height_num'] / 100.0; w = row['Weight_num']
            if h_m < 1.0 or w < 30: return ERROR_SCORE
            bmi = w / (h_m ** 2)
            if sort_mode == 'bmi_desc': return (bmi * 1000) + rating_bonus
            else: return ((100 - bmi) * 1000) + rating_bonus
        elif sort_mode == 'ambidextrous':
            def get_wf_val(text):
                t = str(text).strip().lower()
                if any(k in t for k in ['regularly', 'very high', '4']): return 4
                if any(k in t for k in ['occasionally', 'high', '3']): return 3
                if any(k in t for k in ['medium', 'rarely', '2']): return 2
                return 1
            u_val = get_wf_val(row.get('Weak Foot Usage', ''))
            a_val = get_wf_val(row.get('Weak Foot Accuracy', ''))
            tier_score = 0
            if a_val == 4 and u_val == 4: tier_score = 50000
            elif a_val == 4: tier_score = 40000
            elif a_val == 3: tier_score = 30000
            elif a_val == 2: tier_score = 20000
            sub_tier_bonus = u_val * 100
            return row['Rating'] + tier_score + sub_tier_bonus
        elif sort_mode == 'potw_only':
            ptype = str(row.get('Player Type', '')).upper()
            is_potw = 'POTW' in ptype or 'TRENDING' in ptype
            return (10000 if is_potw else 0) + row['Rating']
        return row['Rating']

    pool_df['Build_Score'] = pool_df.apply(calculate_score, axis=1)
    pool_df = pool_df.reset_index(drop=True)

    # 4. CHỌN ĐÁ CHÍNH (STARTERS)
    required_positions = FORMATIONS.get(formation_name, [])
    unique_formation_positions = set(required_positions)
    
    num_slots = len(required_positions)
    num_players = len(pool_df)
    BIG_PENALTY = 1e9 
    cost_matrix = np.full((num_players, num_slots), BIG_PENALTY)

    for p_idx, row in pool_df.iterrows():
        p_main_pos = str(row['Position']).strip().upper()
        p_sec_pos_list = [s.strip() for s in str(row['Secondary Positions']).split(',') if s.strip()]
        full_pos_list = [p_main_pos] + p_sec_pos_list
        score = row['Build_Score']
        if score == ERROR_SCORE: continue

        for s_idx, req_pos in enumerate(required_positions):
            can_play = req_pos in full_pos_list
            if can_play: 
                main_pos_bonus = 0.0001 if req_pos == p_main_pos else 0
                cost_matrix[p_idx, s_idx] = -(score + main_pos_bonus)

    try: row_ind, col_ind = linear_sum_assignment(cost_matrix)
    except: return []

    final_squad = [None] * 11
    used_indices = set()
    used_nations = set()

    for i in range(len(row_ind)):
        p_idx = row_ind[i]; s_idx = col_ind[i]
        if cost_matrix[p_idx, s_idx] < (BIG_PENALTY / 2):
            row = pool_df.iloc[p_idx]
            pid = str(row.get('Player ID', '')).strip()
            purl = str(row.get('Player URL', '')).strip()
            if not pid and purl:
                m = re.search(r"(\d{14,})", purl); pid = m.group(1) if m else ""
            img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else None

            final_squad[s_idx] = {
                "Is_Starter": True, "Position": required_positions[s_idx],
                "Real_Position": row['Position'], "Player": row['Player'],
                "Rating": row['Rating'], "Type": row['Player Type'], "Image": img_url,
                "Height": row.get('Height', ''), "Weight": row.get('Weight', ''),
                "Age": row.get('Age', ''), "Score": row['Build_Score'], "Data": row.to_dict()
            }
            used_indices.add(p_idx)

    for i in range(11):
        if final_squad[i] is None: final_squad[i] = {"Is_Starter": True, "Position": required_positions[i], "Player": "---", "Rating": 0, "Type": "N/A", "Score": -9999, "Image": None}

    # ==========================================================
    # 5. CHỌN DỰ BỊ (DRAFTING) - CÓ CẬP NHẬT LOGIC CB ĐỘNG
    # ==========================================================
    remaining_pool = pool_df[~pool_df.index.isin(used_indices)].copy()
    remaining_pool = remaining_pool[remaining_pool['Build_Score'] != ERROR_SCORE]
    
    bench_picks = []
    bench_pos_counts = {} 
    gk_on_bench_count = 0
    MAX_BENCH = 12

    # --- [NEW] TÍNH GIỚI HẠN CB DỰ BỊ DỰA TRÊN SƠ ĐỒ ĐÁ CHÍNH ---
    # Đếm số lượng 'CB' trong required_positions
    num_starting_cbs = required_positions.count('CB')
    
    # Nếu đá chính >= 3 CB (Sơ đồ 3HV hoặc 5HV) -> Max 3 dự bị
    # Nếu đá chính < 3 CB (Sơ đồ 4HV) -> Max 2 dự bị
    max_cb_subs_allowed = 3 if num_starting_cbs >= 3 else 2
    # -----------------------------------------------------------

    for _ in range(MAX_BENCH):
        if remaining_pool.empty:
            break
            
        def calculate_draft_priority(row):
            base_score = row['Build_Score']
            pos = str(row.get('Position', '')).strip().upper()
            
            # --- 1. STRICT FORMATION FIT ---
            secs = [s.strip().upper() for s in str(row.get('Secondary Positions', '')).split(',') if s.strip()]
            all_playable_pos = set([pos] + secs)
            if not all_playable_pos.intersection(unique_formation_positions):
                return -999999

            # --- 2. ANTI-SPAM CB (DYNAMIC LIMIT) ---
            if pos == 'GK' and gk_on_bench_count >= 1:
                return -999999
            
            if sort_mode in ['height_desc', 'weight_desc'] and pos == 'CB':
                cb_count = bench_pos_counts.get('CB', 0)
                
                # SỬ DỤNG BIẾN ĐỘNG max_cb_subs_allowed THAY VÌ SỐ CỨNG 3
                if cb_count >= max_cb_subs_allowed:
                    useful_positions = ['LB', 'RB', 'DMF', 'CMF', 'LWF', 'RWF', 'SS', 'CF', 'AMF', 'LMF', 'RMF']
                    is_versatile = any(p in str(row.get('Secondary Positions', '')).upper() for p in useful_positions)
                    
                    if not is_versatile:
                        return -999999 
            
            # --- 3. LUẬT UNITED NATIONS ---
            if sort_mode == 'united_nations':
                p_nation = str(row.get('Nation', '')).strip()
                if p_nation and p_nation in used_nations:
                    return -999999
            
            # --- 4. BONUS ---
            fit_bonus = 0
            if pos in unique_formation_positions:
                fit_bonus = 0.2
            
            current_count_on_bench = bench_pos_counts.get(pos, 0)
            saturation_penalty = current_count_on_bench * 0.1
            
            return base_score + fit_bonus - saturation_penalty

        remaining_pool['Draft_Score'] = remaining_pool.apply(calculate_draft_priority, axis=1)
        
        candidates = remaining_pool[remaining_pool['Draft_Score'] > -500000]
        
        if candidates.empty:
            break
            
        candidates = candidates.sort_values(['Draft_Score', 'Rating'], ascending=[False, False])
        best_pick = candidates.iloc[0]
        
        bench_picks.append(best_pick)
        
        picked_pos = str(best_pick['Position']).strip().upper()
        bench_pos_counts[picked_pos] = bench_pos_counts.get(picked_pos, 0) + 1
        
        if picked_pos == 'GK':
            gk_on_bench_count += 1
        if sort_mode == 'united_nations':
            used_nations.add(str(best_pick.get('Nation', '')).strip())
            
        remaining_pool = remaining_pool.drop(best_pick.name)

    while len(bench_picks) < 12 and not remaining_pool.empty:
        top = remaining_pool.iloc[0]
        bench_picks.append(top)
        remaining_pool = remaining_pool.iloc[1:]

    for row in bench_picks:
        r_get = row.get if isinstance(row, dict) else row.get
        pid = str(r_get('Player ID', '')).strip()
        purl = str(r_get('Player URL', '')).strip()
        if not pid and purl: m = re.search(r"(\d{14,})", purl); pid = m.group(1) if m else ""
        img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else None
        
        final_squad.append({
            "Is_Starter": False, "Position": r_get('Position'), "Player": r_get('Player'),
            "Rating": r_get('Rating'), "Type": r_get('Player Type'), "Image": img_url,
            "Height": r_get('Height', ''), "Weight": r_get('Weight', ''), "Age": r_get('Age', ''),
            "Score": r_get('Build_Score'), "Data": row.to_dict() if hasattr(row, 'to_dict') else row
        })
        
    return final_squad

def find_best_formation_for_team(df, sort_mode, filter_col, filter_val):
    """
    Tìm sơ đồ tối ưu với logic phân cấp (Tier-based Logic):
    1. Ưu tiên TUYỆT ĐỐI cho sự đầy đủ đội hình (Đủ người > Thiếu 1 > Thiếu 2...).
    2. Nếu cùng số lượng người thiếu: So sánh tổng điểm Score.
    3. Nếu cùng điểm Score: So sánh số lượng cầu thủ đá đúng vị trí sở trường.
    """
    best_score = -float('inf')
    best_main_pos_count = -1 
    best_squad = []
    best_formation_name = ""

    # Hằng số phạt cho mỗi vị trí thiếu (Đủ lớn để tách biệt các trường hợp)
    # Ví dụ: Thiếu 1 người bị trừ 1 tỷ điểm. Thiếu 2 người bị trừ 2 tỷ điểm.
    MISSING_PENALTY = 1_000_000_000 

    # Quét qua toàn bộ sơ đồ
    for form_name in FORMATIONS.keys():
        # Build thử đội hình
        squad = auto_build_squad(df, form_name, sort_mode, filter_col, filter_val)
        
        # Lấy danh sách đá chính
        starters = [p for p in squad if p.get('Is_Starter', False)]
        
        # Lọc ra những người CÓ MẶT (không phải placeholder "---")
        valid_starters = [p for p in starters if p['Player'] != "---"]
        
        # Đếm số người thiếu
        missing_count = 11 - len(valid_starters)
        
        # Tính tổng điểm của những người ĐANG CÓ
        current_rating_score = sum(p.get('Score', 0) for p in valid_starters)
        
        # --- TÍNH ĐIỂM TỔNG HỢP (QUAN TRỌNG) ---
        if missing_count == 0:
            # Trường hợp ĐỦ NGƯỜI: Điểm dương bình thường
            current_total_score = current_rating_score
            
            # Bonus đặc biệt cho Rating mode (Ưu tiên DMF) chỉ áp dụng khi đủ người
            if sort_mode == 'rating_desc':
                has_dmf = any(p['Position'] == 'DMF' for p in valid_starters)
                needs_dmf = "DMF" in FORMATIONS[form_name]
                if has_dmf: current_total_score += 50000 
                elif needs_dmf: current_total_score -= 20000
        else:
            # Trường hợp THIẾU NGƯỜI: 
            # Điểm = (Điểm của cầu thủ có sẵn) - (Số người thiếu * 1 Tỷ)
            # Ví dụ: Rating 1000. Thiếu 1 -> Score = -999,999,000
            #        Rating 1200. Thiếu 2 -> Score = -1,999,998,800
            # => Thiếu 1 luôn luôn lớn hơn Thiếu 2.
            current_total_score = current_rating_score - (missing_count * MISSING_PENALTY)

        # --- TÍNH TOÁN POSITION FIDELITY (Số cầu thủ đá đúng Main Position) ---
        current_main_pos_count = 0
        for p in valid_starters:
            assigned_pos = str(p.get('Position', '')).strip().upper()
            real_pos = str(p.get('Real_Position', '')).strip().upper()
            if assigned_pos == real_pos:
                current_main_pos_count += 1

        # --- LOGIC SO SÁNH ---
        # 1. Nếu điểm số mới VƯỢT TRỘI (lớn hơn rõ rệt)
        # (Điều này sẽ tự động chọn đội hình thiếu ít người nhất)
        if current_total_score > best_score + 0.01:
            best_score = current_total_score
            best_main_pos_count = current_main_pos_count
            best_squad = squad
            best_formation_name = form_name
            
        # 2. Nếu điểm số NGANG BẰNG (VD: Cùng thiếu 1 người, cùng tổng rating)
        elif abs(current_total_score - best_score) <= 0.01:
            # Ưu tiên đội hình có nhiều người đá đúng sở trường hơn
            if current_main_pos_count > best_main_pos_count:
                best_score = current_total_score
                best_main_pos_count = current_main_pos_count
                best_squad = squad
                best_formation_name = form_name
            
    return best_formation_name, best_squad

def render_pitch_view(squad_list, formation_name="", sort_mode='rating_desc'):
    """
    Vẽ sơ đồ sân bóng: SỬ DỤNG TỌA ĐỘ CỐ ĐỊNH.
    FIX: Fallback an toàn về 4-4-2 nếu không tìm thấy tọa độ, tránh vỡ hình.
    """
    import streamlit.components.v1 as components
    import re
    import math

    # --- 1. XỬ LÝ SORT MODE ---
    highlight_type = None
    is_reverse = True 
    if 'height' in sort_mode: highlight_type = 'Height'; is_reverse = 'asc' not in sort_mode
    elif 'weight' in sort_mode: highlight_type = 'Weight'; is_reverse = 'asc' not in sort_mode
    elif 'age' in sort_mode: highlight_type = 'Age'; is_reverse = 'asc' not in sort_mode
    elif 'bmi' in sort_mode: highlight_type = 'BMI'; is_reverse = 'asc' not in sort_mode
    elif 'potw' in sort_mode: highlight_type = 'Type'
    elif 'ambidextrous' in sort_mode: highlight_type = 'Ambidextrous'
    elif 'united_nations' in sort_mode: highlight_type = 'Nation'

    # --- 2. TÁCH ĐÁ CHÍNH & DỰ BỊ ---
    starters = squad_list[:11]
    raw_subs = squad_list[11:]

    # --- 3. SORT DỰ BỊ ---
    def get_sort_value(p, key):
        try: return float(re.sub(r'[^\d.]', '', str(p.get(key, '0'))))
        except: return 0

    if highlight_type == 'Height': subs = sorted(raw_subs, key=lambda x: get_sort_value(x, 'Height'), reverse=is_reverse)
    elif highlight_type == 'Weight': subs = sorted(raw_subs, key=lambda x: get_sort_value(x, 'Weight'), reverse=is_reverse)
    elif highlight_type == 'Age': subs = sorted(raw_subs, key=lambda x: get_sort_value(x, 'Age'), reverse=is_reverse)
    elif highlight_type == 'BMI':
        def get_bmi(p):
            h = get_sort_value(p, 'Height') / 100.0; w = get_sort_value(p, 'Weight')
            return w / (h**2) if h > 0 else 0
        subs = sorted(raw_subs, key=get_bmi, reverse=is_reverse)
    elif highlight_type == 'Ambidextrous': subs = sorted(raw_subs, key=lambda x: x.get('Score', 0), reverse=True)
    else: subs = sorted(raw_subs, key=lambda x: x.get('Rating', 0), reverse=True)

    # --- 4. HTML GENERATOR ---
    def create_card_html(p, top=None, left=None, is_sub=False):
        full_name = p['Player'].strip()
        name_parts = full_name.split()
        display_name = name_parts[-1].upper() if len(name_parts) > 1 else full_name.upper()
        if len(display_name) > 9: display_name = display_name[:8] + "."

        rating = p['Rating']
        pos = p['Position']
        img = p['Image'] if p['Image'] else "https://pesdb.net/assets/img/card/f0.png"
        
        # Logic Stat Tag
        val_display = ""
        metric_label = ""
        if highlight_type == 'Height': val_display = f"{p.get('Height', '-')} cm"
        elif highlight_type == 'Weight': val_display = f"{p.get('Weight', '-')} kg"
        elif highlight_type == 'Age': val_display = f"{p.get('Age', '-')} tuổi"
        elif highlight_type == 'BMI':
            try:
                h = float(re.sub(r'[^\d.]', '', str(p.get('Height', '0')))) / 100.0
                w = float(re.sub(r'[^\d.]', '', str(p.get('Weight', '0'))))
                if h > 0: val_display = f"{(w/(h**2)):.1f}"; metric_label = "BMI"
            except: pass
        elif highlight_type == 'Ambidextrous':
            d = p.get('Data', {})
            # --- CẬP NHẬT LOGIC HIỂN THỊ TRÊN THẺ ---
            def get_wf_num(text): 
                t = str(text).strip().lower()
                if any(k in t for k in ['very high', 'regularly', '4']): return '4'
                if any(k in t for k in ['high', 'occasionally', '3']): return '3'
                if any(k in t for k in ['medium', 'rarely', '2']): return '2'
                return '1'

            u = get_wf_num(d.get('Weak Foot Usage', ''))
            a = get_wf_num(d.get('Weak Foot Accuracy', ''))
            val_display = f"🦶{u} | 🎯{a}"
        elif highlight_type == 'Nation': val_display = str(p.get('Data', {}).get('Nation', ''))[:3].upper()

        ptype = str(p['Type']).upper()
        if "POTW" in ptype or "TRENDING" in ptype: accent, shadow, stat_color = "#d946ef", "rgba(217, 70, 239, 0.4)", "#e879f9"
        elif "EPIC" in ptype and "NON" not in ptype: accent, shadow, stat_color = "#fbbf24", "rgba(251, 191, 36, 0.4)", "#fbbf24"
        else: accent, shadow, stat_color = "#38bdf8", "rgba(56, 189, 248, 0.4)", "#38bdf8"

        if is_sub:
            position_css = ""
            card_class = "card-sub"
        else:
            z_idx = int(top) if top else 10
            position_css = f"top: {top}%; left: {left}%; transform: translate(-50%, -50%); z-index: {z_idx};"
            card_class = "card-pitch"

        badge_html = ""
        if val_display:
            label_html = f"<span style='color:#94a3b8; margin-right:3px; font-weight:500'>{metric_label}:</span>" if metric_label else ""
            badge_html = f'<div style="position:absolute; bottom:24px; left:50%; transform:translateX(-50%); background:rgba(15,23,42,0.95); color:{stat_color}; font-size:9px; font-weight:700; padding:1px 8px; border-radius:10px; border:1px solid rgba(255,255,255,0.2); z-index:20; white-space:nowrap; display:flex; align-items:center; box-shadow:0 2px 4px rgba(0,0,0,0.5);">{label_html}<span>{val_display}</span></div>'

        if p['Player'] == "---": return f'<div class="empty-slot {card_class}" style="{position_css}"></div>'

        return f"""
        <div class="p-card {card_class}" style="{position_css}; --accent: {accent}; --shadow: {shadow};">
            {badge_html}
            <div class="p-bg"></div>
            <div class="p-header"><span class="p-pos">{pos}</span><span class="p-rating" style="color: {accent}">{rating}</span></div>
            <div class="p-img-box"><img src="{img}" loading="lazy" onerror="this.src='https://pesdb.net/assets/img/card/f0.png'"></div>
            <div class="p-name">{display_name}</div>
        </div>
        """

    # =========================================================================
    # 🔥 LOGIC SẮP XẾP VỊ TRÍ - FIX LỖI TỌA ĐỘ
    # =========================================================================
    html_starters = ""
    
    # Lấy tọa độ từ mapping
    coords = FORMATION_COORDS.get(formation_name)

    # 🛑 SAFE FALLBACK: Nếu không tìm thấy tọa độ, dùng tạm sơ đồ 4-4-2 chuẩn để không bị vỡ hình
    if not coords or len(coords) != 11:
        # Default 4-4-2 Flat coords
        coords = [
            (92, 50), # GK
            (78, 10), (82, 35), (82, 65), (78, 90), # LB-CB-CB-RB
            (45, 10), (45, 90), # LMF-RMF
            (55, 35), (55, 65), # CMF-CMF
            (15, 35), (15, 65)  # CF-CF
        ]

    # Render với tọa độ cứng (đảm bảo đẹp)
    for i, p in enumerate(starters):
        if i < 11:
            t, l = coords[i]
            html_starters += create_card_html(p, t, l)

    # =========================================================================

    html_subs = "".join([create_card_html(p, is_sub=True) for p in subs])
    rows_desktop = math.ceil(len(subs) / 8)
    final_iframe_height = 800 + 60 + (rows_desktop * 130)

    # CSS (Đã tinh chỉnh kích thước thẻ)
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@700;800&family=Inter:wght@600;700&display=swap');
        :root { --bg-dark: #0f172a; --bg-panel: #1e293b; --pitch-line: rgba(148, 163, 184, 0.15); }
        body { margin: 0; background: transparent; font-family: 'Inter', sans-serif; overflow: hidden; }
        .container { display: flex; flex-direction: column; gap: 10px; width: 100%; margin: 0 auto; }
        /* Sân bóng đẹp hơn */
        .pitch { position: relative; width: 100%; height: 720px; background: radial-gradient(circle at 50% 50%, #172554 0%, #020617 90%); border-radius: 12px; border: 2px solid rgba(255,255,255,0.1); box-shadow: 0 20px 50px rgba(0,0,0,0.6); overflow: hidden; perspective: 1000px; }
        .pitch::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: linear-gradient(var(--pitch-line) 1px, transparent 1px), linear-gradient(90deg, var(--pitch-line) 1px, transparent 1px); background-size: 50px 50px; opacity: 0.4; transform: perspective(600px) rotateX(25deg) scale(1.1); pointer-events: none; }
        .lines { position: absolute; width: 100%; height: 100%; top: 0; left: 0; pointer-events: none; }
        .center-circle { position: absolute; top: 50%; left: 50%; width: 130px; height: 130px; border: 2px solid rgba(255,255,255,0.2); border-radius: 50%; transform: translate(-50%, -50%); }
        .half-line { position: absolute; top: 50%; left: 0; width: 100%; height: 0; border-top: 2px solid rgba(255,255,255,0.2); }
        .box-top { position: absolute; top: -2px; left: 50%; width: 50%; height: 14%; transform: translateX(-50%); border: 2px solid rgba(255,255,255,0.2); border-top: none; background: rgba(255,255,255,0.02); }
        .box-bot { position: absolute; bottom: -2px; left: 50%; width: 50%; height: 14%; transform: translateX(-50%); border: 2px solid rgba(255,255,255,0.2); border-bottom: none; background: rgba(255,255,255,0.02); }
        .p-card { position: relative; width: 85px; height: 115px; border-radius: 6px; cursor: pointer; transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1); }
        .p-card:hover { transform: translate(-50%, -60%) scale(1.1) !important; z-index: 100 !important; }
        .card-pitch { position: absolute; }
        .card-sub { position: relative; margin-bottom: 5px; width: 80px; height: 110px; }
        .card-sub:hover { transform: scale(1.05) !important; }
        .p-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(180deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,1) 100%); backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.15); border-bottom: 3px solid var(--accent); border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .p-header { position: absolute; top: 3px; left: 3px; right: 3px; display: flex; justify-content: space-between; align-items: center; z-index: 3; }
        .p-pos { font-family: 'Exo 2'; font-size: 9px; font-weight: 700; color: #fff; background: rgba(0,0,0,0.6); padding: 1px 4px; border-radius: 3px; }
        .p-rating { font-family: 'Exo 2'; font-size: 16px; font-weight: 800; line-height: 1; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
        .p-img-box { position: absolute; bottom: 20px; left: 0; width: 100%; height: 85px; z-index: 2; display: flex; justify-content: center; align-items: flex-end; overflow: hidden; border-radius: 0 0 6px 6px; }
        .p-img-box img { width: auto; height: 100%; object-fit: contain; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.6)); transition: transform 0.2s; }
        .p-name { position: absolute; bottom: 0; left: 0; width: 100%; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; color: #fff; background: rgba(2, 6, 23, 0.95); z-index: 4; border-radius: 0 0 6px 6px; white-space: nowrap; overflow: hidden; border-top: 1px solid rgba(255,255,255,0.1); }
        .empty-slot { width: 60px; height: 60px; border-radius: 50%; border: 2px dashed rgba(255,255,255,0.2); background: rgba(0,0,0,0.2); transform: translate(-50%, -50%); display:flex; justify-content:center; align-items:center; }
        .empty-slot::after { content: '?'; color: rgba(255,255,255,0.2); font-size: 20px; font-weight: bold; }
        .bench { background: var(--bg-panel); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 15px; }
        .bench-title { color: #94a3b8; font-weight: 700; font-size: 13px; text-transform: uppercase; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; letter-spacing: 0.5px; }
        .bench-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        @media only screen and (max-width: 600px) { .pitch { height: 600px; } .p-card { width: 65px; height: 90px; } .card-sub { width: 60px; height: 85px; } .p-rating { font-size: 14px; } .p-pos { font-size: 8px; } .p-img-box { height: 65px; bottom: 18px; } .p-name { height: 18px; font-size: 9px; } }
    </style>
    """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0">{css}</head>
    <body>
        <div class="container">
            <div class="pitch">
                <div class="lines"><div class="center-circle"></div><div class="half-line"></div><div class="box-top"></div><div class="box-bot"></div></div>
                {html_starters}
            </div>
            <div class="bench"><div class="bench-title">Dự bị ({len(subs)})</div><div class="bench-grid">{html_subs}</div></div>
        </div>
    </body>
    </html>
    """
    
    components.html(html_content, height=final_iframe_height, scrolling=False)

# ==========================================
# KẾT THÚC BƯỚC 1
# ==========================================

# ===== CẤU HÌNH TEAMS CẦN BUILD =====
target_clubs = [
    "FC Barcelona", "Madrid Chamartin B", "Munich", "Internazionale Milano", "Manchester B", "Liverpool R", 
    "Paris Saint-Germain", "Borussia Dortmund", "Bayer 04 Leverkusen", "Madrid Rosas RB", "Arsenal FC", 
    "Chelsea B", "Manchester United", "Atalanta BC", "AC Milan", "Tottenham WB", 
    "Piemonte BN", "Napoli A", "Roma GR"
]
        
# Club được miễn trừ (không bao giờ bán)
PROTECTED_CLUBS = ["FC Barcelona"]
        
target_nations = [
    "Spain", "France", "Argentina", "England", "Portugal", 
    "Brazil", "Netherlands", "Belgium", "Italy", "Germany", 
    "Uruguay", "Japan"
        ]
        
target_leagues = ["Spanish League", "English League", "Italian League", "Bundesliga", "Ligue 1 McDonald's"]


# ===== TỰ ĐỘNG CẬP NHẬT TARGET LISTS DỰA TRÊN PLAYER COUNT =====
def check_squad_requirement(team_df, remove_duplicates=False):
    """
    Kiểm tra đội hình có đủ điều kiện tối thiểu:
    - Có ít nhất 1 GK
    - Có ít nhất 2 CB
    
    Args:
        team_df: DataFrame chứa players của team
        remove_duplicates: Nếu True, loại trùng tên player (dùng cho Nation/League)
    """
    if team_df.empty:
        return False
    
    team_df_unique = team_df.copy()
    
    # Với Nation/League: loại trùng tên, giữ thẻ tốt nhất
    if remove_duplicates and 'Player' in team_df_unique.columns:
        team_df_unique = team_df_unique.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
        team_df_unique = team_df_unique.drop_duplicates(subset=['Player'], keep='first')
    
    gk_count = len(team_df_unique[team_df_unique['Position'] == 'GK'])
    cb_count = len(team_df_unique[team_df_unique['Position'] == 'CB'])
    
    return gk_count >= 1 and cb_count >= 2

def auto_update_target_lists(df):
    """
    Tự động thêm Nation/Club/League vào target lists khi đạt ngưỡng player count:
    - Nation: >= 11 players (và có ít nhất 1 GK + 2 CB)
    - Club: >= 11 players (và có ít nhất 1 GK + 2 CB)
    - League: >= 23 players (và có ít nhất 1 GK + 2 CB)
    """
    global target_clubs, target_nations, target_leagues
    
    if df.empty:
        return
    
    updated = False
    
    # Đếm số lượng players theo Nation
    for nation in df['Nation'].dropna().astype(str).unique():
        if str(nation).strip() == '':
            continue
        nation_str = str(nation).strip()
        nation_df = df[df['Nation'].astype(str) == nation_str]
        
        # Với Nation: loại trùng tên trước khi đếm
        nation_df_unique = nation_df.copy()
        if 'Player' in nation_df_unique.columns:
            nation_df_unique = nation_df_unique.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
            nation_df_unique = nation_df_unique.drop_duplicates(subset=['Player'], keep='first')
        
        # Kiểm tra số lượng và điều kiện đội hình
        if len(nation_df_unique) >= 11 and nation_str not in target_nations:
            if check_squad_requirement(nation_df_unique, remove_duplicates=False):
                target_nations.append(nation_str)
                updated = True
    
    # Đếm số lượng players theo Club
    for club in df['Club'].dropna().astype(str).unique():
        if str(club).strip() == '':
            continue
        club_str = str(club).strip()
        club_df = df[df['Club'].astype(str) == club_str]
        
        # Với Club: không loại trùng (mỗi player chỉ thuộc 1 Club)
        # Kiểm tra số lượng và điều kiện đội hình
        if len(club_df) >= 11 and club_str not in target_clubs:
            if check_squad_requirement(club_df, remove_duplicates=False):
                target_clubs.append(club_str)
                updated = True
    
    # Đếm số lượng players theo League
    for league in df['League'].dropna().astype(str).unique():
        if str(league).strip() == '':
            continue
        league_str = str(league).strip()
        league_df = df[df['League'].astype(str) == league_str]
        
        # Với League: loại trùng tên trước khi đếm
        league_df_unique = league_df.copy()
        if 'Player' in league_df_unique.columns:
            league_df_unique = league_df_unique.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
            league_df_unique = league_df_unique.drop_duplicates(subset=['Player'], keep='first')
        
        # Kiểm tra số lượng và điều kiện đội hình
        if len(league_df_unique) >= 23 and league_str not in target_leagues:
            if check_squad_requirement(league_df_unique, remove_duplicates=False):
                target_leagues.append(league_str)
                updated = True
    
    # Sắp xếp lại các list để dễ đọc
    if updated:
        target_nations.sort()
        target_clubs.sort()
        target_leagues.sort()
    
    return updated


# ==================== PESDB SCRAPER ====================
PESDB_PLAYER_URL_BASE = "https://pesdb.net/efootball/?id="
PESDB_IMAGE_URL_BASE = "https://pesdb.net/assets/img/card/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://pesdb.net/',
    'Connection': 'keep-alive',
}

def extract_ehub_player_id(value: str) -> str:
    """Extract player ID from URL or string"""
    if not value:
        return ""
    s = str(value).strip()
    m = re.search(r"(\d{14,})", s)
    return m.group(1) if m else ""

def make_ehub_player_url(player_id: str) -> str:
    """Tạo URL PESDB từ Player ID"""
    pid = extract_ehub_player_id(player_id)
    return f"{PESDB_PLAYER_URL_BASE}{pid}" if pid else ""

def make_ehub_player_image_url(player_id: str) -> str:
    """Tạo URL hình ảnh từ Player ID - PESDB format"""
    pid = extract_ehub_player_id(player_id)
    if not pid:
        return ""
    return f"{PESDB_IMAGE_URL_BASE}f{pid}.png"

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_ehub_raw_html(url: str, max_retries: int = 3) -> str:
    """Fetch HTML từ PESDB với retry logic"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            
            html = resp.text
            if len(html) < 1000:
                raise Exception(f"HTML too short: {len(html)} chars")
            
            return html
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            continue
    return ""

def extract_player_skills(player_url: str) -> str:
    """Trích xuất Skills từ PESDB
    
    HTML Structure:
    <tbody>
        <tr><th>Player Skills</th></tr>
        <tr><td>Heading</td></tr>
        <tr><td>Man Marking</td></tr>
        ...
    </tbody>
    """
    try:
        if not player_url or not str(player_url).startswith('http'):
            return ""
        
        html = fetch_ehub_raw_html(player_url)
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        skills = []
        
        # Tìm <th>Player Skills</th>
        skill_headers = soup.find_all('th', string=re.compile(r'Player Skills', re.IGNORECASE))
        
        for header in skill_headers:
            # Lấy parent <tr>
            header_row = header.find_parent('tr')
            if not header_row:
                continue
            
            # Lấy tất cả <tr> kế tiếp cho đến khi gặp <th> khác
            current_row = header_row.find_next_sibling('tr')
            
            while current_row:
                # Nếu gặp <th> → dừng (đã sang section khác)
                if current_row.find('th'):
                    break
                
                # Lấy <td>
                td = current_row.find('td')
                if td:
                    skill_name = td.get_text(strip=True)
                    if skill_name:
                        skills.append(skill_name)
                
                current_row = current_row.find_next_sibling('tr')
        
        # Remove duplicates và sort
        skills = sorted(list(set(s for s in skills if s)))
        
        return ', '.join(skills)
        
    except Exception as e:
        return ""

def extract_card_type_from_html(soup) -> str:
    """Trích xuất loại thẻ từ HTML PESDB
    
    Mapping:
    - Trending → POTW
    - Epic, Legendary → EPIC
    - Standard, Highlight, Standard Featured → NON-EPIC
    """
    def detect_prioritized(texts):
        """Trả về loại thẻ theo priority: POTW > NON-EPIC > EPIC."""
        non_epic_detected = False
        epic_detected = False
        
        for text in texts:
            if not text:
                continue
            upper_text = text.upper()
            
            if 'TRENDING' in upper_text or 'POTW' in upper_text:
                return 'POTW'
            
            if ('HIGHLIGHT' in upper_text or 
                'FEATURED' in upper_text or 
                'STANDARD' in upper_text):
                non_epic_detected = True
                continue
            
            if 'LEGENDARY' in upper_text or 'EPIC' in upper_text:
                epic_detected = True
        
        if non_epic_detected:
            return 'NON-EPIC'
        if epic_detected:
            return 'EPIC'
        return None
    
    try:
        # --- Ưu tiên 1: Quét toàn bộ HTML text để bắt keyword đơn giản ---
        raw_html = str(soup).upper()
        if 'TRENDING' in raw_html or 'POTW' in raw_html:
            return 'POTW'
        if 'HIGHLIGHT' in raw_html or 'FEATURED' in raw_html or 'STANDARD' in raw_html:
            return 'NON-EPIC'
        if 'LEGENDARY' in raw_html:
            return 'EPIC'
        if 'EPIC' in raw_html:
            return 'EPIC'
        
        candidate_texts = []
        
        # 1. Mode tabs (ưu tiên)
        mode_tabs = soup.find('div', class_='mode-tabs')
        if mode_tabs:
            active_tab = mode_tabs.find('a', class_='active')
            if active_tab:
                candidate_texts.append(active_tab.get_text(strip=True))
        
        # 2. Các badge / label khác
        selectors = [
            '.player-card-label', '.card-type', '.player-type', '.player-card__type',
            '.player-card__badge', '.mode-title', '.player-info__type'
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                candidate_texts.append(el.get_text(strip=True))
        
        # 3. Script / data attributes (ví dụ data-mode)
        if mode_tabs:
            active_tab = mode_tabs.find('a', class_='active')
            if active_tab and active_tab.has_attr('data-mode'):
                candidate_texts.append(active_tab['data-mode'])
        
        # 4. Tổng hợp và áp dụng priority
        full_text = soup.get_text(separator=' ', strip=True)
        candidate_texts.append(full_text)
        
        detected = detect_prioritized(candidate_texts)
        if detected:
            return detected
        
        return 'NON-EPIC'  # Default
    except:
        return 'NON-EPIC'

def extract_max_level_rating(player_url: str, card_type: str = None, base_html: str = None) -> int:
    """Lấy Overall Rating với logic tùy loại thẻ.
    
    POTW/Trending: dùng level gốc + 4 (không cần max level).
    Loại khác: thử Max Level trước, fallback về level gốc, cuối cùng trả 0.
    """
    def extract_rating_from_html(html: str) -> int:
        """Helper function để trích xuất rating từ HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                th = row.find('th')
                if th and 'Overall Rating' in th.get_text():
                    td = row.find('td')
                    if td:
                        rating_text = td.get_text(strip=True)
                        # rating_text có thể chứa (+12) hoặc ký tự khác → lọc số cuối cùng
                        numbers = re.findall(r'\d+', rating_text)
                        if numbers:
                            try:
                                base_rating = int(numbers[-1])
                                return base_rating + 4  # Tự động +4
                            except:
                                pass
        except:
            pass
        return 0
    
    def get_level1_rating():
        level_html = base_html
        if not level_html:
            level_html = fetch_ehub_raw_html(base_url)
        if level_html:
            rating = extract_rating_from_html(level_html)
            if rating > 0:
                return rating
        return 0
    
    try:
        normalized_card_type = normalize_player_type(card_type) if card_type else None
        
        # Lấy base URL (loại bỏ các tham số mode nếu có)
        base_url = player_url
        if '&mode=max_level' in base_url:
            base_url = base_url.replace('&mode=max_level', '')
        if '?mode=max_level' in base_url:
            base_url = base_url.replace('?mode=max_level', '')
        
        # Nếu là POTW → chỉ cần level gốc +4
        if normalized_card_type == 'POTW':
            return get_level1_rating()
        
        # === BƯỚC 1: Thử lấy từ Max Level (Ưu tiên) ===
        max_level_url = f"{base_url}&mode=max_level" if '?' in base_url else f"{base_url}?mode=max_level"
        html = fetch_ehub_raw_html(max_level_url)
        if html:
            rating = extract_rating_from_html(html)
            if rating > 0:
                return rating
        
        # === BƯỚC 2: Fallback về Level 1 (Dự phòng) ===
        level_rating = get_level1_rating()
        if level_rating > 0:
            return level_rating
        
        # === BƯỚC 3: Trả về 0 nếu cả 2 đều thất bại ===
        return 0
        
    except Exception:
        return 0

def extract_secondary_positions(soup, main_position):
    """
    Trích xuất vị trí phụ từ sơ đồ sân bóng (div class='pitch').
    CHỈ LẤY POS2 (Vị trí sở trường - Đỏ đậm).
    Loại bỏ vị trí chính khỏi danh sách.
    """
    # 1. Nếu là GK -> Không cần lấy vị trí phụ
    if str(main_position).strip().upper() == 'GK':
        return ""

    try:
        pitch_div = soup.find('div', class_='pitch')
        if not pitch_div: return ""
        
        # Danh sách mã vị trí hợp lệ trong game
        VALID_POS = ['GK','CB','LB','RB','DMF','CMF','LMF','RMF','AMF','LWF','RWF','SS','CF']
        found_pos = set()
        
        # Chuẩn hóa vị trí chính (ví dụ: " AMF " -> "AMF")
        main_pos_norm = str(main_position).strip().upper()
        
        # Quét tất cả các div con (đại diện cho các chấm trên sân)
        for div in pitch_div.find_all('div'):
            classes = div.get('class', [])
            
            # --- SỬA ĐỔI TẠI ĐÂY ---
            # Chỉ xử lý nếu trong class có chứa 'pos2'
            if 'pos2' not in classes:
                continue
            # -----------------------

            for c in classes:
                c_upper = c.upper()
                # Nếu là mã vị trí VÀ không trùng với vị trí chính
                if c_upper in VALID_POS and c_upper != main_pos_norm:
                    found_pos.add(c_upper)
                    
        # Trả về chuỗi sắp xếp, ví dụ: "CF, SS"
        return ", ".join(sorted(list(found_pos)))
    except Exception as e:
        return ""

def extract_full_player_info(player_url: str) -> dict:
    """Trích xuất TOÀN BỘ thông tin cầu thủ từ PESDB
    
    Returns:
        dict: {
            'Player': str,
            'Rating': int,  # Từ Max Level
            'Position': str,
            'Nation': str,
            'Club': str,
            'League': str,
            'Skills': str,
            'Region': str,
            'Height': str,
            'Weight': str,
            'Age': str,
            'Foot': str,
            'Weak Foot Usage': str,
            'Weak Foot Accuracy': str,
            'Form': str,
            'Injury Resistance': str,
            'Player_Type': str,  # POTW/EPIC/NON-EPIC
        }
    """
    default_info = {
        'Player': '',
        'Rating': 0,
        'Position': '',
        'Nation': '',
        'Club': '',
        'League': '',
        'Skills': '',
        'Region': '',
        'Height': '',
        'Weight': '',
        'Age': '',
        'Foot': '',
        'Weak Foot Usage': '',
        'Weak Foot Accuracy': '',
        'Form': '',
        'Injury Resistance': '',
        'Player_Type': 'NON-EPIC',
    }
    
    try:
        if not player_url or not str(player_url).startswith('http'):
            return default_info
        
        html = fetch_ehub_raw_html(player_url)
        if not html:
            return default_info
        
        soup = BeautifulSoup(html, 'html.parser')
        info = default_info.copy()
        
        # Mapping từ PESDB labels sang tên fields
        field_mapping = {
            'Player Name': 'Player',
            'Team Name': 'Club',
            'League': 'League',
            'Nationality': 'Nation',
            'Region': 'Region',
            'Height': 'Height',
            'Weight': 'Weight',
            'Age': 'Age',
            'Foot': 'Foot',
            'Weak Foot Usage': 'Weak Foot Usage',
            'Weak Foot Accuracy': 'Weak Foot Accuracy',
            'Form': 'Form',
            'Injury Resistance': 'Injury Resistance',
        }
        
        # Lấy thông tin từ các <tr><th>...</th><td>...</td></tr>
        rows = soup.find_all('tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                key = th.get_text(strip=True).replace(':', '')
                value = td.get_text(strip=True)
                
                # Map sang field name
                if key in field_mapping:
                    field_name = field_mapping[key]
                    info[field_name] = value
                
                # ... (Phần trên giữ nguyên) ...

                # Xử lý Position đặc biệt
                if key == 'Position':
                    pos_div = td.find('div', title=True)
                    if pos_div:
                        info['Position'] = pos_div.get_text(strip=True)
        
        # === THÊM ĐOẠN NÀY VÀO ===
        # Lấy vị trí phụ từ sơ đồ sân bóng
        info['Secondary Positions'] = extract_secondary_positions(soup, info.get('Position', ''))
        # =========================

        # Lấy Skills
        info['Skills'] = extract_player_skills(player_url)
        
        # Lấy Player Type
        info['Player_Type'] = normalize_player_type(extract_card_type_from_html(soup))
        
        # ... (Phần dưới giữ nguyên) ...
        
        # Lấy Skills
        info['Skills'] = extract_player_skills(player_url)
        
        # Lấy Player Type từ loại thẻ
        info['Player_Type'] = normalize_player_type(extract_card_type_from_html(soup))
        
        # Lấy Rating (POTW dùng level gốc +4, thẻ khác ưu tiên Max Level)
        info['Rating'] = extract_max_level_rating(
            player_url,
            card_type=info.get('Player_Type'),
            base_html=html
        )
        
        return info
        
    except Exception as e:
        st.error(f"❌ Lỗi khi trích xuất thông tin: {e}")
        return default_info

def get_unique_values(df: pd.DataFrame, column: str) -> list:
    if column in df.columns:
        vals = [str(x) for x in df[column].unique() if pd.notna(x) and str(x).strip()]
        return sorted(vals)
    return []

def initialize_session_state():
    defaults = {
        'manual_reload_triggered': False,
        'current_tab': 'overview',
        'checkbox_reset_counter': 0,
        'run_pesdb_sync': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def sync_pesdb_missing_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Đồng bộ dữ liệu PESDB (Smart Sync) - Có hỗ trợ Nút Dừng & Resume.
    Sử dụng cơ chế Session State để xử lý từng cầu thủ và làm mới giao diện.
    """
    # 1. KHỞI TẠO TRẠNG THÁI (Chạy lần đầu)
    if 'sync_state' not in st.session_state:
        # Đảm bảo cột tồn tại
        if 'Secondary Positions' not in df.columns:
            df['Secondary Positions'] = ""

        # Lọc danh sách cần cập nhật
        has_url = df['Player URL'].astype(str).str.startswith('http')
        missing_sec_pos = df['Secondary Positions'].astype(str).str.strip() == ''
        missing_skills = df['Skills'].astype(str).str.strip() == ''
        missing_height = df['Height'].astype(str).str.strip() == ''
        
        needs_extraction = df[has_url & (missing_sec_pos | missing_skills | missing_height)]
        
        if needs_extraction.empty:
            st.success("✅ Dữ liệu đã đầy đủ! Không cần quét thêm.")
            st.session_state.run_pesdb_sync = False # Tắt cờ chạy
            return df

        # Lưu trạng thái vào Session
        st.session_state.sync_state = {
            'indices': needs_extraction.index.tolist(), # Danh sách index cần làm
            'total': len(needs_extraction),             # Tổng số
            'current_idx_ptr': 0,                       # Con trỏ hiện tại
            'df_snapshot': df.copy(),                   # Bản sao DF để sửa đổi
            'updated_count': 0
        }
        st.rerun() # Refresh để bắt đầu giao diện xử lý

    # 2. GIAO DIỆN XỬ LÝ (Chạy trong các lần Rerun)
    state = st.session_state.sync_state
    current_ptr = state['current_idx_ptr']
    total = state['total']
    
    # Hiển thị Progress Bar & Status
    progress = min(1.0, current_ptr / total)
    st.progress(progress, text=f"🚀 Đang cập nhật: {current_ptr}/{total} cầu thủ")
    
    # --- NÚT DỪNG CẬP NHẬT ---
    # Vì dùng st.rerun(), nút này sẽ luôn phản hồi được ngay lập tức
    if st.button("🛑 Dừng cập nhật ngay (Lưu kết quả hiện tại)", type="primary"):
        # Lưu những gì đã làm được
        if state['updated_count'] > 0:
            save_data_to_gsheet(state['df_snapshot'])
            st.toast(f"⚠️ Đã dừng! Đã lưu {state['updated_count']} cầu thủ.", icon="💾")
        else:
            st.toast("⚠️ Đã dừng! Chưa có dữ liệu mới nào.", icon="🛑")
            
        final_df = state['df_snapshot']
        del st.session_state.sync_state # Xóa trạng thái
        st.session_state.run_pesdb_sync = False # Tắt cờ chạy của Main App
        time.sleep(1)
        st.rerun()

    # 3. XỬ LÝ DỮ LIỆU (Batch Size = 1 để UI mượt nhất)
    if current_ptr < total:
        idx = state['indices'][current_ptr]
        row = state['df_snapshot'].loc[idx]
        player_name = str(row.get('Player', 'Unknown'))
        
        # Status Box nhỏ
        st.info(f"📡 Đang tải dữ liệu cho: **{player_name}**...")

        try:
            # Gọi hàm crawl dữ liệu
            info = extract_full_player_info(row['Player URL'])
            
            if info and info.get('Player'):
                # Cập nhật vào bản sao DF trong Session State
                state['df_snapshot'].at[idx, 'Secondary Positions'] = info.get('Secondary Positions', '')
                
                # Cập nhật các cột khác nếu thiếu
                cols_to_check = [
                    'Region', 'Height', 'Weight', 'Age', 'Foot',
                    'Weak Foot Usage', 'Weak Foot Accuracy', 'Form', 'Injury Resistance', 'Skills'
                ]
                for col in cols_to_check:
                    current_val = str(state['df_snapshot'].at[idx, col]).strip()
                    if not current_val or current_val == 'nan':
                        state['df_snapshot'].at[idx, col] = info.get(col, '')
                
                state['updated_count'] += 1
                
        except Exception as e:
            print(f"Lỗi {player_name}: {e}")
        
        # Tăng con trỏ và Rerun để xử lý người tiếp theo
        state['current_idx_ptr'] += 1
        st.rerun()
        
    else:
        # 4. HOÀN TẤT
        st.success(f"✅ Đã hoàn tất cập nhật {total} cầu thủ!")
        save_data_to_gsheet(state['df_snapshot'])
        
        final_df = state['df_snapshot']
        del st.session_state.sync_state # Dọn dẹp
        
        # Trả về DF để Main App hiển thị nút tải xuống
        return final_df

# --- MAIN APP ---
def main():
    initialize_session_state()
    inject_modern_ui_theme()

    with st.sidebar:
        st.header("⚙️ Điều khiển")
    
        # 1. Nút tải lại dữ liệu (Giữ nguyên)
        if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.manual_reload_triggered = True
            st.rerun()

        st.divider()

        # 2. NÚT ĐỒNG BỘ MỚI (CÓ THANH TIẾN TRÌNH & TẢI BACKUP)
        st.markdown("### 📡 Cập nhật dữ liệu")
        st.caption("Quét PESDB để lấy Vị trí phụ & Skill")
        
        # Nút kích hoạt
        if st.button("🔁 Quét & Cập nhật PESDB", use_container_width=True, type="primary"):
            st.session_state.run_pesdb_sync = True
            st.rerun()
            
        # Logic xử lý khi đang chạy đồng bộ
        if st.session_state.get('run_pesdb_sync', False):
            # Load dữ liệu tạm để xử lý
            df_sync = load_data_from_gsheet()
            
            # --- CODE MỚI: Gọi hàm trực tiếp, không bọc trong Spinner ---
            # Hàm này sẽ tự Rerun UI liên tục nên không được chặn bằng Spinner
            updated_df = sync_pesdb_missing_fields(df_sync)
            
            # Khi hàm trả về (nghĩa là đã xong hoặc đã dừng), hiện nút tải về
            if isinstance(updated_df, pd.DataFrame):
                csv = updated_df.to_csv(index=False).encode('utf-8-sig')
                
                st.markdown("---")
                st.download_button(
                    label="📥 Tải Backup (Excel/CSV)",
                    data=csv,
                    file_name=f"efootball_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_after_sync"
                )
                
                # Nút thoát chế độ sync thủ công nếu muốn
                if st.button("Trở về màn hình chính"):
                     st.session_state.run_pesdb_sync = False
                     st.rerun()
            # -----------------------------------------------------------
    
        st.divider()
    
        # 3. Menu điều hướng (Giữ nguyên)
        main_menu = st.radio(
            "📑 Điều hướng",
            ["📊 Tổng quan", "👥 Quản lý cầu thủ", "🎮 Quản lý Skills"], # Đã xóa "Phân tích"
            index=0
        )
    
        # Điều hướng chi tiết
        if main_menu == "📊 Tổng quan":
            st.session_state.current_tab = "overview"
    
        elif main_menu == "👥 Quản lý cầu thủ":
            sub_menu = st.radio(
                "⚽ Cầu thủ",
                ["Danh sách", "Đội hình", "Thêm cầu thủ"],
                index=0
            )
            if sub_menu == "Danh sách":
                st.session_state.current_tab = "players"
            elif sub_menu == "Đội hình":
                st.session_state.current_tab = "squad"
            else:
                st.session_state.current_tab = "add"
    
        elif main_menu == "🎮 Quản lý Skills":
            sub_menu = st.radio(
                "🛠️ Skills",
                ["Quản lý", "Kho Skills"],
                index=0
            )
            if sub_menu == "Quản lý":
                st.session_state.current_tab = "skills"
            else:
                st.session_state.current_tab = "inventory"
    
            st.divider()
            st.caption(f"☁️ Google Sheets • Max Squad: {MAX_SQUAD_SIZE}")
        
            # === DEBUG MODE ===
            st.divider()
            if st.checkbox("🐛 Debug Mode"):
                st.caption("**Inventory State:**")
                inv = get_inventory()
                st.json(inv if inv else {"status": "empty"})
                
                st.caption("**Session State:**")
                st.write({
                    'current_tab': st.session_state.current_tab,
                    'checkbox_reset_counter': st.session_state.get('checkbox_reset_counter', 0)
                })

    with st.spinner("⏳ Đang tải dữ liệu từ Google Sheets..."):
        df = load_data_from_gsheet()
    
    # Nếu không có dữ liệu thì dừng sớm để tránh KeyError ở các bước sau
    if df.empty:
        st.error("⚠️ Không tìm thấy dữ liệu cầu thủ trong Google Sheets. Vui lòng kiểm tra `spreadsheet_id` hoặc sheet.")
        return

    # Tự động cập nhật target lists dựa trên player count
    auto_update_target_lists(df)

    # --- HÀM ĐỒNG BỘ PESDB CHO CẦU THỦ CŨ (THỦ CÔNG) ---

    # Nếu user ấn nút đồng bộ PESDB ở sidebar thì chạy ở đây
    if st.session_state.get('run_pesdb_sync', False):
        df = sync_pesdb_missing_fields(df)
        st.session_state.run_pesdb_sync = False

    def build_top23_map(df, group_by, max_size=23):
        """Tạo mapping {(group_value, player_index) -> 'rank/size group_value'}."""
        top_map = {}
        # Nếu DataFrame rỗng hoặc không có cột tương ứng thì trả về map rỗng để tránh KeyError
        if df.empty or group_by not in df.columns:
            return top_map

        values = [v for v in df[group_by].dropna().astype(str).unique() if str(v).strip()]
        for value in values:
            gdf = df[df[group_by].astype(str) == value].copy()
            if gdf.empty:
                continue
            # Với Nation/League: loại trùng tên, giữ thẻ tốt nhất
            if group_by in ['Nation', 'League']:
                gdf = gdf.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
                gdf = gdf.drop_duplicates(subset=['Player'], keep='first')
            # Xác định các tiêu chí sắp xếp
            sort_keys = ['Rating', 'Epic_Priority']
            sort_asc = [False, True]
            
            # THÊM TIÊU CHÍ ƯU TIÊN MỚI: Top23_Count (chỉ áp dụng cho Nation/League khi bị tie)
            if group_by in ['Nation', 'League'] and 'Top23_Count' in gdf.columns:
                sort_keys.append('Top23_Count')
                sort_asc.append(False) # False = Giảm dần, ưu tiên số count cao hơn (thuộc nhiều Top 23 target hơn)
                
            # Sắp xếp theo các tiêu chí đã định
            gdf = gdf.sort_values(sort_keys, ascending=sort_asc).head(max_size)
            size = len(gdf)
            for rank, idx in enumerate(gdf.index.tolist(), start=1):
                top_map[(value, idx)] = f"{rank}/{size} {value}"
        return top_map
    
    # Tạo map cho 3 nhóm
    club_top_map = build_top23_map(df, 'Club')
    league_top_map = build_top23_map(df, 'League')
    nation_top_map = build_top23_map(df, 'Nation')
    
    # Hàm tra cứu nhanh
    def fast_rank(value, idx, mapping):
        return mapping.get((str(value), idx), None)
        
        if df.empty:
            st.error("Không có dữ liệu cầu thủ!")
            return

    current_tab = st.session_state.current_tab

    if SHOW_APP_HERO and current_tab == 'overview':
        render_app_hero(df)

    # Đảm bảo dòng 'if' này thẳng hàng với các dòng code khác trong hàm main()
    if current_tab == 'overview':
        # =========================================================================
        # 🎨 1. CSS: GLASSMORPHISM MODERN UI
        # =========================================================================
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
            
            /* Container Setup */
            .overview-container { display: flex; flex-direction: column; gap: 20px; padding: 10px 0; }
            
            /* Glass Card Style */
            .glass-card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 16px 20px;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                transition: transform 0.2s ease, border-color 0.2s ease;
                position: relative;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                justify-content: center;
                height: 110px;
            }
            
            .glass-card:hover {
                transform: translateY(-3px);
                border-color: rgba(255, 255, 255, 0.2);
                background: rgba(255, 255, 255, 0.06);
            }

            /* Typography */
            .stat-label {
                font-family: 'Outfit', sans-serif;
                font-size: 0.8rem;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
                margin-bottom: 4px;
                z-index: 2;
            }
            
            .stat-value {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 2.2rem;
                font-weight: 700;
                line-height: 1;
                color: #ffffff;
                z-index: 2;
            }
            
            .stat-sub {
                font-family: 'Outfit', sans-serif;
                font-size: 0.75rem;
                color: #64748b;
                margin-top: 6px;
                font-weight: 400;
                display: flex; align-items: center; gap: 4px;
                z-index: 2;
            }

            /* Background Icon Overlay */
            .bg-icon {
                position: absolute;
                right: -15px;
                bottom: -15px;
                font-size: 5rem;
                opacity: 0.05;
                transform: rotate(-10deg);
                pointer-events: none;
                z-index: 1;
            }

            /* Section Header */
            .section-header {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.2rem;
                font-weight: 700;
                color: #e2e8f0;
                display: flex;
                align-items: center;
                gap: 10px;
                margin-top: 20px;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .header-pill {
                background: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
                font-size: 0.7rem;
                padding: 4px 10px;
                border-radius: 20px;
                font-weight: 700;
                letter-spacing: 0.5px;
                border: 1px solid rgba(59, 130, 246, 0.2);
            }

            /* Gradients for Text */
            .grad-blue { background: linear-gradient(135deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .grad-gold { background: linear-gradient(135deg, #fcd34d, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .grad-purple { background: linear-gradient(135deg, #e879f9, #9333ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .grad-green { background: linear-gradient(135deg, #4ade80, #16a34a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .grad-red { background: linear-gradient(135deg, #f87171, #dc2626); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
        """, unsafe_allow_html=True)

        # =========================================================================
        # 🧮 2. XỬ LÝ DỮ LIỆU
        # =========================================================================
        if df.empty:
            st.error("Chưa có dữ liệu.")
            return

        # 1. Chuyển đổi số liệu
        df['Height_num'] = pd.to_numeric(df['Height'], errors='coerce')
        df['Weight_num'] = pd.to_numeric(df['Weight'], errors='coerce')
        df['Age_num'] = pd.to_numeric(df['Age'], errors='coerce')
        df['Rating_num'] = pd.to_numeric(df['Rating'], errors='coerce')

        # 2. Tính BMI
        df['BMI_num'] = df.apply(lambda x: x['Weight_num'] / ((x['Height_num']/100)**2) if x['Height_num'] > 0 else 0, axis=1)

        # 3. Lọc dữ liệu sạch
        valid_stats = df.dropna(subset=['Height_num', 'Weight_num', 'BMI_num', 'Rating_num', 'Age_num'])
        valid_stats = valid_stats[valid_stats['Height_num'] > 0]

        # --- A. CÁC SỐ LIỆU TỔNG QUAN ---
        total_players = len(df)
        total_clubs = df['Club'].nunique()
        total_nations = df['Nation'].nunique()
        total_leagues = df['League'].nunique()

        # --- B. SỐ LIỆU META & THẺ ---
        unwavering_cnt = len(df[df['Form'].astype(str).str.contains('Unwavering', case=False, na=False)])
        
        def is_ambidextrous(row):
            u = str(row.get('Weak Foot Usage', '')).upper()
            a = str(row.get('Weak Foot Accuracy', '')).upper()
            usage_ok = 'VERY HIGH' in u or 'REGULARLY' in u or '4' in u
            acc_ok = 'VERY HIGH' in a or '4' in a
            return usage_ok and acc_ok

        ambi_cnt = df.apply(is_ambidextrous, axis=1).sum()

        epic_cnt = len(df[df['Player Type'] == 'EPIC'])
        potw_cnt = len(df[df['Player Type'] == 'POTW'])

        # --- C. TRUNG BÌNH ---
        avg_rating = df['Rating_num'].mean()
        avg_age = valid_stats['Age_num'].mean()
        avg_height = valid_stats['Height_num'].mean()
        avg_weight = valid_stats['Weight_num'].mean()
        avg_bmi = valid_stats['BMI_num'].mean()

        # =========================================================================
        # 🖥️ 3. GIAO DIỆN DASHBOARD (NEW UI)
        # =========================================================================
        
        # Hàm render Card mới
        def stat_card(col, label, value, sub_text, icon, gradient_class):
            col.markdown(f"""
            <div class="glass-card">
                <div class="bg-icon">{icon}</div>
                <div class="stat-label">{label}</div>
                <div class="stat-value {gradient_class}">{value}</div>
                <div class="stat-sub">{sub_text}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- ROW 1: DATA OVERVIEW ---
        st.markdown("""
        <div class="section-header">
            <span>📦 TỔNG QUAN DATABASE</span>
            <span class="header-pill">REAL-TIME</span>
        </div>
        """, unsafe_allow_html=True)
        
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        stat_card(r1c1, "Tổng Cầu Thủ", f"{total_players:,}", "Total Players", "👥", "grad-blue")
        stat_card(r1c2, "Câu Lạc Bộ", f"{total_clubs}", "Unique Clubs", "🛡️", "grad-blue")
        stat_card(r1c3, "Quốc Gia", f"{total_nations}", "Nations", "🌍", "grad-blue")
        stat_card(r1c4, "Giải Đấu", f"{total_leagues}", "Leagues", "🏆", "grad-blue")

        # --- ROW 2: META STATS ---
        st.markdown("""
        <div class="section-header">
            <span>🔥 CHỈ SỐ META & ĐẶC BIỆT</span>
            <span class="header-pill">KEY METRICS</span>
        </div>
        """, unsafe_allow_html=True)
        
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        stat_card(r2c1, "Unwavering", f"{unwavering_cnt}", "Phong độ ổn định", "📈", "grad-green")
        stat_card(r2c2, "2 Chân Như 1", f"{ambi_cnt}", "Ambidextrous", "🦶", "grad-gold")
        stat_card(r2c3, "Thẻ EPIC", f"{epic_cnt}", "Huyền thoại", "✨", "grad-gold")
        stat_card(r2c4, "Thẻ POTW", f"{potw_cnt}", "Trending / POTW", "⚡", "grad-purple")

        # --- ROW 3: PHYSICAL AVERAGES ---
        st.markdown("""
        <div class="section-header">
            <span>🧬 TRUNG BÌNH THỂ CHẤT</span>
            <span class="header-pill">AVERAGES</span>
        </div>
        """, unsafe_allow_html=True)
        
        r3c1, r3c2, r3c3, r3c4, r3c5 = st.columns(5)
        stat_card(r3c1, "Rating TB", f"{avg_rating:.1f}", "OVR", "⭐", "grad-red")
        stat_card(r3c2, "Tuổi TB", f"{avg_age:.1f}", "Years Old", "🎂", "grad-blue")
        stat_card(r3c3, "Chiều Cao TB", f"{avg_height:.1f}", "cm", "📏", "grad-blue")
        stat_card(r3c4, "Cân Nặng TB", f"{avg_weight:.1f}", "kg", "⚖️", "grad-blue")
        stat_card(r3c5, "BMI TB", f"{avg_bmi:.1f}", "Body Index", "💪", "grad-blue")

        # --- ROW 4: TOP 10 LEADERBOARDS (WITH CHARTS) ---
        st.markdown("""
        <div class="section-header">
            <span>🏅 BẢNG XẾP HẠNG TOP 10</span>
            <span class="header-pill">RANKINGS</span>
        </div>
        """, unsafe_allow_html=True)
        
        import plotly.express as px
        
        l_c1, l_c2, l_c3 = st.columns(3)

        # Hàm vẽ biểu đồ thay thế bảng
        def render_chart_top10(col, group_col, title, color_hex):
            top_df = df[group_col].value_counts().head(10).reset_index()
            top_df.columns = [group_col, 'Count']
            top_df = top_df.sort_values('Count', ascending=True)
            
            fig = px.bar(
                top_df, x='Count', y=group_col, text='Count',
                orientation='h',
                title=None
            )
            fig.update_traces(
                marker_color=color_hex, 
                textposition='outside',
                hovertemplate='%{y}: %{x}'
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Space Grotesk, sans-serif", size=11, color="#e2e8f0"),
                xaxis=dict(showgrid=False, showticklabels=False, title=None),
                yaxis=dict(showgrid=False, title=None),
                margin=dict(l=0, r=30, t=0, b=0),
                height=300,
                showlegend=False
            )
            
            with col.container(border=True):
                st.markdown(f"**{title}**")
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # 1. Top 10 Clubs
        render_chart_top10(l_c1, 'Club', '🏛️ Câu Lạc Bộ (Clubs)', '#3b82f6') # Blue

        # 2. Top 10 Nations
        render_chart_top10(l_c2, 'Nation', '🌍 Quốc Gia (Nations)', '#ef4444') # Red

        # 3. Top 10 Leagues
        df_league_clean = df[df['League'].astype(str).str.strip() != '']
        top_league_df = df_league_clean['League'].value_counts().head(10).reset_index()
        top_league_df.columns = ['League', 'Count']
        top_league_df = top_league_df.sort_values('Count', ascending=True)
        
        fig_lg = px.bar(top_league_df, x='Count', y='League', text='Count', orientation='h')
        fig_lg.update_traces(marker_color='#eab308', textposition='outside') # Gold
        fig_lg.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Space Grotesk, sans-serif", size=11, color="#e2e8f0"),
            xaxis=dict(showgrid=False, showticklabels=False, title=None),
            yaxis=dict(showgrid=False, title=None),
            margin=dict(l=0, r=30, t=0, b=0),
            height=300, showlegend=False
        )
        
        with l_c3.container(border=True):
            st.markdown(f"**🏆 Giải Đấu (Leagues)**")
            st.plotly_chart(fig_lg, use_container_width=True, config={'displayModeBar': False})

    elif current_tab == 'players':
        st.header("👥 Cầu thủ")

        SQUAD_SIZE = 23  # Số cầu thủ mỗi team

        # ===== 1. HÀM TÍNH TOP 23 VÀ TRẢ VỀ THỨ HẠNG (RANK MAP) =====
        def get_top_23_ranked_map(df, group_by, values):
            """
            Trả về dict: {index_cầu_thủ: 'Rank/Total'}
            Ví dụ: {102: '1/23', 105: '5/11'}
            """
            ranked_map = {}
            
            for value in values:
                team_df = df[df[group_by].astype(str) == value].copy()
                if team_df.empty:
                    continue

                # Với Nation/League: loại trùng tên, giữ thẻ tốt nhất
                if group_by in ['Nation', 'League']:
                    team_df['TargetClubPriority'] = team_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in team_df.columns:
                        team_df['Top23_Count'] = 0
                    team_df = team_df.sort_values(
                        ['Player', 'Rating', 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'],
                        ascending=[True, False, True, False, False]
                    )
                    team_df = team_df.drop_duplicates(subset=['Player'], keep='first')
    
                # --- LOGIC CHỌN ĐỘI HÌNH ---
                gk_df = team_df[team_df['Position'] == 'GK']
                cb_df = team_df[team_df['Position'] == 'CB']
                squad = pd.DataFrame()
                remaining_slots = SQUAD_SIZE
    
                # 1. Chọn 1 GK tốt nhất
                if not gk_df.empty:
                    gk_df['TargetClubPriority'] = gk_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in gk_df.columns: gk_df['Top23_Count'] = 0
                    best_gk = gk_df.sort_values(['Rating', 'Epic_Priority', 'Top23_Count'], ascending=[False, True, False]).head(1)
                    squad = pd.concat([squad, best_gk])
                    remaining_slots -= 1
    
                # 2. Chọn 2 CB tốt nhất
                if not cb_df.empty:
                    cb_df['TargetClubPriority'] = cb_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in cb_df.columns: cb_df['Top23_Count'] = 0
                    best_cb = cb_df.sort_values(['Rating', 'Epic_Priority', 'Top23_Count'], ascending=[False, True, False]).head(2)
                    squad = pd.concat([squad, best_cb])
                    remaining_slots -= len(best_cb)
    
                # 3. Chọn các cầu thủ còn lại (theo Rating giảm dần)
                others = team_df.drop(squad.index, errors='ignore')
                if not others.empty:
                    others['TargetClubPriority'] = others['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in others.columns: others['Top23_Count'] = 0
                    top_rest = others.sort_values(['Rating', 'Epic_Priority', 'Top23_Count'], ascending=[False, True, False]).head(remaining_slots)
                    squad = pd.concat([squad, top_rest])
                
                # --- LƯU RANKING ---
                # Sắp xếp lại squad theo Rating để đánh số thứ tự (Rank) cho chuẩn logic "Mạnh nhất"
                final_squad = squad.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
                total_in_squad = len(final_squad)
                
                for rank, (idx, row) in enumerate(final_squad.iterrows(), start=1):
                    ranked_map[idx] = f"{rank}/{total_in_squad}"

            return ranked_map
        
        # Tính toán Rank Map cho từng nhóm
        club_rank_map = get_top_23_ranked_map(df, 'Club', target_clubs)
        nation_rank_map = get_top_23_ranked_map(df, 'Nation', target_nations)
        league_rank_map = get_top_23_ranked_map(df, 'League', target_leagues)

        # ===== PHÁT HIỆN CẦU THỦ TRÙNG (GIỮ NGUYÊN) =====
        def detect_duplicates(df):
            duplicates_info = []
            grouped = df.groupby(['Player', 'Club', 'Nation', 'League'])
            for (player, club, nation, league), group in grouped:
                if len(group) > 1 and club and nation and league:
                    sorted_group = group.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
                    best_card = sorted_group.iloc[0]
                    duplicate_cards = sorted_group.iloc[1:]
                    for _, dup in duplicate_cards.iterrows():
                        duplicates_info.append({
                            'index': dup.name,
                            'player': player,
                            'rating': dup['Rating'],
                            'rarity': dup.get('Player Type', ''),
                            'club': club,
                            'nation': nation,
                            'league': league,
                            'best_rating': best_card['Rating'],
                            'best_rarity': best_card.get('Player Type', '')
                        })
            return duplicates_info

        duplicates = detect_duplicates(df)

        # ===== 2. CẬP NHẬT GỢI Ý BÁN (HIỆN RANK) =====
        def suggest_action(row):
            idx = row.name
            club = str(row.get('Club', '')).strip()
            
            local_protected_clubs = ["FC Barcelona"] 
            if 'PROTECTED_CLUBS' in globals():
                local_protected_clubs = globals()['PROTECTED_CLUBS']
        
            nation = str(row.get('Nation', '')).strip()
            league = str(row.get('League', '')).strip()
            reasons = []

            # 0. Kiểm tra club được bảo vệ
            if club in local_protected_clubs:
                return ' ✅  GIỮ', f" 🛡 ️ {club} - Không bao giờ bán (Fan club)"
            
            # 1. Kiểm tra thẻ trùng
            is_duplicate = any(dup['index'] == idx for dup in duplicates)
            if is_duplicate:
                return '❌ BÁN', "⚠️ Thẻ trùng - Có thẻ tốt hơn (cùng player + club + nation + league)"
            
            # 2. Kiểm tra thuộc Top 23 (DÙNG RANK MAP ĐỂ HIỂN THỊ CHI TIẾT)
            in_top_club = idx in club_rank_map
            in_top_nation = idx in nation_rank_map
            in_top_league = idx in league_rank_map
            
            # Format hiển thị: "Club: Manchester B (5/11)"
            if in_top_club:
                rank_str = club_rank_map[idx]
                reasons.append(f"Club: {club} ({rank_str})")
            if in_top_nation:
                rank_str = nation_rank_map[idx]
                reasons.append(f"Nation: {nation} ({rank_str})")
            if in_top_league:
                rank_str = league_rank_map[idx]
                reasons.append(f"League: {league} ({rank_str})")
            
            # 3. Quyết định
            if reasons:
                return '✅ GIỮ', " | ".join(reasons)
            else:
                return '❌ BÁN', "Không thuộc Top 23 của bất kỳ team nào"

        # Apply suggestion
        rec_df = df.copy()
        suggestions = rec_df.apply(suggest_action, axis=1)
        rec_df['Action'], rec_df['Reasons'] = zip(*suggestions)
        sell_df = rec_df[rec_df['Action'] == '❌ BÁN']

        rank_info_list = []
        for idx, row in rec_df.iterrows():
            ranks = []
            club_rank = fast_rank(row.get('Club', ''), idx, club_top_map)
            if club_rank: ranks.append(club_rank)
            nation_rank = fast_rank(row.get('Nation', ''), idx, nation_top_map)
            if nation_rank: ranks.append(nation_rank)
            league_rank = fast_rank(row.get('League', ''), idx, league_top_map)
            if league_rank: ranks.append(league_rank)
            # Sắp xếp theo thứ tự Club → League → Nation
            rank_info_list.append("\n".join(ranks) if ranks else "")
        
        rec_df['Rank_Info'] = rank_info_list

        # ===== THỐNG KÊ TỔNG QUAN =====
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Tổng cầu thủ", len(df))
        with col2:
            protected_count = len(df[df['Club'].isin(PROTECTED_CLUBS)])
            st.metric("🛡️ FC Barcelona", protected_count)
        with col3:
            st.metric("✅ Đề xuất giữ", len(df) - len(sell_df))
        with col4:
            st.metric("❌ Đề xuất bán", len(sell_df))

        # ===== CẢNH BÁO THẺ TRÙNG =====
        if duplicates:
            st.error(f"⚠️ **CẢNH BÁO:** Phát hiện {len(duplicates)} thẻ TRÙNG (Cùng cầu thủ + Club + Nation + League)")
            
            with st.expander("🔍 Xem chi tiết thẻ trùng", expanded=True):
                dup_data = []
                for dup in duplicates:
                    dup_data.append({
                        'STT': len(dup_data) + 1,
                        'Cầu thủ': dup['player'],
                        'Rating': dup['rating'],
                        'Rarity': dup['rarity'],
                        'Club': dup['club'],
                        'Nation': dup['nation'],
                        'League': dup['league'],
                        'Thẻ tốt nhất': f"{dup['best_rating']} ({dup['best_rarity']})",
                    })
                
                dup_df = pd.DataFrame(dup_data)
                st.dataframe(dup_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Không phát hiện thẻ trùng")              
        
        # 1. THANH ĐIỀU KHIỂN CHÍNH (TOP BAR)
        with st.container(border=True):
            col_search, col_view, col_sort = st.columns([3, 1.5, 2])
            
            with col_search:
                search_query = st.text_input(
                    "🔍 Tìm kiếm",
                    placeholder="Nhập tên, CLB, Skills...",
                    label_visibility="collapsed",
                    key="filter_search_query"
                )
            
            with col_view:
                view_mode = st.radio(
                    "Chế độ xem",
                    ["🎴 Thẻ", "📋 Bảng"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="filter_view_mode"
                )
                
            with col_sort:
                c_s1, c_s2 = st.columns([2, 1])
                with c_s1:
                    sort_options = [
                        'Rating', 'BMI', 'Height', 'Weight', 'Age', 'Player Name'
                    ]
                    sort_col = st.selectbox("Sắp xếp", sort_options, index=0, label_visibility="collapsed", key="filter_sort_col")
                with c_s2:
                    sort_order = st.toggle("Tăng dần", False, key="filter_sort_asc")

        # 2. BỘ LỌC NÂNG CAO (LAYOUT 5 CỘT MỚI)
        with st.expander("🌪️ Bộ lọc nâng cao & Thống kê", expanded=False):
            # Thay đổi từ 4 cột sang 5 cột để chia nhỏ phần "Thuộc tính khác"
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
            
            with f_col1:
                st.markdown("**Cơ bản**")
                action_filter = st.selectbox("Hành động", ["Tất cả", "✅ GIỮ", "❌ BÁN"], key="filter_action")
                pos_list = sorted(df['Position'].unique().tolist())
                position_filter = st.multiselect("Vị trí", pos_list, key="filter_position")
                style_list = sorted([str(x) for x in df['Position Style'].unique() if x])
                style_filter = st.multiselect("Playstyle", style_list, key="filter_style")
            
            with f_col2:
                st.markdown("**Đội bóng**")
                club_list = sorted([str(x) for x in df['Club'].unique() if x])
                club_filter = st.multiselect("CLB", club_list, key="filter_club")
                league_list = ["Tất cả"] + sorted([str(x) for x in df['League'].unique() if x])
                league_filter = st.selectbox("Giải đấu", league_list, key="filter_league")
                nation_list = sorted([str(x) for x in df['Nation'].unique() if x])
                nation_filter = st.multiselect("Quốc gia", nation_list, key="filter_nation")

            with f_col3:
                st.markdown("**Chỉ số & Thể chất**")
                h_values = pd.to_numeric(df['Height'], errors='coerce').dropna()
                h_min, h_max = (int(h_values.min()), int(h_values.max())) if not h_values.empty else (150, 200)
                height_range = st.slider("Chiều cao (cm)", h_min, h_max, (h_min, h_max), key="filter_height_range")
                
                w_values = pd.to_numeric(df['Weight'], errors='coerce').dropna()
                w_min, w_max = (int(w_values.min()), int(w_values.max())) if not w_values.empty else (50, 100)
                weight_range = st.slider("Cân nặng (kg)", w_min, w_max, (w_min, w_max), key="filter_weight_range")

                a_values = pd.to_numeric(df['Age'], errors='coerce').dropna()
                a_min, a_max = (int(a_values.min()), int(a_values.max())) if not a_values.empty else (15, 45)
                age_range = st.slider("Tuổi", a_min, a_max, (a_min, a_max), key="filter_age_range")

            with f_col4:
                st.markdown("**Thuộc tính (1)**")
                type_filter = st.multiselect("Loại thẻ", df['Player Type'].unique(), key="filter_type")
                
                form_list = sorted([str(x) for x in df['Form'].unique() if str(x).strip()])
                form_filter = st.multiselect("Phong độ (Form)", form_list, key="filter_form")
                
                injury_list = sorted([str(x) for x in df['Injury Resistance'].unique() if str(x).strip()])
                injury_filter = st.multiselect("Kháng chấn thương", injury_list, key="filter_injury")

            with f_col5:
                st.markdown("**Thuộc tính (2)**")
                wf_usage_list = sorted([str(x) for x in df['Weak Foot Usage'].unique() if str(x).strip()])
                wf_usage_filter = st.multiselect("Dùng chân ko thuận", wf_usage_list, key="filter_wf_usage")
                
                wf_acc_list = sorted([str(x) for x in df['Weak Foot Accuracy'].unique() if str(x).strip()])
                wf_acc_filter = st.multiselect("Độ chính xác CKT", wf_acc_list, key="filter_wf_acc")
                
                foot_list = ["Tất cả"] + list(df['Foot'].unique()) if 'Foot' in df.columns else []
                foot_filter = st.selectbox("Chân thuận", foot_list, key="filter_foot")
                
                skill_query = st.text_input("Tìm Skill", placeholder="vd: Blocker", key="filter_skill_query")
                
                if st.button("🔄 Reset Filters", use_container_width=True):
                    keys_to_reset = [
                        "filter_search_query", "filter_action", "filter_position", "filter_style",
                        "filter_club", "filter_league", "filter_nation", "filter_type", 
                        "filter_form", "filter_injury", "filter_wf_usage", "filter_wf_acc",
                        "filter_foot", "filter_skill_query", 
                        "filter_height_range", "filter_weight_range", "filter_age_range"
                    ]
                    for k in keys_to_reset:
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()

        # 3. XỬ LÝ LỌC DỮ LIỆU & TÍNH TOÁN BMI
        filtered_df = rec_df.copy()
        
        for col in ['Height', 'Weight', 'Age']:
            filtered_df[f'_num_{col}'] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)

        filtered_df['_num_BMI'] = filtered_df.apply(
            lambda x: x['_num_Weight'] / ((x['_num_Height']/100)**2) if x['_num_Height'] > 0 else 0, 
            axis=1
        )

        # Apply Filters
        if search_query:
            filtered_df = filtered_df[filtered_df['Player'].str.contains(search_query, case=False, na=False)]
        if action_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Action'] == action_filter]
        if position_filter:
            filtered_df = filtered_df[filtered_df['Position'].isin(position_filter)]
        if style_filter:
            filtered_df = filtered_df[filtered_df['Position Style'].isin(style_filter)]
        if club_filter:
            filtered_df = filtered_df[filtered_df['Club'].isin(club_filter)]
        if league_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['League'] == league_filter]
        if nation_filter:
            filtered_df = filtered_df[filtered_df['Nation'].isin(nation_filter)]
        if type_filter:
            filtered_df = filtered_df[filtered_df['Player Type'].isin(type_filter)]
        
        if form_filter: filtered_df = filtered_df[filtered_df['Form'].isin(form_filter)]
        if injury_filter: filtered_df = filtered_df[filtered_df['Injury Resistance'].isin(injury_filter)]
        if wf_usage_filter: filtered_df = filtered_df[filtered_df['Weak Foot Usage'].isin(wf_usage_filter)]
        if wf_acc_filter: filtered_df = filtered_df[filtered_df['Weak Foot Accuracy'].isin(wf_acc_filter)]
        if foot_filter != "Tất cả": filtered_df = filtered_df[filtered_df['Foot'] == foot_filter]
        if skill_query:
            filtered_df = filtered_df[filtered_df['Skills'].astype(str).str.contains(skill_query, case=False, na=False)]

        filtered_df = filtered_df[
            (filtered_df['_num_Height'] >= height_range[0]) & (filtered_df['_num_Height'] <= height_range[1]) &
            (filtered_df['_num_Weight'] >= weight_range[0]) & (filtered_df['_num_Weight'] <= weight_range[1]) &
            (filtered_df['_num_Age'] >= age_range[0]) & (filtered_df['_num_Age'] <= age_range[1])
        ]
        
        # Apply Sorting Logic
        if sort_col == 'Player Name': filtered_df = filtered_df.sort_values('Player', ascending=sort_order)
        elif sort_col == 'BMI': filtered_df = filtered_df.sort_values('_num_BMI', ascending=sort_order)
        elif sort_col in ['Height', 'Weight', 'Age']: filtered_df = filtered_df.sort_values(f'_num_{sort_col}', ascending=sort_order)
        else:
            if sort_col in filtered_df.columns: filtered_df = filtered_df.sort_values(sort_col, ascending=sort_order)

        # 4. DASHBOARD MINI
        st.markdown("---")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Cầu thủ tìm thấy", len(filtered_df))
        m2.metric("Rating TB", f"{filtered_df['Rating'].mean():.1f}")
        m3.metric("Số lượng EPIC", len(filtered_df[filtered_df['Player Type'] == 'EPIC']))
        m4.metric("Số lượng POTW", len(filtered_df[filtered_df['Player Type'] == 'POTW']))
        m5.metric("Đề xuất BÁN", len(filtered_df[filtered_df['Action'] == '❌ BÁN']))
        st.markdown("---")

        # 5. HIỂN THỊ DỮ LIỆU
        if view_mode == "📋 Bảng":
            table_df = filtered_df.copy()
            def get_img_link(row):
                pid = str(row.get('Player ID', '')).strip()
                if pid: return f"https://pesdb.net/assets/img/card/f{pid}.png"
                return "https://pesdb.net/assets/img/card/f0.png"
            table_df['Avatar'] = table_df.apply(get_img_link, axis=1)
            table_df['BMI'] = table_df['_num_BMI'].round(2)
            cols_to_show = ['Avatar', 'Player', 'Rating', 'Position', 'BMI', 'Player Type', 'Club', 'Action', 'Skills', 'Reasons']
            st.dataframe(
                table_df[cols_to_show],
                column_config={
                    "Avatar": st.column_config.ImageColumn("Ảnh", width="small"),
                    "Player": st.column_config.TextColumn("Tên cầu thủ", width="medium"),
                    "Rating": st.column_config.ProgressColumn("OVR", format="%d", min_value=70, max_value=105, width="small"),
                    "Position": st.column_config.TextColumn("VT", width="small"),
                    "BMI": st.column_config.NumberColumn("BMI", format="%.2f", width="small"),
                    "Player Type": st.column_config.TextColumn("Loại", width="small"),
                    "Action": st.column_config.TextColumn("Status", width="small"),
                    "Skills": st.column_config.ListColumn("Kỹ năng", width="medium"),
                    "Reasons": st.column_config.TextColumn("Ghi chú", width="large")
                },
                use_container_width=True, height=800, hide_index=True
            )
        else:
            # --- CHẾ ĐỘ GRID (THẺ) ---
            MAX_ITEMS = 100
            if len(filtered_df) > MAX_ITEMS:
                st.warning(f"⚠️ Đang hiển thị {MAX_ITEMS} cầu thủ đầu tiên. Hãy dùng bộ lọc để tìm cụ thể hơn.")
                display_df = filtered_df.head(MAX_ITEMS)
            else:
                display_df = filtered_df

            cols_per_row = 5
            rows = [display_df.iloc[i:i + cols_per_row] for i in range(0, len(display_df), cols_per_row)]

            # Xác định metric cần highlight trên thẻ dựa trên Sort Col
            highlight_metric = None
            if sort_col in ['BMI', 'Height', 'Weight', 'Age']:
                highlight_metric = sort_col

            for row in rows:
                cols = st.columns(cols_per_row)
                for i, (idx, player) in enumerate(row.iterrows()):
                    with cols[i]:
                        p_data = player.to_dict()
                        # TRUYỀN highlight_metric VÀO ĐÂY ĐỂ HIỆN TOOLTIP/BADGE
                        card_html = render_efootball_card_html(p_data, highlight_metric=highlight_metric)
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        if st.button("🔍 Xem chi tiết", key=f"btn_view_{idx}", use_container_width=True):
                            show_player_modal(player)

        # 6. THANH CÔNG CỤ CUỐI TRANG
        st.divider()
        with st.container(border=True):
            st.markdown("#### 📂 Thao tác dữ liệu")
            ac1, ac2, ac3 = st.columns([1, 1, 2])
            with ac1:
                if len(sell_df) > 0:
                    csv_sell = sell_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("⬇️ Tải DS Bán", csv_sell, "sell_list.csv", "text/csv", use_container_width=True)
            with ac2:
                csv_all = filtered_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("⬇️ Tải DS Lọc", csv_all, "filtered_list.csv", "text/csv", use_container_width=True)
            with ac3:
                with st.expander("🗑️ Xóa cầu thủ (Nguy hiểm)"):
                    st.warning("Chọn cầu thủ để xóa vĩnh viễn khỏi Database")
                    del_options = filtered_df.index.tolist()
                    del_labels = {i: f"{filtered_df.loc[i, 'Player']} ({filtered_df.loc[i, 'Rating']})" for i in del_options}
                    to_delete = st.multiselect("Chọn cầu thủ:", options=del_options, format_func=lambda x: del_labels.get(x, str(x)))
                    if to_delete:
                        if st.button(f"Xác nhận XÓA {len(to_delete)} cầu thủ", type="primary"):
                            try:
                                new_df = df.drop(index=to_delete, errors='ignore')
                                if save_data_to_gsheet(new_df):
                                    st.success("Đã xóa thành công!")
                                    st.cache_data.clear()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")

    elif current_tab == 'skills':
        st.header("🎮 Quản lý Skills & Training")
        
        # --- CONFIG ---
        MAX_SKILLS = 10  # Efootball giới hạn 10 skills (5 gốc + 5 thêm)
        MAX_ADDED_SLOTS = 5
        ITEMS_PER_PAGE = 24

        # --- HELPER: Dialog Training (Trái tim của bản nâng cấp) ---
        @st.dialog("🏋️ Training Center")
        def show_training_modal(idx, row, current_inventory): # current_inventory được truyền từ bên ngoài vào
            """Popup xử lý training thông minh"""
            p_name = row['Player']
            p_pos = str(row['Position']).strip()
            
            # --- CHECK GK MODE ---
            is_gk = p_pos == 'GK'
            
            # Nếu là GK, ta PHẢI dùng kho GK, bất kể current_inventory truyền vào là gì
            # (Để an toàn, ta load lại kho GK ở đây nếu cần, hoặc giả định bên ngoài truyền đúng)
            # Tuy nhiên, để code bên ngoài gọn, ta sẽ load đè nếu là GK
            if is_gk:
                training_inventory = get_gk_inventory_from_gsheet()
                st.info("🧤 Đang sử dụng Kho Skill Thủ Môn")
            else:
                training_inventory = current_inventory # Dùng kho thường
            
            # ... (Phần hiển thị Header, Skill hiện có giữ nguyên) ...
            # Copy lại đoạn hiển thị Header từ code cũ vào đây
            # ...
            base_skills = [s.strip() for s in str(row.get('Skills', '')).split(',') if s.strip()]
            added_skills = [s.strip() for s in str(row.get('Added Skills', '')).split(',') if s.strip()]
            used_slots = len(added_skills)
            remaining_slots = MAX_ADDED_SLOTS - used_slots
            
            c1, c2 = st.columns([1, 3])
            with c1:
                pid = str(row.get('Player ID', '')).strip()
                img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else "https://pesdb.net/assets/img/card/f0.png"
                st.image(img_url, width=80)
            with c2:
                st.subheader(p_name)
                st.caption(f"{p_pos} | {row['Rating']} | {row['Club']}")
                st.progress(used_slots / MAX_ADDED_SLOTS, text=f"Slot: {used_slots}/{MAX_ADDED_SLOTS}")
            st.divider()
            st.markdown("**Skills hiện tại:**")
            skill_badges = ""
            for s in base_skills: skill_badges += f"<span style='background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:10px;font-size:0.8em;margin:2px;display:inline-block'>⭐ {s}</span>"
            for s in added_skills: skill_badges += f"<span style='background:rgba(74, 222, 128, 0.2);color:#4ade80;padding:2px 8px;border-radius:10px;font-size:0.8em;margin:2px;display:inline-block'>✅ {s}</span>"
            st.markdown(skill_badges, unsafe_allow_html=True)
            
            if remaining_slots <= 0:
                st.warning("🔒 Đã full slot!")
                return
            st.divider()
            
            # --- LOGIC STRICT TARGETS ---
            # Hàm get_recommended_skills đã được thiết kế để trả về Priority List chuẩn
            all_missing = get_recommended_skills(p_pos, str(row.get('Skills', '')), str(row.get('Added Skills', '')), 15)
            target_skills = all_missing[:remaining_slots]
            
            if not target_skills:
                st.info("Không có skill chỉ định.")
                return

            options_map = {}
            valid_options = []
            
            for skill in target_skills:
                # Dùng training_inventory đã chọn đúng loại
                stock = training_inventory.get(skill, 0)
                if stock > 0:
                    label = f"🟢 {skill} (Kho: {stock})"
                else:
                    label = f"🔴 {skill} (Hết hàng)"
                valid_options.append(skill)
                options_map[skill] = label
            
            st.markdown(f"#### 🎯 Mục tiêu ({'GK' if is_gk else 'Field'})")
            selected = st.multiselect(
                "Chọn skill:", options=valid_options, format_func=lambda x: options_map.get(x, x),
                default=[s for s in valid_options if training_inventory.get(s, 0) > 0],
                max_selections=remaining_slots
            )
            
            # Validate
            out_of_stock = [s for s in selected if training_inventory.get(s, 0) <= 0]
            
            col_save1, col_save2 = st.columns(2)
            with col_save2:
                btn_disabled = len(selected) == 0 or len(out_of_stock) > 0
                if out_of_stock: st.error(f"⚠️ Hết hàng: {', '.join(out_of_stock)}")
                
                if st.button("💾 Xác nhận thêm", type="primary", use_container_width=True, disabled=btn_disabled):
                    new_added = added_skills + selected
                    df.at[idx, 'Added Skills'] = ", ".join(new_added)
                    if save_data_to_gsheet(df):
                        # GỌI HÀM UPDATE VỚI FLAG is_gk
                        for s in selected:
                            update_inventory_count(s, -1, is_gk=is_gk)
                        
                        st.toast("Thành công!", icon="🎉")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()

        # --- 1. THANH CÔNG CỤ FILTER (Sử dụng st.pills nếu có, fallback st.radio) ---
        with st.container(border=True):
            f1, f2, f3 = st.columns([3, 1, 1.2])
            with f1:
                search_txt = st.text_input(
                    "🔍 Tìm kiếm toàn diện", 
                    placeholder="Nhập tên, kỹ năng, CLB, hoặc Quốc gia...", 
                    label_visibility="collapsed"
                )
            with f2:
                ft_pos = st.multiselect("Vị trí", sorted(df['Position'].unique().tolist()), placeholder="Vị trí", label_visibility="collapsed")
            with f3:
                # CẬP NHẬT OPTIONS ĐÚNG YÊU CẦU
                status_opts = ["Có thể train", "Thiếu skills để thêm", "Đã đủ skills", "Tất cả"]
                ft_status = st.selectbox(
                    "Trạng thái", 
                    status_opts, 
                    index=0, # Mặc định hiển thị những người train được ngay
                    label_visibility="collapsed"
                )
            
            with st.expander("🌪️ Bộ lọc nâng cao (Loại thẻ / Rating)"):
                ef1, ef2 = st.columns(2)
                with ef1:
                    ft_type = st.multiselect("Loại thẻ", ["EPIC", "POTW", "NON-EPIC"], default=[], placeholder="Chọn loại thẻ...")
                with ef2:
                    min_r, max_r = int(df['Rating'].min()), int(df['Rating'].max())
                    rt_range = st.slider("Rating", min_r, max_r, (min_r, max_r))

        # --- 2. XỬ LÝ DỮ LIỆU & PHÂN LOẠI GK/FIELD ---
        
        # [QUAN TRỌNG] Load CẢ 2 kho để check chéo
        inventory_field = get_inventory()
        inventory_gk = get_gk_inventory_from_gsheet()
        
        filtered_df = df.copy()
        
        # A. SEARCH & BASIC FILTER
        if search_txt:
            query = search_txt.lower()
            filtered_df['Search_Data'] = (
                filtered_df['Player'].astype(str) + " " + 
                filtered_df['Club'].astype(str) + " " + 
                filtered_df['Nation'].astype(str) + " " + 
                filtered_df['Skills'].astype(str) + " " +
                filtered_df['Added Skills'].astype(str)
            ).str.lower()
            filtered_df = filtered_df[filtered_df['Search_Data'].str.contains(query)]

        if ft_pos: filtered_df = filtered_df[filtered_df['Position'].isin(ft_pos)]
        if ft_type:
            mapped_types = [t if t != "Standard" else "NON-EPIC" for t in ft_type]
            filtered_df = filtered_df[filtered_df['Player Type'].isin(mapped_types)]
            
        filtered_df = filtered_df[(filtered_df['Rating'] >= rt_range[0]) & (filtered_df['Rating'] <= rt_range[1])]

        # --- B. LOGIC PHÂN LOẠI TRẠNG THÁI (GK AWARENESS) ---
        def classify_status_smart(row):
            # 1. Check Full / Locked
            is_potw = "POTW" in str(row['Player Type']).upper()
            added = [x for x in str(row.get('Added Skills', '')).split(',') if x.strip()]
            
            if is_potw or len(added) >= MAX_ADDED_SLOTS:
                return "Đã đủ skills"

            # 2. Xác định vị trí & Kho tương ứng
            p_pos = str(row['Position']).strip()
            is_gk = p_pos == 'GK'
            
            # [QUAN TRỌNG] Chọn kho để check stock
            current_inv = inventory_gk if is_gk else inventory_field

            # 3. Tính toán Strict Targets (Ưu tiên tuyệt đối)
            remaining_slots = MAX_ADDED_SLOTS - len(added)
            all_missing = get_recommended_skills(p_pos, str(row.get('Skills', '')), str(row.get('Added Skills', '')), 15)
            strict_targets = all_missing[:remaining_slots]
            
            if not strict_targets:
                return "Đã đủ skills" # Không còn skill gợi ý nào
            
            # 4. Check Stock trong kho tương ứng
            # Chỉ cần 1 skill trong nhóm Strict Targets có hàng -> Có thể train
            has_stock = any(current_inv.get(s, 0) > 0 for s in strict_targets)
            
            if has_stock:
                return "Có thể train"
            else:
                return "Thiếu skills để thêm"

        # Áp dụng logic
        filtered_df['Train_Status'] = filtered_df.apply(classify_status_smart, axis=1)

        # Lọc theo Status người dùng chọn
        if ft_status != "Tất cả":
            filtered_df = filtered_df[filtered_df['Train_Status'] == ft_status]

        # --- C. LOGIC SẮP XẾP (BARCELONA FIRST) ---
        filtered_df['Is_Barca'] = filtered_df['Club'].apply(lambda x: 1 if str(x).strip() == "FC Barcelona" else 0)
        filtered_df = filtered_df.sort_values(
            ['Is_Barca', 'Rating', 'Epic_Priority'], 
            ascending=[False, False, True]
        )

        # --- 3. PHÂN TRANG & HIỂN THỊ ---
        total_items = len(filtered_df)
        num_pages = max(1, (total_items // ITEMS_PER_PAGE) + (1 if total_items % ITEMS_PER_PAGE > 0 else 0))
        
        col_pag1, col_pag2 = st.columns([4, 1])
        with col_pag1:
            st.caption(f"Tìm thấy **{total_items}** cầu thủ.")
        with col_pag2:
            if num_pages > 1:
                page = st.number_input("Trang", min_value=1, max_value=num_pages, value=1)
            else:
                page = 1

        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        display_df = filtered_df.iloc[start_idx:end_idx]

        # --- 4. HIỂN THỊ GRID CARD (Logic: Strict Priority / Dành slot tuyệt đối) ---
        if display_df.empty:
            st.info("🔍 Không tìm thấy cầu thủ nào phù hợp.")
        else:
            # CSS Visual
            st.markdown("""
            <style>
            .skill-slot-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 2px; }
            .slot-filled { background-color: #4ade80; box-shadow: 0 0 5px #4ade80; }
            .slot-empty { background-color: #334155; border: 1px solid #475569; }
            </style>
            """, unsafe_allow_html=True)

            # === SỬA ĐỔI TẠI ĐÂY: Render theo từng Row để đúng thứ tự trên Mobile ===
            # Thay vì tạo cols = st.columns(4) bên ngoài, ta lặp từng nhóm 4 cầu thủ
            
            for i in range(0, len(display_df), 4):
                # Lấy nhóm 4 cầu thủ
                chunk = display_df.iloc[i : i + 4]
                # Tạo 4 cột cho hàng này
                cols = st.columns(4)
                
                # Duyệt qua từng cầu thủ trong nhóm
                for j, (idx, row) in enumerate(chunk.iterrows()):
                    with cols[j]: # Điền vào cột tương ứng (0, 1, 2, 3)
                        # A. LẤY DỮ LIỆU CƠ BẢN
                        p_pos = str(row['Position']).strip()
                        p_skills = str(row.get('Skills', ''))
                        p_added = str(row.get('Added Skills', ''))
                        added_list = [x for x in p_added.split(',') if x.strip()]
                        n_added = len(added_list)
                        remaining_slots = MAX_ADDED_SLOTS - n_added
                        is_potw = "POTW" in str(row['Player Type']).upper()
                        
                        # B. LOGIC "DÀNH SLOT TUYỆT ĐỐI"
                        all_missing_ordered = get_recommended_skills(p_pos, p_skills, p_added, 15)
                        strict_targets = all_missing_ordered[:remaining_slots]
                        
                        # LOGIC CHỌN KHO ĐỂ CHECK
                        is_gk_player = p_pos == 'GK'
                        if is_gk_player:
                            check_inventory = get_gk_inventory_from_gsheet()
                        else:
                            check_inventory = inventory_field
                            
                        # Check Stock
                        trainable_skills = [s for s in strict_targets if check_inventory.get(s, 0) > 0]
                        
                        # C. QUYẾT ĐỊNH TRẠNG THÁI NÚT
                        btn_disabled = True
                        btn_type = "secondary"
                        btn_label = "Checking..."
                        
                        if is_potw:
                            btn_label = "🔒 POTW"
                        elif n_added >= MAX_ADDED_SLOTS:
                            btn_label = "✅ Full Slots"
                        elif not strict_targets:
                            btn_label = "🤷‍♂️ Đủ Skill Top"
                        elif len(trainable_skills) > 0:
                            btn_label = f"🏋️ Train ({len(trainable_skills)})"
                            btn_disabled = False
                            btn_type = "primary"
                        else:
                            missing_top1 = strict_targets[0] if strict_targets else ""
                            btn_label = f"⚠️ Thiếu: {missing_top1}"
                            btn_disabled = True

                        # D. RENDER CARD
                        slots_html = ""
                        if is_potw:
                            slots_html = "<span style='color:#d946ef; font-size:0.8em'>🔒 POTW Locked</span>"
                        else:
                            for s in range(MAX_ADDED_SLOTS):
                                cls = "slot-filled" if s < n_added else "slot-empty"
                                slots_html += f"<span class='skill-slot-dot {cls}'></span>"

                        # Highlight Viền cho BARCA
                        is_barca = str(row.get('Club', '')).strip() == "FC Barcelona"
                        # border_style không dùng trong container st.container(border=True) mặc định được, 
                        # nên ta chỉ highlight text tên cầu thủ bên dưới
                        
                        with st.container(border=True):
                            # Layout Card
                            c_img, c_info = st.columns([1, 2.5])
                            with c_img:
                                pid = str(row.get('Player ID', '')).strip()
                                img = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else "https://pesdb.net/assets/img/card/f0.png"
                                st.image(img, use_container_width=True)
                            
                            with c_info:
                                color = "#fbbf24" if row['Epic_Priority'] == 0 else ("#d946ef" if is_potw else "#fff")
                                
                                # Thêm badge BARCA
                                prefix = "🔵🔴 " if is_barca else ""
                                
                                st.markdown(f"<div style='font-weight:bold; color:{color}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{prefix}{row['Player']}</div>", unsafe_allow_html=True)
                                st.caption(f"{p_pos} • {row['Rating']}")
                                st.markdown(f"<div>{slots_html}</div>", unsafe_allow_html=True)
                            
                            if st.button(btn_label, key=f"tr_{idx}", disabled=btn_disabled, type=btn_type, use_container_width=True):
                                show_training_modal(idx, row, inventory_field)

    elif current_tab == 'squad':
        st.header("⚽ Quản lý Đội hình")
        sq_tab1, sq_tab2 = st.tabs(["🤖 Auto Build (Thông minh)", "🛠️ Đội hình 23 (Thủ công)"])

        # =========================================================
        # TAB 1: AUTO BUILD (REAL-TIME & AUTO FORMATION)
        # =========================================================
        with sq_tab1:
            st.caption("🤖 Hệ thống sẽ tự động quét 27 sơ đồ để tìm đội hình mạnh nhất cho tiêu chí bạn chọn.")
            
            with st.container(border=True):
                # Chia làm 2 cột: 1 chọn chế độ, 2 chọn chi tiết
                c1, c2 = st.columns([1, 2])
                
                # Biến lưu cấu hình
                auto_find_formation = True # LUÔN LUÔN TỰ ĐỘNG TÌM SƠ ĐỒ
                selected_formation = None
                filter_col = None
                filter_val = None
                sort_mode = 'rating_desc'
                
                with c1:
                    st.markdown("##### 1. Chế độ")
                    build_mode = st.radio("Chọn kiểu build:", ["Theo Team/Giải", "Theo Chỉ số"], horizontal=True, label_visibility="collapsed")
                
                with c2:
                    st.markdown("##### 2. Cấu hình chi tiết")
                    
                    if build_mode == "Theo Team/Giải":
                        # Giao diện chọn Team
                        col_a, col_b = st.columns(2)
                        with col_a:
                            team_type = st.selectbox("Lọc theo:", ["(Toàn bộ)", "Club", "Nation", "League", "Region"])
                        with col_b:
                            if team_type != "(Toàn bộ)":
                                # --- CẬP NHẬT: SẮP XẾP THEO SỐ LƯỢNG GIẢM DẦN (GIỐNG TAB THỦ CÔNG) ---
                                # 1. Đếm số lượng
                                group_counts = df.groupby(team_type)['Player'].nunique().to_dict()
                                
                                # 2. Lấy danh sách duy nhất và loại bỏ giá trị rỗng
                                unique_vals = [x for x in df[team_type].astype(str).unique() if str(x).strip()]
                                
                                # 3. Sắp xếp: Ưu tiên số lượng giảm dần -> Sau đó đến tên A-Z (để đẹp hơn nếu bằng số lượng)
                                # key=lambda x: (group_counts.get(x, 0), x) -> reverse=True sẽ sort count to nhất lên đầu
                                sorted_opts = sorted(unique_vals, key=lambda x: group_counts.get(x, 0), reverse=True)
                                
                                # 4. Format hiển thị: "Tên (Số lượng)"
                                formatted_opts = [f"{opt} ({group_counts.get(opt, 0)})" for opt in sorted_opts]
                                
                                # 5. Tạo Selectbox
                                selected_display = st.selectbox(f"Chọn {team_type}:", ["(Tất cả)"] + formatted_opts)
                                
                                # 6. Trích xuất giá trị thực để lọc (Bỏ phần số lượng đi)
                                if selected_display == "(Tất cả)":
                                    filter_val = "(Tất cả)"
                                else:
                                    # Cắt chuỗi từ bên phải tại dấu mở ngoặc cuối cùng
                                    filter_val = selected_display.rsplit(" (", 1)[0]
                                
                                filter_col = team_type
                            else:
                                st.selectbox("Giá trị:", ["-"], disabled=True)
                    else:
                        # Giao diện chọn Chỉ số
                        stat_type = st.selectbox("Tiêu chí:", [
                            "⭐ Highest Rating (Mạnh nhất)", 
                            "💪 The Tanks (Chiến Thần BMI Lớn)",     # Mới
                            "⚡ The Agiles (Sóc Nhỏ BMI Nhỏ)",     # Mới
                            "🦶 The Ambidextrous (2 Chân Như 1)",    # Mới
                            "🟣 Form Is Temporary (Full POTW)",     # Mới
                            "🌍 United Nations (Đa Quốc Gia)",      # Mới
                            "🦒 Tallest XI (Cao nhất)", 
                            "🐜 Shortest XI (Thấp nhất)",
                            "⚖️ Heaviest XI (Nặng nhất)",
                            "🪶 Lightest XI (Nhẹ nhất)",
                            "👶 Youngest XI (Trẻ nhất)",
                            "👴 Oldest XI (Già nhất)"
                        ])
                        
                        # Mapping từ Label sang ID
                        if "Rating" in stat_type: sort_mode = 'rating_desc'
                        elif "Tanks" in stat_type: sort_mode = 'bmi_desc'      # Mới
                        elif "Agiles" in stat_type: sort_mode = 'bmi_asc'      # Mới
                        elif "Ambidextrous" in stat_type: sort_mode = 'ambidextrous' # Mới
                        elif "POTW" in stat_type: sort_mode = 'potw_only'      # Mới
                        elif "United Nations" in stat_type: sort_mode = 'united_nations' # Mới
                        elif "Cao nhất" in stat_type: sort_mode = 'height_desc'
                        elif "Thấp nhất" in stat_type: sort_mode = 'height_asc'
                        elif "Nặng nhất" in stat_type: sort_mode = 'weight_desc'
                        elif "Nhẹ nhất" in stat_type: sort_mode = 'weight_asc'
                        elif "Trẻ nhất" in stat_type: sort_mode = 'age_asc'
                        elif "Già nhất" in stat_type: sort_mode = 'age_desc'

            # --- TÍNH TOÁN VÀ HIỂN THỊ NGAY LẬP TỨC ---
            
            # 1. Kiểm tra nhanh dữ liệu (nếu chọn Team)
            if build_mode == "Theo Team/Giải" and filter_col and filter_val and filter_val != "(Tất cả)":
                check_df = df[df[filter_col].astype(str) == filter_val]
                if check_df.empty:
                    st.warning(f"⚠️ Không có dữ liệu cho {filter_val}")
                else:
                    pos_counts = check_df['Position'].value_counts()
                    missing_msg = []
                    if pos_counts.get('GK', 0) == 0: missing_msg.append("Thiếu GK")
                    if pos_counts.get('CB', 0) < 2: missing_msg.append("Thiếu CB thuần")
                    if missing_msg:
                        st.toast(f"⚠️ Cảnh báo nhân sự: {', '.join(missing_msg)}", icon="⚠️")

            # 2. Chạy Auto Build (Luôn dùng find_best_formation_for_team)
            best_squad = []
            found_name = ""
            
            # Chỉ chạy khi có dữ liệu hợp lệ
            should_run = True
            if build_mode == "Theo Team/Giải" and (not filter_val or filter_val == "(Tất cả)" or filter_val == "-"):
                # Nếu chọn toàn bộ database thì hơi nặng, nhưng vẫn cho chạy
                pass 

            if should_run:
                # Dùng spinner để báo đang xử lý
                with st.spinner("🤖 Đang quét 80+ sơ đồ để tìm đội hình tối ưu..."):
                    found_name, best_squad = find_best_formation_for_team(df, sort_mode, filter_col, filter_val)
            
            if not best_squad:
                st.warning("⚠️ Không tìm thấy cầu thủ phù hợp để xếp đội hình!")
            else:
                if found_name:
                    st.success(f"✅ Đội hình tối ưu nhất (Đá chính): **{found_name}**")

# --- CODE MỚI: KIỂM TRA & BÁO THIẾU NGƯỜI ---
                    missing_slots = [p['Position'] for p in best_squad if p.get('Is_Starter') and p['Player'] == "---"]
                    if missing_slots:
                        from collections import Counter
                        missing_counts = Counter(missing_slots)
                        missing_text = ", ".join([f"{k} ({v})" for k, v in missing_counts.items()])
                        st.error(f"⚠️ Đội hình chưa hoàn thiện! Đang thiếu {len(missing_slots)} vị trí: **{missing_text}**")
                        st.info("💡 Hệ thống đã chọn sơ đồ này vì nó cần ít cầu thủ bổ sung nhất.")
                    # ---------------------------------------------

                # --- TÍNH TOÁN CHỈ SỐ (CHO TOÀN BỘ 23 NGƯỜI) ---
                all_valid_players = [p for p in best_squad if p['Rating'] > 0]
                total_players = len(all_valid_players)
                
                t_rat = sum(p['Rating'] for p in all_valid_players)
                a_rat = t_rat / total_players if total_players > 0 else 0
                
                # --- LOGIC TÍNH CHỈ SỐ PHỤ ---
                custom_label = None
                custom_value = None

                if build_mode == "Theo Chỉ số":
                    def get_val(p, key):
                        try: return float(re.sub(r'[^\d.]', '', str(p.get(key, 0))))
                        except: return 0

                    if "Tanks" in stat_type or "Agiles" in stat_type:
                        # Tính BMI trung bình
                        bmis = []
                        for p in all_valid_players:
                            try:
                                h = get_val(p, 'Height') / 100.0
                                w = get_val(p, 'Weight')
                                if h > 0: bmis.append(w/(h**2))
                            except: pass
                        avg = sum(bmis) / len(bmis) if bmis else 0
                        custom_label = "BMI Trung bình"
                        custom_value = f"{avg:.1f}"
                    
                    elif "Ambidextrous" in stat_type:
                        count_tier1 = 0
                        count_tier2 = 0
                        
                        for p in all_valid_players:
                            d = p.get('Data', {})
                            u_str = str(d.get('Weak Foot Usage','')).strip().lower()
                            a_str = str(d.get('Weak Foot Accuracy','')).strip().lower()
                            
                            is_usage_perfect = 'regularly' in u_str or '4' in u_str
                            is_acc_perfect = 'very high' in a_str or '4' in a_str
                            
                            is_usage_good = is_usage_perfect or 'occasionally' in u_str or '3' in u_str
                            is_acc_good = is_acc_perfect or 'high' in a_str or '3' in a_str
                            
                            if is_usage_perfect and is_acc_perfect:
                                count_tier1 += 1
                            elif is_usage_good and is_acc_good:
                                count_tier2 += 1
                                
                        custom_label = "Chân không thuận (Perf/Good)"
                        # Hiển thị dạng: 5 Perfect / 6 Good
                        custom_value = f"{count_tier1} Perf / {count_tier2} Good"

                    elif "United Nations" in stat_type:
                        # FIX: Lấy Nation từ p['Data'] thay vì p['Nation']
                        nations = set(p.get('Data', {}).get('Nation', '') for p in all_valid_players)
                        # Loại bỏ giá trị rỗng nếu có
                        if '' in nations: nations.remove('')
                        
                        custom_label = "Số Quốc gia"
                        custom_value = f"{len(nations)}"
                    
                    elif "POTW" in stat_type:
                        potw_c = sum(1 for p in all_valid_players if 'POTW' in str(p['Type']).upper() or 'TRENDING' in str(p['Type']).upper())
                        custom_label = "Số thẻ POTW"
                        custom_value = f"{potw_c}"
                    elif "Cao" in stat_type or "Thấp" in stat_type:
                        vals = [get_val(p, 'Height') for p in all_valid_players]
                        avg = sum(vals) / len(vals) if vals else 0
                        custom_label = "Chiều cao TB (23)"
                        custom_value = f"{avg:.1f} cm"
                    elif "Nặng" in stat_type or "Nhẹ" in stat_type:
                        vals = [get_val(p, 'Weight') for p in all_valid_players]
                        avg = sum(vals) / len(vals) if vals else 0
                        custom_label = "Cân nặng TB (23)"
                        custom_value = f"{avg:.1f} kg"
                    elif "Trẻ" in stat_type or "Già" in stat_type:
                        vals = [get_val(p, 'Age') for p in all_valid_players]
                        avg = sum(vals) / len(vals) if vals else 0
                        custom_label = "Tuổi TB (23)"
                        custom_value = f"{avg:.1f}"

                # --- HIỂN THỊ METRICS ---
                if custom_label:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Tổng Sức mạnh (23)", t_rat)
                    with m2: st.metric("Rating TB (23)", f"{a_rat:.1f}")
                    with m3: st.metric(custom_label, custom_value)
                else:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Tổng Sức mạnh (23)", t_rat)
                    with m2: st.metric("Rating TB (23)", f"{a_rat:.1f}")
                    with m3: st.metric("Quân số", f"{total_players}/23")
                
                st.divider()
                
                # --- HIỂN THỊ SÂN VÀ BẢNG ---
                col_view1, col_view2 = st.columns([1.3, 1]) 
                
                # Xác định metric để hiển thị tooltip trên sân
                metric_to_show = None
                
                if build_mode == "Theo Chỉ số":
                    # Chiều cao
                    if "Cao" in stat_type or "Thấp" in stat_type or "Tallest" in stat_type or "Shortest" in stat_type: 
                        metric_to_show = 'Height'
                    
                    # Cân nặng
                    elif "Nặng" in stat_type or "Nhẹ" in stat_type or "Heaviest" in stat_type or "Lightest" in stat_type: 
                        metric_to_show = 'Weight'
                    
                    # Tuổi
                    elif "Trẻ" in stat_type or "Già" in stat_type or "Youngest" in stat_type or "Oldest" in stat_type: 
                        metric_to_show = 'Age'
                    
                    # BMI (Tanks / Agiles)
                    elif "Tanks" in stat_type or "Agiles" in stat_type or "BMI" in stat_type:
                        metric_to_show = 'BMI'
                    
                    # Chân thuận (Ambidextrous)
                    elif "Ambidextrous" in stat_type or "Chân" in stat_type: 
                        metric_to_show = 'Ambidextrous'
                    
                    # Quốc gia (United Nations)
                    elif "United Nations" in stat_type or "Quốc Gia" in stat_type:
                        metric_to_show = 'Nation'
                    
                    # Loại thẻ (POTW / Epic)
                    elif "POTW" in stat_type or "Epic" in stat_type:
                        metric_to_show = 'Type'

                # ... (Phần code tính toán logic metric_to_show ở trên giữ nguyên) ...

                # --- BẮT ĐẦU THAY ĐỔI TỪ ĐÂY ---
                # Thay vì chia cột, hiển thị Full width
                st.write("") # Spacer
                
                # Gọi hàm render mới
                render_pitch_view(best_squad, formation_name=found_name, sort_mode=sort_mode)
               

        # =========================================================
        # TAB 2: MANUAL BUILD (GIỮ NGUYÊN)
        # =========================================================
        with sq_tab2:
            st.caption("🛠️ Chế độ kiểm tra Top 23 thẻ tốt nhất (Logic cũ).")
            
            # --- LOGIC CŨ ---
            g1, g2 = st.columns(2)
            with g1:
                group_by = st.selectbox("Theo", ["Club", "Nation", "League", "Region"], index=0, key="old_gb")
            with g2:
                group_counts = df[group_by].value_counts().to_dict()
                group_options = [x for x in df[group_by].astype(str).unique() if str(x).strip()]
                group_options_sorted = sorted(group_options, key=lambda x: group_counts.get(x, 0), reverse=True)
                formatted_options = ["(Tất cả)"] + [f"{opt} ({group_counts.get(opt, 0)})" for opt in group_options_sorted]
                selected_display = st.selectbox(f"Chọn {group_by}", formatted_options, key="old_sel")
            
            if selected_display == "(Tất cả)":
                group_value = "(Tất cả)"
            else:
                group_value = selected_display.rsplit(" (", 1)[0]
            
            df_src = df.copy()
            if group_value != "(Tất cả)":
                df_src = df_src[df_src[group_by].astype(str) == group_value]
            
            if df_src.empty:
                st.warning("Không có cầu thủ.")
            else:
                if group_by in ['Nation', 'League']:
                    df_src['TargetClubPriority'] = df_src['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in df_src.columns: df_src['Top23_Count'] = 0
                    df_src = df_src.sort_values(['Player', 'Rating', 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'], ascending=[True, False, True, False, False])
                    df_src = df_src.drop_duplicates(subset=['Player'], keep='first')

                # Logic lọc GK/CB và chọn top 23 (Code gốc)
                MAX_SQUAD = 23
                squad = pd.DataFrame()
                remaining_slots = MAX_SQUAD
                
                # Chọn GK
                gk_df = df_src[df_src['Position'] == 'GK'].copy()
                if not gk_df.empty:
                    gk_df['TargetClubPriority'] = gk_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in gk_df.columns: gk_df['Top23_Count'] = 0
                    best_gk = gk_df.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(1)
                    squad = pd.concat([squad, best_gk])
                    remaining_slots -= 1
                
                # Chọn CB
                cb_df = df_src[df_src['Position'] == 'CB'].copy()
                if not cb_df.empty:
                    cb_df['TargetClubPriority'] = cb_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in cb_df.columns: cb_df['Top23_Count'] = 0
                    best_cb = cb_df.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(2)
                    squad = pd.concat([squad, best_cb])
                    remaining_slots -= len(best_cb)
                
                # Chọn còn lại
                others = df_src.drop(squad.index, errors='ignore').copy()
                if not others.empty and remaining_slots > 0:
                    others['TargetClubPriority'] = others['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in others.columns: others['Top23_Count'] = 0
                    top_rest = others.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(remaining_slots)
                    squad = pd.concat([squad, top_rest])
                
                squad = squad.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
                
                st.divider()
                st.subheader(f"Danh sách 23 cầu thủ ({len(squad)}/23)")
                
                # --- KHÔI PHỤC HIỂN THỊ CARD CÓ HÌNH ẢNH ---
                for idx, row in squad.iterrows():
                    player_name = row['Player']
                    rating = row['Rating']
                    ptype = str(row['Player Type']).upper()
                    
                    # Logic lấy ảnh mạnh mẽ hơn
                    pid = str(row.get('Player ID', '')).strip()
                    purl = str(row.get('Player URL', '')).strip()
                    if not pid and purl:
                        m = re.search(r"(\d{14,})", purl)
                        pid = m.group(1) if m else ""
                    
                    img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else None
                    
                    card_color = "🟣" if "POTW" in ptype else ("🟡" if "EPIC" in ptype and "NON" not in ptype else "🔵")
                    
                    with st.container(border=True):
                        c_img, c_inf = st.columns([1, 5])
                        with c_img:
                            if img_url:
                                st.image(img_url, width=60) 
                            else:
                                st.markdown("<div style='font-size:40px; text-align:center;'>👤</div>", unsafe_allow_html=True)
                        with c_inf:
                            st.markdown(f"### {card_color} {player_name}")
                            st.markdown(f"**Rating:** {rating} | **Pos:** {row['Position']} | **Type:** {row['Player Type']}")
                            st.caption(f"**Club:** {row.get('Club','')} | **Nation:** {row.get('Nation','')}")

    elif current_tab == 'add':
            st.header("➕ Thêm cầu thủ")
            
            # Initialize session state
            if 'add_preview_data' not in st.session_state:
                st.session_state.add_preview_data = None
            if 'add_show_form' not in st.session_state:
                st.session_state.add_show_form = False
            if 'add_mode' not in st.session_state:
                st.session_state.add_mode = 'new'
            
            # ========== CHỌN CHẾ ĐỘ ==========
            mode = st.radio(
                "Chọn chế độ",
                ["➕ Thêm mới", "🔄 Upgrade cầu thủ có sẵn"],
                horizontal=True,
                key="add_mode_radio"
            )
            
            st.session_state.add_mode = 'upgrade' if mode == "🔄 Upgrade cầu thủ có sẵn" else 'new'
            
            st.divider()
            
            # ========== CHẾ ĐỘ UPGRADE ==========
            if st.session_state.add_mode == 'upgrade':
                st.info("💡 Chế độ này tự động tìm và thay thế thẻ cũ (cùng tên + Club + Nation + League)")
                
                # Bước 1: Chọn cầu thủ
                existing_players = sorted(df['Player'].astype(str).unique().tolist())
                selected_player = st.selectbox(
                    "1️⃣ Chọn cầu thủ cần upgrade",
                    options=[""] + existing_players,
                    help="Chọn cầu thủ từ danh sách có sẵn"
                )
                
                if selected_player:
                    # Hiển thị tất cả phiên bản hiện có
                    player_versions = df[df['Player'] == selected_player].copy()
                    player_versions = player_versions.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
                    
                    st.subheader(f"📋 Phiên bản hiện có của {selected_player}")
                    # Hiển thị thêm cột Secondary Positions để đối chiếu
                    cols_ver = ['Rating', 'Position', 'Secondary Positions', 'Player Type', 'Club', 'Nation', 'League']
                    cols_ver = [c for c in cols_ver if c in player_versions.columns]
                    
                    version_display = player_versions[cols_ver].copy()
                    version_display.insert(0, 'STT', range(1, len(version_display) + 1))
                    st.dataframe(version_display, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 2️⃣ Nhập URL PESDB của phiên bản mới")
                    
                    upgrade_url = st.text_input(
                        "URL PESDB",
                        placeholder="https://pesdb.net/efootball/?id=...",
                        key="upgrade_url"
                    )
                    
                    if st.button("🔍 Lấy thông tin & Preview", type="primary", disabled=not upgrade_url):
                        with st.spinner("⏳ Đang trích xuất dữ liệu..."):
                            player_info = extract_full_player_info(upgrade_url)
                            
                            if player_info and player_info['Player']:
                                st.session_state.add_preview_data = {
                                    'Player': selected_player,
                                    'Rating': player_info.get('Rating', 0),
                                    'Position': player_info['Position'],
                                    'Secondary Positions': player_info.get('Secondary Positions', ''), # Lấy vị trí phụ
                                    'Nation': player_info['Nation'],
                                    'Club': player_info['Club'],
                                    'League': player_info['League'],
                                    'Region': player_info.get('Region', ''),
                                    'Height': player_info.get('Height', ''),
                                    'Weight': player_info.get('Weight', ''),
                                    'Age': player_info.get('Age', ''),
                                    'Foot': player_info.get('Foot', ''),
                                    'Weak Foot Usage': player_info.get('Weak Foot Usage', ''),
                                    'Weak Foot Accuracy': player_info.get('Weak Foot Accuracy', ''),
                                    'Form': player_info.get('Form', ''),
                                    'Injury Resistance': player_info.get('Injury Resistance', ''),
                                    'Skills': player_info['Skills'],
                                    'Player_Type': normalize_player_type(player_info.get('Player_Type', 'NON-EPIC')),
                                    'Player_URL': upgrade_url,
                                    'Player_ID': extract_ehub_player_id(upgrade_url)
                                }
                                st.session_state.add_show_form = True
                                st.success("✅ Đã lấy thông tin thành công!")
                                st.rerun()
                            else:
                                st.error("❌ Không thể lấy thông tin từ URL này!")
            
            # ========== CHẾ ĐỘ THÊM MỚI ==========
            else:
                if not st.session_state.add_show_form:
                    st.markdown("### 🔗 Bước 1: Nhập URL từ PESDB")
                    st.info("💡 Nhập link PESDB để tự động lấy toàn bộ thông tin cầu thủ")
                    
                    pesdb_url = st.text_input(
                        "URL PESDB",
                        placeholder="https://pesdb.net/efootball/?id=105809740719809",
                        help="Ví dụ: https://pesdb.net/efootball/?id=105809740719809"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("🔍 Lấy thông tin", type="primary", use_container_width=True, disabled=not pesdb_url):
                            with st.spinner("⏳ Đang trích xuất dữ liệu từ PESDB..."):
                                player_info = extract_full_player_info(pesdb_url)
                                
                                if player_info and player_info['Player']:
                                    st.session_state.add_preview_data = {
                                        'Player': player_info['Player'],
                                        'Rating': player_info.get('Rating', 0),
                                        'Position': player_info['Position'],
                                        'Secondary Positions': player_info.get('Secondary Positions', ''), # Lấy vị trí phụ
                                        'Nation': player_info['Nation'],
                                        'Club': player_info['Club'],
                                        'League': player_info['League'],
                                        'Region': player_info.get('Region', ''),
                                        'Height': player_info.get('Height', ''),
                                        'Weight': player_info.get('Weight', ''),
                                        'Age': player_info.get('Age', ''),
                                        'Foot': player_info.get('Foot', ''),
                                        'Weak Foot Usage': player_info.get('Weak Foot Usage', ''),
                                        'Weak Foot Accuracy': player_info.get('Weak Foot Accuracy', ''),
                                        'Form': player_info.get('Form', ''),
                                        'Injury Resistance': player_info.get('Injury Resistance', ''),
                                        'Skills': player_info['Skills'],
                                        'Player_Type': normalize_player_type(player_info.get('Player_Type', 'NON-EPIC')),
                                        'Player_URL': pesdb_url,
                                        'Player_ID': extract_ehub_player_id(pesdb_url)
                                    }
                                    st.session_state.add_show_form = True
                                    st.success("✅ Đã lấy thông tin thành công!")
                                    st.rerun()
                                else:
                                    st.error("❌ Không thể lấy thông tin từ URL này. Vui lòng kiểm tra lại!")
                    
                    with col2:
                        if st.button("✍️ Nhập thủ công", use_container_width=True):
                            st.session_state.add_preview_data = {
                                'Player': '',
                                'Rating': 90,
                                'Position': 'CF',
                                'Secondary Positions': '',
                                'Nation': '',
                                'Club': '',
                                'League': '',
                                'Region': '',
                                'Height': '',
                                'Weight': '',
                                'Age': '',
                                'Foot': '',
                                'Weak Foot Usage': '',
                                'Weak Foot Accuracy': '',
                                'Form': '',
                                'Injury Resistance': '',
                                'Skills': '',
                                'Player_Type': 'NON-EPIC',
                                'Player_URL': '',
                                'Player_ID': ''
                            }
                            st.session_state.add_show_form = True
                            st.rerun()
                    
                    st.divider()
                    st.caption("🎯 **Hướng dẫn:** Nhập URL PESDB để tự động lấy thông tin, hoặc chọn 'Nhập thủ công' để tự điền")
            
            # ========== BƯỚC 2: PREVIEW & CHỈNH SỬA (CHUNG CHO CẢ 2 MODE) ==========
            if st.session_state.add_show_form and st.session_state.add_preview_data:
                data = st.session_state.add_preview_data
                
                st.markdown("### 📋 Bước 2: Xem trước & Chỉnh sửa")
                
                # Hiển thị hình ảnh nếu có Player ID
                if data.get('Player_ID'):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        image_url = make_ehub_player_image_url(data['Player_ID'])
                        st.image(image_url, width=200)
                    with col_info:
                        st.markdown(f"## {data.get('Player', 'Unknown Player')}")
                        # Hiển thị nhanh các vị trí
                        st.caption(f"**Vị trí chính:** {data.get('Position')} | **Phụ:** {data.get('Secondary Positions')}")
                else:
                    st.markdown(f"## ✍️ Nhập thông tin cầu thủ mới")
                
                st.divider()
                
                # Form chỉnh sửa
                with st.form("add_player_final_form", clear_on_submit=False):
                    st.subheader("✏️ Thông tin cầu thủ")
                    
                    # Row 1: Tên + Rating + Loại
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        player_name = st.text_input("👤 Tên cầu thủ *", value=data.get('Player', ''), placeholder="Ví dụ: Lionel Messi")
                    with col2:
                        rating = st.number_input("⭐ Rating *", min_value=1, max_value=150, value=data.get('Rating', 90))
                    with col3:
                        type_options = ["NON-EPIC", "POTW", "EPIC"]
                        current_type = data.get('Player_Type', 'NON-EPIC')
                        type_idx = type_options.index(current_type) if current_type in type_options else 0
                        player_type = st.selectbox("🏷️ Loại thẻ *", type_options, index=type_idx)
                    
                    # Row 2: Vị trí + Nhóm vị trí
                    col1, col2 = st.columns(2)
                    with col1:
                        existing_positions = sorted(df['Position'].unique().tolist(), key=lambda x: POSITION_ORDER.get(x, 999))
                        current_pos = data.get('Position', '')
                        if current_pos and current_pos not in existing_positions:
                            existing_positions.insert(0, current_pos)
                        position_idx = existing_positions.index(current_pos) if current_pos in existing_positions else 0
                        position = st.selectbox("📍 Vị trí Chính *", existing_positions, index=position_idx)
                    with col2:
                        position_style = st.selectbox(
                            "🎮 Nhóm vị trí *",
                            POSITION_STYLES,
                            index=POSITION_STYLES.index(POSITIONS.get(position, "Forward"))
                        )

                    # --- MỚI: VỊ TRÍ PHỤ ---
                    st.markdown("#### 🔁 Vị trí phụ (Secondary Positions)")
                    secondary_pos = st.text_input(
                        "Nhập các vị trí phụ (cách nhau bởi dấu phẩy)", 
                        value=data.get('Secondary Positions', ''),
                        help="Ví dụ: LWF, SS, AMF. Để trống nếu không có."
                    )
                    # -----------------------
                    
                    st.divider()
                    st.subheader("🌍 Thông tin đội bóng")
                    
                    # Row 3: Nation + Club + League
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        existing_nations = [""] + sorted([x for x in df['Nation'].astype(str).unique() if str(x).strip()])
                        current_nation = data.get('Nation', '')
                        if current_nation and current_nation not in existing_nations:
                            existing_nations.insert(1, current_nation)
                        nation_idx = existing_nations.index(current_nation) if current_nation in existing_nations else 0
                        nation = st.selectbox("🏴 Quốc gia", existing_nations, index=nation_idx)
                        if nation == "":
                            nation_new = st.text_input("Nhập quốc gia mới", key="nation_new")
                            if nation_new:
                                nation = nation_new
                    
                    with col2:
                        existing_clubs = [""] + sorted([x for x in df['Club'].astype(str).unique() if str(x).strip()])
                        current_club = data.get('Club', '')
                        if current_club and current_club not in existing_clubs:
                            existing_clubs.insert(1, current_club)
                        club_idx = existing_clubs.index(current_club) if current_club in existing_clubs else 0
                        club = st.selectbox("⚽ CLB", existing_clubs, index=club_idx)
                        if club == "":
                            club_new = st.text_input("Nhập CLB mới", key="club_new")
                            if club_new:
                                club = club_new
                    
                    with col3:
                        existing_leagues = [""] + sorted([x for x in df['League'].astype(str).unique() if str(x).strip()])
                        current_league = data.get('League', '')
                        if current_league and current_league not in existing_leagues:
                            existing_leagues.insert(1, current_league)
                        league_idx = existing_leagues.index(current_league) if current_league in existing_leagues else 0
                        league = st.selectbox("🏆 Giải đấu", existing_leagues, index=league_idx)
                        if league == "":
                            league_new = st.text_input("Nhập giải đấu mới", key="league_new")
                            if league_new:
                                league = league_new
                    
                    # Row 4: Thể chất & thuộc tính
                    st.divider()
                    st.subheader("📊 Thể chất & Thuộc tính")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        region_val = st.text_input("Region", value=data.get('Region', ''))
                    with col2:
                        height_val = st.text_input("Height (cm)", value=str(data.get('Height', '') or ''))
                    with col3:
                        weight_val = st.text_input("Weight (kg)", value=str(data.get('Weight', '') or ''))
                    with col4:
                        age_val = st.text_input("Age", value=str(data.get('Age', '') or ''))
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        foot_val = st.text_input("Foot", value=data.get('Foot', ''))
                    with col2:
                        wf_usage_val = st.text_input("Weak Foot Usage", value=data.get('Weak Foot Usage', ''))
                    with col3:
                        wf_acc_val = st.text_input("Weak Foot Accuracy", value=data.get('Weak Foot Accuracy', ''))
                    with col4:
                        form_val = st.text_input("Form", value=data.get('Form', ''))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        injury_val = st.text_input("Injury Resistance", value=data.get('Injury Resistance', ''))
                    
                    # Skills
                    st.divider()
                    st.subheader("🎮 Skills")
                    skills = st.text_area(
                        "Danh sách skills (cách nhau bởi dấu phẩy)",
                        value=data.get('Skills', ''),
                        height=100,
                        help="Ví dụ: Heading, Man Marking, Interception"
                    )
                    
                    st.divider()
                    
                    # Buttons
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col2:
                        cancel_btn = st.form_submit_button("❌ Hủy", use_container_width=True)
                    with col3:
                        save_btn = st.form_submit_button("💾 Lưu cầu thủ", type="primary", use_container_width=True)
                    
                    # Xử lý buttons
                    if cancel_btn:
                        st.session_state.add_preview_data = None
                        st.session_state.add_show_form = False
                        st.rerun()
                    
                    if save_btn:
                        if not player_name:
                            st.error("❌ Vui lòng nhập tên cầu thủ!")
                        elif not position:
                            st.error("❌ Vui lòng chọn vị trí!")
                        else:
                            player_type_norm = normalize_player_type(player_type)
                            # CHẾ ĐỘ UPGRADE
                            if st.session_state.add_mode == 'upgrade':
                                matching_cards = df[
                                    (df['Player'] == player_name) &
                                    (df['Club'].astype(str) == club) &
                                    (df['Nation'].astype(str) == nation) &
                                    (df['League'].astype(str) == league)
                                ]
                                
                                new_df = df.copy()
                                
                                if not matching_cards.empty:
                                    old_idx = matching_cards.index[0]
                                    old_rating = matching_cards.iloc[0]['Rating']
                                    old_type = matching_cards.iloc[0]['Player Type']
                                    
                                    new_df.at[old_idx, 'Rating'] = int(rating)
                                    new_df.at[old_idx, 'Position'] = position
                                    new_df.at[old_idx, 'Position Style'] = position_style
                                    new_df.at[old_idx, 'Secondary Positions'] = secondary_pos # LƯU VỊ TRÍ PHỤ
                                    new_df.at[old_idx, 'Player Type'] = player_type_norm
                                    new_df.at[old_idx, 'Region'] = region_val
                                    new_df.at[old_idx, 'Height'] = height_val
                                    new_df.at[old_idx, 'Weight'] = weight_val
                                    new_df.at[old_idx, 'Age'] = age_val
                                    new_df.at[old_idx, 'Foot'] = foot_val
                                    new_df.at[old_idx, 'Weak Foot Usage'] = wf_usage_val
                                    new_df.at[old_idx, 'Weak Foot Accuracy'] = wf_acc_val
                                    new_df.at[old_idx, 'Form'] = form_val
                                    new_df.at[old_idx, 'Injury Resistance'] = injury_val
                                    new_df.at[old_idx, 'Player URL'] = data.get('Player_URL', '')
                                    new_df.at[old_idx, 'Player ID'] = data.get('Player_ID', '')
                                    new_df.at[old_idx, 'Skills'] = skills
                                    new_df.at[old_idx, 'Added Skills'] = ""
                                    new_df.at[old_idx, 'Epic_Priority'] = 0 if player_type_norm == "EPIC" else 1
                                    
                                    try:
                                        if save_data_to_gsheet(new_df):
                                            rating_diff = int(rating) - old_rating
                                            st.success(f"✅ Đã upgrade **{player_name}**: {old_rating} ({old_type}) → {rating} ({player_type}) ({rating_diff:+d})")
                                            st.info(f"📍 {club} | {nation} | {league}")
                                            
                                            st.session_state.add_preview_data = None
                                            st.session_state.add_show_form = False
                                            st.cache_data.clear()
                                            st.balloons()
                                            
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error("❌ Không thể lưu dữ liệu!")
                                    except Exception as e:
                                        st.error(f"❌ Lỗi: {e}")
                                else:
                                    st.warning(f"⚠️ Không tìm thấy thẻ cũ với Club/Nation/League này")
                                    st.info("💡 Sẽ thêm phiên bản mới thay vì upgrade")
                                    
                                    new_player = {
                                        "Player": player_name,
                                        "Rating": int(rating),
                                        "Position": position,
                                        "Position Style": position_style,
                                        "Secondary Positions": secondary_pos, # LƯU VỊ TRÍ PHỤ
                                        "Player Type": player_type_norm,
                                        "Nation": nation,
                                        "Club": club,
                                        "League": league,
                                        "Region": region_val,
                                        "Height": height_val,
                                        "Weight": weight_val,
                                        "Age": age_val,
                                        "Foot": foot_val,
                                        "Weak Foot Usage": wf_usage_val,
                                        "Weak Foot Accuracy": wf_acc_val,
                                        "Form": form_val,
                                        "Injury Resistance": injury_val,
                                        "Player URL": data.get('Player_URL', ''),
                                        "Player ID": data.get('Player_ID', ''),
                                        "Skills": skills,
                                        "Added Skills": "",
                                        "Epic_Priority": 0 if player_type_norm == "EPIC" else 1,
                                    }
                                    
                                    new_df = pd.concat([new_df, pd.DataFrame([new_player])], ignore_index=True)
                                    
                                    try:
                                        if save_data_to_gsheet(new_df):
                                            st.success(f"✅ Đã thêm phiên bản mới: **{player_name}** {rating} | {club} | {nation} | {league}")
                                            
                                            st.session_state.add_preview_data = None
                                            st.session_state.add_show_form = False
                                            st.cache_data.clear()
                                            st.balloons()
                                            
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error("❌ Không thể lưu dữ liệu!")
                                    except Exception as e:
                                        st.error(f"❌ Lỗi: {e}")
                            
                            # CHẾ ĐỘ THÊM MỚI
                            else:
                                new_player = {
                                    "Player": player_name,
                                    "Rating": int(rating),
                                    "Position": position,
                                    "Position Style": position_style,
                                    "Secondary Positions": secondary_pos, # LƯU VỊ TRÍ PHỤ
                                    "Player Type": player_type_norm,
                                    "Nation": nation,
                                    "Club": club,
                                    "League": league,
                                    "Region": region_val,
                                    "Height": height_val,
                                    "Weight": weight_val,
                                    "Age": age_val,
                                    "Foot": foot_val,
                                    "Weak Foot Usage": wf_usage_val,
                                    "Weak Foot Accuracy": wf_acc_val,
                                    "Form": form_val,
                                    "Injury Resistance": injury_val,
                                    "Player URL": data.get('Player_URL', ''),
                                    "Player ID": data.get('Player_ID', ''),
                                    "Skills": skills,
                                    "Added Skills": "",
                                    "Epic_Priority": 0 if player_type_norm == "EPIC" else 1,
                                }
                                
                                new_df = pd.concat([df, pd.DataFrame([new_player])], ignore_index=True)
                                
                                try:
                                    if save_data_to_gsheet(new_df):
                                        st.success(f"✅ Đã thêm cầu thủ **{player_name}** thành công!")
                                        
                                        st.session_state.add_preview_data = None
                                        st.session_state.add_show_form = False
                                        st.cache_data.clear()
                                        st.balloons()
                                        
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ Không thể lưu dữ liệu vào Google Sheets!")
                                except Exception as e:
                                    st.error(f"❌ Lỗi khi lưu: {e}")
            
    elif current_tab == 'inventory':
        st.header("📦 Quản lý Kho Skills")

        # --- 1. CSS CUSTOM ---
        st.markdown("""
        <style>
        .skill-card {
            background-color: #1e293b; border-radius: 12px; padding: 15px;
            border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            text-align: center; height: 100%;
        }
        .skill-icon { font-size: 24px; margin-bottom: 5px; }
        .skill-name { 
            font-weight: 700; color: #f8fafc; font-size: 0.85rem; 
            margin-bottom: 10px; min-height: 40px; display: flex; 
            align-items: center; justify-content: center;
        }
        .stNumberInput label { display: none; }
        .quantity-badge { font-size: 0.8rem; margin-bottom: 5px; text-transform: uppercase; }
        .has-stock { color: #4ade80; font-weight: bold; }
        .no-stock { color: #ef4444; }
        </style>
        """, unsafe_allow_html=True)

        # --- 2. CHỌN KHO (FIELD vs GK) ---
        inv_type = st.radio("📂 Chọn Kho:", ["🏃 Cầu thủ (Field)", "🧤 Thủ môn (GK)"], horizontal=True)
        is_gk_mode = "Thủ môn" in inv_type

        # --- 3. LOAD DATA TƯƠNG ỨNG ---
        if is_gk_mode:
            inventory = get_gk_inventory_from_gsheet()
            # GK chỉ dùng đúng list priority đã định nghĩa, không có category phức tạp
            target_skills = GK_SKILLS_PRIORITY_LIST
            # Gom tất cả vào 1 nhóm duy nhất cho gọn
            grouped_skills = {"🧤 Kỹ năng Thủ Môn": target_skills}
            st.info("💡 Đây là kho riêng biệt cho Thủ Môn. Skills ở đây không dùng chung với Cầu thủ thường.")
        else:
            inventory = get_inventory()
            all_skills = get_all_known_skills()
            # Logic phân loại cũ cho Field Players
            STRICT_CATEGORIES = {
                "🎮 Dribbling": ["Sole Control", "Scissors Feint", "Double Touch", "Flip Flap", "Marseille Turn", "Sombrero", "Chop Turn", "Cut Behind & Turn", "Scotch Move", "Rabona"],
                "⚽ Passing": ["Weighted Pass", "Pinpoint Crossing", "One-touch Pass", "Through Passing", "No Look Pass", "Low Lofted Pass", "Long Throw"],
                "🎯 Shooting": ["First-time Shot", "Long-Range Shooting", "Long-Range Curler", "Outside Curler", "Chip Shot Control", "Knuckle Shot", "Dipping Shot", "Rising Shot", "Acrobatic Finishing"],
                "🛡️ Defense": ["Man Marking", "Track Back", "Acrobatic Clearance", "Interception", "Blocker", "Heading", "Aerial Superiority", "Sliding Tackle"],
                "✨ Other": ["Captaincy", "Super Sub", "Fighting Spirit", "Gamesmanship", "Penalty Specialist", "Heel Trick"]
            }
            # Gom skill GK ra khỏi list Field (nếu muốn ẩn GK skills ở kho thường)
            # Tuy nhiên code cũ bạn đang gộp chung, giờ ta chỉ hiển thị những gì không phải GK specific hoặc cứ để full
            # Để đơn giản và đúng logic cũ: Field Inventory chứa tất cả skill (trừ những cái thuần GK nếu muốn lọc)
            
            grouped_skills = {k: [] for k in STRICT_CATEGORIES.keys()}
            grouped_skills["❓ Chưa phân loại"] = []
            
            # Helper map
            skill_to_cat = {}
            for cat, skills in STRICT_CATEGORIES.items():
                for s in skills: skill_to_cat[s.lower().replace("-", " ").replace(" ", "")] = cat
            
            for skill in all_skills:
                # Bỏ qua skill thuần GK ở kho Field (để đỡ rối)
                if skill.startswith("GK "): continue 
                
                s_norm = skill.lower().replace("-", " ").replace(" ", "")
                found = False
                if s_norm in skill_to_cat:
                    grouped_skills[skill_to_cat[s_norm]].append(skill)
                    found = True
                else:
                    for cat, targets in STRICT_CATEGORIES.items():
                        for t in targets:
                            if t.lower().replace("-", " ").replace(" ", "") in s_norm:
                                grouped_skills[cat].append(skill)
                                found = True
                                break
                        if found: break
                if not found: grouped_skills["❓ Chưa phân loại"].append(skill)
            
            grouped_skills = {k: v for k, v in grouped_skills.items() if v}

        # --- 4. SUMMARY ---
        total_items = sum(inventory.values())
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"### 🎒 Tồn kho ({'GK' if is_gk_mode else 'Field'}): <span style='color:#4ade80'>{total_items}</span> thẻ", unsafe_allow_html=True)
            with c2:
                if st.button("🔄 Làm mới", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            with c3:
                if st.button("🗑️ Xóa kho này", type="primary"):
                    if is_gk_mode: save_gk_inventory_to_gsheet({k:0 for k in GK_SKILLS_PRIORITY_LIST})
                    else: save_skill_inventory_to_gsheet({})
                    st.rerun()

        st.write("") 

        # --- 5. FORM EDIT ---
        with st.form("inventory_form"):
            tabs = st.tabs(list(grouped_skills.keys()))
            new_values = {}

            for tab_idx, (cat_name, skills_in_cat) in enumerate(grouped_skills.items()):
                with tabs[tab_idx]:
                    cols = st.columns(4)
                    for i, skill in enumerate(sorted(skills_in_cat)):
                        current_qty = inventory.get(skill, 0)
                        
                        icon = "🧤" if is_gk_mode else "✨"
                        if "Dribbling" in cat_name: icon = "🎮"
                        elif "Passing" in cat_name: icon = "⚽"
                        elif "Shooting" in cat_name: icon = "🎯"
                        elif "Defense" in cat_name: icon = "🛡️"
                        
                        stock_class = "has-stock" if current_qty > 0 else "no-stock"
                        stock_text = "Còn hàng" if current_qty > 0 else "Hết hàng"
                        
                        with cols[i % 4]:
                            st.markdown(f"""
                            <div class="skill-card">
                                <div class="skill-icon">{icon}</div>
                                <div class="skill-name">{skill}</div>
                                <div class="quantity-badge {stock_class}">{stock_text}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            val = st.number_input(
                                f"{skill}", min_value=0, max_value=999, 
                                value=int(current_qty), step=1, key=f"inv_{skill}", 
                                label_visibility="collapsed"
                            )
                            new_values[skill] = val
                            st.write("") 

            st.divider()
            col_submit, col_info = st.columns([1, 3])
            with col_submit:
                submitted = st.form_submit_button("💾 CẬP NHẬT KHO", type="primary", use_container_width=True)
            with col_info:
                st.caption("💡 Bạn đang chỉnh sửa kho **" + ("THỦ MÔN" if is_gk_mode else "CẦU THỦ") + "**. Hãy kiểm tra kỹ trước khi lưu.")

        # --- 6. SAVE LOGIC ---
        if submitted:
            has_changes = False
            final_inventory = {}
            for skill, new_qty in new_values.items():
                old_qty = inventory.get(skill, 0)
                if new_qty != old_qty: has_changes = True
                if new_qty > 0: final_inventory[skill] = int(new_qty)
            
            # Với GK, giữ nguyên các key bằng 0 để đảm bảo list priority luôn đủ
            if is_gk_mode:
                for k in GK_SKILLS_PRIORITY_LIST:
                    if k not in final_inventory: final_inventory[k] = 0

            if has_changes:
                with st.spinner("Đang lưu..."):
                    success = False
                    if is_gk_mode: success = save_gk_inventory_to_gsheet(final_inventory)
                    else: success = save_skill_inventory_to_gsheet(final_inventory)
                    
                    if success:
                        st.toast("✅ Đã lưu thành công!", icon="💾")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Lỗi khi lưu.")
            else:
                st.toast("⚠️ Không có thay đổi.", icon="ℹ️")


if __name__ == "__main__":
    main()