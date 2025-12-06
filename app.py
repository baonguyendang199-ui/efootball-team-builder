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

def render_efootball_card_html(player_data, width="100%"):
    """
    Tạo HTML Card (Compact Version - Đã sửa vị trí Badge).
    """
    p_name = player_data.get('Player', 'Unknown')
    rating = player_data.get('Rating', 0)
    pos = player_data.get('Position', '?')
    p_type = str(player_data.get('Type', 'NON-EPIC')).upper()
    action = str(player_data.get('Action', '')).upper()
    
    # Xử lý hình ảnh
    img_url = player_data.get('Image')
    if not img_url:
        pid = str(player_data.get('Player ID', '')).strip()
        if pid:
            img_url = f"https://pesdb.net/assets/img/card/f{pid}.png"
        else:
            img_url = "https://pesdb.net/assets/img/card/f0.png"

    # Màu sắc thẻ
    card_class = "std"
    bg_gradient = "linear-gradient(180deg, #172554 0%, #020617 100%)" # Blue-950 to Slate-950
    
    if "POTW" in p_type or "TRENDING" in p_type:
        card_class = "potw"
        bg_gradient = "linear-gradient(180deg, #581c87 0%, #2e1065 100%)" # Purple
    elif "EPIC" in p_type and "NON" not in p_type:
        card_class = "epic"
        bg_gradient = "linear-gradient(180deg, #713f12 0%, #451a03 100%)" # Amber/Bronze

    club = player_data.get('Club', '')
    
    # --- SỬA VỊ TRÍ BADGE TẠI ĐÂY ---
    # Dời xuống top:35px để tránh đè lên Position/Rating
    # Thêm chút xoay nhẹ (rotate) để trông giống sticker dán lên
    action_html = ""
    if "BÁN" in action:
        action_html = f'<div style="position:absolute; top:35px; right:5px; background:#ef4444; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:4px; z-index:4; box-shadow:0 1px 3px rgba(0,0,0,0.5); transform: rotate(5deg);">BÁN</div>'
    elif "GIỮ" in action:
        action_html = f'<div style="position:absolute; top:35px; right:5px; background:#22c55e; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:4px; z-index:4; box-shadow:0 1px 3px rgba(0,0,0,0.5); transform: rotate(-5deg);">GIỮ</div>'

    html = f"""
    <div class="e-card {card_class}" style="background: {bg_gradient}; width: {width};">
        {action_html}
        <div class="shine"></div>
        <div class="card-header">
            <div class="rating-box">{rating}</div>
            <div class="position-box">{pos}</div>
        </div>
        <img src="{img_url}" class="player-img" onerror="this.src='https://pesdb.net/assets/img/card/f0.png'">
        <div class="card-info">
            <div class="player-name" title="{p_name}">{p_name}</div>
            <div class="sub-info">
                <span style="opacity:0.9; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; max-width: 70%;">{club}</span>
                <span>{player_data.get('Nation', '')[:3].upper()}</span>
            </div>
        </div>
    </div>
    """
    return html

@st.dialog("Hồ sơ cầu thủ", width="large")
def show_player_modal(row):
    """
    Giao diện Scouting Profile - Đã sửa lỗi hiển thị HTML text.
    """
    
    # --- 1. CHUẨN BỊ DỮ LIỆU ---
    p_name = row.get('Player', 'Unknown')
    rating = row.get('Rating', 0)
    pos = row.get('Position', '?')
    style = row.get('Position Style', 'N/A')
    p_type = str(row.get('Player Type', 'Standard')).upper()
    club = row.get('Club', 'Unknown Club')
    nation = row.get('Nation', 'Unknown Nation')
    
    # Xử lý ảnh
    img_url = row.get('Player URL', '') 
    pid = str(row.get('Player ID', '')).strip()
    if not pid and img_url:
        m = re.search(r"(\d{14,})", str(img_url))
        pid = m.group(1) if m else ""
    real_img = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else "https://pesdb.net/assets/img/card/f0.png"

    # Theme Config
    if "POTW" in p_type or "TRENDING" in p_type:
        # Ưu tiên tím trước
        accent_color = "#D946EF" # Fuchsia
        badge_bg = "linear-gradient(135deg, #701a75 0%, #D946EF 100%)"
        shadow_color = "rgba(217, 70, 239, 0.4)"
    elif "EPIC" in p_type and "NON" not in p_type:
        # Chỉ vàng nếu là Epic và KHÔNG phải NON-EPIC
        accent_color = "#F59E0B" # Amber
        badge_bg = "linear-gradient(135deg, #78350f 0%, #F59E0B 100%)"
        shadow_color = "rgba(245, 158, 11, 0.4)"
    else:
        # Mặc định xanh (Non-Epic rơi vào đây)
        accent_color = "#3B82F6" # Blue
        badge_bg = "linear-gradient(135deg, #1e3a8a 0%, #3B82F6 100%)"
        shadow_color = "rgba(59, 130, 246, 0.4)"

    # Helper render thanh chỉ số (LƯU Ý: Phải viết sát lề để không bị lỗi indent)
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
            
        # QUAN TRỌNG: Dòng dưới không được thụt đầu dòng quá sâu
        return f"""<div style="margin-bottom: 8px;"><div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:2px; color:#cbd5e1;"><span>{label}</span><span style="color:{accent_color}; font-weight:600">{value_text}</span></div><div style="display:flex; width:100%;">{bars}</div></div>"""

    # --- 2. XỬ LÝ DANH SÁCH SKILLS ---
    base_skills = [s.strip() for s in str(row.get('Skills','')).split(',') if s.strip()]
    added_skills = [s.strip() for s in str(row.get('Added Skills','')).split(',') if s.strip()]
    
    skills_html = ""
    for s in base_skills:
        skills_html += f'<span class="pf-skill">{s}</span>'
    for s in added_skills:
        skills_html += f'<span class="pf-skill added" title="Added Skill">+{s}</span>'
    if not skills_html:
        skills_html = '<span style="color:#64748b; font-style:italic;">Chưa có kỹ năng</span>'

    # --- 3. RENDER HTML (QUAN TRỌNG: Viết sát lề trái tuyệt đối) ---
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

def get_inventory():
    """Get inventory (with cache)"""
    return get_inventory_from_gsheet()

def update_inventory_count(skill_name, delta):
    """Update skill count trực tiếp trên Google Sheets"""
    try:
        inventory = get_inventory()
        current = inventory.get(skill_name, 0)
        new_count = max(0, current + delta)
        
        if new_count == 0 and skill_name in inventory:
            del inventory[skill_name]
        else:
            inventory[skill_name] = new_count
        
        # Lưu lại Google Sheets
        if save_skill_inventory_to_gsheet(inventory):
            return new_count
        else:
            raise Exception("Không thể lưu inventory")
            
    except Exception as e:
        st.error(f"⚠️ Lỗi cập nhật {skill_name}: {e}")
        return -1

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
# BẮT ĐẦU CODE MỚI - AUTO BUILD (BƯỚC 1)
# ==========================================

FORMATIONS = {
    # =================================================================
    # 🔥 SƠ ĐỒ HIỆN ĐẠI & META (TRENDING NOW)
    # =================================================================
    # Man City (Pep) - Kiểm soát tuyệt đối, trung vệ dâng cao
    "3-2-4-1 (Box Midfield)":       ["GK", "CB", "CB", "CB", "DMF", "DMF", "AMF", "AMF", "LMF", "RMF", "CF"],
    # Leverkusen (Xabi Alonso) - Tấn công trung lộ cực mạnh
    "3-4-2-1 (Xabi Ball)":          ["GK", "CB", "CB", "CB", "LMF", "RMF", "CMF", "CMF", "AMF", "AMF", "CF"], 
    # Real Madrid (Ancelotti) - Biến thể Bellingham đá đỉnh kim cương
    "4-3-1-2 (Diamond)":            ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "AMF", "CF", "CF"],
    # Sơ đồ "Tam tấu" (2 CF + 1 SS) - Rất mạnh để spam ban bật
    "4-1-2-3 (2 CF, 1 SS)":         ["GK", "LB", "CB", "CB", "RB", "DMF", "AMF", "AMF", "SS", "CF", "CF"],

    # =================================================================
    # 🛡️ 4 HẬU VỆ - TIÊU CHUẨN (STANDARD BACK 4)
    # =================================================================
    # Cân bằng nhất, dùng cho mọi lối đá
    "4-2-1-3 (Standard)":           ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "AMF", "LWF", "RWF", "CF"],
    "4-3-3 (Holding)":              ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "LWF", "RWF", "CF"],
    "4-3-3 (Attack)":               ["GK", "LB", "CB", "CB", "RB", "DMF", "AMF", "AMF", "LWF", "RWF", "CF"],
    "4-3-3 (False 9)":              ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "LWF", "RWF", "SS"],

    # Sơ đồ quốc dân, phòng ngự chắc, công rộng
    "4-2-3-1 (Wide)":               ["GK", "LB", "CB", "CB", "RB", "DMF", "DMF", "AMF", "LMF", "RMF", "CF"],
    "4-2-3-1 (Control)":            ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "AMF", "LWF", "RWF", "CF"],

    # =================================================================
    # ⚔️ 4 HẬU VỆ - 2 TIỀN ĐẠO (TWO STRIKERS)
    # =================================================================
    # Cổ điển nhưng hiệu quả (Simeone style)
    "4-4-2 (Flat)":                 ["GK", "LB", "CB", "CB", "RB", "LMF", "RMF", "CMF", "CMF", "CF", "CF"],
    # Tấn công tổng lực (Gegenpressing)
    "4-2-4 (Pressing)":             ["GK", "LB", "CB", "CB", "RB", "CMF", "CMF", "LWF", "RWF", "CF", "CF"],
    "4-2-2-2 (Magic Box)":          ["GK", "LB", "CB", "CB", "RB", "DMF", "DMF", "AMF", "AMF", "CF", "CF"],
    
    # =================================================================
    # 🛡️ 3 HẬU VỆ - TẤN CÔNG BIÊN (BACK 3 ATTACK)
    # =================================================================
    # Conte/Tuchel style
    "3-4-3 (Standard)":             ["GK", "CB", "CB", "CB", "LMF", "RMF", "CMF", "CMF", "LWF", "RWF", "CF"],
    "3-5-2 (Possession)":           ["GK", "CB", "CB", "CB", "LMF", "RMF", "DMF", "CMF", "AMF", "CF", "CF"],
    "3-4-1-2 (Classic)":            ["GK", "CB", "CB", "CB", "LMF", "RMF", "CMF", "CMF", "AMF", "CF", "CF"],

    # =================================================================
    # 🧱 5 HẬU VỆ - PHÒNG NGỰ PHẢN CÔNG (DEFENSIVE/COUNTER)
    # =================================================================
    # Đổ bê tông (Parking Bus)
    "5-4-1 (Low Block)":            ["GK", "LB", "CB", "CB", "CB", "RB", "LMF", "RMF", "DMF", "CMF", "CF"],
    # Phản công nhanh (Meta 3 tiền đạo cắm)
    "5-2-3 (Counter)":              ["GK", "LB", "CB", "CB", "CB", "RB", "DMF", "DMF", "LWF", "RWF", "CF"],
    "5-3-2 (Solid)":                ["GK", "LB", "CB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "CF", "CF"],

    # =================================================================
    # 🎄 SƠ ĐỒ ĐẶC BIỆT (SPECIAL TACTICS)
    # =================================================================
    "4-3-2-1 (Christmas Tree)":     ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "AMF", "AMF", "CF"],
    "4-1-4-1 (Solid Mid)":          ["GK", "LB", "CB", "CB", "RB", "DMF", "LMF", "RMF", "CMF", "CMF", "CF"],
}

# ==========================================
# CẬP NHẬT LOGIC AUTO BUILD (BƯỚC 1)
# ==========================================

# 2. Hàm xử lý logic chọn cầu thủ (Đã nâng cấp)
# ==========================================
# CẬP NHẬT LOGIC: BEST XI + 12 SUBS (BƯỚC 1)
# ==========================================

# ==========================================
# CẬP NHẬT LOGIC: TỐI ƯU HÓA TOÀN CỤC (GLOBAL OPTIMIZER)
# ==========================================

def auto_build_squad(df, formation_name, sort_mode='rating_desc', filter_col=None, filter_val=None):
    pool_df = df.copy()
    
    # 1. Chuẩn hóa dữ liệu số để tính toán
    if 'Height' in pool_df.columns: 
        pool_df['Height_num'] = pd.to_numeric(pool_df['Height'], errors='coerce').fillna(0)
    if 'Weight' in pool_df.columns: 
        pool_df['Weight_num'] = pd.to_numeric(pool_df['Weight'], errors='coerce').fillna(0)
    if 'Age' in pool_df.columns: 
        pool_df['Age_num'] = pd.to_numeric(pool_df['Age'], errors='coerce').fillna(99)
    
    # Chuẩn hóa Vị trí phụ
    if 'Secondary Positions' not in pool_df.columns:
        pool_df['Secondary Positions'] = ""
    else:
        pool_df['Secondary Positions'] = pool_df['Secondary Positions'].fillna("").astype(str).str.upper()

    # 2. Lọc dữ liệu (Team/League...)
    if filter_col and filter_val and filter_val != "(Tất cả)":
        pool_df = pool_df[pool_df[filter_col].astype(str) == filter_val]
        
    if pool_df.empty: return []

    # 3. Xác định điểm số (Score) cho từng cầu thủ dựa trên tiêu chí
    # Mục tiêu: Người có Score cao nhất sẽ được ưu tiên xếp vào đội hình
    def calculate_score(row):
        # 1. THE TANKS (BMI CAO)
        if sort_mode == 'bmi_desc':
            h_m = row['Height_num'] / 100.0
            if h_m > 0:
                bmi = row['Weight_num'] / (h_m ** 2)
                return bmi
            return 0
            
        # 2. THE AGILES (BMI THẤP)
        elif sort_mode == 'bmi_asc':
            h_m = row['Height_num'] / 100.0
            if h_m > 0:
                bmi = row['Weight_num'] / (h_m ** 2)
                return -bmi # Âm để sort giảm dần ra số bé nhất
            return -999

        # 3. THE AMBIDEXTROUS (2 CHÂN NHƯ 1) - PHÂN TẦNG
        elif sort_mode == 'ambidextrous':
            u_str = str(row.get('Weak Foot Usage', '')).strip().lower()
            a_str = str(row.get('Weak Foot Accuracy', '')).strip().lower()
            
            # --- TIER 1: HOÀN HẢO (Regularly + Very High) ---
            is_usage_perfect = 'regularly' in u_str or '4' in u_str
            is_acc_perfect = 'very high' in a_str or '4' in a_str
            
            if is_usage_perfect and is_acc_perfect:
                return 20000 + row['Rating'] # Ưu tiên cao nhất
            
            # --- TIER 2: KHÁ TỐT (Tối thiểu Occasionally + High) ---
            # Chấp nhận: Regularly hoặc Occasionally
            is_usage_good = is_usage_perfect or 'occasionally' in u_str or '3' in u_str
            # Chấp nhận: Very High hoặc High
            is_acc_good = is_acc_perfect or 'high' in a_str or '3' in a_str
            
            if is_usage_good and is_acc_good:
                return 10000 + row['Rating'] # Ưu tiên nhì (thay thế cho Rating thuần túy)
                
            # --- TIER 3: CÒN LẠI ---
            return row['Rating']

        # 4. FORM IS TEMPORARY (FULL POTW)
        elif sort_mode == 'potw_only':
            ptype = str(row.get('Player Type', '')).upper()
            if 'POTW' in ptype or 'TRENDING' in ptype:
                return 10000 + row['Rating']
            return row['Rating'] # POTW lên đầu, còn lại xếp dưới

        # 5. UNITED NATIONS (RATING CAO NHẤT)
        elif sort_mode == 'united_nations':
            # Vẫn dùng Rating để chọn người giỏi nhất của quốc gia đó
            return row['Rating'] + (0.1 if row['Epic_Priority'] == 0 else 0)

        # CÁC CHẾ ĐỘ CŨ (GIỮ NGUYÊN)
        elif sort_mode == 'rating_desc': return row['Rating'] + (0.1 if row['Epic_Priority'] == 0 else 0)
        elif sort_mode == 'height_desc': return row['Height_num']
        elif sort_mode == 'height_asc': return -row['Height_num']
        elif sort_mode == 'weight_desc': return row['Weight_num']
        elif sort_mode == 'weight_asc': return -row['Weight_num']
        elif sort_mode == 'age_desc': return row['Age_num']
        elif sort_mode == 'age_asc': return -row['Age_num']
        
        return row['Rating']

    # Tính Score
    pool_df['Build_Score'] = pool_df.apply(calculate_score, axis=1)

    # -------------------------------------------------------
    # THUẬT TOÁN TỐI ƯU HÓA (GREEDY GLOBAL OPTIMIZATION)
    # Thay vì tìm từng vị trí, ta tạo ra tất cả các cặp (Cầu thủ, Vị trí có thể đá)
    # Sau đó sort toàn bộ danh sách này để chọn ra phương án tốt nhất.
    # -------------------------------------------------------
    
    required_positions = FORMATIONS.get(formation_name, [])
    potential_assignments = []

    # Bước A: Tạo danh sách tất cả các ứng viên cho từng vị trí trong sơ đồ
    for slot_index, pos_req in enumerate(required_positions):
        # Tìm cầu thủ đá được vị trí này (Cả Chính và Phụ)
        # Logic: (Vị trí chính == pos_req) HOẶC (Vị trí phụ chứa pos_req)
        candidates = pool_df[
            (pool_df['Position'] == pos_req) | 
            (pool_df['Secondary Positions'].str.contains(fr'\b{pos_req}\b', regex=True))
        ]
        
        for idx, row in candidates.iterrows():
            potential_assignments.append({
                'score': row['Build_Score'],
                'player_idx': idx,
                'slot_index': slot_index,
                'pos_req': pos_req,
                'data': row,
                'nation': str(row.get('Nation', '')).strip() # Lấy quốc tịch để dùng cho mode United Nations
            })

    # Bước B: Sắp xếp toàn bộ khả năng từ Tốt nhất -> Tệ nhất
    # Ví dụ: Nếu chọn Tallest, cầu thủ 2m02 sẽ đứng đầu danh sách, bất kể đá vị trí nào
    potential_assignments.sort(key=lambda x: x['score'], reverse=True)

    # Bước C: Xếp đội hình (Starting XI)
    final_squad = [None] * 11
    used_indices = set()
    used_nations = set() # 🆕 Set theo dõi quốc gia đã dùng
    
    for assign in potential_assignments:
        p_idx = assign['player_idx']
        s_idx = assign['slot_index']
        p_nation = assign['nation']
        
        # Kiểm tra cơ bản: Cầu thủ chưa dùng & Slot trống
        if p_idx not in used_indices and final_squad[s_idx] is None:
            
            # 🆕 LOGIC ĐẶC BIỆT CHO UNITED NATIONS
            if sort_mode == 'united_nations':
                if p_nation in used_nations and p_nation != "":
                    continue # Bỏ qua nếu quốc gia này đã có người trong đội hình
            
            # Nếu thỏa mãn thì chọn
            row = assign['data']
            
            # Lấy ảnh
            pid = str(row.get('Player ID', '')).strip()
            purl = str(row.get('Player URL', '')).strip()
            if not pid and purl:
                m = re.search(r"(\d{14,})", purl)
                pid = m.group(1) if m else ""
            img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else None

            # Tạo object cầu thủ
            player_obj = {
                "Is_Starter": True,
                "Position": assign['pos_req'], # Vị trí trong sơ đồ
                "Real_Position": row['Position'], # Vị trí gốc
                "Player": row['Player'],
                "Rating": row['Rating'],
                "Type": row['Player Type'],
                "Club": row['Club'],
                "Nation": row['Nation'],
                "Height": row.get('Height', ''),
                "Weight": row.get('Weight', ''),
                "Age": row.get('Age', ''),
                "Image": img_url,
                "Data": row
            }
            
            final_squad[s_idx] = player_obj
            used_indices.add(p_idx)
            if p_nation: used_nations.add(p_nation) # Đánh dấu quốc gia đã dùng

    # Bước D: Điền nốt những vị trí còn thiếu (nếu không tìm được ai phù hợp)
    for i in range(11):
        if final_squad[i] is None:
             final_squad[i] = {
                "Is_Starter": True, 
                "Position": required_positions[i], 
                "Player": "---", 
                "Rating": 0, 
                "Type": "N/A", 
                "Image": None
            }

    # -------------------------------------------------------
    # PHASE 2: CHỌN DỰ BỊ (12 NGƯỜI TỐT NHẤT CÒN LẠI)
    # Không quan tâm vị trí, chỉ quan tâm chỉ số (Score)
    # -------------------------------------------------------
    
    # Lấy pool còn lại
    remaining_pool = pool_df[~pool_df.index.isin(used_indices)]
    remaining_pool = remaining_pool.sort_values('Build_Score', ascending=False)
    
    bench_picks_rows = []

    # =========================================================
    # 🆕 LOGIC DỰ BỊ CHO UNITED NATIONS (23 QUỐC GIA KHÁC NHAU)
    # =========================================================
    if sort_mode == 'united_nations':
        # Bước 1: Cố gắng tìm 12 cầu thủ có quốc tịch KHÁC với 11 người đá chính (và khác nhau)
        for idx, row in remaining_pool.iterrows():
            if len(bench_picks_rows) >= 12:
                break
            
            p_nation = str(row.get('Nation', '')).strip()
            
            # Chỉ chọn nếu quốc gia này CHƯA TỪNG xuất hiện trong danh sách đã dùng (used_nations)
            if p_nation and p_nation not in used_nations:
                bench_picks_rows.append(row)
                used_nations.add(p_nation) # Đánh dấu quốc gia này đã bị chiếm
                used_indices.add(idx)      # Đánh dấu cầu thủ này đã được chọn

        # Bước 2: Nếu database không đủ 23 quốc gia khác nhau, 
        # lấp đầy các slot còn thiếu bằng những cầu thủ giỏi nhất còn lại (chấp nhận trùng)
        if len(bench_picks_rows) < 12:
            needed = 12 - len(bench_picks_rows)
            # Lấy pool mới đã trừ đi những người vừa chọn ở Bước 1
            final_fillers = pool_df[~pool_df.index.isin(used_indices)].sort_values('Build_Score', ascending=False)
            fillers = final_fillers.head(needed)
            for _, row in fillers.iterrows():
                bench_picks_rows.append(row)
                
    else:
        # =========================================================
        # LOGIC CŨ CHO CÁC CHẾ ĐỘ KHÁC (Rating, BMI, v.v.)
        # =========================================================
        # Lấy top 12 người điểm cao nhất bất kể quốc tịch
        temp_picks = remaining_pool.head(12)
        for _, row in temp_picks.iterrows():
            bench_picks_rows.append(row)

    # =========================================================
    # CHUYỂN DỮ LIỆU THÀNH FORMAT SQUAD (Giữ nguyên logic cũ)
    # =========================================================
    for row in bench_picks_rows:
        pid = str(row.get('Player ID', '')).strip()
        purl = str(row.get('Player URL', '')).strip()
        if not pid and purl:
            m = re.search(r"(\d{14,})", purl)
            pid = m.group(1) if m else ""
        img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else None

        final_squad.append({
            "Is_Starter": False,
            "Position": row['Position'],
            "Real_Position": row['Position'],
            "Player": row['Player'],
            "Rating": row['Rating'],
            "Type": row['Player Type'],
            "Club": row['Club'],
            "Nation": row['Nation'],
            "Height": row.get('Height', ''),
            "Weight": row.get('Weight', ''),
            "Age": row.get('Age', ''),
            "Image": img_url,
            "Data": row
        })

    return final_squad

def find_best_formation_for_team(df, sort_mode, filter_col, filter_val):
    """
    Tìm sơ đồ tối ưu dựa trên tiêu chí (Sort Mode).
    - Nếu sort theo Rating: Ưu tiên Rating cao + Có DMF.
    - Nếu sort theo Chiều cao: Ưu tiên Tổng chiều cao lớn nhất (Bất chấp vị trí).
    - Nếu sort theo Tuổi: Ưu tiên Tổng tuổi lớn nhất/nhỏ nhất.
    """
    best_score = -float('inf') # Điểm thấp vô cùng
    best_squad = []
    best_formation_name = ""

    # Helper: Lấy giá trị số từ chuỗi (vd: "194cm" -> 194.0)
    def get_numeric_value(player_data, key):
        try:
            val_str = str(player_data.get(key, 0))
            return float(re.sub(r'[^\d.]', '', val_str))
        except:
            return 0

    # Quét qua toàn bộ sơ đồ
    for form_name in FORMATIONS.keys():
        # Build thử đội hình
        squad = auto_build_squad(df, form_name, sort_mode, filter_col, filter_val)
        
        # Chỉ lấy 11 người ĐÁ CHÍNH để tính điểm
        starters = [p for p in squad if p.get('Is_Starter', False)]
        
        # Đếm số người thực (không phải "---")
        valid_starters = [p for p in starters if p['Rating'] > 0]
        count_valid = len(valid_starters)
        
        # Phạt nặng nếu thiếu người
        if len(valid_starters) < 11:
            current_score = -10000000 
        else:
            # =========================================
            # 🆕 LOGIC TÍNH ĐIỂM SƠ ĐỒ MỚI
            # =========================================
            
            # 1. BMI (Tanks / Agiles)
            if 'bmi' in sort_mode:
                total_bmi = 0
                for p in valid_starters:
                    h = get_numeric_value(p, 'Height') / 100.0
                    w = get_numeric_value(p, 'Weight')
                    if h > 0: total_bmi += (w / (h**2))
                
                if sort_mode == 'bmi_desc': current_score = total_bmi
                else: current_score = -total_bmi

            # 2. Ambidextrous (2 chân như 1)
            elif sort_mode == 'ambidextrous':
                score_bonus = 0
                total_rating = 0
                
                for p in valid_starters:
                    data = p.get('Data', {})
                    u_str = str(data.get('Weak Foot Usage', '')).strip().lower()
                    a_str = str(data.get('Weak Foot Accuracy', '')).strip().lower()
                    
                    # Check Tier 1
                    is_usage_perfect = 'regularly' in u_str or '4' in u_str
                    is_acc_perfect = 'very high' in a_str or '4' in a_str
                    
                    # Check Tier 2
                    is_usage_good = is_usage_perfect or 'occasionally' in u_str or '3' in u_str
                    is_acc_good = is_acc_perfect or 'high' in a_str or '3' in a_str

                    if is_usage_perfect and is_acc_perfect:
                        score_bonus += 20000 # Điểm thưởng lớn
                    elif is_usage_good and is_acc_good:
                        score_bonus += 10000 # Điểm thưởng vừa
                        
                    total_rating += p['Rating']
                
                current_score = score_bonus + total_rating

            # 3. POTW Only
            elif sort_mode == 'potw_only':
                count_potw = 0
                total_rating = 0
                for p in valid_starters:
                    if 'POTW' in str(p['Type']).upper() or 'TRENDING' in str(p['Type']).upper():
                        count_potw += 1
                    total_rating += p['Rating']
                current_score = (count_potw * 10000) + total_rating

            # 4. United Nations
            elif sort_mode == 'united_nations':
                # Đếm số quốc gia duy nhất
                unique_nations = set(p['Nation'] for p in valid_starters if p['Nation'])
                total_rating = sum(p['Rating'] for p in valid_starters)
                
                # Ưu tiên sơ đồ nào xếp được nhiều quốc gia nhất
                current_score = (len(unique_nations) * 100000) + total_rating
            
            # 1. CASE: RATING (MẶC ĐỊNH)
            if sort_mode == 'rating_desc':
                # Cộng tổng Rating
                current_score = sum(p['Rating'] for p in valid_starters)
                
                # Ưu tiên DMF (Chỉ áp dụng khi build đội hình mạnh nhất)
                has_dmf = any(p['Position'] == 'DMF' for p in valid_starters)
                needs_dmf = "DMF" in FORMATIONS[form_name]
                if has_dmf: current_score += 50000 # Bonus cực lớn cho đội có DMF
                elif needs_dmf: current_score -= 20000 # Phạt nếu cần DMF mà không có
            
            # 2. CASE: CHIỀU CAO (TALLEST / SHORTEST)
            elif 'height' in sort_mode:
                total_height = sum(get_numeric_value(p, 'Height') for p in valid_starters)
                
                if sort_mode == 'height_desc': # Tallest
                    current_score = total_height 
                else: # Shortest (Ưu tiên chiều cao thấp -> Điểm càng thấp càng tốt -> Lấy âm)
                    current_score = -total_height 

            # 3. CASE: CÂN NẶNG (HEAVIEST / LIGHTEST)
            elif 'weight' in sort_mode:
                total_weight = sum(get_numeric_value(p, 'Weight') for p in valid_starters)
                
                if sort_mode == 'weight_desc': 
                    current_score = total_weight
                else: 
                    current_score = -total_weight

            # 4. CASE: TUỔI (OLDEST / YOUNGEST)
            elif 'age' in sort_mode:
                total_age = sum(get_numeric_value(p, 'Age') for p in valid_starters)
                
                if sort_mode == 'age_desc': # Oldest
                    current_score = total_age
                else: # Youngest
                    current_score = -total_age

        # So sánh và cập nhật Best Team
        if current_score > best_score:
            best_score = current_score
            best_squad = squad
            best_formation_name = form_name
            
    return best_formation_name, best_squad

def render_pitch_view(squad_list, highlight_type=None):
    """
    Vẽ sơ đồ sân bóng với Tooltip thông minh.
    - highlight_type: 'Age', 'Height', 'Weight' hoặc None.
    - Khi hover vào thẻ, sẽ hiện thông số tương ứng.
    """
    import streamlit.components.v1 as components
    
    # 1. Định nghĩa độ sâu
    DEPTH_MAP = {
        'CF': 12, 'SS': 20, 'LWF': 20, 'RWF': 20,
        'AMF': 32, 'LMF': 45, 'RMF': 45, 
        'CMF': 50, 'DMF': 60,
        'LB': 75, 'RB': 75, 'CB': 82, 'GK': 93
    }

    # 2. Phân nhóm
    starters_list = [p for p in squad_list if p.get('Is_Starter', False)]
    groups = {p['Position']: [] for p in starters_list}
    for p in starters_list:
        groups[p['Position']].append(p)

    final_cards_html = ""
    LEFT_SIDE = ['LWF', 'LMF', 'LB']
    RIGHT_SIDE = ['RWF', 'RMF', 'RB']

    for pos, players in groups.items():
        count = len(players)
        if count == 0: continue
        top = DEPTH_MAP.get(pos, 50)
        
        for i, p in enumerate(players):
            left = 50 
            if pos in LEFT_SIDE: left = 15
            elif pos in RIGHT_SIDE: left = 85
            else:
                is_midfield_duo = (pos == 'DMF' and len(groups.get('CMF', [])) == 1) or \
                                  (pos == 'CMF' and len(groups.get('DMF', [])) == 1)
                
                if is_midfield_duo and count == 1:
                    if pos == 'DMF': left = 40
                    if pos == 'CMF': left = 60
                elif count == 1: left = 50
                elif count == 2: left = 35 if i == 0 else 65
                elif count == 3: left = 30 if i == 0 else (50 if i == 1 else 70)
                elif count == 4: left = 20 + (i * 20)

            # --- XỬ LÝ TOOLTIP (HOVER INFO) ---
            # --- XỬ LÝ TOOLTIP (HOVER INFO) - ĐÃ CẬP NHẬT ---
            tooltip_text = f"{p['Player']} | Rating: {p['Rating']}" # Mặc định
            
            # Lấy dữ liệu gốc để tra cứu các chỉ số sâu hơn
            p_data = p.get('Data', {})
            
            if highlight_type == 'Height':
                tooltip_text = f"{p['Player']}\nChiều cao: {p.get('Height', '?')} cm"
            
            elif highlight_type == 'Weight':
                tooltip_text = f"{p['Player']}\nCân nặng: {p.get('Weight', '?')} kg"
            
            elif highlight_type == 'Age':
                tooltip_text = f"{p['Player']}\nTuổi: {p.get('Age', '?')}"
            
            elif highlight_type == 'BMI':
                try:
                    # Lấy số từ chuỗi (vd: "185" hoặc "185cm")
                    h_str = str(p.get('Height', '0'))
                    w_str = str(p.get('Weight', '0'))
                    h = float(re.sub(r'[^\d.]', '', h_str)) / 100.0
                    w = float(re.sub(r'[^\d.]', '', w_str))
                    
                    if h > 0:
                        bmi = w / (h**2)
                        tooltip_text = f"{p['Player']}\nBMI: {bmi:.1f} ({w}kg / {int(h*100)}cm)"
                    else:
                        tooltip_text = f"{p['Player']}\nBMI: ?"
                except:
                    tooltip_text = f"{p['Player']}\nBMI: Lỗi dữ liệu"
            
            elif highlight_type == 'Ambidextrous':
                usage = str(p_data.get('Weak Foot Usage', '?'))
                acc = str(p_data.get('Weak Foot Accuracy', '?'))
                tooltip_text = f"{p['Player']}\nWF Usage: {usage}\nWF Accuracy: {acc}"

            elif highlight_type == 'Nation':
                tooltip_text = f"{p['Player']}\nQuốc tịch: {p.get('Nation', '?')}"

            elif highlight_type == 'Type':
                tooltip_text = f"{p['Player']}\nLoại thẻ: {p.get('Type', '?')}"
            
            # --- RENDER HTML ---
            player_name = p['Player']
            if player_name == "---":
                card_html = f"""<div style="position: absolute; top: {top}%; left: {left}%; transform: translate(-50%, -50%); width: 70px; height: 90px; background: rgba(255,255,255,0.05); border-radius: 6px; border: 1px dashed #666; display: flex; align-items: center; justify-content: center; color: #888; font-size: 10px; z-index: 5;"><div style="text-align:center;">{pos}<br>Trống</div></div>"""
            else:
                ptype = str(p['Type']).upper()
                border_color = "#f59e0b" if "EPIC" in ptype else ("#a855f7" if "POTW" in ptype else "#3b82f6")
                img_src = p['Image']
                img_tag = f"""<img src='{img_src}' style='width:48px;height:auto;margin-bottom:3px;display:block;' onerror="this.onerror=null;this.src='https://pesdb.net/assets/img/card/f0.png';this.style.display='none';this.nextElementSibling.style.display='block';"><div style='font-size:24px;margin-bottom:3px;display:none;'>👤</div>""" if img_src else "<div style='font-size:24px;margin-bottom:3px;'>👤</div>"
                
                # Thêm thuộc tính title="{tooltip_text}" vào thẻ div bao ngoài
                card_html = f"""
                <div title="{tooltip_text}" style="position: absolute; top: {top}%; left: {left}%; transform: translate(-50%, -50%); width: 85px; padding: 4px 2px; display: flex; flex-direction: column; align-items: center; background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(10, 15, 30, 0.98) 100%); border: 1px solid {border_color}; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); z-index: 10; cursor: pointer; transition: all 0.2s ease;" onmouseover="this.style.transform='translate(-50%, -50%) scale(1.15)'; this.style.zIndex='100';" onmouseout="this.style.transform='translate(-50%, -50%) scale(1)'; this.style.zIndex='10';">
                    {img_tag}
                    <div style="font-family: 'Segoe UI', sans-serif; font-size: 10px; font-weight: 700; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 95%; text-align: center; text-shadow: 1px 1px 2px black; margin-bottom: 2px;">{player_name}</div>
                    <div style="display:flex; gap:3px; align-items:center;">
                        <div style="font-family: sans-serif; font-size: 9px; font-weight:bold; color: #cbd5e1; background: rgba(255,255,255,0.1); padding: 1px 4px; border-radius: 3px;">{pos}</div>
                        <div style="font-family: sans-serif; font-size: 10px; font-weight:bold; color: {border_color};">{p['Rating']}</div>
                    </div>
                </div>"""
            final_cards_html += card_html

    css = """<style>body { margin: 0; padding: 0; background: transparent; overflow: hidden; } .pitch-container { position: relative; width: 100%; height: 750px; background: linear-gradient(180deg, #1e5631 0%, #14532d 40%, #064e3b 100%); border: 2px solid rgba(255,255,255,0.7); border-radius: 12px; box-shadow: inset 0 0 60px rgba(0,0,0,0.5); } .grass-pattern { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: repeating-linear-gradient(0deg, transparent, transparent 50px, rgba(0,0,0,0.08) 50px, rgba(0,0,0,0.08) 100px); z-index: 1; pointer-events: none; } .lines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; } .line { position: absolute; background: rgba(255,255,255,0.4); } .border-line { position: absolute; border: 2px solid rgba(255,255,255,0.4); } .center-line { top: 50%; left: 0; width: 100%; height: 2px; } .center-circle { top: 50%; left: 50%; width: 120px; height: 120px; border-radius: 50%; transform: translate(-50%, -50%); } .center-dot { top: 50%; left: 50%; width: 6px; height: 6px; background: rgba(255,255,255,0.6); border-radius: 50%; transform: translate(-50%, -50%); } .box-top { top: 0; left: 50%; width: 45%; height: 15%; border-top: none; transform: translateX(-50%); } .box-bottom { bottom: 0; left: 50%; width: 45%; height: 15%; border-bottom: none; transform: translateX(-50%); } .goal-top { top: 0; left: 50%; width: 20%; height: 5%; border-top: none; transform: translateX(-50%); } .goal-bottom { bottom: 0; left: 50%; width: 20%; height: 5%; border-bottom: none; transform: translateX(-50%); }</style>"""
    html_content = f"""<!DOCTYPE html><html><head>{css}</head><body><div class="pitch-container"><div class="grass-pattern"></div><div class="lines"><div class="line center-line"></div><div class="border-line center-circle"></div><div class="line center-dot"></div><div class="border-line box-top"></div><div class="border-line box-bottom"></div><div class="border-line goal-top"></div><div class="border-line goal-bottom"></div></div>{final_cards_html}</div></body></html>"""
    components.html(html_content, height=760, scrolling=False)

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
    Loại bỏ vị trí chính khỏi danh sách.
    FIX: Nếu vị trí chính là GK thì trả về rỗng ngay lập tức.
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
            for c in classes:
                c_upper = c.upper()
                # Nếu là mã vị trí VÀ không trùng với vị trí chính
                if c_upper in VALID_POS and c_upper != main_pos_norm:
                    found_pos.add(c_upper)
                    
        # Trả về chuỗi sắp xếp, ví dụ: "CF, CMF, LWF, RWF, SS"
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
    Đồng bộ dữ liệu PESDB (Smart Sync).
    CHỈ QUÉT những cầu thủ còn thiếu thông tin (Vị trí phụ, Skills, Chiều cao...).
    Bỏ qua những người đã có đủ dữ liệu để tiết kiệm thời gian.
    """
    if df.empty or 'Player URL' not in df.columns:
        st.info("ℹ️ Không có dữ liệu hoặc thiếu cột Player URL.")
        return df

    # Đảm bảo cột tồn tại
    if 'Secondary Positions' not in df.columns:
        df['Secondary Positions'] = ""

    # --- BỘ LỌC THÔNG MINH ---
    # 1. Có URL hợp lệ
    has_url = df['Player URL'].astype(str).str.startswith('http')
    
    # 2. Kiểm tra các trường còn thiếu (Trống hoặc NaN)
    missing_sec_pos = df['Secondary Positions'].astype(str).str.strip() == ''
    missing_skills = df['Skills'].astype(str).str.strip() == ''
    missing_height = df['Height'].astype(str).str.strip() == ''
    
    # 3. Lọc ra danh sách cần cập nhật: Có URL VÀ (Thiếu Vị trí phụ HOẶC Thiếu Skills HOẶC Thiếu Chiều cao)
    needs_extraction = df[has_url & (missing_sec_pos | missing_skills | missing_height)]

    total_to_process = len(needs_extraction)
    total_players = len(df)

    if total_to_process == 0:
        st.success(f"✅ Dữ liệu đã đầy đủ! (Đã kiểm tra {total_players} cầu thủ). Không cần quét thêm.")
        return df

    st.info(f"🔍 Phát hiện **{total_to_process}** cầu thủ thiếu dữ liệu (Vị trí phụ/Skills...). Bắt đầu cập nhật...")
    
    st.session_state['auto_extracting'] = True
    updated = False

    progress_bar = st.progress(0, text=f"🚀 Đang chuẩn bị...")
    status_box = st.empty()

    # Biến đếm
    count = 0

    # Chỉ duyệt qua những dòng cần cập nhật
    for i, row in needs_extraction.iterrows():
        count += 1
        player_name = str(row.get('Player', '') or '').strip()
        
        # Cập nhật thanh tiến trình
        percent = int((count / total_to_process) * 100)
        status_box.info(f"📡 [{count}/{total_to_process}] Đang cập nhật: **{player_name}**")
        progress_bar.progress(percent, text=f"Đang xử lý {percent}%")

        try:
            info = extract_full_player_info(row['Player URL'])
            
            if info and info.get('Player'):
                # Ghi đè dữ liệu mới
                df.at[i, 'Secondary Positions'] = info.get('Secondary Positions', '')
                
                # Cập nhật các cột khác nếu đang thiếu
                for col in [
                    'Region', 'Height', 'Weight', 'Age', 'Foot',
                    'Weak Foot Usage', 'Weak Foot Accuracy', 'Form', 'Injury Resistance', 'Skills'
                ]:
                    current_val = str(df.at[i, col]).strip()
                    if not current_val or current_val == 'nan':
                        df.at[i, col] = info.get(col, '')
                
                updated = True
                
        except Exception as e:
            print(f"Lỗi {player_name}: {e}") # Log nhẹ, không làm phiền UI
            continue

    if updated:
        progress_bar.progress(1.0, text="✅ Đang lưu vào Google Sheets...")
        save_data_to_gsheet(df)
        st.cache_data.clear()
        status_box.success(f"✅ Đã cập nhật xong {total_to_process} cầu thủ!")
        time.sleep(2)
        status_box.empty()
        progress_bar.empty()
    
    st.session_state['auto_extracting'] = False
    return df


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
            # Load dữ liệu tạm để xử lý (tránh lỗi nếu df chưa được load ở main)
            df_sync = load_data_from_gsheet()
            
            with st.spinner("⏳ Đang kết nối máy chủ PESDB... Vui lòng không tắt tab."):
                # Chạy hàm quét (đã nâng cấp ở Bước 1)
                updated_df = sync_pesdb_missing_fields(df_sync)
                
                # Tạo file CSV backup
                csv = updated_df.to_csv(index=False).encode('utf-8-sig')
                
                st.success("✅ Cập nhật hoàn tất!")
                
                # Hiện nút tải về ngay lập tức
                st.download_button(
                    label="📥 Tải Backup (Excel/CSV)",
                    data=csv,
                    file_name=f"efootball_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_after_sync"
                )
            
            # Tắt trạng thái chạy để không lặp lại vòng lặp
            st.session_state.run_pesdb_sync = False
    
        st.divider()
    
        # 3. Menu điều hướng (Giữ nguyên)
        main_menu = st.radio(
            "📑 Điều hướng",
            ["📊 Tổng quan", "📈 Phân tích", "👥 Quản lý cầu thủ", "🎮 Quản lý Skills"],
            index=0
        )
    
        # Điều hướng chi tiết
        if main_menu == "📊 Tổng quan":
            st.session_state.current_tab = "overview"
        elif main_menu == "📈 Phân tích":
            st.session_state.current_tab = "analytics"
    
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

    if current_tab == 'overview':
        st.header("📊 Tổng quan")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Tổng cầu thủ", len(df))
        with c2:
            st.metric("Rating TB", f"{df['Rating'].mean():.1f}")
        with c3:
            st.metric("Epic", int((df['Player Type'].astype(str).str.upper() == 'EPIC').sum()))
        with c4:
            st.metric("POTW", int((df['Player Type'].astype(str).str.upper() == 'POTW').sum()))
        with c5:
            if 'Region' in df.columns:
                region_series = df['Region'].astype(str).str.strip()
                region_series = region_series[region_series.ne("")]
                region_count = int(region_series.nunique())
                st.metric("Region", region_count)
            else:
                st.metric("Region", 0)

        st.divider()

        import plotly.express as px
        
        # ⚽ Top 10 Clubs
        st.subheader("⚽ Top 10 Clubs")
        club_counts = df['Club'].value_counts().reset_index(name='Số lượng')
        club_counts.columns = ['Câu lạc bộ', 'Số lượng']
        club_counts = club_counts.head(10)
        
        fig_club = px.bar(
            club_counts,
            x="Câu lạc bộ",   # trục X là tên CLB
            y="Số lượng",     # trục Y là số lượng
            text="Số lượng"
        )
        fig_club.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
        fig_club.update_layout(
            xaxis=dict(categoryorder="total descending", autorange=True),
            yaxis=dict(autorange=True),
            dragmode="pan"
        )
        fig_club = apply_plotly_theme(fig_club)
        config = {
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "zoom2d", "zoomIn2d", "zoomOut2d",
                "autoScale2d", "resetScale2d",
                "select2d", "lasso2d"
            ],
            "displaylogo": False
        }
        st.plotly_chart(fig_club, use_container_width=True, config=config, key="overview_fig_club")
        
        st.divider()
        
        # 🌍 Top 10 Nations
        st.subheader("🌍 Top 10 Nations")
        nation_counts = df['Nation'].value_counts().reset_index(name='Số lượng')
        nation_counts.columns = ['Quốc gia', 'Số lượng']
        nation_counts = nation_counts.head(10)
        
        fig_nation = px.bar(
            nation_counts,
            x="Quốc gia",
            y="Số lượng",
            text="Số lượng"
        )
        fig_nation.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
        fig_nation.update_layout(
            xaxis=dict(categoryorder="total descending", autorange=True),
            yaxis=dict(autorange=True),
            dragmode="pan"
        )
        fig_nation = apply_plotly_theme(fig_nation)
        st.plotly_chart(fig_nation, use_container_width=True, config=config, key="overview_fig_nation")
        
        st.divider()
        
        # 🏆 Top 10 Leagues
        st.subheader("🏆 Top 10 Leagues")
        league_counts = df['League'].value_counts().reset_index(name='Số lượng')
        league_counts.columns = ['Giải đấu', 'Số lượng']
        league_counts = league_counts.head(10)
        
        fig_league = px.bar(
            league_counts,
            x="Giải đấu",
            y="Số lượng",
            text="Số lượng"
        )
        fig_league.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
        fig_league.update_layout(
            xaxis=dict(categoryorder="total descending", autorange=True),
            yaxis=dict(autorange=True),
            dragmode="pan"
        )
        fig_league = apply_plotly_theme(fig_league)
        st.plotly_chart(fig_league, use_container_width=True, config=config, key="overview_fig_league")
        
        st.divider()
        
        # 🌐 Top 10 Regions (nếu có dữ liệu)
        if 'Region' in df.columns:
            st.subheader("🌐 Top 10 Regions")
            region_counts = (
                df['Region']
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .value_counts()
                .reset_index(name='Số lượng')
            )
            if not region_counts.empty:
                region_counts.columns = ['Region', 'Số lượng']
                region_counts = region_counts.head(10)
                
                fig_region = px.bar(
                    region_counts,
                    x="Region",
                    y="Số lượng",
                    text="Số lượng"
                )
                fig_region.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                fig_region.update_layout(
                    xaxis=dict(categoryorder="total descending", autorange=True),
                    yaxis=dict(autorange=True),
                    dragmode="pan"
                )
                fig_region = apply_plotly_theme(fig_region)
                st.plotly_chart(fig_region, use_container_width=True, config=config, key="overview_fig_region")
                
                st.divider()
        
        # 🔥 Top 10 Most Needed Skills
        st.subheader("🔥 Top 10 Most Needed Skills")
        MAX_SKILLS_OV = 15
        MAX_ADDED_SKILLS_OV = 5
        
        skill_need_counts = {}
        
        for _, row in df.iterrows():
            position = str(row.get('Position', '')).strip()
            player_type_val = str(row.get('Player Type', '')).upper()
            
            # Bỏ qua POTW (không thể thêm skill) và vị trí không có priority
            if player_type_val == 'POTW' or position not in POSITION_SKILLS_PRIORITY:
                continue
            
            base = str(row.get('Skills', '')).strip()
            added = str(row.get('Added Skills', '')).strip()
            
            base_list = [s.strip() for s in base.split(',') if s.strip()] if base else []
            added_list = [s.strip() for s in added.split(',') if s.strip()] if added else []
            
            total_count = len(base_list) + len(added_list)
            remaining_slots = MAX_ADDED_SKILLS_OV - len(added_list)
            
            # Nếu đã full slot thêm hoặc đủ 15 skill thì không tính là "cần thêm"
            if total_count >= MAX_SKILLS_OV or remaining_slots <= 0:
                continue
            
            recs = get_recommended_skills(position, base, added, MAX_SKILLS_OV)
            if remaining_slots > 0:
                recs = recs[:remaining_slots]
            
            for skill in recs:
                if not skill:
                    continue
                skill_need_counts[skill] = skill_need_counts.get(skill, 0) + 1
        
        if skill_need_counts:
            skills_df = (
                pd.DataFrame(
                    [{'Skill': k, 'Số cầu thủ': v} for k, v in skill_need_counts.items()]
                )
                .sort_values('Số cầu thủ', ascending=False)
                .head(10)
            )
            
            fig_skill = px.bar(
                skills_df,
                x="Skill",
                y="Số cầu thủ",
                text="Số cầu thủ"
            )
            fig_skill.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
            fig_skill.update_layout(
            xaxis=dict(categoryorder="total descending", autorange=True),
            yaxis=dict(autorange=True),
            dragmode="pan"
            )
            fig_skill = apply_plotly_theme(fig_skill)
            st.plotly_chart(fig_skill, use_container_width=True, config=config, key="overview_fig_skill")
        else:
            st.info("🎉 Hiện không có skill nào được gợi ý thêm cho cầu thủ.")
        
        st.divider()
        
        # 📍 Phân bố theo vị trí (Bar Chart)
        st.subheader("📍 Phân bố theo vị trí")
        pos_counts = df['Position'].value_counts().reset_index(name='Số lượng')
        pos_counts.columns = ['Vị trí', 'Số lượng']
        
        fig_pos = px.bar(
            pos_counts,
            x="Vị trí",
            y="Số lượng",
            text="Số lượng"
        )
        fig_pos.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
        fig_pos.update_layout(
        xaxis=dict(categoryorder="total descending", autorange=True),
        yaxis=dict(autorange=True),
        dragmode="pan"
        )
        fig_pos = apply_plotly_theme(fig_pos)
        st.plotly_chart(fig_pos, use_container_width=True, config=config, key="overview_fig_pos")
        
        st.divider()
        
        # 🏷️ Phân bố theo loại (Pie Chart)
        st.subheader("🏷️ Phân bố theo loại")
        type_counts = df['Player Type'].value_counts().reset_index(name='Số lượng')
        type_counts.columns = ['Loại', 'Số lượng']
        
        fig_type = px.pie(
            type_counts,
            names="Loại",
            values="Số lượng",
            hole=0.3
        )
        fig_type.update_traces(
            textinfo="percent+label",
            hoverinfo="skip",
            hovertemplate=None
        )
        fig_type.update_layout(dragmode="pan")
        fig_type = apply_plotly_theme(fig_type)
        st.plotly_chart(fig_type, use_container_width=True, config=config, key="overview_fig_type")
        
        st.divider()
        
        # 👣 Tỉ lệ chân thuận
        if 'Foot' in df.columns:
            st.subheader("👣 Tỉ lệ chân thuận")
            foot_counts = df['Foot'].value_counts().reset_index(name='Số lượng')
            foot_counts.columns = ['Chân thuận', 'Số lượng']
            
            # Tính tỉ lệ phần trăm
            total_foot = foot_counts['Số lượng'].sum()
            foot_counts['Tỉ lệ'] = (foot_counts['Số lượng'] / total_foot * 100).round(1)
            foot_counts['Hiển thị'] = foot_counts['Chân thuận'] + ' (' + foot_counts['Tỉ lệ'].astype(str) + '%)'
            
            fig_foot = px.pie(
                foot_counts,
                names="Chân thuận",
                values="Số lượng",
                hole=0.3,
                labels={'Chân thuận': 'Chân thuận', 'Số lượng': 'Số lượng'}
            )
            fig_foot.update_traces(
                textinfo="percent+label",
                hoverinfo="label+value+percent",
                hovertemplate="<b>%{label}</b><br>Số lượng: %{value}<br>Tỉ lệ: %{percent}<extra></extra>"
            )
            fig_foot.update_layout(dragmode="pan")
            fig_foot = apply_plotly_theme(fig_foot)
            st.plotly_chart(fig_foot, use_container_width=True, config=config, key="overview_fig_foot")
            
            st.divider()
        
        # 📊 Chiều cao trung bình theo vị trí
        if 'Height' in df.columns and 'Position' in df.columns:
            st.subheader("📊 Chiều cao trung bình theo vị trí")
            height_pos_df = df[df['Height'].astype(str).str.strip().ne('')].copy()
            height_pos_df['Height_num'] = pd.to_numeric(height_pos_df['Height'], errors='coerce')
            height_pos_df = height_pos_df.dropna(subset=['Height_num', 'Position'])
            
            if not height_pos_df.empty:
                avg_height_by_pos = height_pos_df.groupby('Position')['Height_num'].mean().sort_values(ascending=False).reset_index()
                avg_height_by_pos.columns = ['Vị trí', 'Chiều cao TB (cm)']
                avg_height_by_pos['Chiều cao TB (cm)'] = avg_height_by_pos['Chiều cao TB (cm)'].round(1)
                
                fig_avg_height = px.bar(
                    avg_height_by_pos,
                    x="Vị trí",
                    y="Chiều cao TB (cm)",
                    text="Chiều cao TB (cm)"
                )
                fig_avg_height.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                fig_avg_height.update_layout(
                    xaxis=dict(categoryorder="total descending", autorange=True),
                    yaxis=dict(autorange=True),
                    dragmode="pan"
                )
                fig_avg_height = apply_plotly_theme(fig_avg_height)
                st.plotly_chart(fig_avg_height, use_container_width=True, config=config, key="overview_fig_avg_height")
                
                st.divider()
        
        # ⚖️ Cân nặng trung bình theo vị trí
        if 'Weight' in df.columns and 'Position' in df.columns:
            st.subheader("⚖️ Cân nặng trung bình theo Vị trí")
            weight_pos_df = df[df['Weight'].astype(str).str.strip().ne('')].copy()
            weight_pos_df['Weight_num'] = pd.to_numeric(weight_pos_df['Weight'], errors='coerce')
            weight_pos_df = weight_pos_df.dropna(subset=['Weight_num', 'Position'])
            
            if not weight_pos_df.empty:
                # Group theo Position và tính trung bình
                avg_weight_by_pos = weight_pos_df.groupby('Position')['Weight_num'].mean().sort_values(ascending=False).reset_index()
                avg_weight_by_pos.columns = ['Vị trí', 'Cân nặng TB (kg)']
                avg_weight_by_pos['Cân nặng TB (kg)'] = avg_weight_by_pos['Cân nặng TB (kg)'].round(1)
                
                fig_avg_weight = px.bar(
                    avg_weight_by_pos,
                    x="Vị trí",
                    y="Cân nặng TB (kg)",
                    text="Cân nặng TB (kg)"
                )
                fig_avg_weight.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                fig_avg_weight.update_layout(
                    xaxis=dict(categoryorder="total descending", autorange=True),
                    yaxis=dict(autorange=True),
                    dragmode="pan"
                )
                fig_avg_weight = apply_plotly_theme(fig_avg_weight)
                st.plotly_chart(fig_avg_weight, use_container_width=True, config=config, key="overview_fig_avg_weight")
                
                st.divider()
        
        # 📊 Trung bình BMI theo vị trí
        if 'Height' in df.columns and 'Weight' in df.columns and 'Position' in df.columns:
            st.subheader("📊 Trung bình BMI theo Vị trí")
            
            # Lọc dữ liệu có height và weight
            bmi_df = df[df['Height'].astype(str).str.strip().ne('') & df['Weight'].astype(str).str.strip().ne('')].copy()
            bmi_df['Height_num'] = pd.to_numeric(bmi_df['Height'], errors='coerce')
            bmi_df['Weight_num'] = pd.to_numeric(bmi_df['Weight'], errors='coerce')
            
            # Loại bỏ dòng thiếu dữ liệu
            bmi_df = bmi_df.dropna(subset=['Height_num', 'Weight_num', 'Position'])
            
            if not bmi_df.empty:
                # Tính BMI: Cân nặng (kg) / (Chiều cao (m))^2
                bmi_df['BMI'] = bmi_df['Weight_num'] / ((bmi_df['Height_num'] / 100) ** 2)
                
                # Tính trung bình theo vị trí
                avg_bmi_pos = bmi_df.groupby('Position')['BMI'].mean().sort_values(ascending=False).reset_index()
                avg_bmi_pos.columns = ['Vị trí', 'BMI TB']
                avg_bmi_pos['BMI TB'] = avg_bmi_pos['BMI TB'].round(2)
                
                fig_bmi = px.bar(
                    avg_bmi_pos,
                    x="Vị trí",
                    y="BMI TB",
                    text="BMI TB",
                    color="BMI TB",  # Tô màu theo độ lớn BMI
                    color_continuous_scale='Viridis'
                )
                fig_bmi.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                fig_bmi.update_layout(
                    xaxis=dict(categoryorder="total descending", autorange=True),
                    yaxis=dict(autorange=True, title="BMI Trung bình"),
                    dragmode="pan",
                    coloraxis_showscale=False  # Ẩn thanh scale màu cho gọn
                )
                fig_bmi = apply_plotly_theme(fig_bmi)
                st.plotly_chart(fig_bmi, use_container_width=True, config=config, key="overview_fig_avg_bmi")
                
                st.divider()

    elif current_tab == 'analytics':
        st.header("📈 Phân tích chi tiết")
        
        import plotly.express as px
        
        config = {
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "zoom2d", "zoomIn2d", "zoomOut2d",
                "autoScale2d", "resetScale2d",
                "select2d", "lasso2d"
            ],
            "displaylogo": False
        }
        
        analysis_tabs = st.tabs(["⚽ CLB", "🌍 Nation", "🏆 League", "👥 Players"])
        
        # ===== TAB CLB =====
        with analysis_tabs[0]:
            if 'Club' in df.columns:
                st.markdown("### ⚽ Phân tích theo Câu lạc bộ")
                
                # Chuẩn bị dữ liệu
                height_club_df = df[df['Height'].astype(str).str.strip().ne('')].copy() if 'Height' in df.columns else pd.DataFrame()
                if not height_club_df.empty:
                    height_club_df['Height_num'] = pd.to_numeric(height_club_df['Height'], errors='coerce')
                    height_club_df = height_club_df.dropna(subset=['Height_num', 'Club'])
                
                weight_club_df = df[df['Weight'].astype(str).str.strip().ne('')].copy() if 'Weight' in df.columns else pd.DataFrame()
                if not weight_club_df.empty:
                    weight_club_df['Weight_num'] = pd.to_numeric(weight_club_df['Weight'], errors='coerce')
                    weight_club_df = weight_club_df.dropna(subset=['Weight_num', 'Club'])
                
                age_club_df = df[df['Age'].astype(str).str.strip().ne('')].copy() if 'Age' in df.columns else pd.DataFrame()
                if not age_club_df.empty:
                    age_club_df['Age_num'] = pd.to_numeric(age_club_df['Age'], errors='coerce')
                    age_club_df = age_club_df.dropna(subset=['Age_num', 'Club'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📏 CLB cao nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not height_club_df.empty:
                        # Chỉ tính các CLB có >= 10 cầu thủ
                        club_counts = height_club_df['Club'].value_counts()
                        valid_clubs = club_counts[club_counts >= 10].index
                        height_club_df_filtered = height_club_df[height_club_df['Club'].isin(valid_clubs)]
                        
                        if not height_club_df_filtered.empty:
                            avg_height_club = height_club_df_filtered.groupby('Club')['Height_num'].mean().sort_values(ascending=False).head(10).reset_index()
                            avg_height_club.columns = ['CLB', 'Chiều cao TB (cm)']
                            avg_height_club['Chiều cao TB (cm)'] = avg_height_club['Chiều cao TB (cm)'].round(1)
                            
                            fig_height_club = px.bar(
                                avg_height_club,
                                x="CLB",
                                y="Chiều cao TB (cm)",
                                text="Chiều cao TB (cm)"
                            )
                            fig_height_club.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_height_club.update_layout(
                                xaxis=dict(categoryorder="total descending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_height_club = apply_plotly_theme(fig_height_club)
                            st.plotly_chart(fig_height_club, use_container_width=True, config=config, key="analytics_height_club")
                        else:
                            st.info("Không có CLB nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu chiều cao")
                    
                    st.markdown("#### ⚖️ CLB nặng nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not weight_club_df.empty:
                        # Chỉ tính các CLB có >= 10 cầu thủ
                        club_counts = weight_club_df['Club'].value_counts()
                        valid_clubs = club_counts[club_counts >= 10].index
                        weight_club_df_filtered = weight_club_df[weight_club_df['Club'].isin(valid_clubs)]
                        
                        if not weight_club_df_filtered.empty:
                            avg_weight_club = weight_club_df_filtered.groupby('Club')['Weight_num'].mean().sort_values(ascending=False).head(10).reset_index()
                            avg_weight_club.columns = ['CLB', 'Cân nặng TB (kg)']
                            avg_weight_club['Cân nặng TB (kg)'] = avg_weight_club['Cân nặng TB (kg)'].round(1)
                            
                            fig_weight_club = px.bar(
                                avg_weight_club,
                                x="CLB",
                                y="Cân nặng TB (kg)",
                                text="Cân nặng TB (kg)"
                            )
                            fig_weight_club.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_weight_club.update_layout(
                                xaxis=dict(categoryorder="total descending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_weight_club = apply_plotly_theme(fig_weight_club)
                            st.plotly_chart(fig_weight_club, use_container_width=True, config=config, key="analytics_weight_club")
                        else:
                            st.info("Không có CLB nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu cân nặng")
                
                with col2:
                    st.markdown("#### 🎂 CLB trẻ nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not age_club_df.empty:
                        # Chỉ tính các CLB có >= 10 cầu thủ
                        club_counts = age_club_df['Club'].value_counts()
                        valid_clubs = club_counts[club_counts >= 10].index
                        age_club_df_filtered = age_club_df[age_club_df['Club'].isin(valid_clubs)]
                        
                        if not age_club_df_filtered.empty:
                            avg_age_club = age_club_df_filtered.groupby('Club')['Age_num'].mean().sort_values(ascending=True).head(10).reset_index()
                            avg_age_club.columns = ['CLB', 'Tuổi TB']
                            avg_age_club['Tuổi TB'] = avg_age_club['Tuổi TB'].round(1)
                            
                            fig_age_club = px.bar(
                                avg_age_club,
                                x="CLB",
                                y="Tuổi TB",
                                text="Tuổi TB"
                            )
                            fig_age_club.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_age_club.update_layout(
                                xaxis=dict(categoryorder="total ascending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_age_club = apply_plotly_theme(fig_age_club)
                            st.plotly_chart(fig_age_club, use_container_width=True, config=config, key="analytics_age_club")
                        else:
                            st.info("Không có CLB nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu tuổi")
                    
                    st.markdown("#### 👣 CLB nhiều chân trái nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if 'Foot' in df.columns:
                        foot_club_df = df[df['Foot'].astype(str).str.strip().str.upper().isin(['LEFT', 'L'])].copy()
                        if not foot_club_df.empty:
                            # Chỉ tính các CLB có >= 10 cầu thủ
                            total_by_club = df.groupby('Club').size()
                            valid_clubs = total_by_club[total_by_club >= 10].index
                            foot_club_df_filtered = foot_club_df[foot_club_df['Club'].isin(valid_clubs)]
                            
                            if not foot_club_df_filtered.empty:
                                left_foot_club = foot_club_df_filtered['Club'].value_counts().head(10).reset_index()
                                left_foot_club.columns = ['CLB', 'Số chân trái']
                                left_foot_club['Tổng cầu thủ'] = left_foot_club['CLB'].map(total_by_club)
                                left_foot_club['Tỉ lệ (%)'] = (left_foot_club['Số chân trái'] / left_foot_club['Tổng cầu thủ'] * 100).round(1)
                                
                                fig_left_club = px.bar(
                                    left_foot_club,
                                    x="CLB",
                                    y="Tỉ lệ (%)",
                                    text="Tỉ lệ (%)",
                                    hover_data=['Số chân trái', 'Tổng cầu thủ']
                                )
                                fig_left_club.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>Tỉ lệ: %{y:.1f}%<br>Số chân trái: %{customdata[0]}<br>Tổng: %{customdata[1]}<extra></extra>")
                                fig_left_club.update_layout(
                                    xaxis=dict(categoryorder="total descending", autorange=True),
                                    yaxis=dict(autorange=True),
                                    dragmode="pan",
                                    height=400
                                )
                                fig_left_club = apply_plotly_theme(fig_left_club)
                                st.plotly_chart(fig_left_club, use_container_width=True, config=config, key="analytics_left_club")
                            else:
                                st.info("Không có CLB nào có đủ 10 cầu thủ")
                        else:
                            st.info("Chưa có dữ liệu chân trái")
                    else:
                        st.info("Chưa có cột Foot")
                
                st.markdown("#### 🌍 CLB đa quốc gia nhất (Top 10, tối thiểu 10 cầu thủ)")
                if 'Nation' in df.columns:
                    # Chỉ tính các CLB có >= 10 cầu thủ
                    total_by_club = df.groupby('Club').size()
                    valid_clubs = total_by_club[total_by_club >= 10].index
                    df_filtered = df[df['Club'].isin(valid_clubs)]
                    
                    if not df_filtered.empty:
                        nation_diversity = df_filtered.groupby('Club')['Nation'].nunique().sort_values(ascending=False).head(10).reset_index()
                        nation_diversity.columns = ['CLB', 'Số quốc gia']
                        
                        fig_diversity = px.bar(
                            nation_diversity,
                            x="CLB",
                            y="Số quốc gia",
                            text="Số quốc gia"
                        )
                        fig_diversity.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                        fig_diversity.update_layout(
                            xaxis=dict(categoryorder="total descending", autorange=True),
                            yaxis=dict(autorange=True),
                            dragmode="pan",
                            height=400
                        )
                        fig_diversity = apply_plotly_theme(fig_diversity)
                        st.plotly_chart(fig_diversity, use_container_width=True, config=config, key="analytics_diversity_club")
                    else:
                        st.info("Không có CLB nào có đủ 10 cầu thủ")
            else:
                st.info("Chưa có dữ liệu Club")
        
        # ===== TAB NATION =====
        with analysis_tabs[1]:
            if 'Nation' in df.columns:
                st.markdown("### 🌍 Phân tích theo Quốc gia")
                
                height_nation_df = df[df['Height'].astype(str).str.strip().ne('')].copy() if 'Height' in df.columns else pd.DataFrame()
                if not height_nation_df.empty:
                    height_nation_df['Height_num'] = pd.to_numeric(height_nation_df['Height'], errors='coerce')
                    height_nation_df = height_nation_df.dropna(subset=['Height_num', 'Nation'])
                
                weight_nation_df = df[df['Weight'].astype(str).str.strip().ne('')].copy() if 'Weight' in df.columns else pd.DataFrame()
                if not weight_nation_df.empty:
                    weight_nation_df['Weight_num'] = pd.to_numeric(weight_nation_df['Weight'], errors='coerce')
                    weight_nation_df = weight_nation_df.dropna(subset=['Weight_num', 'Nation'])
                
                age_nation_df = df[df['Age'].astype(str).str.strip().ne('')].copy() if 'Age' in df.columns else pd.DataFrame()
                if not age_nation_df.empty:
                    age_nation_df['Age_num'] = pd.to_numeric(age_nation_df['Age'], errors='coerce')
                    age_nation_df = age_nation_df.dropna(subset=['Age_num', 'Nation'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📏 Quốc gia cao nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not height_nation_df.empty:
                        # Chỉ tính các quốc gia có >= 10 cầu thủ
                        nation_counts = height_nation_df['Nation'].value_counts()
                        valid_nations = nation_counts[nation_counts >= 10].index
                        height_nation_df_filtered = height_nation_df[height_nation_df['Nation'].isin(valid_nations)]
                        
                        if not height_nation_df_filtered.empty:
                            avg_height_nation = height_nation_df_filtered.groupby('Nation')['Height_num'].mean().sort_values(ascending=False).head(10).reset_index()
                            avg_height_nation.columns = ['Quốc gia', 'Chiều cao TB (cm)']
                            avg_height_nation['Chiều cao TB (cm)'] = avg_height_nation['Chiều cao TB (cm)'].round(1)
                            
                            fig_height_nation = px.bar(
                                avg_height_nation,
                                x="Quốc gia",
                                y="Chiều cao TB (cm)",
                                text="Chiều cao TB (cm)"
                            )
                            fig_height_nation.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_height_nation.update_layout(
                                xaxis=dict(categoryorder="total descending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_height_nation = apply_plotly_theme(fig_height_nation)
                            st.plotly_chart(fig_height_nation, use_container_width=True, config=config, key="analytics_height_nation")
                        else:
                            st.info("Không có quốc gia nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu chiều cao")
                    
                    st.markdown("#### ⚖️ Quốc gia nặng nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not weight_nation_df.empty:
                        # Chỉ tính các quốc gia có >= 10 cầu thủ
                        nation_counts = weight_nation_df['Nation'].value_counts()
                        valid_nations = nation_counts[nation_counts >= 10].index
                        weight_nation_df_filtered = weight_nation_df[weight_nation_df['Nation'].isin(valid_nations)]
                        
                        if not weight_nation_df_filtered.empty:
                            avg_weight_nation = weight_nation_df_filtered.groupby('Nation')['Weight_num'].mean().sort_values(ascending=False).head(10).reset_index()
                            avg_weight_nation.columns = ['Quốc gia', 'Cân nặng TB (kg)']
                            avg_weight_nation['Cân nặng TB (kg)'] = avg_weight_nation['Cân nặng TB (kg)'].round(1)
                            
                            fig_weight_nation = px.bar(
                                avg_weight_nation,
                                x="Quốc gia",
                                y="Cân nặng TB (kg)",
                                text="Cân nặng TB (kg)"
                            )
                            fig_weight_nation.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_weight_nation.update_layout(
                                xaxis=dict(categoryorder="total descending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_weight_nation = apply_plotly_theme(fig_weight_nation)
                            st.plotly_chart(fig_weight_nation, use_container_width=True, config=config, key="analytics_weight_nation")
                        else:
                            st.info("Không có quốc gia nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu cân nặng")
                
                with col2:
                    st.markdown("#### 🎂 Quốc gia trẻ nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not age_nation_df.empty:
                        # Chỉ tính các quốc gia có >= 10 cầu thủ
                        nation_counts = age_nation_df['Nation'].value_counts()
                        valid_nations = nation_counts[nation_counts >= 10].index
                        age_nation_df_filtered = age_nation_df[age_nation_df['Nation'].isin(valid_nations)]
                        
                        if not age_nation_df_filtered.empty:
                            avg_age_nation = age_nation_df_filtered.groupby('Nation')['Age_num'].mean().sort_values(ascending=True).head(10).reset_index()
                            avg_age_nation.columns = ['Quốc gia', 'Tuổi TB']
                            avg_age_nation['Tuổi TB'] = avg_age_nation['Tuổi TB'].round(1)
                            
                            fig_age_nation = px.bar(
                                avg_age_nation,
                                x="Quốc gia",
                                y="Tuổi TB",
                                text="Tuổi TB"
                            )
                            fig_age_nation.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_age_nation.update_layout(
                                xaxis=dict(categoryorder="total ascending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_age_nation = apply_plotly_theme(fig_age_nation)
                            st.plotly_chart(fig_age_nation, use_container_width=True, config=config, key="analytics_age_nation")
                        else:
                            st.info("Không có quốc gia nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu tuổi")
                    
                    st.markdown("#### 👣 Quốc gia nhiều chân trái nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if 'Foot' in df.columns:
                        foot_nation_df = df[df['Foot'].astype(str).str.strip().str.upper().isin(['LEFT', 'L'])].copy()
                        if not foot_nation_df.empty:
                            # Chỉ tính các quốc gia có >= 10 cầu thủ
                            total_by_nation = df.groupby('Nation').size()
                            valid_nations = total_by_nation[total_by_nation >= 10].index
                            foot_nation_df_filtered = foot_nation_df[foot_nation_df['Nation'].isin(valid_nations)]
                            
                            if not foot_nation_df_filtered.empty:
                                left_foot_nation = foot_nation_df_filtered['Nation'].value_counts().head(10).reset_index()
                                left_foot_nation.columns = ['Quốc gia', 'Số chân trái']
                                left_foot_nation['Tổng cầu thủ'] = left_foot_nation['Quốc gia'].map(total_by_nation)
                                left_foot_nation['Tỉ lệ (%)'] = (left_foot_nation['Số chân trái'] / left_foot_nation['Tổng cầu thủ'] * 100).round(1)
                                
                                fig_left_nation = px.bar(
                                    left_foot_nation,
                                    x="Quốc gia",
                                    y="Tỉ lệ (%)",
                                    text="Tỉ lệ (%)",
                                    hover_data=['Số chân trái', 'Tổng cầu thủ']
                                )
                                fig_left_nation.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>Tỉ lệ: %{y:.1f}%<br>Số chân trái: %{customdata[0]}<br>Tổng: %{customdata[1]}<extra></extra>")
                                fig_left_nation.update_layout(
                                    xaxis=dict(categoryorder="total descending", autorange=True),
                                    yaxis=dict(autorange=True),
                                    dragmode="pan",
                                    height=400
                                )
                                fig_left_nation = apply_plotly_theme(fig_left_nation)
                                st.plotly_chart(fig_left_nation, use_container_width=True, config=config, key="analytics_left_nation")
                            else:
                                st.info("Không có quốc gia nào có đủ 10 cầu thủ")
                        else:
                            st.info("Chưa có dữ liệu chân trái")
                    else:
                        st.info("Chưa có cột Foot")
                
                st.markdown("#### 🌍 Quốc gia xuất khẩu nhiều nhất (Top 10, tối thiểu 10 cầu thủ)")
                if 'Club' in df.columns:
                    # Chỉ tính các quốc gia có >= 10 cầu thủ
                    total_by_nation = df.groupby('Nation').size()
                    valid_nations = total_by_nation[total_by_nation >= 10].index
                    df_filtered = df[df['Nation'].isin(valid_nations)]
                    
                    if not df_filtered.empty:
                        nation_club_diversity = df_filtered.groupby('Nation')['Club'].nunique().sort_values(ascending=False).head(10).reset_index()
                        nation_club_diversity.columns = ['Quốc gia', 'Số CLB']
                        
                        fig_export_nation = px.bar(
                            nation_club_diversity,
                            x="Quốc gia",
                            y="Số CLB",
                            text="Số CLB"
                        )
                        fig_export_nation.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                        fig_export_nation.update_layout(
                            xaxis=dict(categoryorder="total descending", autorange=True),
                            yaxis=dict(autorange=True),
                            dragmode="pan",
                            height=400
                        )
                        fig_export_nation = apply_plotly_theme(fig_export_nation)
                        st.plotly_chart(fig_export_nation, use_container_width=True, config=config, key="analytics_export_nation")
                    else:
                        st.info("Không có quốc gia nào có đủ 10 cầu thủ")
            else:
                st.info("Chưa có dữ liệu Nation")
        
        # ===== TAB LEAGUE =====
        with analysis_tabs[2]:
            if 'League' in df.columns:
                st.markdown("### 🏆 Phân tích theo Giải đấu")
                
                height_league_df = df[df['Height'].astype(str).str.strip().ne('')].copy() if 'Height' in df.columns else pd.DataFrame()
                if not height_league_df.empty:
                    height_league_df['Height_num'] = pd.to_numeric(height_league_df['Height'], errors='coerce')
                    height_league_df = height_league_df.dropna(subset=['Height_num', 'League'])
                
                weight_league_df = df[df['Weight'].astype(str).str.strip().ne('')].copy() if 'Weight' in df.columns else pd.DataFrame()
                if not weight_league_df.empty:
                    weight_league_df['Weight_num'] = pd.to_numeric(weight_league_df['Weight'], errors='coerce')
                    weight_league_df = weight_league_df.dropna(subset=['Weight_num', 'League'])
                
                age_league_df = df[df['Age'].astype(str).str.strip().ne('')].copy() if 'Age' in df.columns else pd.DataFrame()
                if not age_league_df.empty:
                    age_league_df['Age_num'] = pd.to_numeric(age_league_df['Age'], errors='coerce')
                    age_league_df = age_league_df.dropna(subset=['Age_num', 'League'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📏 Giải đấu cao nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not height_league_df.empty:
                        # Chỉ tính các giải đấu có >= 10 cầu thủ
                        league_counts = height_league_df['League'].value_counts()
                        valid_leagues = league_counts[league_counts >= 10].index
                        height_league_df_filtered = height_league_df[height_league_df['League'].isin(valid_leagues)]
                        
                        if not height_league_df_filtered.empty:
                            avg_height_league = height_league_df_filtered.groupby('League')['Height_num'].mean().sort_values(ascending=False).head(10).reset_index()
                            avg_height_league.columns = ['Giải đấu', 'Chiều cao TB (cm)']
                            avg_height_league['Chiều cao TB (cm)'] = avg_height_league['Chiều cao TB (cm)'].round(1)
                            
                            fig_height_league = px.bar(
                                avg_height_league,
                                x="Giải đấu",
                                y="Chiều cao TB (cm)",
                                text="Chiều cao TB (cm)"
                            )
                            fig_height_league.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_height_league.update_layout(
                                xaxis=dict(categoryorder="total descending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_height_league = apply_plotly_theme(fig_height_league)
                            st.plotly_chart(fig_height_league, use_container_width=True, config=config, key="analytics_height_league")
                        else:
                            st.info("Không có giải đấu nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu chiều cao")
                    
                    st.markdown("#### ⚖️ Giải đấu nặng nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not weight_league_df.empty:
                        # Chỉ tính các giải đấu có >= 10 cầu thủ
                        league_counts = weight_league_df['League'].value_counts()
                        valid_leagues = league_counts[league_counts >= 10].index
                        weight_league_df_filtered = weight_league_df[weight_league_df['League'].isin(valid_leagues)]
                        
                        if not weight_league_df_filtered.empty:
                            avg_weight_league = weight_league_df_filtered.groupby('League')['Weight_num'].mean().sort_values(ascending=False).head(10).reset_index()
                            avg_weight_league.columns = ['Giải đấu', 'Cân nặng TB (kg)']
                            avg_weight_league['Cân nặng TB (kg)'] = avg_weight_league['Cân nặng TB (kg)'].round(1)
                            
                            fig_weight_league = px.bar(
                                avg_weight_league,
                                x="Giải đấu",
                                y="Cân nặng TB (kg)",
                                text="Cân nặng TB (kg)"
                            )
                            fig_weight_league.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_weight_league.update_layout(
                                xaxis=dict(categoryorder="total descending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_weight_league = apply_plotly_theme(fig_weight_league)
                            st.plotly_chart(fig_weight_league, use_container_width=True, config=config, key="analytics_weight_league")
                        else:
                            st.info("Không có giải đấu nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu cân nặng")
                
                with col2:
                    st.markdown("#### 🎂 Giải đấu trẻ nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if not age_league_df.empty:
                        # Chỉ tính các giải đấu có >= 10 cầu thủ
                        league_counts = age_league_df['League'].value_counts()
                        valid_leagues = league_counts[league_counts >= 10].index
                        age_league_df_filtered = age_league_df[age_league_df['League'].isin(valid_leagues)]
                        
                        if not age_league_df_filtered.empty:
                            avg_age_league = age_league_df_filtered.groupby('League')['Age_num'].mean().sort_values(ascending=True).head(10).reset_index()
                            avg_age_league.columns = ['Giải đấu', 'Tuổi TB']
                            avg_age_league['Tuổi TB'] = avg_age_league['Tuổi TB'].round(1)
                            
                            fig_age_league = px.bar(
                                avg_age_league,
                                x="Giải đấu",
                                y="Tuổi TB",
                                text="Tuổi TB"
                            )
                            fig_age_league.update_traces(textposition="outside", hoverinfo="skip", hovertemplate=None)
                            fig_age_league.update_layout(
                                xaxis=dict(categoryorder="total ascending", autorange=True),
                                yaxis=dict(autorange=True),
                                dragmode="pan",
                                height=400
                            )
                            fig_age_league = apply_plotly_theme(fig_age_league)
                            st.plotly_chart(fig_age_league, use_container_width=True, config=config, key="analytics_age_league")
                        else:
                            st.info("Không có giải đấu nào có đủ 10 cầu thủ")
                    else:
                        st.info("Chưa có dữ liệu tuổi")
                    
                    st.markdown("#### 👣 Giải đấu nhiều chân trái nhất (Top 10, tối thiểu 10 cầu thủ)")
                    if 'Foot' in df.columns:
                        foot_league_df = df[df['Foot'].astype(str).str.strip().str.upper().isin(['LEFT', 'L'])].copy()
                        if not foot_league_df.empty:
                            # Chỉ tính các giải đấu có >= 10 cầu thủ
                            total_by_league = df.groupby('League').size()
                            valid_leagues = total_by_league[total_by_league >= 10].index
                            foot_league_df_filtered = foot_league_df[foot_league_df['League'].isin(valid_leagues)]
                            
                            if not foot_league_df_filtered.empty:
                                left_foot_league = foot_league_df_filtered['League'].value_counts().head(10).reset_index()
                                left_foot_league.columns = ['Giải đấu', 'Số chân trái']
                                left_foot_league['Tổng cầu thủ'] = left_foot_league['Giải đấu'].map(total_by_league)
                                left_foot_league['Tỉ lệ (%)'] = (left_foot_league['Số chân trái'] / left_foot_league['Tổng cầu thủ'] * 100).round(1)
                                
                                fig_left_league = px.bar(
                                    left_foot_league,
                                    x="Giải đấu",
                                    y="Tỉ lệ (%)",
                                    text="Tỉ lệ (%)",
                                    hover_data=['Số chân trái', 'Tổng cầu thủ']
                                )
                                fig_left_league.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>Tỉ lệ: %{y:.1f}%<br>Số chân trái: %{customdata[0]}<br>Tổng: %{customdata[1]}<extra></extra>")
                                fig_left_league.update_layout(
                                    xaxis=dict(categoryorder="total descending", autorange=True),
                                    yaxis=dict(autorange=True),
                                    dragmode="pan",
                                    height=400
                                )
                                fig_left_league = apply_plotly_theme(fig_left_league)
                                st.plotly_chart(fig_left_league, use_container_width=True, config=config, key="analytics_left_league")
                            else:
                                st.info("Không có giải đấu nào có đủ 10 cầu thủ")
                        else:
                            st.info("Chưa có dữ liệu chân trái")
                    else:
                        st.info("Chưa có cột Foot")
            else:
                st.info("Chưa có dữ liệu League")
        
        # ===== TAB PLAYERS =====
        with analysis_tabs[3]:
            st.markdown("### 👥 Phân tích theo Cầu thủ")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🏔️ Top 10 cao nhất")
                if 'Height' in df.columns:
                    height_df = df[df['Height'].astype(str).str.strip().ne('')].copy()
                    height_df['Height_num'] = pd.to_numeric(height_df['Height'], errors='coerce')
                    height_df = height_df.dropna(subset=['Height_num'])
                    if not height_df.empty:
                        top_height = height_df.nlargest(10, 'Height_num')[['Player', 'Height_num', 'Position', 'Club', 'Rating']].copy()
                        top_height = top_height.sort_values('Height_num', ascending=True)
                        
                        fig_top_height = px.bar(
                            top_height,
                            x="Height_num",
                            y="Player",
                            orientation='h',
                            text="Height_num",
                            hover_data=['Position', 'Club', 'Rating'],
                            labels={'Height_num': 'Chiều cao (cm)', 'Player': 'Cầu thủ'}
                        )
                        fig_top_height.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br>Chiều cao: %{x} cm<br>Vị trí: %{customdata[0]}<br>Club: %{customdata[1]}<br>Rating: %{customdata[2]}<extra></extra>")
                        fig_top_height.update_layout(
                            yaxis=dict(autorange="reversed"),
                            dragmode="pan",
                            height=400
                        )
                        fig_top_height = apply_plotly_theme(fig_top_height)
                        st.plotly_chart(fig_top_height, use_container_width=True, config=config, key="analytics_top_height")
                    else:
                        st.info("Chưa có dữ liệu")
                else:
                    st.info("Chưa có cột Height")
            
            with col2:
                st.markdown("#### ⚖️ Top 10 nhẹ nhất")
                if 'Weight' in df.columns:
                    weight_df = df[df['Weight'].astype(str).str.strip().ne('')].copy()
                    weight_df['Weight_num'] = pd.to_numeric(weight_df['Weight'], errors='coerce')
                    weight_df = weight_df.dropna(subset=['Weight_num'])
                    if not weight_df.empty:
                        top_weight = weight_df.nsmallest(10, 'Weight_num')[['Player', 'Weight_num', 'Position', 'Club', 'Rating']].copy()
                        top_weight = top_weight.sort_values('Weight_num', ascending=True)
                        
                        fig_top_weight = px.bar(
                            top_weight,
                            x="Weight_num",
                            y="Player",
                            orientation='h',
                            text="Weight_num",
                            hover_data=['Position', 'Club', 'Rating'],
                            labels={'Weight_num': 'Cân nặng (kg)', 'Player': 'Cầu thủ'}
                        )
                        fig_top_weight.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br>Cân nặng: %{x} kg<br>Vị trí: %{customdata[0]}<br>Club: %{customdata[1]}<br>Rating: %{customdata[2]}<extra></extra>")
                        fig_top_weight.update_layout(
                            yaxis=dict(autorange="reversed"),
                            dragmode="pan",
                            height=400
                        )
                        fig_top_weight = apply_plotly_theme(fig_top_weight)
                        st.plotly_chart(fig_top_weight, use_container_width=True, config=config, key="analytics_top_weight")
                    else:
                        st.info("Chưa có dữ liệu")
                else:
                    st.info("Chưa có cột Weight")
            
            with col3:
                st.markdown("#### 🎂 Top 10 trẻ nhất")
                if 'Age' in df.columns:
                    age_df = df[df['Age'].astype(str).str.strip().ne('')].copy()
                    age_df['Age_num'] = pd.to_numeric(age_df['Age'], errors='coerce')
                    age_df = age_df.dropna(subset=['Age_num'])
                    if not age_df.empty:
                        top_age = age_df.nsmallest(10, 'Age_num')[['Player', 'Age_num', 'Position', 'Club', 'Rating']].copy()
                        top_age = top_age.sort_values('Age_num', ascending=True)
                        
                        fig_top_age = px.bar(
                            top_age,
                            x="Age_num",
                            y="Player",
                            orientation='h',
                            text="Age_num",
                            hover_data=['Position', 'Club', 'Rating'],
                            labels={'Age_num': 'Tuổi', 'Player': 'Cầu thủ'}
                        )
                        fig_top_age.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br>Tuổi: %{x}<br>Vị trí: %{customdata[0]}<br>Club: %{customdata[1]}<br>Rating: %{customdata[2]}<extra></extra>")
                        fig_top_age.update_layout(
                            yaxis=dict(autorange="reversed"),
                            dragmode="pan",
                            height=400
                        )
                        fig_top_age = apply_plotly_theme(fig_top_age)
                        st.plotly_chart(fig_top_age, use_container_width=True, config=config, key="analytics_top_age")
                    else:
                        st.info("Chưa có dữ liệu")
                else:
                    st.info("Chưa có cột Age")

    elif current_tab == 'players':
        st.header("👥 Cầu thủ")

        SQUAD_SIZE = 23  # Số cầu thủ mỗi team

        # ===== TÍNH TOP 23 CHO MỖI TEAM =====
        def get_top_23_players(df, group_by, values):
            top_players = set()
            for value in values:
                team_df = df[df[group_by].astype(str) == value].copy()
                if not team_df.empty:
                    # Với Nation/League: loại trùng tên
                    if group_by in ['Nation', 'League']:
                        team_df['TargetClubPriority'] = team_df['Club'].isin(target_clubs).astype(int)
                        if 'Top23_Count' not in team_df.columns:
                            team_df['Top23_Count'] = 0
                        team_df = team_df.sort_values(
                            ['Player', 'Rating', 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'],
                            ascending=[True, False, True, False, False]
                        )
                        team_df = team_df.drop_duplicates(subset=['Player'], keep='first')
        
                    # Bước 1: chọn GK tốt nhất (nếu có)
                    gk_df = team_df[team_df['Position'] == 'GK']
                    cb_df = team_df[team_df['Position'] == 'CB']
                    squad = pd.DataFrame()
                    remaining_slots = SQUAD_SIZE
        
                    # Chọn 1 GK tốt nhất
                    if not gk_df.empty:
                        gk_df['TargetClubPriority'] = gk_df['Club'].isin(target_clubs).astype(int)
                        if 'Top23_Count' not in gk_df.columns:
                            gk_df['Top23_Count'] = 0
                        best_gk = gk_df.sort_values(
                            ['Rating', 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'],
                            ascending=[False, True, False, False]
                        ).head(1)
                        squad = pd.concat([squad, best_gk])
                        remaining_slots -= 1
        
                    # Chọn 2 CB tốt nhất
                    if not cb_df.empty:
                        cb_df['TargetClubPriority'] = cb_df['Club'].isin(target_clubs).astype(int)
                        if 'Top23_Count' not in cb_df.columns:
                            cb_df['Top23_Count'] = 0
                        best_cb = cb_df.sort_values(
                            ['Rating', 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'],
                            ascending=[False, True, False, False]
                        ).head(2)
                        squad = pd.concat([squad, best_cb])
                        remaining_slots -= len(best_cb)
        
                    # Bước 2: chọn các cầu thủ còn lại
                    others = team_df.drop(squad.index)
                    if not others.empty:
                        others['TargetClubPriority'] = others['Club'].isin(target_clubs).astype(int)
                        if 'Top23_Count' not in others.columns:
                            others['Top23_Count'] = 0
                        top_rest = others.sort_values(
                            ['Rating', 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'],
                            ascending=[False, True, False, False]
                        ).head(remaining_slots)
                        squad = pd.concat([squad, top_rest])
        
                    top_players.update(squad.index.tolist())
            return top_players
        
        # Tính top 23 cho từng loại team
        top_club_players = get_top_23_players(df, 'Club', target_clubs)
        top_nation_players = get_top_23_players(df, 'Nation', target_nations)
        top_league_players = get_top_23_players(df, 'League', target_leagues)

        # ===== PHÁT HIỆN CẦU THỦ TRÙNG =====
        def detect_duplicates(df):
            """Phát hiện cầu thủ trùng: CÙNG TÊN + Club + Nation + League"""
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

        # ===== GỢI Ý BÁN =====
        def suggest_action(row):
            idx = row.name
            club = str(row.get('Club', '')).strip()
            
            # === THÊM DÒNG NÀY ĐỂ SỬA LỖI ===
            # Định nghĩa danh sách bảo vệ ngay tại đây nếu chưa tìm thấy biến global
            local_protected_clubs = ["FC Barcelona"] 
            if 'PROTECTED_CLUBS' in globals():
                local_protected_clubs = globals()['PROTECTED_CLUBS']
            # ================================
        
            nation = str(row.get('Nation', '')).strip()
            league = str(row.get('League', '')).strip()
            reasons = []

            # 0. Kiểm tra club được bảo vệ (SỬA DÙNG BIẾN MỚI)
            if club in local_protected_clubs:
                return ' ✅  GIỮ', f" 🛡 ️ {club} - Không bao giờ bán (Fan club)"

    # ... (các phần dưới giữ nguyên)
            
            # 1. Kiểm tra thẻ trùng (cùng player + club + nation + league)
            is_duplicate = any(dup['index'] == idx for dup in duplicates)
            if is_duplicate:
                return '❌ BÁN', "⚠️ Thẻ trùng - Có thẻ tốt hơn (cùng player + club + nation + league)"
            
            # 2. Kiểm tra thuộc Top 23
            in_top_club = idx in top_club_players
            in_top_nation = idx in top_nation_players
            in_top_league = idx in top_league_players
            
            if in_top_club:
                reasons.append(f"Top 23 Club: {club}")
            if in_top_nation:
                reasons.append(f"Top 23 Nation: {nation}")
            if in_top_league:
                reasons.append(f"Top 23 League: {league}")
            
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

        st.divider()

        # ===== BỘ LỌC NÂNG CAO =====
        st.subheader("🔍 Tìm kiếm & Lọc")
        
        # Row 1: Tìm kiếm + Action filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "🔍 Tìm cầu thủ",
                placeholder="Nhập tên cầu thủ...",
                key="filter_search_query"
            )
        with col2:
            action_filter = st.selectbox(
                "Hành động",
                ["Tất cả", "✅ GIỮ", "❌ BÁN"],
                key="filter_action"
            )
        
        # Row 2: Position, Type, League, Position Style
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            position_filter = st.selectbox(
                "Vị trí",
                ["Tất cả"] + get_unique_values(df, 'Position'),
                key="filter_position"
            )
        with col2:
            type_filter = st.selectbox(
                "Loại",
                ["Tất cả"] + get_unique_values(df, 'Player Type'),
                key="filter_type"
            )
        with col3:
            league_filter = st.selectbox(
                "League",
                ["Tất cả"] + get_unique_values(df, 'League'),
                key="filter_league"
            )
        with col4:
            pos_style = st.selectbox(
                "Phong cách",
                ["Tất cả"] + get_unique_values(df, 'Position Style'),
                key="filter_pos_style"
            )
        
        # Row 3: Club, Nation, Rating, Epic only
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            club_filter = st.selectbox(
                "Club",
                ["Tất cả"] + get_unique_values(df, 'Club'),
                key="filter_club"
            )
        with col2:
            nation_filter = st.selectbox(
                "Nation",
                ["Tất cả"] + get_unique_values(df, 'Nation'),
                key="filter_nation"
            )
        with col3:
            rmin, rmax = int(df['Rating'].min()), int(df['Rating'].max())
            rating_range = st.slider(
                "Rating",
                rmin, rmax, (rmin, rmax),
                key="filter_rating_range"
            )
        with col4:
            epic_only = st.checkbox(
                "Chỉ EPIC",
                value=False,
                key="filter_epic_only"
            )
        
        # Row 4: Region, Foot, Age, Height
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            region_filter = st.selectbox(
                "Region",
                ["Tất cả"] + get_unique_values(df, 'Region'),
                key="filter_region"
            )
        with col2:
            foot_filter = st.selectbox(
                "Chân thuận",
                ["Tất cả"] + get_unique_values(df, 'Foot'),
                key="filter_foot"
            )
        with col3:
            # Age có thể trống, xử lý an toàn
            if 'Age' in df.columns and df['Age'].astype(str).str.strip().ne('').any():
                age_numeric = pd.to_numeric(df['Age'], errors='coerce').dropna()
                if not age_numeric.empty:
                    amin, amax = int(age_numeric.min()), int(age_numeric.max())
                    age_range = st.slider(
                        "Age",
                        amin, amax, (amin, amax),
                        key="filter_age_range"
                    )
                else:
                    age_range = None
            else:
                age_range = None
                st.caption("Age: chưa có dữ liệu")
        with col4:
            # Height (cm)
            if 'Height' in df.columns and df['Height'].astype(str).str.strip().ne('').any():
                h_numeric = pd.to_numeric(df['Height'], errors='coerce').dropna()
                if not h_numeric.empty:
                    hmin, hmax = int(h_numeric.min()), int(h_numeric.max())
                    height_range = st.slider(
                        "Height (cm)",
                        hmin, hmax, (hmin, hmax),
                        key="filter_height_range"
                    )
                else:
                    height_range = None
            else:
                height_range = None
                st.caption("Height: chưa có dữ liệu")
        
        # Row 5: Skills + WF / Form filters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            skill_query = st.text_input(
                "Tìm trong Skills",
                placeholder="vd: Long Range Shooting",
                key="filter_skill_query"
            )
        with col2:
            wf_usage_filter = st.selectbox(
                "WF Usage",
                ["Tất cả"] + get_unique_values(df, 'Weak Foot Usage'),
                key="filter_wf_usage"
            )
        with col3:
            wf_acc_filter = st.selectbox(
                "WF Accuracy",
                ["Tất cả"] + get_unique_values(df, 'Weak Foot Accuracy'),
                key="filter_wf_acc"
            )
        
        # Row 6: Form, Injury Resistance
        col1, col2 = st.columns(2)
        with col1:
            form_filter = st.selectbox(
                "Form",
                ["Tất cả"] + get_unique_values(df, 'Form'),
                key="filter_form"
            )
        with col2:
            injury_filter = st.selectbox(
                "Chống chấn thương",
                ["Tất cả"] + get_unique_values(df, 'Injury Resistance'),
                key="filter_injury"
            )
        
        # Row 7: Reset bộ lọc
        _, reset_col, _ = st.columns([4, 1, 4])
        with reset_col:
            if st.button("🔄 Reset bộ lọc", use_container_width=True, key="btn_reset_filters"):
                for k in [
                    "filter_search_query", "filter_action",
                    "filter_position", "filter_type", "filter_league", "filter_pos_style",
                    "filter_club", "filter_nation", "filter_rating_range", "filter_epic_only",
                    "filter_region", "filter_foot", "filter_age_range", "filter_height_range",
                    "filter_skill_query", "filter_wf_usage", "filter_wf_acc",
                    "filter_form", "filter_injury",
                    "filter_sort_col", "filter_sort_order", "filter_view_mode"
                ]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        
        # ===== APPLY FILTERS =====
        filtered_df = rec_df.copy()
        
        if search_query:
            filtered_df = filtered_df[filtered_df['Player'].str.contains(search_query, case=False, na=False)]
        if action_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Action'] == action_filter]
        if position_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Position'] == position_filter]
        if type_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Player Type'] == type_filter]
        if league_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['League'] == league_filter]
        if club_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Club'] == club_filter]
        if nation_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Nation'] == nation_filter]
        if region_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Region'] == region_filter]
        if foot_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Foot'] == foot_filter]
        if pos_style != "Tất cả":
            filtered_df = filtered_df[filtered_df['Position Style'] == pos_style]
        if epic_only:
            filtered_df = filtered_df[filtered_df['Player Type'].astype(str).str.upper() == 'EPIC']
        if skill_query:
            filtered_df = filtered_df[filtered_df['Skills'].astype(str).str.contains(re.escape(skill_query), case=False, na=False)]
        if wf_usage_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Weak Foot Usage'] == wf_usage_filter]
        if wf_acc_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Weak Foot Accuracy'] == wf_acc_filter]
        if form_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Form'] == form_filter]
        if injury_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df['Injury Resistance'] == injury_filter]
        
        # Apply numeric ranges
        filtered_df = filtered_df[(filtered_df['Rating'] >= rating_range[0]) & (filtered_df['Rating'] <= rating_range[1])]
        if age_range is not None and 'Age' in filtered_df.columns:
            age_series = pd.to_numeric(filtered_df['Age'], errors='coerce')
            mask = (age_series >= age_range[0]) & (age_series <= age_range[1])
            filtered_df = filtered_df[mask]
        if height_range is not None and 'Height' in filtered_df.columns:
            h_series = pd.to_numeric(filtered_df['Height'], errors='coerce')
            mask_h = (h_series >= height_range[0]) & (h_series <= height_range[1])
            filtered_df = filtered_df[mask_h]
        
        # ===== SORTING =====
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_col = st.selectbox(
                "Sắp xếp theo",
                options=[
                    'Rating', 'Player', 'Position', 'Player Type',
                    'Club', 'Nation', 'League',
                    'Height', 'Weight', 'BMI'
                ],
                index=0,
                key="filter_sort_col"
            )
        with col2:
            sort_order = st.radio(
                "Thứ tự",
                ["Giảm dần", "Tăng dần"],
                horizontal=True,
                index=0,
                key="filter_sort_order"
            )
        
        asc = (sort_order == "Tăng dần")
        if sort_col == 'Position':
            filtered_df['_sort_pos'] = filtered_df['Position'].map(POSITION_ORDER)
            filtered_df = filtered_df.sort_values(by='_sort_pos', ascending=asc)
            filtered_df = filtered_df.drop(columns=['_sort_pos'])
        elif sort_col in ['Height', 'Weight']:
            col_name = sort_col
            tmp_col = f"_sort_{col_name.lower()}"
            filtered_df[tmp_col] = pd.to_numeric(filtered_df[col_name], errors='coerce')
            filtered_df = filtered_df.sort_values(by=tmp_col, ascending=asc, na_position="last")
            filtered_df = filtered_df.drop(columns=[tmp_col])
        elif sort_col == 'BMI':
            # BMI = weight (kg) / (height(m))^2
            h = pd.to_numeric(filtered_df['Height'], errors='coerce')
            w = pd.to_numeric(filtered_df['Weight'], errors='coerce')
            bmi = w / ((h / 100.0) ** 2)
            filtered_df['_sort_bmi'] = bmi
            filtered_df = filtered_df.sort_values(by='_sort_bmi', ascending=asc, na_position="last")
            filtered_df = filtered_df.drop(columns=['_sort_bmi'])
        else:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=asc)
        
        # ===== DISPLAY TABLE =====
        st.info(f"📊 Hiển thị **{len(filtered_df)}** / {len(rec_df)} cầu thủ")

        # ===== ĐỊNH NGHĨA COLUMNS TRƯỚC (ĐỂ DÙNG CHO EXPORT) =====
        display_columns = [
            'Player', 'Rating', 'Position', 'Position Style', 'Player Type',
            'Club', 'Nation', 'League',
            'Region', 'Height', 'Weight', 'Age', 'Foot',
            'Weak Foot Usage', 'Weak Foot Accuracy', 'Form', 'Injury Resistance',
            'Action', 'Reasons', 'Skills'
        ]
        available_columns = [c for c in display_columns if c in filtered_df.columns]
        
        # ===== NÚT CHUYỂN ĐỔI CHỂ ĐỘ HIỂN THỊ =====
        view_mode = st.radio(
            "Chế độ hiển thị:",
            ["📋 Bảng", "🎴 Card"],
            horizontal=True,
            index=1,
            key="filter_view_mode"
        )
        
        if view_mode == "🎴 Card":
            st.markdown("### 🎴 Danh sách cầu thủ")
            
            # CSS nhỏ để nút bấm dính liền với thẻ hơn, nhìn như một khối thống nhất
            st.markdown("""
            <style>
            /* Thu nhỏ khoảng cách giữa các element trong cột để Card và Button gần nhau */
            [data-testid="stColumn"] > div > div[data-testid="stVerticalBlock"] {
                gap: 0.5rem; 
            }
            div.stButton > button {
                border-radius: 0 0 8px 8px; /* Bo tròn góc dưới cho khớp với card */
                margin-top: -5px; /* Kéo nút lên một chút */
            }
            </style>
            """, unsafe_allow_html=True)
            
            cols_per_row = 6
            rows = [filtered_df.iloc[i:i + cols_per_row] for i in range(0, len(filtered_df), cols_per_row)]

            for row in rows:
                cols = st.columns(cols_per_row)
                for i, (idx, player) in enumerate(row.iterrows()):
                    with cols[i]:
                        # 1. Render Card (Visual)
                        p_data = {
                            'Player': player['Player'],
                            'Rating': player['Rating'],
                            'Position': player['Position'],
                            'Type': player['Player Type'],
                            'Club': player.get('Club', ''),
                            'Nation': player.get('Nation', ''),
                            'Player ID': player.get('Player ID', ''),
                            'Player URL': player.get('Player URL', ''),
                            'Action': player.get('Action', ''),
                            'Image': None
                        }
                        # Render HTML thẻ
                        card_html = render_efootball_card_html(p_data)
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # 2. Render Button (Interaction) - Nằm ngay dưới thẻ
                        # Dùng icon kính lúp hoặc text ngắn gọn
                        if st.button("🔍 Xem hồ sơ", key=f"btn_card_{idx}", use_container_width=True):
                            show_player_modal(player)
                
                # Tạo khoảng cách giữa các hàng
                st.write("") 
                st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        
        else:
            # ===== CHẾ ĐỘ BẢNG =====
            display_df = filtered_df[available_columns].copy()
            display_df.insert(0, 'STT', range(1, len(display_df) + 1))
            
            st.dataframe(
                display_df,
                column_config={
                    "STT": st.column_config.NumberColumn("STT", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Rating": st.column_config.NumberColumn("Rating", width="small"),
                    "Position": st.column_config.TextColumn("Vị trí", width="small"),
                    "Position Style": st.column_config.TextColumn("Phong cách", width="small"),
                    "Player Type": st.column_config.TextColumn("Loại", width="small"),
                    "Club": st.column_config.TextColumn("Club", width="medium"),
                    "Nation": st.column_config.TextColumn("Nation", width="small"),
                    "League": st.column_config.TextColumn("League", width="small"),
                    "Action": st.column_config.TextColumn("Hành động", width="small"),
                    "Reasons": st.column_config.TextColumn("Lý do", width="large"),
                    "Skills": st.column_config.TextColumn("Skills", width="large"),
                },
                use_container_width=True,
                height=600,
                hide_index=True
            )        
# ===== EXPORT & ACTIONS =====
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(sell_df) > 0:
                sell_csv = sell_df[available_columns].to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label=f"⬇️ Tải danh sách BÁN ({len(sell_df)})",
                    data=sell_csv,
                    file_name="players_to_sell.csv",
                    mime="text/csv"
                )
        
        with col2:
            all_csv = rec_df[available_columns].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"⬇️ Tải tất cả ({len(rec_df)})",
                data=all_csv,
                file_name="players_with_suggestions.csv",
                mime="text/csv"
            )
        
        with col3:
            filtered_csv = filtered_df[available_columns].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"⬇️ Tải kết quả lọc ({len(filtered_df)})",
                data=filtered_csv,
                file_name="players_filtered.csv",
                mime="text/csv"
            )
        
        # ===== BÁN CẦU THỦ (ĐỀ XUẤT) =====
        with st.expander("🗑️ Bán cầu thủ được đề xuất"):
            st.warning("⚠️ Hành động này sẽ xóa vĩnh viễn cầu thủ khỏi Google Sheets")
            
            # Hiển thị danh sách đề xuất bán
            sell_display = sell_df[['Player', 'Rating', 'Position', 'Player Type', 'Club', 'Nation', 'League', 'Reasons']].copy()
            sell_display.insert(0, 'STT', range(1, len(sell_display) + 1))
            st.dataframe(sell_display, use_container_width=True, hide_index=True)
            
            idx_options = sell_df.index.tolist()
            labels = {i: f"{sell_df.loc[i, 'Player']} ({sell_df.loc[i, 'Position']}) – {sell_df.loc[i, 'Rating']}" 
                      for i in idx_options}
            to_sell = st.multiselect(
                "Chọn cầu thủ để bán",
                options=idx_options,
                format_func=lambda x: labels.get(x, str(x)),
                key="sell_recommended"
            )
            
            if st.button("🗑️ Bán cầu thủ đã chọn", type="primary", disabled=len(to_sell) == 0, key="btn_sell_recommended"):
                try:
                    new_df = df.drop(index=to_sell, errors='ignore')
                    if save_data_to_gsheet(new_df):
                        st.success(f"✅ Đã bán (xóa) {len(to_sell)} cầu thủ")
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi khi bán: {e}")
        
        # ===== XÓA CẦU THỦ TÙY CHỌN =====
        with st.expander("🗑️ Xóa cầu thủ tùy chọn (Nâng cao)"):
            st.error("⚠️ **CẢNH BÁO:** Bạn có thể xóa BẤT KỲ cầu thủ nào, kể cả cầu thủ được đề xuất giữ!")
            
            st.markdown("---")
            st.subheader("🔍 Tìm và chọn cầu thủ cần xóa")
            
            # Bộ lọc nhanh
            del_col1, del_col2, del_col3 = st.columns(3)
            with del_col1:
                del_search = st.text_input("Tìm theo tên", placeholder="Nhập tên cầu thủ...", key="del_search")
            with del_col2:
                del_position = st.multiselect("Vị trí", sorted(df['Position'].unique().tolist()), key="del_position")
            with del_col3:
                del_club = st.multiselect("Club", sorted([x for x in df['Club'].unique() if str(x).strip()]), key="del_club")
            
            # Apply filters
            del_df = rec_df.copy()
            if del_search:
                del_df = del_df[del_df['Player'].str.contains(del_search, case=False, na=False)]
            if del_position:
                del_df = del_df[del_df['Position'].isin(del_position)]
            if del_club:
                del_df = del_df[del_df['Club'].isin(del_club)]
            
            st.info(f"📊 Tìm thấy **{len(del_df)}** cầu thủ")
            
            if not del_df.empty:
                # Hiển thị bảng
                del_display = del_df[['Player', 'Rating', 'Position', 'Player Type', 'Club', 'Nation', 'League', 'Region', 'Action', 'Reasons']].copy()
                del_display.insert(0, 'STT', range(1, len(del_display) + 1))
                st.dataframe(del_display, use_container_width=True, hide_index=True, height=400)
                
                st.markdown("---")
                
                # Chọn cầu thủ
                del_idx_options = del_df.index.tolist()
                del_labels = {i: f"{del_df.loc[i, 'Player']} ({del_df.loc[i, 'Position']}) – {del_df.loc[i, 'Rating']} – {del_df.loc[i, 'Action']}" 
                          for i in del_idx_options}
                
                to_delete = st.multiselect(
                    "Chọn cầu thủ cần xóa",
                    options=del_idx_options,
                    format_func=lambda x: del_labels.get(x, str(x)),
                    key="delete_custom"
                )
                
                if to_delete:
                    # Thống kê cầu thủ sẽ xóa
                    delete_preview = del_df.loc[to_delete]
                    protected_count = len(delete_preview[delete_preview['Club'].isin(PROTECTED_CLUBS)])
                    keep_count = len(delete_preview[delete_preview['Action'] == '✅ GIỮ'])
                    
                    st.warning(f"🗑️ Sẽ xóa **{len(to_delete)}** cầu thủ:")
                    warn_col1, warn_col2, warn_col3 = st.columns(3)
                    with warn_col1:
                        st.metric("Tổng", len(to_delete))
                    with warn_col2:
                        if protected_count > 0:
                            st.metric("🛡️ FC Barcelona", protected_count, delta="Được bảo vệ!", delta_color="inverse")
                    with warn_col3:
                        if keep_count > 0:
                            st.metric("✅ Đề xuất giữ", keep_count, delta="Cẩn thận!", delta_color="inverse")
                    
                    # Checkbox xác nhận
                    confirm_delete = st.checkbox(
                        f"✅ Tôi xác nhận xóa {len(to_delete)} cầu thủ này (KHÔNG THỂ HOÀN TÁC)",
                        key="confirm_delete"
                    )
                    
                    if st.button(
                        f"🗑️ XÓA {len(to_delete)} CẦU THỦ", 
                        type="primary", 
                        disabled=not confirm_delete,
                        key="btn_delete_custom",
                        use_container_width=True
                    ):
                        try:
                            new_df = df.drop(index=to_delete, errors='ignore')
                            if save_data_to_gsheet(new_df):
                                st.success(f"✅ Đã xóa {len(to_delete)} cầu thủ thành công!")
                                st.cache_data.clear()
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi khi xóa: {e}")
            else:
                st.info("🔍 Không tìm thấy cầu thủ nào với bộ lọc hiện tại")
        
        # ===== THỐNG KÊ 23+ =====
        with st.expander("📈 Thống kê đội hình 23+"):
            threshold = st.slider("Ngưỡng tối thiểu", 1, 50, 23, key="stats23_threshold")
            
            def show_table(title, series):
                st.subheader(title)
                counts = series.value_counts()
                enough = counts[counts >= threshold]
                if enough.empty:
                    st.info("Chưa có nhóm nào đủ ngưỡng")
                else:
                    out = enough.rename_axis(title).reset_index(name='Số lượng')
                    out.insert(0, 'STT', range(1, len(out) + 1))
                    st.dataframe(out, use_container_width=True, hide_index=True)
            
            show_table("Club", df['Club'].astype(str))
            show_table("Nation", df['Nation'].astype(str))
            show_table("League", df['League'].astype(str))
            if 'Region' in df.columns:
                show_table("Region", df['Region'].astype(str))

    elif current_tab == 'skills':
        st.header("🎮 Quản lý Skills")
        MAX_SKILLS = 15
        MAX_ADDED_SKILLS = 5
        
        with st.expander("🔍 Tìm kiếm nâng cao", expanded=False):
            search_col1, search_col2, search_col3 = st.columns(3)
            with search_col1:
                sm_player_search = st.text_input("Tên cầu thủ", placeholder="Nhập tên...", key="sm_player_search")
                sm_position = st.multiselect("Vị trí", sorted(df['Position'].unique().tolist()), key="sm_position")
            with search_col2:
                sm_player_type = st.multiselect("Loại cầu thủ", ["EPIC", "POTW", "NON-EPIC"], key="sm_player_type")
            club_options = sorted([x for x in df['Club'].unique() if str(x).strip()])
            if 'sm_club' not in st.session_state:
                default_club = ['FC Barcelona'] if 'FC Barcelona' in club_options else []
            else:
                default_club = st.session_state.get('sm_club', [])
            sm_club = st.multiselect("Club", club_options, default=default_club, key="sm_club")
            with search_col3:
                sm_nation = st.multiselect("Quốc gia", sorted([x for x in df['Nation'].unique() if str(x).strip()]), key="sm_nation")
                sm_league = st.multiselect("League", sorted([x for x in df['League'].unique() if str(x).strip()]), key="sm_league")
            
            rating_col1, rating_col2, filter_col = st.columns([2, 2, 2])
            with rating_col1:
                rating_min = st.number_input("Rating từ", min_value=1, max_value=150, value=1, key="sm_rating_min")
            with rating_col2:
                rating_max = st.number_input("Rating đến", min_value=1, max_value=150, value=150, key="sm_rating_max")
            with filter_col:
                filter_options = ["Tất cả", "Có gợi ý", "Không thể thêm skills", "Đã đủ skills"]
                if 'sm_filter' not in st.session_state:
                    st.session_state['sm_filter'] = "Có gợi ý"
                sm_filter = st.selectbox("Trạng thái Skills", filter_options, key="sm_filter")
        
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        with quick_col1:
            if st.button("⭐ EPIC", use_container_width=True, key="quick_epic"):
                st.session_state['quick_filter'] = 'EPIC'
                st.rerun()
        with quick_col2:
            if st.button("🟣 POTW", use_container_width=True, key="quick_potw"):
                st.session_state['quick_filter'] = 'POTW'
                st.rerun()
        with quick_col3:
            if st.button("🔄 Reset", use_container_width=True, key="quick_reset"):
                st.session_state['quick_filter'] = None
                st.rerun()
        
        if 'quick_filter' in st.session_state and st.session_state['quick_filter']:
            if st.session_state['quick_filter'] == 'EPIC':
                sm_player_type = ['EPIC']
            elif st.session_state['quick_filter'] == 'POTW':
                sm_player_type = ['POTW']
            else:
                sm_player_type = st.session_state.get('sm_player_type', [])
        else:
            sm_player_type = st.session_state.get('sm_player_type', [])
        
        sm_df = df.copy()
        
        if sm_player_search:
            sm_df = sm_df[sm_df['Player'].str.contains(sm_player_search, case=False, na=False)]
        if sm_position:
            sm_df = sm_df[sm_df['Position'].isin(sm_position)]
        if sm_player_type:
            sm_df = sm_df[sm_df['Player Type'].astype(str).str.upper().isin(sm_player_type)]
        if sm_club:
            sm_df = sm_df[sm_df['Club'].isin(sm_club)]
        if sm_nation:
            sm_df = sm_df[sm_df['Nation'].isin(sm_nation)]
        if sm_league:
            sm_df = sm_df[sm_df['League'].isin(sm_league)]
        
        sm_df = sm_df[(sm_df['Rating'] >= rating_min) & (sm_df['Rating'] <= rating_max)]

        # Tự động sort theo Rating giảm dần
        sm_df = sm_df.sort_values('Rating', ascending=False)
        
        def determine_skill_status(row):
            position = str(row.get('Position', '')).strip()
            player_type_value = str(row.get('Player Type', '')).upper()
            base = str(row.get('Skills', '')).strip()
            added = str(row.get('Added Skills', '')).strip()
            
            base_list = [s.strip() for s in base.split(',') if s.strip()] if base else []
            added_list = [s.strip() for s in added.split(',') if s.strip()] if added else []
            
            total_count = len(base_list) + len(added_list)
            remaining_slots = MAX_ADDED_SKILLS - len(added_list)
            
            if player_type_value == 'POTW':
                return 'locked'
            if total_count >= MAX_SKILLS or remaining_slots <= 0:
                return 'full'
            if position not in POSITION_SKILLS_PRIORITY:
                return 'no_hint'
            
            recommendations = get_recommended_skills(position, base, added, MAX_SKILLS)
            if remaining_slots > 0:
                recommendations = recommendations[:remaining_slots]
            else:
                recommendations = []
            
            if recommendations:
                return 'has_hint'
            return 'no_hint'
        
        sm_df['Skill_Status'] = sm_df.apply(determine_skill_status, axis=1)
        
        if sm_filter == "Không thể thêm skills":
            sm_df = sm_df[sm_df['Skill_Status'] == 'locked']
        elif sm_filter == "Có gợi ý":
            sm_df = sm_df[sm_df['Skill_Status'] == 'has_hint']
        elif sm_filter == "Đã đủ skills":
            sm_df = sm_df[sm_df['Skill_Status'].isin(['full', 'no_hint'])]
        
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        with summary_col1:
            st.metric("Tìm thấy", len(sm_df))
        with summary_col2:
            epic_count = (sm_df['Player Type'].astype(str).str.upper() == 'EPIC').sum()
            st.metric("EPIC", epic_count)
        with summary_col3:
            potw_count = (sm_df['Player Type'].astype(str).str.upper() == 'POTW').sum()
            st.metric("POTW", potw_count)
        with summary_col4:
            avg_rating = sm_df['Rating'].mean() if len(sm_df) > 0 else 0
            st.metric("Rating TB", f"{avg_rating:.1f}")
        
        st.divider()
        
        if sm_df.empty:
            st.info("🔍 Không tìm thấy cầu thủ nào")
        else:
            for idx, row in sm_df.iterrows():
                player_name = row['Player']
                position = row['Position']
                rating = row['Rating']
                player_type = row['Player Type']
                
                base_skills = str(df.loc[idx, 'Skills']).strip()
                added_skills = str(df.loc[idx, 'Added Skills']).strip()
                
                base_skills_list = [s.strip() for s in base_skills.split(',') if s.strip()] if base_skills else []
                added_skills_list = [s.strip() for s in added_skills.split(',') if s.strip()] if added_skills else []
                all_skills_list = base_skills_list + added_skills_list
                
                base_count = len(base_skills_list)
                added_count = len(added_skills_list)
                total_count = len(all_skills_list)
                remaining_slots = MAX_ADDED_SKILLS - added_count
                
                recommended = get_recommended_skills(position, base_skills, added_skills, MAX_SKILLS)
                recommended = recommended[:remaining_slots]
                
                is_epic = str(player_type).upper() == "EPIC"
                is_potw = str(player_type).upper() == "POTW"
                
                if is_epic:
                    card_color = "🟡"
                elif is_potw:
                    card_color = "🟣"
                else:
                    card_color = "🔵"
                
                with st.container(border=True):
                    h1, h2, h3 = st.columns([3, 1, 1])
                    with h1:
                        st.markdown(f"### {card_color} {player_name}")
                    with h2:
                        st.markdown(f"**{position}** • {rating}")
                    with h3:
                        if is_potw:
                            st.markdown(f"🔒 **POTW**")
                        elif remaining_slots > 0:
                            st.markdown(f"💡 **+{remaining_slots}** slot")
                        else:
                            st.markdown(f"✅ **Full**")
                    
                    st.markdown(f"**📋 Skills:** ({total_count})")
                    
                    if base_skills_list:
                        st.caption(f"🎮 Gốc ({base_count}):")
                        base_html = " ".join([f'<span style="background:#e3f2fd;color:#1565c0;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:13px;border:1px solid #90caf9;">⭐ {s}</span>' for s in base_skills_list])
                        st.markdown(base_html, unsafe_allow_html=True)
                
                    if added_skills_list:
                        st.caption(f"➕ Đã thêm ({added_count}):")
                        added_html = " ".join([f'<span style="background:#d4edda;color:#155724;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:13px;border:1px solid #c3e6cb;">✅ {s}</span>' for s in added_skills_list])
                        st.markdown(added_html, unsafe_allow_html=True)
                
                    if not base_skills_list and not added_skills_list:
                        st.caption(f"_Chưa có skills (0/{MAX_SKILLS})_")
                    
                    if is_potw:
                        st.info("🔒 Cầu thủ POTW không thể thêm skills ngoài skills gốc")
                    elif total_count >= MAX_SKILLS:
                        st.success(f"✅ Đã đạt giới hạn tối đa {MAX_SKILLS} skills!")
                    elif recommended:
                        st.markdown(f"**💡 Gợi ý thêm:** (Còn {remaining_slots} slot)")
                        
                        selected_skills = []
                        num_cols = min(len(recommended), 5)
                        cols = st.columns(num_cols)
                        
                        reset_key = st.session_state.get('checkbox_reset_counter', 0)
                        
                        # 🔧 FIX: Load fresh inventory mỗi lần render
                        current_inventory = get_inventory()
                        
                        for i, skill in enumerate(recommended):
                            with cols[i % num_cols]:
                                stock_count = current_inventory.get(skill, 0)
                                stock_display = f"({stock_count})" if stock_count > 0 else "(❌)"
                                label = f"**#{i+1}** {skill} {stock_display}"
                                
                                # Disable checkbox nếu hết hàng
                                disabled = stock_count <= 0
                                
                                if st.checkbox(label, key=f"skill_{idx}_{i}_{reset_key}", 
                                             disabled=disabled,
                                             label_visibility="visible"):
                                    selected_skills.append(skill)
                        
                        if selected_skills:
                            new_total = total_count + len(selected_skills)
                            
                            if new_total > MAX_SKILLS:
                                st.error(f"⚠️ Không thể thêm {len(selected_skills)} skills! (Vượt giới hạn {MAX_SKILLS})")
                            else:
                                # 🔧 FIX: Kiểm tra inventory REALTIME
                                fresh_inventory = get_inventory()
                                unavailable_skills = []
                                for skill in selected_skills:
                                    if fresh_inventory.get(skill, 0) <= 0:
                                        unavailable_skills.append(skill)
                                
                                if unavailable_skills:
                                    st.error(f"⚠️ Kho không đủ skills: {', '.join(unavailable_skills)}")
                                    st.info("💡 Vui lòng kiểm tra tab 'Kho Skills' để thêm skills cần thiết")
                                else:
                                    if st.button(f"➕ Thêm {len(selected_skills)} skill → Tổng: {new_total}/{MAX_SKILLS}", 
                                               key=f"add_{idx}_{reset_key}", 
                                               type="primary", 
                                               use_container_width=True):
                                        
                                        # 🔧 FIX: Transaction safety
                                        try:
                                            with st.spinner("💾 Đang lưu..."):
                                                # STEP 1: Cập nhật DataFrame
                                                new_added_skills = added_skills_list + selected_skills
                                                new_added_skills_str = ', '.join(new_added_skills)
                                                df.at[idx, 'Added Skills'] = new_added_skills_str
                                                
                                                # STEP 2: Lưu vào Google Sheets
                                                save_success = save_data_to_gsheet(df)
                                                
                                                if not save_success:
                                                    raise Exception("Lỗi khi lưu vào Google Sheets")
                                                
                                                # STEP 3: CHỈ trừ inventory SAU KHI lưu thành công
                                                for skill in selected_skills:
                                                    update_inventory_count(skill, -1)
                                                
                                                # STEP 4: Clear cache
                                                st.cache_data.clear()
                                            
                                            st.toast(f"✅ Đã thêm {len(selected_skills)} skills cho {player_name}!", icon="✅")
                                            st.session_state.checkbox_reset_counter += 1
                                            st.session_state.current_tab = 'skills'
                                            
                                            import time
                                            time.sleep(0.5)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"❌ Lỗi: {e}")
                                            st.warning("⚠️ Dữ liệu không bị thay đổi - vui lòng thử lại")
                    else:
                        if total_count < MAX_SKILLS:
                            st.info(f"ℹ️ Không có gợi ý thêm cho vị trí {position} (Hiện có {total_count}/{MAX_SKILLS} skills)")
                        else:
                            st.success(f"✅ Đã đạt giới hạn tối đa {MAX_SKILLS} skills!")

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
                                group_counts = df[team_type].value_counts().to_dict()
                                
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
                    if pos_counts.get('CB', 0) < 2: missing_msg.append("Thiếu CB")
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
                        nations = set(p['Nation'] for p in all_valid_players if p['Nation'])
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

                with col_view1:
                    st.caption(f"📍 Sơ đồ Đá chính (11) - Chế độ xem: {metric_to_show if metric_to_show else 'Mặc định'}")
                    render_pitch_view(best_squad, highlight_type=metric_to_show)
                
                with col_view2:
                    st.caption("📋 Danh sách Đầy đủ (23)")
                    
                    s_df = pd.DataFrame(best_squad)
                    
                    if 'Is_Starter' in s_df.columns:
                        s_df['Role'] = s_df['Is_Starter'].apply(lambda x: "⭐ START" if x else "🔄 SUB")
                    
                    cols_show = ['Role', 'Position', 'Player', 'Rating', 'Club']
                    if build_mode == "Theo Chỉ số":
                        if "Cao" in stat_type or "Thấp" in stat_type: cols_show.append('Height')
                        elif "Nặng" in stat_type or "Nhẹ" in stat_type: cols_show.append('Weight')
                        elif "Trẻ" in stat_type or "Già" in stat_type: cols_show.append('Age')
                        elif "United Nations" in stat_type or "Quốc Gia" in stat_type: cols_show.append('Nation')
                        elif "Ambidextrous" in stat_type or "Chân" in stat_type: cols_show.append('Ambidextrous')
                        elif "Tanks" in stat_type or "Agiles" in stat_type or "BMI" in stat_type: cols_show.append('BMI')
                    
                    final_cols = [c for c in cols_show if c in s_df.columns]
                    
                    st.dataframe(
                        s_df[final_cols], 
                        hide_index=True, 
                        use_container_width=True, 
                        height=750,
                        column_config={
                            "Rating": st.column_config.NumberColumn("OVR", format="%d"),
                            "Player": st.column_config.TextColumn("Cầu thủ", width="medium"),
                            "Role": st.column_config.TextColumn("Vai trò", width="small"),
                        }
                    )

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
                                            
                                            import time
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
                                            
                                            import time
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
                                        
                                        import time
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ Không thể lưu dữ liệu vào Google Sheets!")
                                except Exception as e:
                                    st.error(f"❌ Lỗi khi lưu: {e}")
            
    elif current_tab == 'inventory':
        # Thêm CSS cho icons trắng
        st.markdown("""
            <style>
            div.stButton > button[key^="dec_"],
            div.stButton > button[key^="inc_"] {
                color: white !important;
                font-size: 1.2rem !important;
                font-weight: bold !important;
            }
            
            div.stButton > button[key^="dec_"] p,
            div.stButton > button[key^="inc_"] p {
                color: white !important;
            }
            
            /* Optional: Add hover effect */
            div.stButton > button[key^="inc_"]:hover {
                background: linear-gradient(135deg, #4ade80, #22c55e) !important;
            }
            
            div.stButton > button[key^="dec_"]:hover {
                background: linear-gradient(135deg, #ef4444, #dc2626) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.header("📦 Kho Skills")
        
        inventory = get_inventory()
        all_known_skills = get_all_known_skills()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tổng loại skills", len(all_known_skills))
        with col2:
            st.metric("Skills trong kho", len(inventory))
        with col3:
            total_count = sum(inventory.values())
            st.metric("Tổng số lượng", total_count)
        
        st.divider()
        
        with st.expander("➕ Thêm Skills vào kho", expanded=True):
            st.caption("Chọn skills và số lượng cần thêm")
            
            selected_skills_add = st.multiselect(
                "Chọn skills cần thêm",
                options=all_known_skills,
                default=[],
                key="quick_add_skills"
            )
            
            if selected_skills_add:
                add_col1, add_col2 = st.columns([3, 1])
                with add_col1:
                    add_quantity = st.number_input(
                        "Số lượng (mỗi skill)", 
                        min_value=1, 
                        max_value=100, 
                        value=1,
                        key="add_quantity"
                    )
                with add_col2:
                    st.write("")
                    st.write("")
                    if st.button("➕ Thêm vào kho", type="primary", use_container_width=True):
                        for skill in selected_skills_add:
                            update_inventory_count(skill, add_quantity)
                        st.success(f"✅ Đã thêm {len(selected_skills_add)} skills x {add_quantity}")
                        st.rerun()
        
        st.divider()
        
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search_filter = st.text_input("🔍 Tìm kiếm skill", placeholder="Nhập tên skill...")
        with filter_col2:
            show_mode = st.radio("Hiển thị", ["Tất cả", "Chỉ trong kho", "Chỉ chưa có"], horizontal=True, label_visibility="collapsed")
        
        if show_mode == "Chỉ trong kho":
            display_skills = [s for s in all_known_skills if inventory.get(s, 0) > 0]
        elif show_mode == "Chỉ chưa có":
            display_skills = [s for s in all_known_skills if inventory.get(s, 0) == 0]
        else:
            display_skills = all_known_skills
        
        if search_filter:
            display_skills = [s for s in display_skills if search_filter.lower() in s.lower()]
        
        st.caption(f"Hiển thị {len(display_skills)} skills")
        
        if not display_skills:
            st.info("🔍 Không tìm thấy skills nào")
        else:
            st.subheader("Danh sách Skills")
            
            for skill in display_skills:
                current_count = inventory.get(skill, 0)
                
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        if current_count > 0:
                            st.markdown(f"**{skill}** ✅")
                        else:
                            st.markdown(f"{skill}")
                    
                    with col2:
                        st.metric("Số lượng", current_count)
                    
                    with col3:
                        if st.button("➖", key=f"dec_{skill}", use_container_width=True, disabled=current_count == 0):
                            update_inventory_count(skill, -1)
                            st.rerun()
                    
                    with col4:
                        if st.button("➕", key=f"inc_{skill}", use_container_width=True):
                            update_inventory_count(skill, 1)
                            st.rerun()
        
        st.divider()
        with st.expander("⚙️ Thao tác nâng cao"):
            st.subheader("Nhập/Xuất dữ liệu")
            
            if st.button("📥 Xuất kho ra JSON", use_container_width=True):
                json_str = json.dumps(inventory, ensure_ascii=False, indent=2)
                st.download_button(
                    label="💾 Tải file JSON",
                    data=json_str,
                    file_name="skill_inventory.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            uploaded_file = st.file_uploader("📤 Nhập kho từ JSON", type=['json'])
            if uploaded_file:
                try:
                    imported_data = json.load(uploaded_file)
                    if st.button("✅ Xác nhận nhập kho", type="primary"):
                        save_skill_inventory_to_gsheet(imported_data)
                        st.success("✅ Đã nhập kho thành công!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi khi đọc file: {e}")
            
            st.divider()
            
            st.subheader("⚠️ Xóa kho")
            if st.button("🗑️ Xóa toàn bộ kho", type="secondary", use_container_width=True):
                if st.checkbox("Xác nhận xóa toàn bộ kho skills"):
                    save_skill_inventory_to_gsheet({})
                    st.success("✅ Đã xóa toàn bộ kho")
                    st.rerun()


if __name__ == "__main__":
    main()