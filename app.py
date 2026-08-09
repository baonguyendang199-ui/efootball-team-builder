# -*- coding: utf-8 -*-
# app.py – Efootball Team Builder (Google Sheets version)
import os
import shutil
import time
from pathlib import Path
from datetime import datetime
import re
from io import BytesIO
import hashlib
import uuid
from urllib.parse import quote, urlparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
import plotly.express as px
import streamlit as st
import json
from google.oauth2.service_account import Credentials
import gspread
import numpy as np
from scipy.optimize import linear_sum_assignment
import math

st.set_page_config(
    page_title="Efootball Team Builder",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EFConstants:
    POSITIONS = ['GK', 'CB', 'LB', 'RB', 'DMF', 'CMF', 'LMF', 'RMF', 'AMF', 'LWF', 'RWF', 'SS', 'CF']
    
    # Mapping nhóm chỉ số (Progression)
    PROG_STATS = [
        {'name': 'Shooting', 'affects': ['Finishing', 'Place Kicking', 'Curl']},
        {'name': 'Passing', 'affects': ['Low Pass', 'Lofted Pass']},
        {'name': 'Dribbling', 'affects': ['Ball Control', 'Dribbling', 'Tight Possession']},
        {'name': 'Dexterity', 'affects': ['Offensive Awareness', 'Acceleration', 'Balance']},
        {'name': 'Lower Body Strength', 'affects': ['Speed', 'Kicking Power', 'Stamina']},
        {'name': 'Aerial Strength', 'affects': ['Heading', 'Jump', 'Physical Contact']},
        {'name': 'Defending', 'affects': ['Defensive Awareness', 'Defensive Engagement', 'Tackling', 'Aggression']},
        {'name': 'GK 1', 'affects': ['Goalkeeping', 'Jump']},
        {'name': 'GK 2', 'affects': ['GK Parrying', 'GK Reach']},
        {'name': 'GK 3', 'affects': ['GK Catching', 'GK Reflexes']}
    ]

    # Hệ số quan trọng (Coefficients)
    COEFFICIENTS = {
        'Height':              [186, 136, 49, 49, 61, 37, 12, 12, 37, 49, 49, 62, 99],
        'Offensive Awareness': [0, 14, 61, 61, 61, 98, 98, 98, 171, 159, 159, 173, 210],
        'Ball Control':        [13, 27, 86, 86, 122, 171, 171, 171, 196, 159, 159, 210, 123],
        'Dribbling':           [0, 14, 61, 61, 37, 98, 110, 122, 122, 159, 159, 123, 62],
        'Tight Possession':    [0, 0, 37, 37, 24, 49, 73, 61, 73, 86, 86, 86, 37],
        'Low Pass':            [27, 41, 61, 61, 122, 208, 135, 135, 196, 73, 73, 99, 37],
        'Lofted Pass':         [40, 68, 147, 147, 122, 159, 196, 196, 159, 98, 98, 74, 12],
        'Finishing':           [0, 27, 24, 24, 37, 73, 86, 86, 184, 159, 159, 284, 358],
        'Place Kicking':       [0, 14, 24, 24, 12, 12, 24, 24, 12, 12, 12, 12, 12], 
        'Curl':                [0, 14, 24, 24, 12, 12, 24, 24, 12, 12, 12, 12, 12],
        'Heading':             [0, 55, 24, 24, 61, 24, 12, 12, 24, 24, 24, 25, 62],
        'Defensive Awareness': [13, 286, 147, 147, 220, 86, 49, 49, 24, 12, 12, 0, 0],
        'Defensive Engagement':[0, 14, 24, 24, 24, 24, 24, 24, 24, 24, 24, 12, 12],
        'Tackling':            [0, 191, 86, 86, 122, 86, 24, 24, 24, 12, 12, 12, 12],
        'Aggression':          [0, 82, 37, 37, 98, 37, 12, 12, 12, 12, 12, 12, 12],
        'Kicking Power':       [53, 27, 24, 24, 49, 73, 24, 24, 73, 61, 61, 99, 123],
        'Speed':               [13, 136, 220, 220, 61, 61, 196, 196, 98, 220, 220, 86, 99],
        'Acceleration':        [40, 150, 184, 184, 61, 86, 159, 159, 86, 159, 159, 99, 123],
        'Physical Contact':    [80, 204, 98, 98, 122, 49, 24, 24, 24, 37, 37, 37, 86],
        'Balance':             [0, 0, 24, 24, 12, 24, 61, 61, 24, 73, 73, 74, 86],
        'Jump':                [133, 109, 37, 37, 37, 12, 12, 12, 12, 24, 24, 37, 62],
        'Goalkeeping':         [279, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'GK Catching':         [226, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'GK Reach':            [226, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'GK Reflexes':         [173, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'GK Parrying':         [173, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'Stamina':             [0, 68, 196, 196, 196, 196, 147, 147, 86, 49, 49, 49, 37],
        'Weak Foot Accuracy':  [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
    }
    
    BOOSTERS = [
        {'name': 'None', 'stats': []},
        {'name': 'Accuracy', 'stats': ['Low Pass', 'Lofted Pass', 'Finishing', 'Kicking Power']},
        {'name': 'Aerial', 'stats': ['Finishing', 'Heading', 'Jump', 'Physical Contact']},
        {'name': 'Agility', 'stats': ['Speed', 'Acceleration', 'Balance', 'Stamina']},
        {'name': 'Ball-carrying', 'stats': ['Dribbling', 'Tight Possession', 'Speed', 'Balance']},
        {'name': 'Crossing', 'stats': ['Lofted Pass', 'Curl', 'Speed', 'Stamina']},
        {'name': 'Defending', 'stats': ['Defensive Awareness', 'Tackling', 'Acceleration', 'Jump']},
        {'name': 'Duel', 'stats': ['Defensive Awareness', 'Tackling', 'Speed', 'Stamina']},
        {'name': 'Fantasista', 'stats': ['Ball Control', 'Dribbling', 'Finishing', 'Balance']},
        {'name': 'Free-kick', 'stats': ['Finishing', 'Place Kicking', 'Curl', 'Kicking Power']},
        {'name': 'Goalkeeping', 'stats': ['Goalkeeping', 'GK Catching', 'GK Parrying', 'GK Reflexes']},
        {'name': 'Passing', 'stats': ['Low Pass', 'Lofted Pass', 'Curl', 'Kicking Power']},
        {'name': 'Physicality', 'stats': ['Jump', 'Physical Contact', 'Balance', 'Stamina']},
        {'name': 'Shooting', 'stats': ['Ball Control', 'Finishing', 'Kicking Power', 'Physical Contact']},
        {'name': 'Speed', 'stats': ['Speed', 'Acceleration', 'Dribbling', 'Stamina']},
        {'name': 'Strength', 'stats': ['Speed', 'Kicking Power', 'Jump', 'Physical Contact']},
        {'name': 'Technique', 'stats': ['Ball Control', 'Dribbling', 'Tight Possession', 'Low Pass']}
    ]

    @staticmethod
    def get_pos_idx(pos):
        return EFConstants.POSITIONS.index(pos) if pos in EFConstants.POSITIONS else 12

class EFMath:
    @staticmethod
    def get_points_for_level(max_level):
        # Logic tính tổng điểm có được khi đạt max level
        # Đây là ước lượng dựa trên đường cong chuẩn của game
        if max_level <= 1: return 0
        # Formula đơn giản hóa: (MaxLevel - 1) * 2
        return (max_level - 1) * 2

    @staticmethod
    def calc_cost(current_level):
        # Chi phí để nâng cấp stat tiếp theo
        # > 4: 1pt, >8: 2pts...
        if current_level < 4: return 1
        if current_level < 8: return 2
        if current_level < 12: return 3
        if current_level < 16: return 4
        if current_level < 20: return 5
        if current_level < 24: return 6
        return 7 # Cap cost

    @staticmethod
    def calculate_ovr(stats, pos_idx):
        k = 0
        for key, val in stats.items():
            if key in EFConstants.COEFFICIENTS:
                coef = EFConstants.COEFFICIENTS[key][pos_idx]
                if key == 'Weak Foot Accuracy':
                    val_calc = math.floor(59 * val / 3 + 40)
                    k += (val_calc - 25) * coef
                else:
                    k += (val - 25) * coef
        
        precise = math.floor(((k + 500) / 1000) * 100) / 100
        return precise

class EFAutoBuild:
    @staticmethod
    def optimize(base_stats, position, available_points):
        """Thuật toán Greedy để tự động phân phối điểm tối ưu OVR"""
        pos_idx = EFConstants.get_pos_idx(position)
        
        # Sao chép allocation hiện tại (bắt đầu từ 0)
        allocation = {stat['name']: 0 for stat in EFConstants.PROG_STATS}
        current_stats = base_stats.copy()
        remaining_points = available_points
        
        # Vòng lặp tối ưu
        while remaining_points > 0:
            best_stat_name = None
            best_efficiency = -1
            
            # Thử nâng cấp từng loại chỉ số
            for group in EFConstants.PROG_STATS:
                grp_name = group['name']
                curr_lvl = allocation[grp_name]
                
                # Check giới hạn
                if curr_lvl >= 99: continue # Không thể nâng quá 99
                
                # Tính chi phí
                cost = EFMath.calc_cost(curr_lvl)
                if cost > remaining_points: continue
                if cost == 0: cost = 1 # Tránh chia cho 0 (dù logic cost >=1)
                
                # Tính OVR tăng thêm bao nhiêu?
                # Thay vì tính lại toàn bộ OVR, ta tính tổng (Hệ số * 1) của các chỉ số con
                gain = 0
                for affected in group['affects']:
                    # Chỉ số hiện tại của stat con
                    curr_val = current_stats.get(affected, 40)
                    if curr_val >= 99: continue # Đã max stat con
                    
                    coef = EFConstants.COEFFICIENTS.get(affected, [0]*13)[pos_idx]
                    gain += coef # Tăng 1 đơn vị stat = tăng 'coef' điểm hệ số
                
                efficiency = gain / cost
                
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_stat_name = grp_name
            
            # Nếu tìm được nước đi tốt nhất
            if best_stat_name and best_efficiency > 0:
                cost = EFMath.calc_cost(allocation[best_stat_name])
                allocation[best_stat_name] += 1
                remaining_points -= cost
                
                # Update temp stats
                group = next(g for g in EFConstants.PROG_STATS if g['name'] == best_stat_name)
                for affected in group['affects']:
                    if affected in current_stats:
                        current_stats[affected] = min(current_stats[affected] + 1, 99)
            else:
                break # Không còn gì để nâng hoặc không đủ điểm
                
        return allocation, remaining_points

## Calculator removed


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

SPECIAL_SQUAD_OPTIONS = [
    ("🦶 The Ambidextrous (2 Chân Như 1)", "ambidextrous"),
    ("🟣 Form Is Temporary (Full POTW)", "potw_only"),
    ("🌍 United Nations (Đa Nation)", "united_nations"),
]
GENERIC_SQUAD_FIELDS = [
    ("Rating", "rating"),
    ("Height", "height"),
    ("Weight", "weight"),
    ("Age", "age"),
    ("BMI", "bmi"),
    ("Arm Length", "arm_length"),
    ("Shoulder Width", "shoulder_width"),
    ("Neck Length", "neck_length"),
    ("Chest Measurement", "chest_measurement"),
    ("Neck Size", "neck_size"),
    ("Shoulder Height", "shoulder_height"),
    ("Leg Length", "leg_length"),
    ("Thigh Size", "thigh_size"),
    ("Waist Size", "waist_size"),
    ("Arm Size", "arm_size"),
    ("Calf Size", "calf_size"),
    ("Leg Coverage Radius", "leg_coverage_radius"),
    ("Arm Coverage Radius", "arm_coverage_radius"),
    ("Jumping Height", "jumping_height"),
    ("Torso Collision", "torso_collision"),
    ("Leg Length Based Height", "leg_length_based_height"),
]
GENERIC_SORT_DIRECTIONS = [
    ("Highest first", "desc"),
    ("Lowest first", "asc"),
]
MAX_GENERIC_FIELD_VALUES = {
    'height': 250,
    'weight': 150,
    'age': 100,
    'rating': 150,
}


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
    base_rating = int(player_data.get('Rating', 0) or 0)
    rating = int(player_data.get('Effective_Nation_Rating', base_rating) or base_rating)
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
    if "SELL" in action:
        top_badge_html = f'<div style="position:absolute; top:35px; right:5px; background:#ef4444; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:4px; z-index:4; box-shadow:0 1px 3px rgba(0,0,0,0.5); transform: rotate(5deg);">SELL</div>'
    elif "KEEP" in action:
        top_badge_html = f'<div style="position:absolute; top:35px; right:5px; background:#22c55e; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:4px; z-index:4; box-shadow:0 1px 3px rgba(0,0,0,0.5); transform: rotate(-5deg);">KEEP</div>'

    booster_badge_html = ""
    if player_data.get('National Booster', False):
        b_peak = player_data.get('Booster Rating 11-23', '') or player_data.get('Effective_Nation_Rating', '')
        if b_peak:
            booster_badge_html = (
                f'<div style="position:absolute; top:5px; left:5px; '
                f'background:#7c3aed; color:white; font-size:8px; '
                f'font-weight:bold; padding:1px 5px; border-radius:3px; '
                f'z-index:5;">⚡{b_peak}</div>'
            )
    
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
                metric_val = f"{player_data.get('Age', '-')} yrs"
        except:
            pass
            
    metric_html = ""
    if metric_val:
        # LƯU Ý: Đoạn này phải viết liền 1 dòng, không được xuống dòng
        label_html = f"<span style='color:#94a3b8; font-weight:500; margin-right:4px'>{metric_label}:</span>" if metric_label else ""
        metric_html = f'<div style="position: absolute; bottom: 58px; left: 50%; transform: translateX(-50%); background: rgba(15, 23, 42, 0.95); color: {stat_color}; font-size: 10px; font-weight: 700; padding: 2px 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); z-index: 20; white-space: nowrap; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; align-items: center;">{label_html}<span>{metric_val}</span></div>'

    # --- HTML CARD TỔNG (CŨNG PHẢI 1 DÒNG) ---
    html = f"""<div class="e-card {card_class}" style="background: {bg_gradient}; width: {width};" title="{p_name} | {rating}">{metric_html}{top_badge_html}{booster_badge_html}<div class="shine"></div><div class="card-header"><div class="rating-box">{rating}</div><div class="position-box">{pos}</div></div><img src="{img_url}" class="player-img" onerror="this.src='https://pesdb.net/assets/img/card/f0.png'"><div class="card-info"><div class="player-name">{p_name}</div><div class="sub-info"><span style="opacity:0.9; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; max-width: 70%;">{club}</span><span>{str(player_data.get('Nation', ''))[:3].upper()}</span></div></div></div>"""
    
    return html

@st.dialog("Player Profile", width="large")
def show_player_modal(row):
    """
    Giao diện Scouting Profile - Phiên bản Fix lỗi hiển thị Code Text.
    Lưu ý: Các dòng HTML bên trong f-string phải viết sát lề trái.
    """
    # --- 1. CHUẨN BỊ DỮ LIỆU ---
    p_name = row.get('Player', 'Unknown')
    base_rating = int(row.get('Rating', 0) or 0)
    rating = int(row.get('Effective_Nation_Rating', base_rating) or base_rating)
    pos = row.get('Position', '?')
    style = row.get('Position Style', 'N/A')
    p_type = str(row.get('Player Type', 'Standard')).upper()
    club = row.get('Club', 'Unknown Club')
    nation = row.get('Nation', 'Unknown Nation')
    
    action = str(row.get('Action', 'N/A')).upper()
    reasons = str(row.get('Reasons', 'No analysis yet'))
    
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
    if not skills_html: skills_html = '<span style="color:#64748b; font-style:italic;">No skills yet</span>'

    # --- 2.5 BODY MODEL ---
    has_body_model = any(str(row.get(field, '') or '').strip() for field in PESDATA_BODY_MODEL_FIELDS)
    if has_body_model:
        body_items = []
        for field in PESDATA_BODY_MODEL_FIELDS:
            txt = str(row.get(field, '') or '').strip()
            if not txt:
                continue
            body_items.append(f'<div class="model-item"><div class="model-label">{field}</div><div class="model-value">{txt}</div></div>')
        body_model_html = '<div class="pf-section-title">Body Model</div><div class="model-grid">' + ''.join(body_items) + '</div>'
    else:
        body_model_html = ''

    # --- 3. REASONS BLOCK ---
    action_bg = "rgba(34, 197, 94, 0.2)" if "KEEP" in action else "rgba(239, 68, 68, 0.2)"
    action_border = "#22c55e" if "KEEP" in action else "#ef4444"
    action_text = "#4ade80" if "KEEP" in action else "#f87171"

    reasons_html = ""
    if action != "N/A" and action != "":
        # HTML viết sát lề trái
        reasons_html = f"""<div style="margin: 0 20px 10px 20px; padding: 12px; background: {action_bg}; border: 1px solid {action_border}; border-radius: 8px; display: flex; align-items: flex-start; gap: 10px;"><div style="font-weight: 800; font-size: 1.1rem; color: {action_text}; white-space: nowrap;">{action}</div><div style="font-size: 0.9rem; color: #e2e8f0; border-left: 1px solid rgba(255,255,255,0.2); padding-left: 10px; line-height: 1.4;"><div style="font-weight:600; font-size:0.75rem; color:#94a3b8; text-transform:uppercase; margin-bottom:2px;">STRATEGY ANALYSIS</div>{reasons}</div></div>"""

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
.model-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
.model-item {{ display: grid; grid-template-columns: 1fr auto; gap: 6px; padding: 8px 10px; background: rgba(255,255,255,0.04); border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); }}
.model-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
.model-value {{ font-size: 0.95rem; font-weight: 700; color: #e2e8f0; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
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
<div class="pf-section-title">Physical Stats</div>
<div class="stat-grid" style="margin-bottom: 20px;">
<div class="stat-item"><div class="stat-label">Height</div><div class="stat-val">{row.get('Height','-')} <small style="font-size:0.7em; color:#64748b">cm</small></div></div>
<div class="stat-item"><div class="stat-label">Weight</div><div class="stat-val">{row.get('Weight','-')} <small style="font-size:0.7em; color:#64748b">kg</small></div></div>
<div class="stat-item"><div class="stat-label">Age</div><div class="stat-val">{row.get('Age','-')}</div></div>
<div class="stat-item"><div class="stat-label">Preferred Foot</div><div class="stat-val">{row.get('Foot','-')}</div></div>
</div>
<div class="pf-section-title">Technique & Form</div>
<div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 8px;">
{render_stat_bar("Weak Foot Usage", row.get('Weak Foot Usage', '-'))}
{render_stat_bar("Weak Foot Accuracy", row.get('Weak Foot Accuracy', '-'))}
{render_stat_bar("Form / Condition", row.get('Form', '-'))}
{render_stat_bar("Injury Resistance", row.get('Injury Resistance', '-'), max_score=3)}
</div>
</div>
<div>
<div class="pf-section-title">Playing Style</div>
<div style="margin-bottom:20px; font-weight:600; font-size:1.1rem; color:{accent_color}">{style}</div>
<div class="pf-section-title">Skill List</div>
<div class="skill-container">{skills_html}</div>
{body_model_html}
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

    if row.get('National Booster', False):
        b1 = row.get('Booster Rating 1-7', 0)
        b2 = row.get('Booster Rating 8-10', 0)
        b3 = row.get('Booster Rating 11-23', 0)
        st.markdown(f"""
        <div style="margin:10px 0; padding:12px; background:rgba(124,58,237,0.15);
             border:1px solid #7c3aed; border-radius:8px;">
            <div style="font-weight:700; color:#a78bfa; margin-bottom:6px;">
                ⚡ National Booster Active
            </div>
            <div style="font-size:0.9rem; color:#e2e8f0; display:flex; gap:16px;">
                <span>🔵 1–7 players: <b>{b1}</b></span>
                <span>🟡 8–10 players: <b>{b2}</b></span>
                <span>🔴 11–23 players: <b>{b3}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer Actions
    st.write("")
    c1, c2 = st.columns([1, 4])
    with c1:
        if row.get('Player URL'):
            efhub_link = make_ehub_player_url(row.get('Player URL')) or row.get('Player URL')
            st.link_button("🌐 EFHub Link", efhub_link, use_container_width=True)
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
    top_positions_text = " & ".join(top_positions) if top_positions else "Multiple Positions"
    last_sync = datetime.now().strftime("%d/%m/%Y • %H:%M")
    
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-copy">
                <div class="hero-eyebrow">UI Refresh • {last_sync}</div>
                <h1>Control Center for Efootball Team Builder</h1>
                <p class="hero-desc">
                    The redesigned interface applies user-centric principles, visual hierarchy, 
                    WCAG accessibility, and AI support for the squad build workflow, 
                    helping the experience stay faster and consistent across devices.
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
                    <span>Total Players</span>
                    <strong>{total_players}</strong>
                    <small>{unique_clubs} clubs • {unique_leagues} leagues</small>
                </div>
                <div class="stat-card">
                    <span>Average Rating</span>
                    <strong>{avg_rating_display}</strong>
                    <small>Top positions: {top_positions_text}</small>
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
    """Connect to Google Sheets"""
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

@st.cache_data(ttl=60)
def load_data_from_gsheet():
    """Read data from Google Sheets"""
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
            "Player URL", "Player ID", "Skills", "Added Skills", "Secondary Positions",
            "National Booster", "Booster Type", "Booster Rating 1-7", "Booster Rating 8-10", "Booster Rating 11-23",
            *PESDATA_BODY_MODEL_FIELDS
        ]
        for col in required_cols:
            if col not in df.columns:
                if col == "Rating":
                    df[col] = 0
                elif col == "Booster Type":
                    df[col] = "None"
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
            "Player URL", "Player ID", "Skills", "Added Skills", "Secondary Positions", "Booster Type",
            *PESDATA_BODY_MODEL_FIELDS
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

        # Migrate legacy column names if present
        _legacy_cols = {
            'Has_National_Booster': 'National Booster',
            'Booster_Rating_1_7': 'Booster Rating 1-7',
            'Booster_Rating_8_10': 'Booster Rating 8-10',
            'Booster_Rating_11_23': 'Booster Rating 11-23',
        }
        for old_col, new_col in _legacy_cols.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]

        if 'Booster Type' not in df.columns:
            df['Booster Type'] = df['National Booster'].apply(lambda v: 'National' if _parse_bool(v) else 'None') if 'National Booster' in df.columns else 'None'
        else:
            df['Booster Type'] = df['Booster Type'].apply(_normalize_booster_type)
            if 'National Booster' in df.columns:
                df.loc[df['Booster Type'] == 'None', 'Booster Type'] = df.loc[df['Booster Type'] == 'None', 'National Booster'].apply(lambda v: 'National' if _parse_bool(v) else 'None')

        df['Booster Type'] = df['Booster Type'].apply(_normalize_booster_type)
        df['National Booster'] = df['Booster Type'].apply(lambda t: t == 'National')

        df = apply_national_booster(df)
        df = apply_club_league_booster(df)
        df = calculate_top23_count(df)
        
        return df
    except Exception as e:
        st.error(f"❌ Error reading data: {e}")
        return pd.DataFrame()

def save_data_to_gsheet(df):
    """Write data to Google Sheets"""
    try:
        # Check if dataframe is empty
        if df.empty:
            st.error("⚠️ Cannot save: DataFrame is empty!")
            return False
            
        client = get_gsheet_connection()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        
        # Remove Epic_Priority column before saving
        df_save = df.drop(columns=['Epic_Priority', 'Effective_Nation_Rating', 'Effective_Club_Rating', 'Effective_League_Rating', 'Top23_Count'], errors='ignore').copy()
        
        # CRITICAL: Replace NaN/inf values with empty string or 0
        # This prevents JSON error when saving to Google Sheets
        df_save = df_save.fillna('')  # Fill NaN with empty string
        
        # Replace inf values if any
        df_save = df_save.replace([float('inf'), float('-inf')], '')
        
        # Check again after cleaning
        if df_save.empty:
            st.error("⚠️ Cannot save: DataFrame is empty after processing!")
            return False
        
        # Clear and update
        sheet.clear()
        sheet.update([df_save.columns.values.tolist()] + df_save.values.tolist())
        return True
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")
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
        "Captaincy", "Sole Control", "Outside Curler",
        "Heel Trick"
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
    _RANK_COL = {'Nation': 'Effective_Nation_Rating', 'Club': 'Effective_Club_Rating', 'League': 'Effective_League_Rating'}
    _candidate = _RANK_COL.get(group_by, 'Rating')
    rank_col = _candidate if _candidate in group_df.columns else 'Rating'
    if group_by in ['Nation', 'League']:
        group_df = group_df.sort_values(['Player', rank_col, 'Epic_Priority'], ascending=[True, False, True])
        group_df = group_df.drop_duplicates(subset=['Player'], keep='first')

    # Xác định các tiêu chí sắp xếp
    sort_keys = [rank_col, 'Epic_Priority']
    sort_asc = [False, True]
    
    # THÊM TIÊU CHÍ ƯU TIÊN MỚI: Top23_Count (chỉ áp dụng cho Nation/League khi bị tie)
    if group_by in ['Nation', 'League'] and 'Top23_Count' in group_df.columns:
        sort_keys.append('Top23_Count')
        sort_asc.append(False) # False = Giảm dần
    
    # Sort theo các tiêu chí đã định
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

def _parse_bool(val) -> bool:
    """Parse boolean from Google Sheets cell (handles TRUE/True/1/YES/''/False etc.)."""
    return str(val).strip().upper() in ("TRUE", "YES", "1", "Y")


def _normalize_booster_type(val: str) -> str:
    """Normalize booster type values from sheet or form inputs."""
    if val is None:
        return 'None'
    text = str(val).strip().title()
    if text in ['National', 'Club', 'League']:
        return text
    if 'club' in text.lower():
        return 'Club'
    if 'league' in text.lower():
        return 'League'
    if 'nation' in text.lower() or 'potw' in text.lower():
        return 'National'
    return 'None'


def apply_national_booster(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Effective_Nation_Rating for each player.
    For National Booster cards, the effective rating for Nation ranking is a
    depth-tiered boosted value. For all other cards it equals the base Rating.
    Depth = number of DISTINCT player names of that nationality in the full squad.
    """
    if 'National Booster' not in df.columns:
        df['National Booster'] = False
    for col in ['Booster Rating 1-7', 'Booster Rating 8-10', 'Booster Rating 11-23']:
        if col not in df.columns:
            df[col] = 0

    df['National Booster'] = df['National Booster'].apply(_parse_bool)

    for col in ['Booster Rating 1-7', 'Booster Rating 8-10', 'Booster Rating 11-23']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['Effective_Nation_Rating'] = df['Rating'].copy()

    nation_depth = df.groupby('Nation')['Player'].nunique()

    def _boosted_rating(row):
        if row.get('Booster Type', 'None') != 'National':
            return row['Rating']
        depth = int(nation_depth.get(row['Nation'], 0))
        if depth <= 7:
            val = row['Booster Rating 1-7']
        elif depth <= 10:
            val = row['Booster Rating 8-10']
        else:
            val = row['Booster Rating 11-23']
        return int(val) if val > 0 else row['Rating']

    df['Effective_Nation_Rating'] = df.apply(_boosted_rating, axis=1)
    return df


def apply_club_league_booster(df: pd.DataFrame) -> pd.DataFrame:
    for col in ['Booster Rating 1-7', 'Booster Rating 8-10', 'Booster Rating 11-23']:
        if col not in df.columns:
            df[col] = 0

    df['Effective_Club_Rating']   = df['Rating'].copy()
    df['Effective_League_Rating'] = df['Rating'].copy()

    club_depth   = df.groupby(['Club',   'Nation'])['Player'].nunique()
    league_depth = df.groupby(['League', 'Nation'])['Player'].nunique()

    def _boosted(row, depth, booster_type):
        if row.get('Booster Type', 'None') != booster_type:
            return row['Rating']
        if depth <= 7:
            val = row['Booster Rating 1-7']
        elif depth <= 10:
            val = row['Booster Rating 8-10']
        else:
            val = row['Booster Rating 11-23']
        return int(val) if val > 0 else row['Rating']

    df['Effective_Club_Rating'] = df.apply(
        lambda r: _boosted(r, int(club_depth.get((r['Club'], r['Nation']), 0)), 'Club'), axis=1
    )
    df['Effective_League_Rating'] = df.apply(
        lambda r: _boosted(r, int(league_depth.get((r['League'], r['Nation']), 0)), 'League'), axis=1
    )
    return df


def apply_squad_national_boosters(squad, nation_build=False, filter_col=None):
    """
    Show effective rating on pitch cards based on the ACTUAL squad depth
    within the built 23-man squad (starters + bench) - not the whole player pool.
    This supports National, Club, and League booster types.
    """
    nation_count_in_squad = {}
    club_count_in_squad = {}
    league_count_in_squad = {}

    for p in squad:
        if p.get('Player') and p['Player'] != '---':
            data = p.get('Data', {})
            nation = str(data.get('Nation', '')).strip()
            club = str(data.get('Club', '')).strip()
            league = str(data.get('League', '')).strip()
            if nation:
                nation_count_in_squad[nation] = nation_count_in_squad.get(nation, 0) + 1
            if club and nation:
                club_count_in_squad[(club, nation)] = club_count_in_squad.get((club, nation), 0) + 1
            if league and nation:
                league_count_in_squad[(league, nation)] = league_count_in_squad.get((league, nation), 0) + 1

    def _tier_value(data_dict, depth):
        if depth <= 7:
            val = data_dict.get('Booster Rating 1-7', 0)
        elif depth <= 10:
            val = data_dict.get('Booster Rating 8-10', 0)
        else:
            val = data_dict.get('Booster Rating 11-23', 0)
        try:
            val = int(val)
        except (TypeError, ValueError):
            val = 0
        base = data_dict.get('Rating', 0)
        return val if val > 0 else int(base)

    for p in squad:
        if p.get('Player') and p['Player'] != '---':
            data = p.get('Data', {})
            booster_type = _normalize_booster_type(data.get('Booster Type', 'None'))
            if booster_type == 'None':
                continue

            nation = str(data.get('Nation', '')).strip()
            if booster_type == 'National':
                depth = nation_count_in_squad.get(nation, 0)
            elif booster_type == 'Club':
                depth = club_count_in_squad.get((str(data.get('Club', '')).strip(), nation), 0)
            elif booster_type == 'League':
                depth = league_count_in_squad.get((str(data.get('League', '')).strip(), nation), 0)
            else:
                depth = 0

            p['Rating'] = _tier_value(data, depth)
    return squad


def build_squad_based_effective_ratings(df: pd.DataFrame, squad: list) -> pd.DataFrame:
    """
    Recompute effective ratings for the full player pool based on the actual depth
    inside a built squad (starters + bench), mirroring Squad Builder's logic.
    """
    out_df = df.copy()

    if 'National Booster' not in out_df.columns:
        out_df['National Booster'] = False
    for col in ['Booster Rating 1-7', 'Booster Rating 8-10', 'Booster Rating 11-23']:
        if col not in out_df.columns:
            out_df[col] = 0

    out_df['National Booster'] = out_df['National Booster'].apply(_parse_bool)
    for col in ['Booster Rating 1-7', 'Booster Rating 8-10', 'Booster Rating 11-23']:
        out_df[col] = pd.to_numeric(out_df[col], errors='coerce').fillna(0).astype(int)

    def _depth_map_for(group_col: str) -> dict:
        depth = {}
        for p in squad or []:
            if not p.get('Player') or p['Player'] == '---':
                continue
            data = p.get('Data', {})
            nation = str(data.get('Nation', '')).strip()
            value = str(data.get(group_col, '')).strip()
            if not value:
                continue

            if group_col == 'Nation':
                key = nation
            elif group_col == 'Club':
                key = (value, nation)
            elif group_col == 'League':
                key = (value, nation)
            else:
                key = value

            if key:
                depth[key] = depth.get(key, 0) + 1
        return depth

    def _tier_value(data_dict, depth):
        if depth <= 7:
            val = data_dict.get('Booster Rating 1-7', 0)
        elif depth <= 10:
            val = data_dict.get('Booster Rating 8-10', 0)
        else:
            val = data_dict.get('Booster Rating 11-23', 0)
        try:
            val = int(val)
        except (TypeError, ValueError):
            val = 0
        base = data_dict.get('Rating', 0)
        return val if val > 0 else base

    def _effective_for(row, group_col, depth_map, booster_type):
        if str(row.get('Booster Type', 'None')).strip().title() != booster_type:
            return row.get('Rating', 0)
        value = str(row.get(group_col, '')).strip()
        depth = int(depth_map.get(value, 0))
        return _tier_value(row.to_dict(), depth)

    nation_depth = _depth_map_for('Nation')
    club_depth = _depth_map_for('Club')
    league_depth = _depth_map_for('League')

    out_df['Effective_Nation_Rating'] = out_df.apply(
        lambda r: _effective_for(r, 'Nation', nation_depth, 'National'), axis=1
    )
    out_df['Effective_Club_Rating'] = out_df.apply(
        lambda r: _effective_for(r, 'Club', club_depth, 'Club'), axis=1
    )
    out_df['Effective_League_Rating'] = out_df.apply(
        lambda r: _effective_for(r, 'League', league_depth, 'League'), axis=1
    )

    return out_df


def get_top23_indices(df: pd.DataFrame, group_by: str, max_size: int = 23) -> set:
    """Lấy index của Top 23 cầu thủ cho 1 nhóm (Nation/League/Club) - Logic tương tự build_top23_map nhưng chỉ lấy index."""
    top_indices = set()
    values = [v for v in df[group_by].dropna().astype(str).unique() if v.strip()]
    
    for value in values:
        gdf = df[df[group_by].astype(str) == value].copy()
        if gdf.empty:
            continue

        _RANK_COL = {'Nation': 'Effective_Nation_Rating', 'Club': 'Effective_Club_Rating', 'League': 'Effective_League_Rating'}
        _candidate = _RANK_COL.get(group_by, 'Rating')
        primary_sort_key = _candidate if _candidate in gdf.columns else 'Rating'
            
        if group_by in ['Nation', 'League']:
            # Type trùng tên, giữ thẻ tốt nhất
            gdf = gdf.sort_values(['Player', primary_sort_key, 'Epic_Priority'], ascending=[True, False, True])
            gdf = gdf.drop_duplicates(subset=['Player'], keep='first')
            
        # Sort cơ bản: Rating, Epic_Priority
        # **Lưu ý: Không dùng Top23_Count ở đây để tránh vòng lặp phụ thuộc**
        gdf = gdf.sort_values([primary_sort_key, 'Epic_Priority'], ascending=[False, True]).head(max_size)
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
    #    a) Player nằm trong Top 23 của team đó (raw indices)
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
    """Read skill inventory from Google Sheets"""
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
        st.error(f"❌ Error reading inventory from Google Sheets: {e}")
        return {}

def save_skill_inventory_to_gsheet(inventory):
    """Save skill inventory to Google Sheets"""
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
        st.error(f"❌ Error saving inventory: {e}")
        return False

# --- GK INVENTORY SYSTEM ---
GK_SKILLS_PRIORITY_LIST = [
    "GK Low Punt", "GK High Punt", "GK Long Throw", "GK Penalty Saver", 
    "Fighting Spirit", "Low Lofted Pass", "One-touch Pass", "Through Passing", 
    "Weighted Pass", "Outside Curler", "Sole Control", "Heel Trick", "Captaincy"
]

@st.cache_data(ttl=10)
def get_gk_inventory_from_gsheet():
    """Read GK skill inventory separately"""
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
        st.error(f"❌ GK Inventory error: {e}")
        return {}

def save_gk_inventory_to_gsheet(inventory):
    """Save GK inventory"""
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
        st.error(f"❌ Error saving GK inventory: {e}")
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
        st.error(f"⚠️ Update error: {e}")
        return False

def get_inventory():
    """Get inventory (with cache)"""
    return get_inventory_from_gsheet()

# --- CONFIG ---
MAX_SQUAD_SIZE = 23


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
    "4-3-1-2 (2 CF, 1 SS)": ["GK", "LB", "CB", "CB", "RB", "DMF", "CMF", "CMF", "SS", "CF", "CF"],
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
    "4-3-1-2 (2 CF, 1 SS)":[
        (92, 50), (78, 15), (82, 38), (82, 62), (78, 85), (68, 50), (50, 30), (50, 70), (20, 50), (15, 35), (15, 65)
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
        (92, 50), (80, 25), (82, 50), (80, 75),   # GK, 3 CBs
        (55, 10), (55, 90), (60, 35), (60, 65),   # LMF, RMF, 2 CMs
        (22, 20), (22, 80), (15, 50)               # LWF, CF, RWF
    ],
    "3-4-3 (Pressing)": [
        (92, 50), (78, 25), (80, 50), (78, 75),   # GK, 3 CBs (pushed higher)
        (50, 10), (50, 90), (55, 35), (55, 65),   # wider MFs, higher press
        (18, 20), (18, 80), (12, 50)               # forwards closer to goal
    ],
    "3-4-3 (Defensive)": [
        (92, 50), (82, 25), (84, 50), (82, 75),   # GK, 3 CBs (deep)
        (62, 10), (62, 90), (65, 35), (65, 65),   # MFs sitting deep
        (28, 20), (28, 80), (22, 50)               # forwards deeper starting
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
    if filter_col and filter_val and filter_val != "(All)":
        pool_df = pool_df[pool_df[filter_col].astype(str) == filter_val]
    if pool_df.empty: return []

    _BUILD_COL = {'Nation': 'Effective_Nation_Rating', 'Club': 'Effective_Club_Rating', 'League': 'Effective_League_Rating'}
    _bcol = _BUILD_COL.get(filter_col, 'Rating')
    pool_df['_build_rating'] = pool_df[_bcol] if _bcol in pool_df.columns else pool_df['Rating']

    # Sort sơ bộ
    pool_df = pool_df.sort_values(['_build_rating', 'Epic_Priority'], ascending=[False, True])
    pool_df = pool_df.drop_duplicates(subset=['Player'], keep='first')
    pool_df = pool_df.reset_index(drop=True)

# --- LOGIC MỚI CHO UNITED NATIONS (DÒNG 844) ---
    if sort_mode == 'united_nations':
        # BƯỚC 1: Sort toàn bộ theo Rating
        pool_df = pool_df.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
        
        # BƯỚC 2: Lấy đại diện XUẤT SẮC NHẤT mỗi quốc gia
        # ✅ FIX: Giữ nguyên pool_df gốc, chỉ tạo pool phụ cho Starters
        pool_df_nations = pool_df.drop_duplicates(subset=['Nation'], keep='first').copy()
        
        # BƯỚC 3: Đảm bảo có GK
        if 'GK' not in pool_df_nations['Position'].values:
            current_nations = pool_df_nations['Nation'].unique()
            extra_gks = pool_df[(pool_df['Position'] == 'GK') & 
                               (~pool_df['Nation'].isin(current_nations))]
            extra_gks = extra_gks.sort_values('Rating', ascending=False).head(3)
            pool_df_nations = pd.concat([pool_df_nations, extra_gks]).reset_index(drop=True)
        
        # ✅ FIX: GHI ĐÈ pool_df để Hungarian Algorithm sử dụng
        pool_df = pool_df_nations.reset_index(drop=True)

    required_positions = FORMATIONS.get(formation_name, [])
    if not required_positions:
        return []
    unique_formation_positions = set(required_positions)

    # 3. HỆ THỐNG TÍNH ĐIỂM (SCORING)
    ERROR_SCORE = -999999

    def calculate_score(row):
        eff_rating = row['_build_rating']
        rating_bonus = eff_rating / 100000.0 
        
        if sort_mode == 'rating_desc': 
            return eff_rating
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
            return eff_rating + tier_score + sub_tier_bonus
        elif sort_mode == 'potw_only':
            ptype = str(row.get('Player Type', '')).upper()
            is_potw = 'POTW' in ptype or 'TRENDING' in ptype
            return (10000 if is_potw else 0) + eff_rating
        elif '_' in sort_mode:
            field, direction = sort_mode.rsplit('_', 1)
            field = field.lower()
            direction = direction.lower()
            if field == 'bmi':
                h_m = row['Height_num'] / 100.0
                w = row['Weight_num']
                if h_m < 1.0 or w < 30:
                    return ERROR_SCORE
                bmi = w / (h_m ** 2)
                if direction == 'desc':
                    return (bmi * 1000) + rating_bonus
                return ((100 - bmi) * 1000) + rating_bonus
            if field == 'rating':
                return eff_rating if direction == 'desc' else -eff_rating
            if field != 'bmi':
                label = field.replace('_', ' ').title()
                if field in ['height', 'weight', 'age']:
                    val = row.get(f"{label}_num", 0.0)
                else:
                    raw_val = row.get(label, row.get('Data', {}).get(label, 0.0))
                    try:
                        val = float(re.sub(r'[^\d.]', '', str(raw_val).replace(',', '.')))
                    except ValueError:
                        val = 0.0
                return val + rating_bonus if direction == 'desc' else -val + rating_bonus

    pool_df['Build_Score'] = pool_df.apply(calculate_score, axis=1)

    def _select_squad(pdf):
        num_players = len(pdf)
        num_slots = len(required_positions)
        BIG_PENALTY = 1e9
        cost_matrix = np.full((num_players, num_slots), BIG_PENALTY)

        for p_idx, row in pdf.iterrows():
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

        try:
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
        except Exception:
            return [], pdf

        fsquad = [None] * 11
        used_idx = set()

        for i in range(len(row_ind)):
            p_idx = row_ind[i]; s_idx = col_ind[i]
            if cost_matrix[p_idx, s_idx] < (BIG_PENALTY / 2):
                row = pdf.iloc[p_idx]
                pid = str(row.get('Player ID', '')).strip()
                purl = str(row.get('Player URL', '')).strip()
                if not pid and purl:
                    m = re.search(r"(\d{14,})", purl); pid = m.group(1) if m else ""
                img_url = f"https://pesdb.net/assets/img/card/f{pid}.png" if pid else None

                fsquad[s_idx] = {
                    "Is_Starter": True, "Position": required_positions[s_idx],
                    "Real_Position": row['Position'], "Player": row['Player'],
                    "Rating": row['Rating'], "Type": row['Player Type'], "Image": img_url,
                    "Height": row.get('Height', ''), "Weight": row.get('Weight', ''),
                    "Age": row.get('Age', ''), "Score": row['Build_Score'], "Data": row.to_dict()
                }
                used_idx.add(p_idx)

        for i in range(11):
            if fsquad[i] is None:
                fsquad[i] = {"Is_Starter": True, "Position": required_positions[i], "Player": "---", "Rating": 0, "Type": "N/A", "Score": -9999, "Image": None}

        # --- CHỌN DỰ BỊ (DRAFTING) ---
        remaining_pool = pdf[~pdf.index.isin(used_idx)].copy()
        remaining_pool = remaining_pool[remaining_pool['Build_Score'] != ERROR_SCORE]

        bench_picks = []
        bench_pos_counts = {}
        gk_on_bench_count = 0
        used_nations_local = set()
        MAX_BENCH = 12

        num_starting_cbs = required_positions.count('CB')
        max_cb_subs_allowed = 3 if num_starting_cbs >= 3 else 2

        remaining_pool['_pos'] = remaining_pool['Position'].astype(str).str.strip().str.upper()
        remaining_pool['_nation'] = remaining_pool['Nation'].astype(str).str.strip()

        def _can_fit_formation(row):
            secs = [s.strip().upper() for s in str(row.get('Secondary Positions', '')).split(',') if s.strip()]
            return bool(set([row['_pos']] + secs).intersection(unique_formation_positions))
        remaining_pool['_fits_formation'] = remaining_pool.apply(_can_fit_formation, axis=1)
        remaining_pool['_fit_bonus'] = remaining_pool['_pos'].apply(lambda p: 0.2 if p in unique_formation_positions else 0.0)

        if sort_mode in ['height_desc', 'weight_desc']:
            _useful = {'LB', 'RB', 'DMF', 'CMF', 'LWF', 'RWF', 'SS', 'CF', 'AMF', 'LMF', 'RMF'}
            def _is_cb_versatile(row):
                secs = {s.strip().upper() for s in str(row.get('Secondary Positions', '')).split(',') if s.strip()}
                return bool(secs.intersection(_useful))
            remaining_pool['_cb_versatile'] = remaining_pool.apply(_is_cb_versatile, axis=1)
        else:
            remaining_pool['_cb_versatile'] = False

        for _ in range(MAX_BENCH):
            if remaining_pool.empty:
                break

            mask = remaining_pool['_fits_formation']

            if gk_on_bench_count >= 1:
                mask = mask & (remaining_pool['_pos'] != 'GK')

            if sort_mode in ['height_desc', 'weight_desc']:
                cb_count = bench_pos_counts.get('CB', 0)
                if cb_count >= max_cb_subs_allowed:
                    mask = mask & ~((remaining_pool['_pos'] == 'CB') & ~remaining_pool['_cb_versatile'])

            if sort_mode == 'united_nations':
                mask = mask & ~remaining_pool['_nation'].isin(used_nations_local)

            candidates = remaining_pool[mask].copy()
            if candidates.empty:
                break

            candidates['_saturation'] = candidates['_pos'].map(lambda p: bench_pos_counts.get(p, 0) * 0.1)
            candidates['Draft_Score'] = candidates['Build_Score'] + candidates['_fit_bonus'] - candidates['_saturation']

            candidates = candidates.sort_values(['Draft_Score', '_build_rating'], ascending=[False, False])
            best_pick = candidates.iloc[0]

            bench_picks.append(best_pick)

            picked_pos = best_pick['_pos']
            bench_pos_counts[picked_pos] = bench_pos_counts.get(picked_pos, 0) + 1

            if picked_pos == 'GK':
                gk_on_bench_count += 1
            if sort_mode == 'united_nations':
                used_nations_local.add(best_pick['_nation'])

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

            fsquad.append({
                "Is_Starter": False, "Position": r_get('Position'), "Player": r_get('Player'),
                "Rating": r_get('Rating'), "Type": r_get('Player Type'), "Image": img_url,
                "Height": r_get('Height', ''), "Weight": r_get('Weight', ''), "Age": r_get('Age', ''),
                "Score": r_get('Build_Score'), "Data": row.to_dict() if hasattr(row, 'to_dict') else row
            })

        return fsquad, pdf

    # ==========================================================
    # 5. VÒNG LẶP HỘI TỤ (FIXED-POINT ITERATION)
    #    Build thử -> tính depth thực tế trong squad vừa build ->
    #    cập nhật lại _build_rating cho Booster Type National/Club/League
    #    rồi build lại. Lặp đến khi đội hình không đổi nữa.
    # ==========================================================
    def _depth_maps_of(fsquad):
        nation_depth = {}
        club_depth = {}
        league_depth = {}
        for p in fsquad:
            if p.get('Player') and p['Player'] != '---':
                data = p.get('Data', {})
                nation = str(data.get('Nation', '')).strip()
                club = str(data.get('Club', '')).strip()
                league = str(data.get('League', '')).strip()

                if nation:
                    nation_depth[nation] = nation_depth.get(nation, 0) + 1
                if club and nation:
                    club_depth[(club, nation)] = club_depth.get((club, nation), 0) + 1
                if league and nation:
                    league_depth[(league, nation)] = league_depth.get((league, nation), 0) + 1

        return nation_depth, club_depth, league_depth

    def _tier_value(data_dict, depth):
        if depth <= 7:
            val = data_dict.get('Booster Rating 1-7', 0)
        elif depth <= 10:
            val = data_dict.get('Booster Rating 8-10', 0)
        else:
            val = data_dict.get('Booster Rating 11-23', 0)
        try:
            val = int(val)
        except (TypeError, ValueError):
            val = 0
        base = data_dict.get('Rating', 0)
        return val if val > 0 else base

    def _refresh_build_rating(row, nation_depth, club_depth, league_depth):
        booster_type = _normalize_booster_type(row.get('Booster Type', 'None'))
        if booster_type == 'National':
            depth = nation_depth.get(str(row.get('Nation', '')).strip(), 0)
        elif booster_type == 'Club':
            depth = club_depth.get((str(row.get('Club', '')).strip(), str(row.get('Nation', '')).strip()), 0)
        elif booster_type == 'League':
            depth = league_depth.get((str(row.get('League', '')).strip(), str(row.get('Nation', '')).strip()), 0)
        else:
            return row.get('_build_rating', row.get('Rating', 0))
        return _tier_value(row.to_dict(), depth)

    MAX_ITER = 8
    prev_signature = None
    seen_signatures = set()
    final_squad = []

    for _iter_n in range(MAX_ITER):
        final_squad, pool_df = _select_squad(pool_df)
        if not final_squad:
            break

        signature = tuple(sorted(
            p.get('Player', '') for p in final_squad
            if p.get('Player') and p['Player'] != '---'
        ))

        if signature == prev_signature:
            break
        if signature in seen_signatures:
            break
        seen_signatures.add(signature)
        prev_signature = signature

        pool_df = pool_df.copy()
        nation_depth, club_depth, league_depth = _depth_maps_of(final_squad)
        pool_df['_build_rating'] = pool_df.apply(
            lambda r: _refresh_build_rating(r, nation_depth, club_depth, league_depth), axis=1
        )

    return apply_squad_national_boosters(final_squad, filter_col=filter_col)

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
    # Ví dụ: Thiếu 1 người bị trừ 1 tỷ points remaining. Thiếu 2 người bị trừ 2 tỷ points remaining.
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
    if sort_mode.startswith('rating'):
        highlight_type = 'Rating'
        is_reverse = 'asc' not in sort_mode
    elif sort_mode.startswith('height'):
        highlight_type = 'Height'
        is_reverse = 'asc' not in sort_mode
    elif sort_mode.startswith('weight'):
        highlight_type = 'Weight'
        is_reverse = 'asc' not in sort_mode
    elif sort_mode.startswith('age'):
        highlight_type = 'Age'
        is_reverse = 'asc' not in sort_mode
    elif sort_mode.startswith('bmi'):
        highlight_type = 'BMI'
        is_reverse = 'asc' not in sort_mode
    elif sort_mode == 'potw_only':
        highlight_type = 'Type'
    elif sort_mode == 'ambidextrous':
        highlight_type = 'Ambidextrous'
    elif sort_mode == 'united_nations':
        highlight_type = 'Nation'
    elif '_' in sort_mode:
        highlight_type = sort_mode.rsplit('_', 1)[0].replace('_', ' ').title()
        is_reverse = 'asc' not in sort_mode

    # --- 2. TÁCH ĐÁ CHÍNH & DỰ BỊ ---
    starters = squad_list[:11]
    raw_subs = squad_list[11:]

    # --- 3. SORT DỰ BỊ ---
    def get_sort_value(p, key):
        raw = p.get(key, None)
        if raw is None and isinstance(p.get('Data', None), dict):
            raw = p['Data'].get(key, None)
        try: return float(re.sub(r'[^\d.]', '', str(raw or '0')))
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
    elif highlight_type not in ['Type', 'Nation', None]:
        subs = sorted(raw_subs, key=lambda x: get_sort_value(x, highlight_type), reverse=is_reverse)
    else: subs = sorted(raw_subs, key=lambda x: x.get('Rating', 0), reverse=True)

    # --- 4. HTML GENERATOR ---
    def create_card_html(p, top=None, left=None, is_sub=False):
        full_name = p['Player'].strip()
        name_parts = full_name.split()
        display_name = name_parts[-1].upper() if len(name_parts) > 1 else full_name.upper()
        if len(display_name) > 9: display_name = display_name[:8] + "."

        pos = p['Position']
        img = p['Image'] if p['Image'] else "https://pesdb.net/assets/img/card/f0.png"

        data = p.get('Data', {})
        base_rating = int(data.get('Rating', p['Rating']) or p['Rating'])
        booster_type = _normalize_booster_type(data.get('Booster Type', 'None'))
        rating = int(p.get('Rating', base_rating) or base_rating)

        booster_badge = ""
        if booster_type != 'None' and rating > base_rating:
            booster_badge = (
                '<div style="position:absolute; top:2px; left:2px; background:#7c3aed; '
                'color:white; font-size:7px; font-weight:bold; padding:1px 4px; '
                'border-radius:3px; z-index:21;">&#9889;</div>'
            )
        
        # Logic Stat Tag
        val_display = ""
        metric_label = ""
        def get_data_value(key):
            raw = p.get(key, None)
            if raw is None and isinstance(data, dict):
                raw = data.get(key, None)
            return raw

        if highlight_type == 'Height':
            raw = get_data_value('Height')
            val_display = f"{raw} cm" if raw not in [None, ''] else ''
        elif highlight_type == 'Weight':
            raw = get_data_value('Weight')
            val_display = f"{raw} kg" if raw not in [None, ''] else ''
        elif highlight_type == 'Age':
            raw = get_data_value('Age')
            val_display = f"{raw} yrs" if raw not in [None, ''] else ''
        elif highlight_type == 'BMI':
            try:
                h = float(re.sub(r'[^\d.]', '', str(get_data_value('Height') or '0'))) / 100.0
                w = float(re.sub(r'[^\d.]', '', str(get_data_value('Weight') or '0')))
                if h > 0:
                    val_display = f"{(w/(h**2)):.1f}"
                    metric_label = 'BMI'
            except:
                pass
        elif highlight_type == 'Ambidextrous':
            d = data or {}
            def get_wf_num(text):
                t = str(text).strip().lower()
                if any(k in t for k in ['very high', 'regularly', '4']): return '4'
                if any(k in t for k in ['high', 'occasionally', '3']): return '3'
                if any(k in t for k in ['medium', 'rarely', '2']): return '2'
                return '1'
            u = get_wf_num(d.get('Weak Foot Usage', ''))
            a = get_wf_num(d.get('Weak Foot Accuracy', ''))
            val_display = f"🦶{u} | 🎯{a}"
            metric_label = 'Ambidextrous'
        elif highlight_type == 'Nation':
            raw = get_data_value('Nation')
            val_display = str(raw)[:3].upper() if raw not in [None, ''] else ''
            metric_label = 'Nation'
        elif highlight_type == 'Rating':
            raw = get_data_value('Rating')
            val_display = str(int(raw or p.get('Rating', 0)))
        elif highlight_type:
            raw_val = get_data_value(highlight_type)
            val_display = str(raw_val) if raw_val not in [None, ''] else ''

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
            {booster_badge}
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
            <div class="bench"><div class="bench-title">Substitutes ({len(subs)})</div><div class="bench-grid">{html_subs}</div></div>
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
        
target_leagues = ["Spanish League", "English League", "Italian League", "Bundesliga", "Ligue 1 McDonald's", "MEIJI YASUDA J1 LEAGUE"]


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
    
    # Sort lại các list để dễ đọc
    if updated:
        target_nations.sort()
        target_clubs.sort()
        target_leagues.sort()
    
    return updated


# ==================== PESDB SCRAPER ====================
PESDB_PLAYER_URL_BASE = "https://pesdb.net/efootball/?id="
PESDB_IMAGE_URL_BASE = "https://pesdb.net/assets/img/card/"
PESDATA_API_BASE = "https://www.pesdata.net/api/player/detail"
PESDATA_API_VERSION = "1.9.0"
PESDATA_API_TOKEN = "null"
PESDATA_API_SECRET = "777888"
PESDATA_BODY_MODEL_FIELDS = [
    'Arm Length', 'Shoulder Width', 'Neck Length', 'Chest Measurement',
    'Neck Size', 'Shoulder Height', 'Leg Length', 'Thigh Size', 'Waist Size',
    'Arm Size', 'Calf Size', 'Leg Coverage Radius', 'Arm Coverage Radius',
    'Jumping Height', 'Torso Collision', 'Leg Length Based Height'
]
PESDATA_APPEARANCE_KEY_MAP = {
    'ArmLength': 'Arm Length',
    'ShoulderWidth': 'Shoulder Width',
    'NeckLength': 'Neck Length',
    'ChestMeasurement': 'Chest Measurement',
    'NeckSize': 'Neck Size',
    'ShoulderHeight': 'Shoulder Height',
    'LegLength': 'Leg Length',
    'ThighSize': 'Thigh Size',
    'WaistSize': 'Waist Size',
    'ArmSize': 'Arm Size',
    'CalfSize': 'Calf Size',
    'LegCoverageRadius': 'Leg Coverage Radius',
    'ArmCoverageRadius': 'Arm Coverage Radius',
    'JumpingHeight': 'Jumping Height',
    'TorsoCollision': 'Torso Collision',
    'LegLengthBasedHeight': 'Leg Length Based Height'
}
PESDATA_APPEARANCE_KEY_MAP_REVERSE = {v: k for k, v in PESDATA_APPEARANCE_KEY_MAP.items()}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://pesdb.net/',
    'Connection': 'keep-alive',
}


def _pesdata_encode_value(value: str) -> str:
    return quote(str(value), safe="'")


def _build_pesdata_signature(params: dict) -> dict:
    clean_params = {k: str(v) for k, v in params.items() if v is not None and str(v) != ''}
    sorted_keys = sorted(clean_params.keys())
    query = '&'.join(f"{k}={_pesdata_encode_value(clean_params[k])}" for k in sorted_keys)
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex[:13]
    payload = f"{timestamp}{nonce}{PESDATA_API_SECRET}{query}"
    signature = hashlib.md5(payload.encode('utf-8')).hexdigest()
    return {
        'timestamp': timestamp,
        'nonce': nonce,
        'signature': signature,
    }


def _extract_pesdata_player_id(value: str) -> str:
    if not value:
        return ""
    text = str(value).strip()
    # First match query parameter id= in URLs like ?id=123...
    m = re.search(r"[?&]id=(\d{12,})", text)
    if m:
        return m.group(1)
    # Then match pesdata player/detail/<id> URLs
    m = re.search(r"player/detail/(\d{12,})", text)
    if m:
        return m.group(1)
    # Fallback to any trailing 12+ digit sequence
    m = re.search(r"(\d{12,})", text)
    return m.group(1) if m else ""


def fetch_pesdata_player_json(player_id_or_url: str) -> dict:
    pid = _extract_pesdata_player_id(player_id_or_url)
    if not pid:
        return {}

    params = {'id': pid}
    signature = _build_pesdata_signature(params)
    headers = HEADERS.copy()
    headers.update({
        'version': PESDATA_API_VERSION,
        'token': PESDATA_API_TOKEN,
        'x-timestamp': signature['timestamp'],
        'x-nonce': signature['nonce'],
        'x-signature': signature['signature'],
        'Referer': f'https://www.pesdata.net/player/detail/{pid}',
        'Accept': 'application/json, text/plain, */*',
    })

    try:
        resp = requests.get(PESDATA_API_BASE, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            if data.get('data'):
                if isinstance(data['data'], list) and data['data']:
                    return data['data'][0]
                if isinstance(data['data'], dict):
                    return data['data']
            if data.get('code') in (0, 200) and isinstance(data.get('data'), dict):
                return data['data']
    except Exception:
        pass
    return {}


def extract_ehub_player_id(value: str) -> str:
    """Extract player ID from URL or string"""
    if not value:
        return ""
    s = str(value).strip()
    m = re.search(r"(\d{14,})", s)
    return m.group(1) if m else ""

def make_ehub_player_url(player_id: str) -> str:
    """Tạo URL EFHub player từ Player ID hoặc URL"""
    pid = extract_ehub_player_id(player_id)
    return f"https://efhub.com/players/{pid}" if pid else ""

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
    Type khác: thử Max Level trước, fallback về level gốc, cuối cùng trả 0.
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
    CHỈ LẤY POS2 (Position sở trường - Đỏ đậm).
    Type bỏ vị trí chính khỏi danh sách.
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
    """Trích xuất TOÀN BỘ thông tin cầu thủ từ PESDB hoặc PESDATA.
    
    Returns:
        dict: {
            'Player': str,
            'Rating': int,
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
            'Player_Type': str,
            ... body model fields ...
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
    for field_name in PESDATA_BODY_MODEL_FIELDS:
        default_info[field_name] = ''

    try:
        normalized_url = str(player_url).strip()
        pesdata_id = _extract_pesdata_player_id(normalized_url)
        pesdb_url = None

        if pesdata_id:
            pesdb_url = f"https://pesdb.net/efootball/?id={pesdata_id}"
        elif normalized_url.isdigit():
            pesdb_url = f"https://pesdb.net/efootball/?id={normalized_url}"
        else:
            pesdb_url = normalized_url

        if not pesdb_url or not str(pesdb_url).startswith('http'):
            return default_info

        html = fetch_ehub_raw_html(pesdb_url)
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
                if key in field_mapping:
                    field_name = field_mapping[key]
                    info[field_name] = value
                if key == 'Position':
                    pos_div = td.find('div', title=True)
                    if pos_div:
                        info['Position'] = pos_div.get_text(strip=True)

        # Lấy vị trí phụ từ sơ đồ sân bóng
        info['Secondary Positions'] = extract_secondary_positions(soup, info.get('Position', ''))
        info['Skills'] = extract_player_skills(pesdb_url)
        info['Player_Type'] = normalize_player_type(extract_card_type_from_html(soup))
        info['Rating'] = extract_max_level_rating(
            pesdb_url,
            card_type=info.get('Player_Type'),
            base_html=html
        )

        # Nếu có PESDATA ID, lấy thêm body model từ PESDATA API
        if pesdata_id:
            pesdata_data = fetch_pesdata_player_json(pesdata_id)
            appearance = pesdata_data.get('appearance') or {}
            for json_key, field_name in PESDATA_APPEARANCE_KEY_MAP.items():
                info[field_name] = appearance.get(json_key, '')
        else:
            # Nếu URL/PID khác dạng, thử extract ID và lấy body model
            player_id = extract_ehub_player_id(normalized_url)
            if player_id:
                pesdata_data = fetch_pesdata_player_json(player_id)
                appearance = pesdata_data.get('appearance') or {}
                for json_key, field_name in PESDATA_APPEARANCE_KEY_MAP.items():
                    if not info.get(field_name):
                        info[field_name] = appearance.get(json_key, '')

        return info

    except Exception as e:
        st.error(f"❌ Error extracting information: {e}")
        return default_info


def get_unique_values(df: pd.DataFrame, column: str) -> list:
    if column in df.columns:
        vals = [str(x) for x in df[column].unique() if pd.notna(x) and str(x).strip()]
        return sorted(vals)
    return []


# ------------------- Body Clustering Utilities -------------------
BODY_FEATURE_COLUMNS = [
    'Height', 'Weight', 'Arm Length', 'Shoulder Width', 'Neck Length',
    'Chest Measurement', 'Neck Size', 'Shoulder Height', 'Leg Length',
    'Thigh Size', 'Waist Size', 'Arm Size', 'Calf Size'
]


def check_body_columns(df: pd.DataFrame) -> list:
    """Return list of missing required body feature columns."""
    missing = [c for c in BODY_FEATURE_COLUMNS if c not in df.columns]
    return missing


@st.cache_data(ttl=300)
def compute_pca_and_scale(df: pd.DataFrame, feature_cols: list, n_components: int = None):
    """
    Scale features (z-score) and compute PCA.
    Returns: scaled array, pca object, explained_variance_ratio_
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

    X = df[feature_cols].copy()
    # Ensure numeric and fillna
    for c in feature_cols:
        X[c] = pd.to_numeric(X[c], errors='coerce').fillna(0.0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values)

    # Auto choose components if not provided (keep all then user can pick)
    pca = PCA(n_components=n_components if n_components else min(len(feature_cols), X_scaled.shape[0]))
    X_pca = pca.fit_transform(X_scaled)

    return X_scaled, X_pca, pca, scaler


@st.cache_data(ttl=300)
def compute_kmeans(X_for_clustering, k: int, random_state: int = 42):
    """Run KMeans and return labels, model and inertia."""
    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=k, random_state=random_state, n_init='auto')
    labels = km.fit_predict(X_for_clustering)
    return labels, km, km.inertia_


@st.cache_data(ttl=300)
def evaluate_k_range(X_for_clustering, k_min: int = 2, k_max: int = 8):
    """Compute inertia and silhouette for range of k. Returns dicts."""
    from sklearn.metrics import silhouette_score
    inertias = {}
    silhouettes = {}
    for k in range(k_min, k_max + 1):
        try:
            labels, km, inertia = compute_kmeans(X_for_clustering, k)
            inertias[k] = float(inertia)
            # silhouette requires at least 2 clusters and less than n_samples
            if len(set(labels)) > 1 and len(labels) > k:
                silhouettes[k] = float(silhouette_score(X_for_clustering, labels))
            else:
                silhouettes[k] = None
        except Exception:
            inertias[k] = None
            silhouettes[k] = None
    return inertias, silhouettes

# ------------------- end utilities -------------------

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

        # Lọc danh sách cần cập nhật chỉ dựa trên Body Model thiếu
        player_urls = df['Player URL'].astype(str).str.strip()
        has_url = player_urls.str.startswith('http')
        missing_body = df[PESDATA_BODY_MODEL_FIELDS].fillna('').astype(str).applymap(lambda x: str(x).strip() == '').any(axis=1)

        valid_id = player_urls[has_url].apply(lambda x: bool(_extract_pesdata_player_id(x)))
        valid_id_count = int(valid_id.sum())
        invalid_id_count = len(player_urls[has_url]) - valid_id_count
        missing_body_count = int(missing_body[has_url].sum())
        missing_url_count = int((~has_url).sum())

        st.info(f"🔍 URLs: {len(player_urls[has_url])}, valid PESDATA ID: {valid_id_count}, invalid ID: {invalid_id_count}, missing body model: {missing_body_count}, no URL: {missing_url_count}")
        if missing_url_count > 0:
            st.warning(f"⚠️ {missing_url_count} player(s) have no valid Player URL and cannot be auto-updated.")
        if invalid_id_count > 0:
            st.warning(f"⚠️ {invalid_id_count} player(s) have a Player URL but no valid PESDATA ID could be extracted.")

        eligible_players = df[has_url & missing_body]
        needs_extraction = eligible_players[eligible_players['Player URL'].apply(lambda x: bool(_extract_pesdata_player_id(str(x).strip())))]

        if needs_extraction.empty:
            st.success("✅ All existing players already have PESDATA Body Model info or no valid PESDATA IDs.")
            st.session_state.run_pesdb_sync = False # Tắt cờ chạy
            return df

        # Lưu trạng thái vào Session
        st.session_state.sync_state = {
            'indices': needs_extraction.index.tolist(), # Danh sách index cần làm
            'total': len(needs_extraction),             # Tổng số
            'current_idx_ptr': 0,                       # Con trỏ hiện tại
            'df_snapshot': df.copy(),                   # Bản sao DF để sửa đổi
            'updated_count': 0,
            'failed': [],
            'started_at': time.time(),
        }
        st.rerun() # Refresh để bắt đầu giao diện xử lý

    # 2. GIAO DIỆN XỬ LÝ (Chạy trong các lần Rerun)
    state = st.session_state.sync_state
    current_ptr = state['current_idx_ptr']
    total = state['total']
    
    # Display progress bar & status
    progress = min(1.0, current_ptr / total)
    elapsed = int(time.time() - state.get('started_at', time.time()))
    st.progress(progress, text=f"🚀 Updating: {current_ptr}/{total} players")
    st.caption(f"⏱ Elapsed: {elapsed}s • Processed: {current_ptr}/{total} • Updated: {state['updated_count']}")
    st.markdown(f"**Current target:** {current_ptr + 1}/{total}")
    
    # --- NÚT DỪNG CẬP NHẬT ---
    # Vì dùng st.rerun(), nút này sẽ luôn phản hồi được ngay lập tức
    if st.button("🛑 Stop update now (Save current progress)", type="primary"):
        # Lưu những gì đã làm được
        if state['updated_count'] > 0:
            save_data_to_gsheet(state['df_snapshot'])
            st.toast(f"⚠️ Stopped! Saved {state['updated_count']} cầu thủ.", icon="💾")
        else:
            st.toast("⚠️ Stopped! No new data processed.", icon="🛑")
            
        final_df = state['df_snapshot']
        del st.session_state.sync_state # Xóa trạng thái
        st.session_state.run_pesdb_sync = False # Tắt cờ chạy của Main App
        time.sleep(1)
        st.rerun()

    # 3. XỬ LÝ DỮ LIỆU (Batch Size = 10 để lưu mỗi 10 cầu thủ)
    if current_ptr < total:
        batch_size = min(10, total - current_ptr)
        updated_in_batch = 0
        processed_in_batch = 0

        for _ in range(batch_size):
            idx = state['indices'][state['current_idx_ptr']]
            row = state['df_snapshot'].loc[idx]
            player_name = str(row.get('Player', 'Unknown'))
            processed_in_batch += 1

            # Status Box nhỏ
            st.info(f"📡 Loading data for: **{player_name}** ({state['current_idx_ptr'] + 1}/{total})...")

            try:
                pesdata_id = _extract_pesdata_player_id(row.get('Player URL', ''))
                if not pesdata_id:
                    state['failed'].append({
                        'idx': idx,
                        'name': player_name,
                        'url': row.get('Player URL', ''),
                        'pid': '',
                        'reason': 'No valid PESDATA ID extracted from Player URL'
                    })
                else:
                    pesdata_data = fetch_pesdata_player_json(pesdata_id)
                    appearance = pesdata_data.get('appearance') or {}
                    row_updated = False

                    for field in PESDATA_BODY_MODEL_FIELDS:
                        current_val = str(state['df_snapshot'].at[idx, field]).strip()
                        if not current_val or current_val == 'nan':
                            appearance_key = PESDATA_APPEARANCE_KEY_MAP_REVERSE.get(field, '')
                            new_val = appearance.get(appearance_key, '') if appearance_key else ''
                            if new_val is not None and str(new_val).strip() != '':
                                state['df_snapshot'].at[idx, field] = new_val
                                row_updated = True

                    if row_updated:
                        state['updated_count'] += 1
                        updated_in_batch += 1
                    else:
                        failure_text = 'PESDATA API returned nothing useful for body model'
                        if appearance:
                            failure_text = 'PESDATA API returned data but no missing fields were filled'
                        state['failed'].append({
                            'idx': idx,
                            'name': player_name,
                            'url': row.get('Player URL', ''),
                            'pid': pesdata_id,
                            'reason': failure_text
                        })
            except Exception as e:
                state['failed'].append({
                    'idx': idx,
                    'name': player_name,
                    'url': row.get('Player URL', ''),
                    'pid': '',
                    'reason': f'Exception while fetching PESDATA: {e}'
                })

            state['current_idx_ptr'] += 1
            if state['current_idx_ptr'] >= total:
                break

        if processed_in_batch > 0:
            save_data_to_gsheet(state['df_snapshot'])
            st.success(f"💾 Saved batch of {processed_in_batch} player(s). Updated {updated_in_batch} new player(s) in this batch.")
            if state['failed']:
                st.warning(f"⚠️ {len(state['failed'])} player(s) could not be updated in this run. See the failed list at the end.")
            time.sleep(1)
            st.rerun()
    else:
        # 4. HOÀN TẤT
        st.success(f"✅ Finished updating {total} cầu thủ!")
        save_data_to_gsheet(state['df_snapshot'])

        final_df = state['df_snapshot']
        if state['failed']:
            st.warning(f"⚠️ Update finished but {len(state['failed'])} player(s) still have missing Body Model values.")
            failed_table = pd.DataFrame(state['failed'])[['name', 'url', 'pid', 'reason']]
            failed_table = failed_table.rename(columns={
                'name': 'Player',
                'url': 'Player URL',
                'pid': 'Extracted ID',
                'reason': 'Failure Reason'
            })
            st.dataframe(failed_table, use_container_width=True)

            reason_counts = failed_table['Failure Reason'].value_counts().reset_index()
            reason_counts.columns = ['Failure Reason', 'Count']
            st.markdown("**Failure summary:**")
            st.table(reason_counts)
        else:
            st.success("✅ All eligible players were updated successfully.")

        del st.session_state.sync_state # Dọn dẹp

        # Trả về DF để Main App hiển thị nút tải xuống
        return final_df

# --- MAIN APP ---
def main():
    initialize_session_state()
    inject_modern_ui_theme()

    with st.sidebar:
        st.header("⚙️ Controls")
    
        # 1. Nút tải lại dữ liệu (Giữ nguyên)
        if st.button("🔄 Reload data", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.manual_reload_triggered = True
            st.rerun()

        if st.button("🧲 Auto update old players", use_container_width=True, help="Update all existing players with missing PESDATA body model and PESDB info."):
            st.session_state.run_pesdb_sync = True
            st.rerun()

        st.divider()
    
        # 3. Menu điều hướng
        main_menu = st.radio(
            "📑 Navigation",
            ["📊 Overview", "👥 Manage Players", "🎮 Manage Skills", "🏋️ Body Analysis", "🏋️ Physical Profile"],
            index=0
        )

        # Điều hướng chi tiết
        if main_menu == "📊 Overview":
            st.session_state.current_tab = "overview"

        elif main_menu == "👥 Manage Players":
            sub_menu = st.radio(
                "⚽ Player",
                ["Player List", "Squad", "Add Player"],
                index=0
            )
            if sub_menu == "Player List":
                st.session_state.current_tab = "players"
            elif sub_menu == "Squad":
                st.session_state.current_tab = "squad"
            elif sub_menu == "Add Player":
                st.session_state.current_tab = "add"
            else:
                st.session_state.current_tab = "players"

        elif main_menu == "🎮 Manage Skills":
            sub_menu = st.radio(
                "🛠️ Skills",
                ["Manage", "Skill Inventory"],
                index=0
            )
            if sub_menu == "Manage":
                st.session_state.current_tab = "skills"
            elif sub_menu == "Skill Inventory":
                st.session_state.current_tab = "inventory"
            else:
                st.session_state.current_tab = "skills"

        elif main_menu == "🏋️ Body Analysis":
            st.session_state.current_tab = "body"
        elif main_menu == "🏋️ Physical Profile":
            st.session_state.current_tab = "profile_map"

        # Tools removed

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

    with st.spinner("⏳ Loading data from Google Sheets..."):
        df = load_data_from_gsheet()
    
    # Nếu không có dữ liệu thì dừng sớm để tránh KeyError ở các bước sau
    if df.empty:
        st.error("⚠️ Player data not found in Google Sheets. Please check `spreadsheet_id` or sheet.")
        return

    # Tự động cập nhật target lists dựa trên player count
    auto_update_target_lists(df)

    # --- HÀM ĐỒNG BỘ PESDB CHO PLAYER CŨ (THỦ CÔNG) ---

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
            _RANK_COL = {'Nation': 'Effective_Nation_Rating', 'Club': 'Effective_Club_Rating', 'League': 'Effective_League_Rating'}
            _candidate = _RANK_COL.get(group_by, 'Rating')
            rank_col = _candidate if _candidate in gdf.columns else 'Rating'
            # Với Nation/League: loại trùng tên, giữ thẻ tốt nhất
            if group_by in ['Nation', 'League']:
                gdf = gdf.sort_values(['Player', rank_col, 'Epic_Priority'], ascending=[True, False, True])
                gdf = gdf.drop_duplicates(subset=['Player'], keep='first')
            # Xác định các tiêu chí sắp xếp
            sort_keys = [rank_col, 'Epic_Priority']
            sort_asc = [False, True]
            
            # THÊM TIÊU CHÍ ƯU TIÊN MỚI: Top23_Count (chỉ áp dụng cho Nation/League khi bị tie)
            if group_by in ['Nation', 'League'] and 'Top23_Count' in gdf.columns:
                sort_keys.append('Top23_Count')
                sort_asc.append(False) # False = Giảm dần, ưu tiên số count cao hơn (thuộc nhiều Top 23 target hơn)
                
            # Sort theo các tiêu chí đã định
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
        st.error("No player data available!")
        return

    current_tab = st.session_state.current_tab

    # render_app_hero() dọc được xóa - dead code
    # if SHOW_APP_HERO and current_tab == 'overview':
    #     render_app_hero(df)

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
            st.error("No data available.")
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
            <span>📦 DATABASE OVERVIEW</span>
            <span class="header-pill">REAL-TIME</span>
        </div>
        """, unsafe_allow_html=True)
        
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        stat_card(r1c1, "Total Players", f"{total_players:,}", "Total Players", "👥", "grad-blue")
        stat_card(r1c2, "Clubs", f"{total_clubs}", "Unique Clubs", "🛡️", "grad-blue")
        stat_card(r1c3, "Nations", f"{total_nations}", "Nations", "🌍", "grad-blue")
        stat_card(r1c4, "Leagues", f"{total_leagues}", "Leagues", "🏆", "grad-blue")

        # --- ROW 2: META STATS ---
        st.markdown("""
        <div class="section-header">
            <span>🔥 META & SPECIAL METRICS</span>
            <span class="header-pill">KEY METRICS</span>
        </div>
        """, unsafe_allow_html=True)
        
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        stat_card(r2c1, "Unwavering", f"{unwavering_cnt}", "Stable form", "📈", "grad-green")
        stat_card(r2c2, "Ambidextrous", f"{ambi_cnt}", "Two-footed", "🦶", "grad-gold")
        stat_card(r2c3, "Epic cards", f"{epic_cnt}", "Legendary cards", "✨", "grad-gold")
        stat_card(r2c4, "POTW cards", f"{potw_cnt}", "Trending / POTW", "⚡", "grad-purple")

        # --- ROW 3: PHYSICAL AVERAGES ---
        st.markdown("""
        <div class="section-header">
            <span>🧬 PHYSICAL AVERAGES</span>
            <span class="header-pill">AVERAGES</span>
        </div>
        """, unsafe_allow_html=True)
        
        r3c1, r3c2, r3c3, r3c4, r3c5 = st.columns(5)
        stat_card(r3c1, "Avg Rating", f"{avg_rating:.1f}", "OVR", "⭐", "grad-red")
        stat_card(r3c2, "Avg Age", f"{avg_age:.1f}", "Years Old", "🎂", "grad-blue")
        stat_card(r3c3, "Avg Height", f"{avg_height:.1f}", "cm", "📏", "grad-blue")
        stat_card(r3c4, "Avg Weight", f"{avg_weight:.1f}", "kg", "⚖️", "grad-blue")
        stat_card(r3c5, "Avg BMI", f"{avg_bmi:.1f}", "Body Index", "💪", "grad-blue")

        # --- ROW 4: TOP 10 LEADERBOARDS (WITH CHARTS) ---
        st.markdown("""
        <div class="section-header">
            <span>🏅 TOP 10 RANKINGS</span>
            <span class="header-pill">RANKINGS</span>
        </div>
        """, unsafe_allow_html=True)
        
        
        
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
        render_chart_top10(l_c1, 'Club', '🏛️ Clubs', '#3b82f6') # Blue

        # 2. Top 10 Nations
        render_chart_top10(l_c2, 'Nation', '🌍 Top Nations', '#ef4444') # Red

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
            st.markdown(f"**🏆 Top Leagues**")
            st.plotly_chart(fig_lg, use_container_width=True, config={'displayModeBar': False})

    elif current_tab == 'body':
        st.header("🏋️ Body Analysis")

        # 1. Ensure required body columns exist
        missing_cols = check_body_columns(df)
        if missing_cols:
            st.error("⚠️ Required body measurement columns are missing from the data: " + ", ".join(missing_cols))
        else:
            # Panel điều khiển
            with st.expander("Filters & settings", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 2])
                group_level = col1.selectbox("Group positions for clustering", ["Position Style", "Position"], index=0)
                if group_level == "Position":
                    positions = get_unique_values(df, 'Position')
                    chosen_position = col1.selectbox("Choose Position", ['(All)'] + positions, index=0)
                else:
                    styles = get_unique_values(df, 'Position Style')
                    chosen_style = col1.selectbox("Choose Position Style", ['(All)'] + styles, index=0)

                # PCA components selection placeholder (will compute suggestions)
                inertia_display = col2.empty()
                silhouette_display = col2.empty()
                run_button = col3.button("Run clustering")

            # Lọc dữ liệu theo bộ lọc đã chọn
            if group_level == 'Position' and chosen_position and chosen_position != '(All)':
                sub_df = df[df['Position'].astype(str) == chosen_position].copy()
            elif group_level == 'Position Style' and chosen_style and chosen_style != '(All)':
                sub_df = df[df['Position Style'].astype(str) == chosen_style].copy()
            else:
                sub_df = df.copy()

            n_players = len(sub_df)
            if n_players < 10:
                st.info(f"The selected group has too few players for clustering (need at least 10). Current count: {n_players}")
            else:
                # Chuẩn bị dữ liệu features
                feature_cols = BODY_FEATURE_COLUMNS.copy()
                for c in feature_cols:
                    sub_df[c] = pd.to_numeric(sub_df.get(c, 0), errors='coerce').fillna(0.0)

                # Compute PCA (all components) to show explained variance
                X_scaled, X_pca_full, pca_obj, scaler = compute_pca_and_scale(sub_df, feature_cols, n_components=min(len(feature_cols), max(1, n_players)))
                evr = list(pca_obj.explained_variance_ratio_)
                cum_evr = np.cumsum(evr)
                # Default n_components: >=80% variance or min 3
                default_n_comp = int(next((i+1 for i,v in enumerate(cum_evr) if v >= 0.8), min(3, len(evr))))
                max_comp = min(len(evr), 10)

                # UI: choose number of PCs used for clustering
                pcs_col1, pcs_col2 = st.columns([3,2])
                pcs_col1.markdown("**Explained variance (per PC)**")
                ev_df = pd.DataFrame({ 'PC': [f'PC{i+1}' for i in range(len(evr))], 'Explained': [float(x) for x in evr], 'Cumulative': [float(x) for x in cum_evr] })
                fig_e = px.bar(ev_df, x='PC', y='Explained', title='Explained Variance by PC')
                fig_e.add_scatter(x=ev_df['PC'], y=ev_df['Cumulative'], mode='lines+markers', name='Cumulative')
                apply_plotly_theme(fig_e)
                pcs_col1.plotly_chart(fig_e, use_container_width=True, config={'displayModeBar': False})

                n_pcs = pcs_col2.slider("Number of PCs for clustering", min_value=2, max_value=max_comp, value=default_n_comp)

                # Prepare data for clustering: use first n_pcs of PCA (but still keep PC1/PC2 for visualization)
                X_for_cluster = X_pca_full[:, :n_pcs]

                # Auto determine best K
                with st.spinner('Estimating recommended K (Elbow + Silhouette)...'):
                    inertias, silhouettes = evaluate_k_range(X_for_cluster, 2, min(8, max(2, n_players-1)))

                # Suggest K by highest silhouette (if available)
                suggested_k = 3
                valid_sil = {k:v for k,v in silhouettes.items() if v is not None}
                if valid_sil:
                    suggested_k = max(valid_sil, key=valid_sil.get)
                else:
                    # fallback: choose k with largest decrease in inertia
                    prev = None; best_k = 3
                    for k in sorted(inertias.keys()):
                        if prev is not None and inertias[k] is not None and prev is not None:
                            pass
                        prev = inertias[k]
                    suggested_k = best_k

                # Quick user help and one-click presets
                with st.expander("Quick guide: 3 steps", expanded=False):
                    st.write("1) Choose filters (optional). 2) Select K or use a preset. 3) View clusters and add to basket/sync.")

                preset_cols = st.columns([1,1,1,2])
                with preset_cols[0]:
                    if st.button("Preset: Defensive (K=4)"):
                        st.session_state['body_preset_k'] = 4
                        st.session_state['body_preset_mode'] = 'defensive'
                with preset_cols[1]:
                    if st.button("Preset: Balanced (K=5)"):
                        st.session_state['body_preset_k'] = 5
                        st.session_state['body_preset_mode'] = 'balanced'
                with preset_cols[2]:
                    if st.button("Preset: Attack (K=3)"):
                        st.session_state['body_preset_k'] = 3
                        st.session_state['body_preset_mode'] = 'attack'
                with preset_cols[3]:
                    mode = st.session_state.get('body_preset_mode', '(none)')
                    kval = st.session_state.get('body_preset_k', '-')
                    st.markdown(f"**Preset active:** {mode} — K={kval}")

                k_default = st.session_state.get('body_preset_k', int(suggested_k))
                k_choice = st.slider("Số cluster K", min_value=2, max_value=8, value=int(k_default))

                # Run KMeans with chosen K when user click run or always run
                labels, kmodel, inertia_val = compute_kmeans(X_for_cluster, int(k_choice))

                # Attach PC1, PC2 and cluster to DataFrame
                pcs = X_pca_full
                sub_df = sub_df.reset_index(drop=True)
                sub_df['PC1'] = pcs[:,0]
                sub_df['PC2'] = pcs[:,1] if pcs.shape[1] > 1 else 0.0
                sub_df['Cluster'] = labels.astype(int)

                # Derive cluster descriptive names (suggestions)
                # Use mean z-score (X_scaled) per cluster
                df_scaled = pd.DataFrame(X_scaled, columns=feature_cols)
                df_scaled['Cluster'] = labels
                cluster_summaries = {}
                for cl in sorted(df_scaled['Cluster'].unique()):
                    means = df_scaled[df_scaled['Cluster']==cl].mean()
                    # exclude the Cluster column itself when picking top features
                    means = means.drop(labels=['Cluster'], errors='ignore')
                    # pick top 2 features by absolute mean
                    top_feats = means.abs().sort_values(ascending=False).head(2).index.tolist()
                    desc_parts = []
                    for f in top_feats:
                        val = means[f]
                        arrow = '↑' if val > 0 else '↓'
                        desc_parts.append(f"{f} {arrow}")
                    suggested_name = ", ".join(desc_parts)
                    cluster_summaries[cl] = suggested_name

                # Let user edit cluster names
                st.markdown("**Cluster names (suggested)**")
                cluster_name_map = {}
                for cl in sorted(cluster_summaries.keys()):
                    default_name = f"Cluster {cl}: {cluster_summaries[cl]}"
                    new_name = st.text_input(f"Cluster name #{cl}", value=default_name, key=f"cluster_name_{cl}")
                    cluster_name_map[cl] = new_name

                # Map cluster names
                sub_df['Cluster Name'] = sub_df['Cluster'].map(cluster_name_map)

                # Scatter plot PC1 vs PC2 colored by cluster
                fig = px.scatter(sub_df, x='PC1', y='PC2', color='Cluster Name', hover_data=['Player','Position','Rating'], title='PC1 vs PC2 (colored by cluster)')
                apply_plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                # Filters & result table
                st.markdown("**Result filters**")
                c1, c2, c3 = st.columns([3,2,2])
                clusters_available = sorted(sub_df['Cluster'].unique())
                sel_clusters = c1.multiselect("Select clusters", options=clusters_available, default=clusters_available)
                pos_options = get_unique_values(sub_df, 'Position')
                sel_positions = c2.multiselect("Position", options=pos_options, default=pos_options)
                min_rating = int(sub_df['Rating'].min()) if 'Rating' in sub_df.columns else 0
                max_rating = int(sub_df['Rating'].max()) if 'Rating' in sub_df.columns else 100
                sel_rating = c3.slider("Rating", min_value=min_rating, max_value=max_rating, value=(min_rating, max_rating))

                filtered = sub_df[sub_df['Cluster'].isin(sel_clusters) & sub_df['Position'].isin(sel_positions) & sub_df['Rating'].between(sel_rating[0], sel_rating[1])].copy()

                display_cols = ['Player','Position','Rating','Cluster','Cluster Name'] + feature_cols
                st.dataframe(filtered[display_cols].sort_values(['Cluster','Rating'], ascending=[True, False]), use_container_width=True)

                # Team basket (independent)
                if 'body_basket' not in st.session_state:
                    st.session_state['body_basket'] = []

                st.markdown("**Team basket (independent)**")
                pick_col1, pick_col2 = st.columns([3,1])
                pick_list = pick_col1.multiselect("Select players to add to basket", options=filtered['Player'].tolist())
                if pick_col2.button("Add to basket"):
                    for p in pick_list:
                        if p not in st.session_state['body_basket']:
                            st.session_state['body_basket'].append(p)

                if st.session_state['body_basket']:
                    st.markdown(f"**Currently {len(st.session_state['body_basket'])} players in basket**")
                    st.write(st.session_state['body_basket'])
                    if st.button("Clear basket" ):
                        st.session_state['body_basket'] = []

                    # Imbalance warning
                    basket_df = sub_df[sub_df['Player'].isin(st.session_state['body_basket'])].copy()
                    if not basket_df.empty:
                        # Map to style group
                        basket_df['Style Group'] = basket_df['Position'].map(lambda p: POSITIONS.get(p, 'Other'))
                        for style in ['Defender','Midfielder','Forward']:
                            grp = basket_df[basket_df['Style Group']==style]
                            if len(grp) >= 3:
                                top_cluster = grp['Cluster'].value_counts(normalize=True).max()
                                if top_cluster >= 0.7:
                                    st.warning(f"⚠️ The {style} group is heavily skewed to one cluster ({top_cluster*100:.0f}%). Consider adding more physical diversity.")
                to_export = filtered.copy()
                to_export['Cluster Name'] = to_export['Cluster Name'].astype(str)
                to_export = to_export[display_cols]
                to_export_bytes = BytesIO()
                with pd.ExcelWriter(to_export_bytes, engine='openpyxl') as writer:
                    # write full sheet
                    to_export.to_excel(writer, index=False, sheet_name='Filtered')
                    # also sheet per cluster
                    for cl in sorted(to_export['Cluster'].unique()):
                        to_export[to_export['Cluster']==cl].to_excel(writer, index=False, sheet_name=f'Cluster_{cl}')
                to_export_bytes.seek(0)
                st.download_button('📥 Download Excel (Filtered + per-cluster)', data=to_export_bytes, file_name='body_clustering.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    elif current_tab == 'profile_map':
        st.header("🏋️ Physical Profile")

        def _to_numeric_fill(df_obj, cols):
            for c in cols:
                if c in df_obj.columns:
                    df_obj[c] = pd.to_numeric(df_obj[c], errors='coerce').fillna(0.0)
                else:
                    df_obj[c] = 0.0
            return df_obj

        archetype_features = {
            'wall': ['Torso Collision', 'Shoulder Width', 'Chest Measurement', 'Waist Size'],
            'spider_leg': ['Leg Length', 'Leg Coverage Radius'],
            'aerial': ['Height', 'Jumping Height', 'Shoulder Height'],
            'stability': ['Weight', 'Thigh Size', 'Calf Size'],
            'keeper': ['Arm Length', 'Arm Coverage Radius', 'Arm Size']
        }

        all_feat_cols = []
        for group in archetype_features.values():
            all_feat_cols.extend(group)
        all_feat_cols = list(dict.fromkeys(all_feat_cols))

        profile_df = df.copy()
        profile_df = _to_numeric_fill(profile_df, all_feat_cols)
        profile_df['Position'] = profile_df['Position'].fillna('(Unknown)')
        profile_df['Rating'] = pd.to_numeric(profile_df.get('Rating', profile_df.get('OVR Rating', 0)), errors='coerce').fillna(0).astype(int)

        if profile_df.empty:
            st.error('No player data available for display.')
            return

        for col in all_feat_cols:
            profile_df[f'{col}_pct'] = profile_df.groupby('Position')[col].transform(lambda x: x.rank(pct=True, method='max') * 100 if len(x) else 0)

        def make_tag_list(row):
            tags = []
            wall_cols = [f'{c}_pct' for c in archetype_features['wall']]
            if profile_df.columns.tolist() and all(c in row.index for c in wall_cols):
                if row[wall_cols].mean() >= 80:
                    tags.append('🛡️ Wall Defender')
            spider_cols = [f'{c}_pct' for c in archetype_features['spider_leg']]
            if all(c in row.index for c in spider_cols) and row[spider_cols].mean() >= 80:
                tags.append('🕷️ Spider Legs')
            aerial_cols = [f'{c}_pct' for c in archetype_features['aerial']]
            if all(c in row.index for c in aerial_cols) and row[aerial_cols].mean() >= 80:
                tags.append('✈️ Air Beast')
            stability_cols = [f'{c}_pct' for c in archetype_features['stability']]
            if all(c in row.index for c in stability_cols) and row[stability_cols].mean() >= 80:
                tags.append('🧱 Bulldozer')
            if str(row.get('Position', '')).upper() == 'GK':
                keeper_cols = [f'{c}_pct' for c in archetype_features['keeper']]
                if all(c in row.index for c in keeper_cols) and row[keeper_cols].mean() >= 80:
                    tags.append('🧤 Spider Keeper')
            return tags

        profile_df['Archetype_Tags'] = profile_df.apply(make_tag_list, axis=1)
        tag_labels = ['🛡️ Wall Defender', '🕷️ Spider Legs', '✈️ Air Beast', '🧱 Bulldozer', '🧤 Spider Keeper']

        def score_axis(row, cols):
            cols_pct = [f'{c}_pct' for c in cols]
            valid_cols = [c for c in cols_pct if c in row.index]
            if not valid_cols:
                return 0
            return float(row[valid_cols].mean())

        profile_df['Power'] = profile_df.apply(lambda r: score_axis(r, ['Chest Measurement', 'Shoulder Width', 'Weight', 'Thigh Size']), axis=1)
        profile_df['Reach'] = profile_df.apply(lambda r: score_axis(r, ['Leg Length', 'Arm Length', 'Arm Coverage Radius']), axis=1)
        profile_df['Aerial'] = profile_df.apply(lambda r: score_axis(r, ['Height', 'Jumping Height', 'Shoulder Height']), axis=1)
        profile_df['Stability'] = profile_df.apply(lambda r: score_axis(r, ['Weight', 'Thigh Size', 'Calf Size', 'Leg Coverage Radius']), axis=1)
        profile_df['Length'] = profile_df.apply(lambda r: score_axis(r, ['Leg Length', 'Arm Length', 'Shoulder Height', 'Jumping Height']), axis=1)
        profile_df['Core'] = profile_df.apply(lambda r: score_axis(r, ['Torso Collision', 'Chest Measurement', 'Waist Size']), axis=1)
        profile_df['Goalkeeping'] = profile_df.apply(lambda r: score_axis(r, ['Arm Length', 'Arm Coverage Radius']), axis=1)

        preset = st.sidebar.selectbox('What player profile are you looking for?', [
            '(None)',
            'Strong dueler & wall defender',
            'Hold-up forward/midfielder',
            'Sweep tackler'
        ])
        st.sidebar.markdown('---')
        selected_positions = st.sidebar.multiselect('Select positions', sorted(profile_df['Position'].dropna().unique()), default=sorted(profile_df['Position'].dropna().unique()))
        selected_tags = st.sidebar.multiselect('Select archetype tags', tag_labels, default=tag_labels)
        show_raw = st.sidebar.checkbox('Show detailed raw stats', value=False)

        filter_col_left, filter_col_right = st.columns([3,1])
        selected_type = filter_col_right.selectbox('Filter by body type', ['All'] + tag_labels, index=0)

        results = profile_df.copy()
        if preset == 'Strong dueler & wall defender':
            results = results[results['Position'].isin(['CB'])]
            results = results[results['Archetype_Tags'].apply(lambda tags: '🛡️ Wall Defender' in tags)]
        elif preset == 'Hold-up forward/midfielder':
            results = results[results['Position'].isin(['ST', 'MF', 'CM', 'AM', 'LM', 'RM'])]
            results = results[results['Archetype_Tags'].apply(lambda tags: '🧱 Bulldozer' in tags)]
        elif preset == 'Sweep tackler':
            results = results[results['Position'].isin(['DMF', 'CB'])]
            results = results[results['Archetype_Tags'].apply(lambda tags: '🕷️ Spider Legs' in tags)]

        results = results[results['Position'].isin(selected_positions)]
        if selected_type != 'All':
            results = results[results['Archetype_Tags'].apply(lambda tags: selected_type in tags)]
        results = results[results['Archetype_Tags'].apply(lambda tags: any(tag in tags for tag in selected_tags))]

        results['Tag_Display'] = results['Archetype_Tags'].apply(lambda tags: ' '.join(tags) if tags else '—')
        results = results.sort_values(['Rating', 'Power', 'Reach'], ascending=[False, False, False])

        tag_counts = {tag: results['Archetype_Tags'].apply(lambda tags: tag in tags).sum() for tag in tag_labels}

        results['Tag_Display'] = results['Archetype_Tags'].apply(lambda tags: ' '.join(tags) if tags else '—')
        results = results.sort_values(['Rating', 'Power', 'Reach'], ascending=[False, False, False])

        tag_counts = {tag: results['Archetype_Tags'].apply(lambda tags: tag in tags).sum() for tag in tag_labels}

        st.markdown('#### 🎯 Archetype Overview')
        c1, c2, c3, c4, c5 = st.columns(5)
        card_data = [
            ('🛡️ Wall Defender', tag_counts['🛡️ Wall Defender'], 'Physical wall, strong contact, hold the line', c1),
            ('🕷️ Spider Legs', tag_counts['🕷️ Spider Legs'], 'Tackles, range, interception coverage', c2),
            ('✈️ Air Beast', tag_counts['✈️ Air Beast'], 'Aerial wins, jump, high ball control', c3),
            ('🧱 Bulldozer', tag_counts['🧱 Bulldozer'], 'Stability, body strength, anchor play', c4),
            ('🧤 Spider Keeper', tag_counts['🧤 Spider Keeper'], 'GK reach, arm span, shot coverage', c5),
        ]
        for title, count, desc, col in card_data:
            col.markdown(f"<div style='background:#111827;padding:16px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);'>"
                         f"<div style='font-size:1rem;font-weight:700;margin-bottom:6px'>{title}</div>"
                         f"<div style='font-size:2rem;font-weight:800;color:#60a5fa'>{count}</div>"
                         f"<div style='font-size:0.85rem;color:#94a3b8;margin-top:8px'>{desc}</div>"
                         f"</div>", unsafe_allow_html=True)

        sort_mode = st.radio('Sort top candidates by:', ['Rating', 'Power', 'Reach', 'Aerial', 'Stability'], horizontal=True)
        if sort_mode in results.columns:
            results = results.sort_values(sort_mode, ascending=False)

        if 'profile_basket' not in st.session_state:
            st.session_state['profile_basket'] = []

        st.markdown('---')
        st.markdown('#### 🔥 Candidate scatter plot')

        plot_axes = ['Power', 'Reach', 'Aerial', 'Stability', 'Length', 'Core']
        axis_col1, axis_col2, axis_col3 = st.columns([2,2,2])
        x_axis = axis_col1.selectbox('X axis', options=plot_axes, index=0)
        y_axis = axis_col2.selectbox('Y axis', options=plot_axes, index=1)
        top_n = axis_col3.slider('Show top players', min_value=6, max_value=30, value=12, step=1)

        results = results.copy()
        results['Archetype'] = results['Archetype_Tags'].apply(lambda tags: tags[0] if tags else 'No archetype')
        top_results = results.head(top_n).copy()

        if not top_results.empty:
            fig = px.scatter(
                top_results,
                x=x_axis,
                y=y_axis,
                color='Archetype',
                size='Rating',
                symbol='Position',
                hover_data=['Player', 'Position', 'Club', 'Nation', 'Rating', 'Tag_Display'],
                title=f'Top {top_n} candidates: {x_axis} vs {y_axis}'
            )
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='rgba(148,163,184,0.24)'),
                yaxis=dict(gridcolor='rgba(148,163,184,0.24)'),
                legend=dict(title='Archetype', orientation='h', y=-0.2, x=0.5, xanchor='center'),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})

            st.markdown('**Top candidates detail**')
            st.dataframe(
                top_results[['Player', 'Position', 'Club', 'Nation', 'Rating', x_axis, y_axis, 'Tag_Display']]
                .rename(columns={'Tag_Display': 'Archetype'}),
                use_container_width=True
            )

            add_players = st.multiselect('Select players to add to basket', options=top_results['Player'].tolist())
            if st.button('Add selected to basket'):
                for player_name in add_players:
                    if player_name not in st.session_state['profile_basket']:
                        st.session_state['profile_basket'].append(player_name)
                if add_players:
                    st.success(f'Added {len(add_players)} player(s) to basket')
        else:
            st.info('No candidates found for the current filters.')

        st.markdown('---')
        st.markdown('#### 🧺 Selection Basket')
        if st.session_state['profile_basket']:
            for i, player_name in enumerate(st.session_state['profile_basket']):
                remove_col, name_col = st.columns([1, 9])
                name_col.markdown(f"- {player_name}")
                if remove_col.button('Remove', key=f'remove_{i}'):
                    st.session_state['profile_basket'].remove(player_name)
                    st.experimental_rerun()
        else:
            st.info('No players in basket yet. Click Add to basket on a card to save.')

        st.markdown('---')
        st.markdown('#### 🔍 Player Details')
        sel_player = st.selectbox('Select player to view profile:', options=['(None)'] + results['Player'].tolist())
        if sel_player and sel_player != '(None)':
            player_row = results[results['Player'] == sel_player].iloc[0]
            st.markdown(f"### {player_row['Player']} — {player_row['Position']} | OVR {player_row['Rating']}")
            if player_row['Archetype_Tags']:
                badges = ' '.join([f"<span style='background:#1f2937;color:#f8fafc;padding:6px 10px;border-radius:999px;margin-right:6px;font-size:0.9rem'>{tag}</span>" for tag in player_row['Archetype_Tags']])
                st.markdown(badges, unsafe_allow_html=True)

            radar_axes = ['Power', 'Reach', 'Aerial', 'Stability', 'Length', 'Core']
            radar_values = [
                int(player_row['Power']),
                int(player_row['Reach']),
                int(player_row['Aerial']),
                int(player_row['Stability']),
                int(player_row['Length']),
                int(player_row['Core'])
            ]
            if str(player_row['Position']).upper() == 'GK':
                radar_axes.append('Goalkeeping')
                radar_values.append(int(player_row['Goalkeeping']))

            profile_radar_df = pd.DataFrame({'axis': radar_axes, 'value': radar_values})

            archetype_ideal = {
                '🛡️ Wall Defender': {'Power': 95, 'Reach': 90, 'Aerial': 85, 'Stability': 92, 'Length': 80, 'Core': 88, 'Goalkeeping': 0},
                '🕷️ Spider Legs': {'Power': 80, 'Reach': 95, 'Aerial': 82, 'Stability': 88, 'Length': 94, 'Core': 75, 'Goalkeeping': 0},
                '✈️ Air Beast': {'Power': 85, 'Reach': 88, 'Aerial': 98, 'Stability': 80, 'Length': 85, 'Core': 82, 'Goalkeeping': 0},
                '🧱 Bulldozer': {'Power': 88, 'Reach': 78, 'Aerial': 80, 'Stability': 95, 'Length': 78, 'Core': 92, 'Goalkeeping': 0},
                '🧤 Spider Keeper': {'Power': 70, 'Reach': 96, 'Aerial': 80, 'Stability': 88, 'Length': 90, 'Core': 78, 'Goalkeeping': 96},
            }

            selected_tags = [tag for tag in player_row['Archetype_Tags'] if tag in archetype_ideal]
            if selected_tags:
                ideal_values = {axis: np.mean([archetype_ideal[tag].get(axis, 0) for tag in selected_tags]) for axis in radar_axes}
            else:
                ideal_values = {axis: 65 for axis in radar_axes}

            archetype_radar_df = pd.DataFrame({
                'axis': radar_axes * 2,
                'value': [ideal_values[a] for a in radar_axes] + radar_values,
                'type': ['Archetype Ideal'] * len(radar_axes) + ['Player Profile'] * len(radar_axes)
            })

            fig = px.line_polar(archetype_radar_df, r='value', theta='axis', color='type', line_close=True, template='plotly_dark')
            fig.update_traces(fill='toself', selector=dict(name='Player Profile'), marker=dict(size=8), line=dict(width=2))
            fig.update_traces(fill='none', selector=dict(name='Archetype Ideal'), marker=dict(size=6), line=dict(dash='dash', width=2))
            fig.update_layout(
                polar=dict(
                    bgcolor='rgba(17,24,39,0.8)',
                    radialaxis=dict(gridcolor='rgba(148,163,184,0.24)', tickfont=dict(color='#cbd5e1')),
                    angularaxis=dict(tickfont=dict(color='#e2e8f0'))
                ),
                legend=dict(orientation='h', y=-0.1, x=0.5, xanchor='center', font=dict(color='#cbd5e1')),
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0',
                margin=dict(l=0, r=0, t=20, b=0)
            )

            st.markdown('**Radar profile**: compare the player with the best-matching archetype.')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            st.markdown(
                "**Radar notes:**<br>"
                "- **Power**: upper-body force, collision impact, and physical presence.<br>"
                "- **Reach**: limb extension, space coverage, and stretch range.<br>"
                "- **Aerial**: jumping strength, high-ball control, and aerial dominance.<br>"
                "- **Stability**: balance, body control, and resistance to being pushed off.<br>"
                "- **Length**: overall reach and body span for covering space.<br>"
                "- **Core**: torso strength, bracing power, and contact stability."
                , unsafe_allow_html=True)

            if show_raw:
                raw_cols = [c for c in all_feat_cols if c in profile_df.columns]
                raw_rows = player_row[raw_cols].to_frame(name='Value')
                st.markdown('**Raw stat details**')
                st.dataframe(raw_rows, use_container_width=True)

        if results.empty:
            st.warning('No players match the current filters. Try different tags or reset the preset.')

        try:
            export_df = results[['Player', 'Position', 'Rating', 'Club', 'Nation', 'Tag_Display']].rename(columns={'Tag_Display': 'Archetype'})
            export_bytes = BytesIO()
            with pd.ExcelWriter(export_bytes, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False, sheet_name='Results')
            export_bytes.seek(0)
            st.download_button('📥 Download results to Excel', data=export_bytes, file_name='physical_profile_results.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except Exception as e:
            st.error(f'Error exporting Excel: {e}')

    elif current_tab == 'players':
        st.header("👥 Players")

        SQUAD_SIZE = 23  # Số cầu thủ mỗi team

        # ===== 1. HÀM TÍNH TOP 23 VÀ TRẢ VỀ THỨ HẠNG (RANK MAP) =====
        def get_top_23_ranked_map(df, group_by, values):
            """
            Trả về dict: {index_cầu_thủ: 'Rank/Total'}
            Ví dụ: {102: '1/23', 105: '5/11'}
            Dựa trên effective ratings được tính lại theo depth thật trong squad build,
            không dùng proxy từ toàn bộ kho thẻ.
            """
            ranked_map = {}
            _RANK_COL = {'Nation': 'Effective_Nation_Rating', 'Club': 'Effective_Club_Rating', 'League': 'Effective_League_Rating'}
            rank_col = _RANK_COL.get(group_by, 'Rating')
            
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
                        ['Player', rank_col, 'Epic_Priority', 'Top23_Count', 'TargetClubPriority'],
                        ascending=[True, False, True, False, False]
                    )
                    team_df = team_df.drop_duplicates(subset=['Player'], keep='first')
    
                # --- LOGIC CHỌN ĐỘI HÌNH ---
                gk_df = team_df[team_df['Position'] == 'GK']
                cb_df = team_df[team_df['Position'] == 'CB']
                squad = pd.DataFrame()
                remaining_slots = SQUAD_SIZE
    
                # 1. Choose 1 GK tốt nhất
                if not gk_df.empty:
                    gk_df['TargetClubPriority'] = gk_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in gk_df.columns: gk_df['Top23_Count'] = 0
                    best_gk = gk_df.sort_values([rank_col, 'Epic_Priority', 'Top23_Count'], ascending=[False, True, False]).head(1)
                    squad = pd.concat([squad, best_gk])
                    remaining_slots -= 1
    
                # 2. Choose 2 CB tốt nhất
                if not cb_df.empty:
                    cb_df['TargetClubPriority'] = cb_df['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in cb_df.columns: cb_df['Top23_Count'] = 0
                    best_cb = cb_df.sort_values([rank_col, 'Epic_Priority', 'Top23_Count'], ascending=[False, True, False]).head(2)
                    squad = pd.concat([squad, best_cb])
                    remaining_slots -= len(best_cb)
    
                # 3. Choose các cầu thủ còn lại
                others = team_df.drop(squad.index, errors='ignore')
                if not others.empty:
                    others['TargetClubPriority'] = others['Club'].isin(target_clubs).astype(int)
                    if 'Top23_Count' not in others.columns: others['Top23_Count'] = 0
                    top_rest = others.sort_values([rank_col, 'Epic_Priority', 'Top23_Count'], ascending=[False, True, False]).head(remaining_slots)
                    squad = pd.concat([squad, top_rest])
                
                # --- LƯU RANKING ---
                final_squad = squad.sort_values([rank_col, 'Epic_Priority'], ascending=[False, True])
                total_in_squad = len(final_squad)
                
                for rank, (idx, row) in enumerate(final_squad.iterrows(), start=1):
                    ranked_map[idx] = f"{rank}/{total_in_squad}"

            return ranked_map
        
        # Tính toán Rank Map cho từng nhóm dựa trên squad thực tế vừa được build ở tab Squad.
        # Nếu có squad vừa build trong session state thì ưu tiên dùng nó để đảm bảo
        # Players tab khớp đúng với formation hiện đang hiển thị trong Squad Builder.
        ranking_squad = st.session_state.get('last_built_squad', [])

        if not ranking_squad:
            try:
                _, ranking_squad = find_best_formation_for_team(df, 'rating_desc', None, None)
            except Exception:
                ranking_squad = []

        if not ranking_squad:
            try:
                ranking_squad = auto_build_squad(df, list(FORMATIONS.keys())[0], sort_mode='rating_desc')
            except Exception:
                ranking_squad = []

        ranking_df = build_squad_based_effective_ratings(df, ranking_squad)

        club_rank_map = get_top_23_ranked_map(ranking_df, 'Club', target_clubs)
        nation_rank_map = get_top_23_ranked_map(ranking_df, 'Nation', target_nations)
        league_rank_map = get_top_23_ranked_map(ranking_df, 'League', target_leagues)

        # Đồng bộ rank info hiển thị ở Players tab với cùng logic effective rating mới
        club_top_map = build_top23_map(ranking_df, 'Club')
        league_top_map = build_top23_map(ranking_df, 'League')
        nation_top_map = build_top23_map(ranking_df, 'Nation')

        # ===== PHÁT HIỆN PLAYER TRÙNG (KEEP NGUYÊN) =====
        def detect_duplicates(df):
            duplicates_info = []
            grouped = df.groupby(['Player', 'Club', 'Nation', 'League'])
            for (player, club, nation, league), group in grouped:
                if len(group) > 1 and club and nation and league:
                    # Best by Effective_Club_Rating → determines Club and League squad inclusion
                    sort_col = 'Effective_Club_Rating' if 'Effective_Club_Rating' in group.columns else 'Rating'
                    sorted_by_rating = group.sort_values([sort_col, 'Epic_Priority'], ascending=[False, True])
                    best_overall_idx = sorted_by_rating.index[0]
                    
                    # Best by Effective_Nation_Rating → determines Nation squad inclusion
                    sorted_by_nation = group.sort_values(['Effective_Nation_Rating', 'Epic_Priority'], ascending=[False, True])
                    best_nation_idx = sorted_by_nation.index[0]
                    
                    # A card is NOT a duplicate if it wins along at least one dimension.
                    keep_indices = {best_overall_idx, best_nation_idx}
                    best_card = sorted_by_rating.iloc[0]
                    
                    for idx in group.index:
                        if idx not in keep_indices:
                            dup = group.loc[idx]
                            duplicates_info.append({
                                'index': idx,
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

        duplicates = detect_duplicates(ranking_df)

        # ===== 2. CẬP NHẬT GỢI Ý SELL (HIỆN RANK) =====
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
                return ' ✅  KEEP', f" 🛡 ️ {club} - Never sell (Fan club)"
            
            # 2. Kiểm tra thuộc Top 23 (DÙNG RANK MAP ĐỂ HIỂN THỊ CHI TIẾT)
            in_top_club = idx in club_rank_map
            in_top_nation = idx in nation_rank_map
            in_top_league = idx in league_rank_map
            
            # Format hiển thị: "Club: Manchester B (5/11)"
            if in_top_club:
                rank_str = club_rank_map[idx]
                base = row.get('Rating', '')
                eff_club = row.get('Effective_Club_Rating', base)
                boost_note = f" [Boosted {base}→{eff_club}]" if eff_club != base else ""
                reasons.append(f"Club: {club} ({rank_str}){boost_note}")
            if in_top_nation:
                rank_str = nation_rank_map[idx]
                base = row.get('Rating', '')
                eff = row.get('Effective_Nation_Rating', base)
                boost_note = f" [Boosted {base}→{eff}]" if eff != base else ""
                reasons.append(f"Nation: {nation} ({rank_str}){boost_note}")
            if in_top_league:
                rank_str = league_rank_map[idx]
                base = row.get('Rating', '')
                eff_league = row.get('Effective_League_Rating', base)
                boost_note = f" [Boosted {base}→{eff_league}]" if eff_league != base else ""
                reasons.append(f"League: {league} ({rank_str}){boost_note}")
            
            # 3. Kiểm tra thẻ trùng (nếu có): chỉ SELL nếu thẻ không nằm trong bất kỳ Top23 nào
            is_duplicate = any(dup['index'] == idx for dup in duplicates)
            if is_duplicate and not (in_top_club or in_top_nation or in_top_league):
                return '❌ SELL', "⚠️ Duplicate card - Better card exists (same player + club + nation + league)"

            # 4. Quyết định: nếu player nằm trong ít nhất một Top 23 rank thì KEEP
            if in_top_club or in_top_nation or in_top_league:
                return '✅ KEEP', " | ".join(reasons) if reasons else "Included in at least one Top 23 team"

            return '❌ SELL', "Not part of any Top 23 team"

        # Apply suggestion
        rec_df = ranking_df.copy()
        suggestions = rec_df.apply(suggest_action, axis=1)
        rec_df['Action'], rec_df['Reasons'] = zip(*suggestions)
        sell_df = rec_df[rec_df['Action'] == '❌ SELL']

        rank_info_list = []
        for idx, row in rec_df.iterrows():
            ranks = []
            club_rank = fast_rank(row.get('Club', ''), idx, club_top_map)
            if club_rank: ranks.append(club_rank)
            nation_rank = fast_rank(row.get('Nation', ''), idx, nation_top_map)
            if nation_rank: ranks.append(nation_rank)
            league_rank = fast_rank(row.get('League', ''), idx, league_top_map)
            if league_rank: ranks.append(league_rank)
            # Sort theo thứ tự Club → League → Nation
            rank_info_list.append("\n".join(ranks) if ranks else "")
        
        rec_df['Rank_Info'] = rank_info_list

        # ===== THỐNG KÊ TỔNG QUAN =====
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Total Players", len(df))
        with col2:
            protected_count = len(df[df['Club'].isin(PROTECTED_CLUBS)])
            st.metric("🛡️ FC Barcelona", protected_count)
        with col3:
            st.metric("✅ Recommended Keep", len(df) - len(sell_df))
        with col4:
            st.metric("❌ Recommended Sell", len(sell_df))

        # ===== CẢNH BÁO THẺ TRÙNG =====
        if duplicates:
            st.error(f"⚠️ **WARNING:** Detected {len(duplicates)} duplicate cards (same player + Club + Nation + League)")
            
            with st.expander("🔍 View duplicate card details", expanded=True):
                dup_data = []
                for dup in duplicates:
                    dup_data.append({
                        'STT': len(dup_data) + 1,
                        'Player': dup['player'],
                        'Rating': dup['rating'],
                        'Rarity': dup['rarity'],
                        'Club': dup['club'],
                        'Nation': dup['nation'],
                        'League': dup['league'],
                        'Best card': f"{dup['best_rating']} ({dup['best_rarity']})",
                    })
                
                dup_df = pd.DataFrame(dup_data)
                st.dataframe(dup_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No duplicate cards detected")              
        
        # 1. THANH ĐIỀU KHIỂN CHÍNH (TOP BAR)
        with st.container(border=True):
            col_search, col_view, col_sort = st.columns([3, 1.5, 2])
            
            with col_search:
                search_query = st.text_input(
                    "🔍 Search",
                    placeholder="Enter name, Club, Skills...",
                    label_visibility="collapsed",
                    key="filter_search_query"
                )
            
            with col_view:
                view_mode = st.radio(
                    "View mode",
                    ["🎴 Cards", "📋 Table"],
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
                    sort_col = st.selectbox("Sort", sort_options, index=0, label_visibility="collapsed", key="filter_sort_col")
                with c_s2:
                    sort_order = st.toggle("Ascending", False, key="filter_sort_asc")

        # 2. BỘ LỌC NÂNG CAO (LAYOUT 5 CỘT MỚI)
        with st.expander("🌪️ Advanced filters & stats", expanded=False):
            # Thay đổi từ 4 cột sang 5 cột để chia nhỏ phần "Thuộc tính khác"
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
            
            with f_col1:
                st.markdown("**Basic**")
                action_filter = st.selectbox("Action", ["All", "✅ KEEP", "❌ SELL"], key="filter_action")
                pos_list = sorted(df['Position'].unique().tolist())
                position_filter = st.multiselect("Position", pos_list, key="filter_position")
                style_list = sorted([str(x) for x in df['Position Style'].unique() if x])
                style_filter = st.multiselect("Playstyle", style_list, key="filter_style")
            
            with f_col2:
                st.markdown("**Team**")
                club_list = sorted([str(x) for x in df['Club'].unique() if x])
                club_filter = st.multiselect("Club", club_list, key="filter_club")
                league_list = ["All"] + sorted([str(x) for x in df['League'].unique() if x])
                league_filter = st.selectbox("League", league_list, key="filter_league")
                nation_list = sorted([str(x) for x in df['Nation'].unique() if x])
                nation_filter = st.multiselect("Nation", nation_list, key="filter_nation")

            with f_col3:
                st.markdown("**Stats & Physical**")
                h_values = pd.to_numeric(df['Height'], errors='coerce').dropna()
                h_min, h_max = (int(h_values.min()), int(h_values.max())) if not h_values.empty else (150, 200)
                height_range = st.slider("Height (cm)", h_min, h_max, (h_min, h_max), key="filter_height_range")
                
                w_values = pd.to_numeric(df['Weight'], errors='coerce').dropna()
                w_min, w_max = (int(w_values.min()), int(w_values.max())) if not w_values.empty else (50, 100)
                weight_range = st.slider("Weight (kg)", w_min, w_max, (w_min, w_max), key="filter_weight_range")

                a_values = pd.to_numeric(df['Age'], errors='coerce').dropna()
                a_min, a_max = (int(a_values.min()), int(a_values.max())) if not a_values.empty else (15, 45)
                age_range = st.slider("Age", a_min, a_max, (a_min, a_max), key="filter_age_range")

            with f_col4:
                st.markdown("**Attributes (1)**")
                type_filter = st.multiselect("Card Type", df['Player Type'].unique(), key="filter_type")
                
                form_list = sorted([str(x) for x in df['Form'].unique() if str(x).strip()])
                form_filter = st.multiselect("Form", form_list, key="filter_form")
                
                injury_list = sorted([str(x) for x in df['Injury Resistance'].unique() if str(x).strip()])
                injury_filter = st.multiselect("Injury Resistance", injury_list, key="filter_injury")

            with f_col5:
                st.markdown("**Attributes (2)**")
                wf_usage_list = sorted([str(x) for x in df['Weak Foot Usage'].unique() if str(x).strip()])
                wf_usage_filter = st.multiselect("Non-dominant Foot Usage", wf_usage_list, key="filter_wf_usage")
                
                wf_acc_list = sorted([str(x) for x in df['Weak Foot Accuracy'].unique() if str(x).strip()])
                wf_acc_filter = st.multiselect("Weak Foot Accuracy", wf_acc_list, key="filter_wf_acc")
                
                foot_list = ["All"] + list(df['Foot'].unique()) if 'Foot' in df.columns else []
                foot_filter = st.selectbox("Preferred Foot", foot_list, key="filter_foot")
                
                skill_query = st.text_input("Search Skill", placeholder="vd: Blocker", key="filter_skill_query")
                
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
        if action_filter != "All":
            filtered_df = filtered_df[filtered_df['Action'] == action_filter]
        if position_filter:
            filtered_df = filtered_df[filtered_df['Position'].isin(position_filter)]
        if style_filter:
            filtered_df = filtered_df[filtered_df['Position Style'].isin(style_filter)]
        if club_filter:
            filtered_df = filtered_df[filtered_df['Club'].isin(club_filter)]
        if league_filter != "All":
            filtered_df = filtered_df[filtered_df['League'] == league_filter]
        if nation_filter:
            filtered_df = filtered_df[filtered_df['Nation'].isin(nation_filter)]
        if type_filter:
            filtered_df = filtered_df[filtered_df['Player Type'].isin(type_filter)]
        
        if form_filter: filtered_df = filtered_df[filtered_df['Form'].isin(form_filter)]
        if injury_filter: filtered_df = filtered_df[filtered_df['Injury Resistance'].isin(injury_filter)]
        if wf_usage_filter: filtered_df = filtered_df[filtered_df['Weak Foot Usage'].isin(wf_usage_filter)]
        if wf_acc_filter: filtered_df = filtered_df[filtered_df['Weak Foot Accuracy'].isin(wf_acc_filter)]
        if foot_filter != "All": filtered_df = filtered_df[filtered_df['Foot'] == foot_filter]
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
        m1.metric("Players found", len(filtered_df))
        m2.metric("Avg Rating", f"{filtered_df['Rating'].mean():.1f}")
        m3.metric("EPIC count", len(filtered_df[filtered_df['Player Type'] == 'EPIC']))
        m4.metric("POTW count", len(filtered_df[filtered_df['Player Type'] == 'POTW']))
        m5.metric("Recommended SELL", len(filtered_df[filtered_df['Action'] == '❌ SELL']))
        st.markdown("---")

        # 5. HIỂN THỊ DỮ LIỆU
        if view_mode == "📋 Table":
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
                    "Avatar": st.column_config.ImageColumn("Image", width="small"),
                    "Player": st.column_config.TextColumn("Player name", width="medium"),
                    "Rating": st.column_config.ProgressColumn("OVR", format="%d", min_value=70, max_value=105, width="small"),
                    "Position": st.column_config.TextColumn("VT", width="small"),
                    "BMI": st.column_config.NumberColumn("BMI", format="%.2f", width="small"),
                    "Player Type": st.column_config.TextColumn("Type", width="small"),
                    "Action": st.column_config.TextColumn("Status", width="small"),
                    "Skills": st.column_config.ListColumn("Skills", width="medium"),
                    "Reasons": st.column_config.TextColumn("Notes", width="large")
                },
                use_container_width=True, height=800, hide_index=True
            )
        else:
            # --- CHẾ ĐỘ GRID (THẺ) ---
            MAX_ITEMS = 100
            if len(filtered_df) > MAX_ITEMS:
                st.warning(f"⚠️ Showing the first {MAX_ITEMS} players. Use filters to narrow results.")
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
                        
                        if st.button("🔍 View details", key=f"btn_view_{idx}", use_container_width=True):
                            show_player_modal(player)

        # 6. THANH CÔNG CỤ CUỐI TRANG
        st.divider()
        with st.container(border=True):
            st.markdown("#### 📂 Data actions")
            ac1, ac2, ac3 = st.columns([1, 1, 2])
            with ac1:
                if len(sell_df) > 0:
                    csv_sell = sell_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("⬇️ Download Sell List", csv_sell, "sell_list.csv", "text/csv", use_container_width=True)
            with ac2:
                csv_all = filtered_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("⬇️ Download Filtered List", csv_all, "filtered_list.csv", "text/csv", use_container_width=True)
            with ac3:
                with st.expander("🗑️ Delete player (Dangerous)"):
                    st.warning("Choose players to permanently delete from the database")
                    del_options = filtered_df.index.tolist()
                    del_labels = {i: f"{filtered_df.loc[i, 'Player']} ({filtered_df.loc[i, 'Rating']})" for i in del_options}
                    to_delete = st.multiselect("Choose player:", options=del_options, format_func=lambda x: del_labels.get(x, str(x)))
                    if to_delete:
                        if st.button(f"Confirm DELETE {len(to_delete)} cầu thủ", type="primary"):
                            try:
                                new_df = df.drop(index=to_delete, errors='ignore')
                                if save_data_to_gsheet(new_df):
                                    st.success("Deleted successfully!")
                                    st.cache_data.clear()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

    elif current_tab == 'skills':
        st.header("🎮 Manage Skills & Training")
        
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
                st.info("🧤 Using GK Skill Inventory")
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
            st.markdown("**Current Skills:**")
            skill_badges = ""
            for s in base_skills: skill_badges += f"<span style='background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:10px;font-size:0.8em;margin:2px;display:inline-block'>⭐ {s}</span>"
            for s in added_skills: skill_badges += f"<span style='background:rgba(74, 222, 128, 0.2);color:#4ade80;padding:2px 8px;border-radius:10px;font-size:0.8em;margin:2px;display:inline-block'>✅ {s}</span>"
            st.markdown(skill_badges, unsafe_allow_html=True)
            
            if remaining_slots <= 0:
                st.warning("🔒 Slot full!")
                return
            st.divider()
            
            # --- LOGIC STRICT TARGETS ---
            # Hàm get_recommended_skills đã được thiết kế để trả về Priority List chuẩn
            all_missing = get_recommended_skills(p_pos, str(row.get('Skills', '')), str(row.get('Added Skills', '')), 15)
            target_skills = all_missing[:remaining_slots]
            
            if not target_skills:
                st.info("No skill specified.")
                return

            options_map = {}
            valid_options = []
            
            for skill in target_skills:
                # Dùng training_inventory đã chọn đúng loại
                stock = training_inventory.get(skill, 0)
                if stock > 0:
                    label = f"🟢 {skill} (Kho: {stock})"
                else:
                    label = f"🔴 {skill} (Out of stock)"
                valid_options.append(skill)
                options_map[skill] = label
            
            st.markdown(f"#### 🎯 Targets ({'GK' if is_gk else 'Field'})")
            selected = st.multiselect(
                "Choose skill:", options=valid_options, format_func=lambda x: options_map.get(x, x),
                default=[s for s in valid_options if training_inventory.get(s, 0) > 0],
                max_selections=remaining_slots
            )
            
            # Validate
            out_of_stock = [s for s in selected if training_inventory.get(s, 0) <= 0]
            
            col_save1, col_save2 = st.columns(2)
            with col_save2:
                btn_disabled = len(selected) == 0 or len(out_of_stock) > 0
                if out_of_stock: st.error(f"⚠️ Out of stock: {', '.join(out_of_stock)}")
                
                if st.button("💾 Confirm add", type="primary", use_container_width=True, disabled=btn_disabled):
                    new_added = added_skills + selected
                    df.at[idx, 'Added Skills'] = ", ".join(new_added)
                    if save_data_to_gsheet(df):
                        # GỌI HÀM UPDATE VỚI FLAG is_gk
                        for s in selected:
                            update_inventory_count(s, -1, is_gk=is_gk)
                        
                        st.toast("Success!", icon="🎉")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()

        # --- 1. THANH CÔNG CỤ FILTER (Sử dụng st.pills nếu có, fallback st.radio) ---
        with st.container(border=True):
            f1, f2, f3 = st.columns([3, 1, 1.2])
            with f1:
                search_txt = st.text_input(
                    "🔍 Search toàn diện", 
                    placeholder="Enter name, skill, Club, or Nation...", 
                    label_visibility="collapsed"
                )
            with f2:
                ft_pos = st.multiselect("Position", sorted(df['Position'].unique().tolist()), placeholder="Position", label_visibility="collapsed")
            with f3:
                # CẬP NHẬT OPTIONS ĐÚNG YÊU CẦU
                status_opts = ["Trainable", "Missing skills to add", "Full skills", "All"]
                ft_status = st.selectbox(
                    "Status", 
                    status_opts, 
                    index=0, # Mặc định hiển thị những người train được ngay
                    label_visibility="collapsed"
                )
            
            with st.expander("🌪️ Advanced filters (Card Type / Rating)"):
                ef1, ef2 = st.columns(2)
                with ef1:
                    ft_type = st.multiselect("Card Type", ["EPIC", "POTW", "NON-EPIC"], default=[], placeholder="Choose card type...")
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
                return "Full skills"

            # 2. Xác định vị trí & Kho tương ứng
            p_pos = str(row['Position']).strip()
            is_gk = p_pos == 'GK'
            
            # [QUAN TRỌNG] Choose kho để check stock
            current_inv = inventory_gk if is_gk else inventory_field

            # 3. Tính toán Strict Targets (Ưu tiên tuyệt đối)
            remaining_slots = MAX_ADDED_SLOTS - len(added)
            all_missing = get_recommended_skills(p_pos, str(row.get('Skills', '')), str(row.get('Added Skills', '')), 15)
            strict_targets = all_missing[:remaining_slots]
            
            if not strict_targets:
                return "Full skills" # Không còn skill gợi ý nào
            
            # 4. Check Stock trong kho tương ứng
            # Chỉ cần 1 skill trong nhóm Strict Targets có hàng -> Trainable
            has_stock = any(current_inv.get(s, 0) > 0 for s in strict_targets)
            
            if has_stock:
                return "Trainable"
            else:
                return "Missing skills to add"

        # Áp dụng logic
        filtered_df['Train_Status'] = filtered_df.apply(classify_status_smart, axis=1)

        # Lọc theo Status người dùng chọn
        if ft_status != "All":
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
            st.caption(f"Found **{total_items}** players.")
        with col_pag2:
            if num_pages > 1:
                page = st.number_input("Page", min_value=1, max_value=num_pages, value=1)
            else:
                page = 1

        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        display_df = filtered_df.iloc[start_idx:end_idx]

        # --- 4. HIỂN THỊ GRID CARD (Logic: Strict Priority / Dành slot tuyệt đối) ---
        if display_df.empty:
            st.info("🔍 No matching players found.")
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
                            btn_label = f"⚠️ Missing: {missing_top1}"
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
                                # Pass the correct inventory depending on player position to avoid extra API calls
                                show_training_modal(idx, row, inventory_gk if is_gk_player else inventory_field)

    elif current_tab == 'squad':
        st.header("⚽ Squad Management")
        sq_tab1, = st.tabs(["🤖 Auto Build (Smart)"])

        # =========================================================
        # TAB 1: AUTO BUILD (REAL-TIME & AUTO FORMATION)
        # =========================================================
        with sq_tab1:
            st.caption("🤖 Choose your squad build mode and criteria. Random mode will pick 23 players from the selected rarity group.")
            
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
                    st.markdown("##### 1. Mode")
                    build_mode = st.radio("Choose build type:", ["By Team/League", "By Stats"], horizontal=True, label_visibility="collapsed")
                
                with c2:
                    st.markdown("##### 2. Detailed configuration")
                    
                    if build_mode == "By Team/League":
                        # Giao diện chọn Team
                        col_a, col_b = st.columns(2)
                        with col_a:
                            team_type = st.selectbox("Filter by:", ["(All)", "Club", "Nation", "League", "Region"])
                        with col_b:
                            if team_type != "(All)":
                                # --- CẬP NHẬT: SẮP XẾP THEO SỐ LƯỢNG GIẢM DẦN (GIỐNG TAB THỦ CÔNG) ---
                                # 1. Đếm số lượng
                                group_counts = df.groupby(team_type)['Player'].nunique().to_dict()
                                
                                # 2. Lấy danh sách duy nhất và loại bỏ giá trị rỗng
                                unique_vals = [x for x in df[team_type].astype(str).unique() if str(x).strip()]
                                
                                # 3. Sort: Ưu tiên số lượng giảm dần -> Sau đó đến tên A-Z (để đẹp hơn nếu bằng số lượng)
                                sorted_opts = sorted(unique_vals, key=lambda x: group_counts.get(x, 0), reverse=True)
                                
                                # 4. Format hiển thị: "Tên (Số lượng)"
                                formatted_opts = [f"{opt} ({group_counts.get(opt, 0)})" for opt in sorted_opts]
                                
                                # 5. Tạo Selectbox
                                selected_display = st.selectbox(f"Choose {team_type}:", ["(All)"] + formatted_opts)
                                
                                # 6. Tách giá trị thực để lọc (Bỏ phần số lượng đi)
                                if selected_display == "(All)":
                                    filter_val = "(All)"
                                else:
                                    filter_val = selected_display.rsplit(" (", 1)[0]
                                
                                filter_col = team_type
                            else:
                                st.selectbox("Value:", ["-"], disabled=True)
                    elif build_mode == "By Stats":
                        # Giao diện chọn loại Squad
                        stat_category = st.radio(
                            "Choose squad category:",
                            ["Special Squads", "Stat + Direction"],
                            horizontal=True,
                            label_visibility="collapsed"
                        )

                        if stat_category == "Special Squads":
                            stat_type = st.selectbox("Special squad criteria:", [label for label, _ in SPECIAL_SQUAD_OPTIONS])
                            sort_mode = dict(SPECIAL_SQUAD_OPTIONS).get(stat_type, 'rating_desc')
                            stat_field = None
                            stat_direction = None
                        else:
                            col_a, col_b = st.columns([2, 1])
                            with col_a:
                                stat_field = st.selectbox(
                                    "Stat field:",
                                    [label for label, _ in GENERIC_SQUAD_FIELDS],
                                    label_visibility="collapsed"
                                )
                            with col_b:
                                stat_direction = st.selectbox(
                                    "Direction:",
                                    [label for label, _ in GENERIC_SORT_DIRECTIONS],
                                    label_visibility="collapsed"
                                )
                            direction = 'desc' if stat_direction == 'Highest first' else 'asc'
                            stat_key = dict(GENERIC_SQUAD_FIELDS).get(stat_field, 'rating')
                            sort_mode = f"{stat_key}_{direction}"
                            stat_type = f"{stat_field} ({stat_direction})"

            # --- TÍNH TOÁN VÀ HIỂN THỊ NGAY LẬP TỨC ---
            
            # 1. Kiểm tra nhanh dữ liệu (nếu chọn Team)
            if build_mode == "By Team/League" and filter_col and filter_val and filter_val != "(All)":
                check_df = df[df[filter_col].astype(str) == filter_val]
                if check_df.empty:
                    st.warning(f"⚠️ No data for {filter_val}")
                else:
                    pos_counts = check_df['Position'].value_counts()
                    missing_msg = []
                    if pos_counts.get('GK', 0) == 0: missing_msg.append("Missing GK")
                    if pos_counts.get('CB', 0) < 2: missing_msg.append("Missing natural CB")
                    if missing_msg:
                        st.toast(f"⚠️ Squad warning: {', '.join(missing_msg)}", icon="⚠️")

            # 2. Chạy Auto Build
            best_squad = []
            found_name = ""

            # Chỉ chạy khi có dữ liệu hợp lệ
            should_run = True
            if build_mode == "By Team/League" and (not filter_val or filter_val == "(All)" or filter_val == "-"):
                # Nếu chọn toàn bộ database thì hơi nặng, nhưng vẫn cho chạy
                pass 

            if should_run:
                # Dùng spinner để báo đang xử lý
                with st.spinner("🤖 Scanning 80+ formations to find the optimal squad..."):
                    found_name, best_squad = find_best_formation_for_team(df, sort_mode, filter_col, filter_val)
                
            if not best_squad:
                st.warning("⚠️ No suitable players found for squad formation!")
            else:
                # Lưu squad vừa build để tab Players dùng chung logic đánh giá Top 23
                st.session_state['last_built_squad'] = best_squad
                st.session_state['last_built_formation'] = found_name

                if found_name:
                    st.success(f"✅ Best optimal lineup (Starters): **{found_name}**")

# --- CODE MỚI: KIỂM TRA & BÁO THIẾU NGƯỜI ---
                    missing_slots = [p['Position'] for p in best_squad if p.get('Is_Starter') and p['Player'] == "---"]
                    if missing_slots:
                        from collections import Counter
                        missing_counts = Counter(missing_slots)
                        missing_text = ", ".join([f"{k} ({v})" for k, v in missing_counts.items()])
                        st.error(f"⚠️ Lineup incomplete! Missing {len(missing_slots)} positions: **{missing_text}**")
                        st.info("💡 The system chose this formation because it requires the fewest additional players.")
                    # ---------------------------------------------

                # --- TÍNH TOÁN CHỈ SỐ (CHO TOÀN BỘ 23 NGƯỜI) ---
                all_valid_players = [p for p in best_squad if p['Rating'] > 0]
                total_players = len(all_valid_players)
                
                t_rat = sum(p['Rating'] for p in all_valid_players)
                a_rat = t_rat / total_players if total_players > 0 else 0
                
                # --- LOGIC TÍNH CHỈ SỐ PHỤ ---
                custom_label = None
                custom_value = None

                if build_mode == "By Stats":
                    def get_val(p, key):
                        try:
                            raw = p.get(key, None)
                            if raw is None and isinstance(p.get('Data', None), dict):
                                raw = p['Data'].get(key, None)
                            return float(re.sub(r'[^\d.]', '', str(raw))) if raw not in [None, ''] else 0
                        except:
                            return 0

                    if stat_category == "Stat + Direction":
                        if stat_field == "BMI":
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
                        else:
                            vals = [get_val(p, stat_field) for p in all_valid_players]
                            avg = sum(vals) / len(vals) if vals else 0
                            custom_label = f"{stat_field} TB (23)"
                            custom_value = f"{avg:.1f}"
                    elif "Tanks" in stat_type or "Agiles" in stat_type:
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
                                
                        custom_label = "Weak foot (Perf/Good)"
                        # Hiển thị dạng: 5 Perfect / 6 Good
                        custom_value = f"{count_tier1} Perf / {count_tier2} Good"

                    elif "United Nations" in stat_type:
                        # FIX: Lấy Nation từ p['Data'] thay vì p['Nation']
                        nations = set(p.get('Data', {}).get('Nation', '') for p in all_valid_players)
                        # Type bỏ giá trị rỗng nếu có
                        if '' in nations: nations.remove('')
                        
                        custom_label = "Nation count"
                        custom_value = f"{len(nations)}"
                    
                    elif "POTW" in stat_type:
                        potw_c = sum(1 for p in all_valid_players if 'POTW' in str(p['Type']).upper() or 'TRENDING' in str(p['Type']).upper())
                        custom_label = "POTW card count"
                        custom_value = f"{potw_c}"
                    elif "Cao" in stat_type or "Thấp" in stat_type:
                        vals = [get_val(p, 'Height') for p in all_valid_players]
                        avg = sum(vals) / len(vals) if vals else 0
                        custom_label = "Height TB (23)"
                        custom_value = f"{avg:.1f} cm"
                    elif "Nặng" in stat_type or "Nhẹ" in stat_type:
                        vals = [get_val(p, 'Weight') for p in all_valid_players]
                        avg = sum(vals) / len(vals) if vals else 0
                        custom_label = "Weight TB (23)"
                        custom_value = f"{avg:.1f} kg"
                    elif "Trẻ" in stat_type or "Già" in stat_type:
                        vals = [get_val(p, 'Age') for p in all_valid_players]
                        avg = sum(vals) / len(vals) if vals else 0
                        custom_label = "Age TB (23)"
                        custom_value = f"{avg:.1f}"

                # --- HIỂN THỊ METRICS ---
                if custom_label:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Total Power (23)", t_rat)
                    with m2: st.metric("Avg Rating (23)", f"{a_rat:.1f}")
                    with m3: st.metric(custom_label, custom_value)
                else:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Total Power (23)", t_rat)
                    with m2: st.metric("Avg Rating (23)", f"{a_rat:.1f}")
                    with m3: st.metric("Squad size", f"{total_players}/23")
                
                st.divider()
                
                # --- HIỂN THỊ SÂN VÀ BẢNG ---
                col_view1, col_view2 = st.columns([1.3, 1]) 
                
                # Xác định metric để hiển thị tooltip trên sân
                metric_to_show = None
                
                if build_mode == "By Stats":
                    if stat_category == "Stat + Direction":
                        if stat_field == "BMI":
                            metric_to_show = 'BMI'
                        else:
                            metric_to_show = stat_field
                    else:
                        # Height
                        if "Cao" in stat_type or "Thấp" in stat_type or "Tallest" in stat_type or "Shortest" in stat_type: 
                            metric_to_show = 'Height'
                        # Weight
                        elif "Nặng" in stat_type or "Nhẹ" in stat_type or "Heaviest" in stat_type or "Lightest" in stat_type: 
                            metric_to_show = 'Weight'
                        # Age
                        elif "Trẻ" in stat_type or "Già" in stat_type or "Youngest" in stat_type or "Oldest" in stat_type: 
                            metric_to_show = 'Age'
                        # BMI (Tanks / Agiles)
                        elif "Tanks" in stat_type or "Agiles" in stat_type or "BMI" in stat_type:
                            metric_to_show = 'BMI'
                        # Preferred Foot (Ambidextrous)
                        elif "Ambidextrous" in stat_type or "Chân" in stat_type: 
                            metric_to_show = 'Ambidextrous'
                        # Nation (United Nations)
                        elif "United Nations" in stat_type or "Nation" in stat_type:
                            metric_to_show = 'Nation'
                        # Card Type (POTW / Epic)
                        elif "POTW" in stat_type or "Epic" in stat_type:
                            metric_to_show = 'Type'
                # ... (Phần code tính toán logic metric_to_show ở trên giữ nguyên) ...

                # --- BẮT ĐẦU THAY ĐỔI TỪ ĐÂY ---
                # Thay vì chia cột, hiển thị Full width
                st.write("") # Spacer
                
                # Gọi hàm render mới
                render_pitch_view(best_squad, formation_name=found_name, sort_mode=sort_mode)
               

        # Manual squad tab removed.
    elif current_tab == 'add':
            st.header("➕ Add player")
            
            # Initialize session state
            if 'add_preview_data' not in st.session_state:
                st.session_state.add_preview_data = None
            if 'add_show_form' not in st.session_state:
                st.session_state.add_show_form = False
            if 'add_mode' not in st.session_state:
                st.session_state.add_mode = 'new'
            
            # ========== CHỌN CHẾ ĐỘ ==========
            mode = st.radio(
                "Choose mode",
                ["➕ Add", "🔄 Upgrade existing player"],
                horizontal=True,
                key="add_mode_radio"
            )
            
            st.session_state.add_mode = 'upgrade' if mode == "🔄 Upgrade existing player" else 'new'
            
            st.divider()
            
            # ========== CHẾ ĐỘ UPGRADE ==========
            if st.session_state.add_mode == 'upgrade':
                st.info("💡 This mode automatically finds and replaces old cards (same name + Club + Nation + League)")
                
                # Bước 1: Choose cầu thủ
                existing_players = sorted(df['Player'].astype(str).unique().tolist())
                selected_player = st.selectbox(
                    "1️⃣ Choose player to upgrade",
                    options=[""] + existing_players,
                    help="Choose a player from the existing list"
                )
                
                if selected_player:
                    # Hiển thị tất cả phiên bản hiện có
                    player_versions = df[df['Player'] == selected_player].copy()
                    player_versions = player_versions.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
                    
                    st.subheader(f"📋 Existing version of {selected_player}")
                    # Hiển thị thêm cột Secondary Positions để đối chiếu
                    cols_ver = ['Rating', 'Position', 'Secondary Positions', 'Player Type', 'Club', 'Nation', 'League']
                    cols_ver = [c for c in cols_ver if c in player_versions.columns]
                    
                    version_display = player_versions[cols_ver].copy()
                    version_display.insert(0, 'STT', range(1, len(version_display) + 1))
                    st.dataframe(version_display, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.markdown("### 2️⃣ Enter the new version PESDB URL or ID")
                    
                    upgrade_input = st.text_input(
                        "PESDB URL or Player ID",
                        placeholder="105809740719809 or https://pesdb.net/efootball/?id=105809740719809 or https://efhub.com/players/106784161310028",
                        key="upgrade_url"
                    )
                    
                    # Tự động fetch khi input thay đổi
                    if upgrade_input and upgrade_input != st.session_state.get('last_upgrade_input', ''):
                        st.session_state.last_upgrade_input = upgrade_input
                        
                        # Xử lý input: chỉ link pesdata.net dùng để lấy Body model; số thường vẫn dùng PESDB
                        if upgrade_input.isdigit():
                            upgrade_url = f"https://pesdb.net/efootball/?id={upgrade_input}"
                        elif "pesdata.net" in upgrade_input or "player/detail/" in upgrade_input:
                            upgrade_url = upgrade_input
                        elif "efhub.com" in upgrade_input:
                            _pid = extract_ehub_player_id(upgrade_input)
                            upgrade_url = f"https://pesdb.net/efootball/?id={_pid}" if _pid else upgrade_input
                        else:
                            upgrade_url = upgrade_input
                        
                        with st.spinner("⏳ Extracting data..."):
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
                                    'Player_ID': extract_ehub_player_id(upgrade_url),
                                    **{field: player_info.get(field, '') for field in PESDATA_BODY_MODEL_FIELDS},
                                    'Booster Type': 'None',
                                    'National Booster': False,
                                    'Booster Rating 1-7': 0,
                                    'Booster Rating 8-10': 0,
                                    'Booster Rating 11-23': 0,
                                }
                                st.session_state.add_show_form = True
                                st.success("✅ Successfully fetched info!")
                                st.rerun()
                            else:
                                st.error("❌ Cannot fetch info from this URL!")
            
            # ========== CHẾ ĐỘ THÊM MỚI ==========
            else:
                if not st.session_state.add_show_form:
                    st.markdown("### 🔗 Step 1: Enter PESDB URL or ID")
                    st.info("💡 Enter the PESDB link, player ID, or efhub link to automatically fetch full player info")
                    
                    pesdb_input = st.text_input(
                        "PESDB URL or Player ID",
                        placeholder="105809740719809 or https://pesdb.net/efootball/?id=105809740719809 or https://efhub.com/players/106784161310028",
                        help="Example: 105809740719809 or https://pesdb.net/efootball/?id=105809740719809 or https://efhub.com/players/106784161310028"
                    )
                    
                    # Tự động fetch khi input thay đổi
                    if pesdb_input and pesdb_input != st.session_state.get('last_pesdb_input', ''):
                        st.session_state.last_pesdb_input = pesdb_input
                        
                        # Xử lý input: số hoặc efhub dùng PESDB cũ; chỉ pesdata.net mới dùng link mới
                        if pesdb_input.isdigit():
                            pesdb_url = f"https://pesdb.net/efootball/?id={pesdb_input}"
                        elif "pesdata.net" in pesdb_input or "player/detail/" in pesdb_input:
                            pesdb_url = pesdb_input
                        elif "efhub.com" in pesdb_input:
                            _pid = extract_ehub_player_id(pesdb_input)
                            pesdb_url = f"https://pesdb.net/efootball/?id={_pid}" if _pid else pesdb_input
                        else:
                            pesdb_url = pesdb_input
                        
                        with st.spinner("⏳ Extracting data from PESDB..."):
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
                                    'Player_ID': extract_ehub_player_id(pesdb_url),
                                    **{field: player_info.get(field, '') for field in PESDATA_BODY_MODEL_FIELDS},
                                    'Booster Type': 'None',
                                    'National Booster': False,
                                    'Booster Rating 1-7': 0,
                                    'Booster Rating 8-10': 0,
                                    'Booster Rating 11-23': 0,
                                }
                                st.session_state.add_show_form = True
                                st.success("✅ Successfully fetched info!")
                            else:
                                st.error("❌ Cannot fetch info from this URL. Please check again!")
                    
                    # Nút nhập tay nếu cần
                    if st.button("✍️ Enter manually instead", use_container_width=True):
                            manual_preview = {
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
                                'Player_ID': '',
                                'National Booster': False,
                                'Booster Rating 1-7': 0,
                                'Booster Rating 8-10': 0,
                                'Booster Rating 11-23': 0,
                            }
                            for field in PESDATA_BODY_MODEL_FIELDS:
                                manual_preview[field] = ''
                            st.session_state.add_preview_data = manual_preview
                            st.session_state.add_show_form = True
                            st.rerun()
                    
                    st.divider()
                    st.caption("🎯 **Guide:** Enter the PESDB URL to fetch info automatically, or choose 'Enter manually' to fill it in yourself")
            
            # ========== BƯỚC 2: PREVIEW & CHỈNH SỬA (CHUNG CHO CẢ 2 MODE) ==========
            if st.session_state.add_show_form and st.session_state.add_preview_data:
                data = st.session_state.add_preview_data
                
                st.markdown("### 📋 Step 2: Review & edit")
                
                # Hiển thị hình ảnh nếu có Player ID
                if data.get('Player_ID'):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        image_url = make_ehub_player_image_url(data['Player_ID'])
                        st.image(image_url, width=200)
                    with col_info:
                        st.markdown(f"## {data.get('Player', 'Unknown Player')}")
                        # Hiển thị nhanh các vị trí
                        st.caption(f"**Main Position:** {data.get('Position')} | **Secondary:** {data.get('Secondary Positions')}")
                else:
                    st.markdown(f"## ✍️ Enter new player information")

                if any(data.get(field) for field in PESDATA_BODY_MODEL_FIELDS):
                    with st.expander("📦 PESDATA Body Model Preview", expanded=True):
                        cols = st.columns(2)
                        for idx, field_name in enumerate(PESDATA_BODY_MODEL_FIELDS):
                            if not data.get(field_name):
                                continue
                            with cols[idx % 2]:
                                st.text_input(field_name, value=data.get(field_name, ''), key=f"preview_{field_name}", disabled=True)

                st.divider()

                # Form chỉnh sửa
                with st.form("add_player_final_form", clear_on_submit=False):
                    st.subheader("✏️ Player information")
                    
                    # Row 1: Tên + Rating + Type
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        player_name = st.text_input("👤 Player name *", value=data.get('Player', ''), placeholder="Example: Lionel Messi")
                    with col2:
                        rating = st.number_input("⭐ Rating *", min_value=1, max_value=150, value=data.get('Rating', 90))
                    with col3:
                        type_options = ["NON-EPIC", "POTW", "EPIC"]
                        current_type = data.get('Player_Type', 'NON-EPIC')
                        type_idx = type_options.index(current_type) if current_type in type_options else 0
                        player_type = st.selectbox("🏷️ Card Type *", type_options, index=type_idx)
                    
                    # Row 2: Position + Nhóm vị trí
                    col1, col2 = st.columns(2)
                    with col1:
                        existing_positions = sorted(df['Position'].unique().tolist(), key=lambda x: POSITION_ORDER.get(x, 999))
                        current_pos = data.get('Position', '')
                        if current_pos and current_pos not in existing_positions:
                            existing_positions.insert(0, current_pos)
                        position_idx = existing_positions.index(current_pos) if current_pos in existing_positions else 0
                        position = st.selectbox("📍 Main Position *", existing_positions, index=position_idx)
                    with col2:
                        position_style = st.selectbox(
                            "🎮 Position Group *",
                            POSITION_STYLES,
                            index=POSITION_STYLES.index(POSITIONS.get(position, "Forward"))
                        )

                    # --- MỚI: VỊ TRÍ PHỤ ---
                    st.markdown("#### 🔁 Secondary Positions")
                    secondary_pos = st.text_input(
                        "Enter secondary positions (comma-separated)", 
                        value=data.get('Secondary Positions', ''),
                        help="Example: LWF, SS, AMF. Leave blank if none."
                    )
                    # -----------------------
                    
                    st.divider()
                    st.subheader("🌍 Team information")
                    
                    # Row 3: Nation + Club + League
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        existing_nations = [""] + sorted([x for x in df['Nation'].astype(str).unique() if str(x).strip()])
                        current_nation = data.get('Nation', '')
                        if current_nation and current_nation not in existing_nations:
                            existing_nations.insert(1, current_nation)
                        nation_idx = existing_nations.index(current_nation) if current_nation in existing_nations else 0
                        nation = st.selectbox("🏴 Nation", existing_nations, index=nation_idx)
                        if nation == "":
                            nation_new = st.text_input("Enter a new nation", key="nation_new")
                            if nation_new:
                                nation = nation_new
                    
                    with col2:
                        existing_clubs = [""] + sorted([x for x in df['Club'].astype(str).unique() if str(x).strip()])
                        current_club = data.get('Club', '')
                        if current_club and current_club not in existing_clubs:
                            existing_clubs.insert(1, current_club)
                        club_idx = existing_clubs.index(current_club) if current_club in existing_clubs else 0
                        club = st.selectbox("⚽ Club", existing_clubs, index=club_idx)
                        if club == "":
                            club_new = st.text_input("Enter a new club", key="club_new")
                            if club_new:
                                club = club_new
                    
                    with col3:
                        existing_leagues = [""] + sorted([x for x in df['League'].astype(str).unique() if str(x).strip()])
                        current_league = data.get('League', '')
                        if current_league and current_league not in existing_leagues:
                            existing_leagues.insert(1, current_league)
                        league_idx = existing_leagues.index(current_league) if current_league in existing_leagues else 0
                        league = st.selectbox("🏆 League", existing_leagues, index=league_idx)
                        if league == "":
                            league_new = st.text_input("Enter a new league", key="league_new")
                            if league_new:
                                league = league_new
                    
                    # Row 4: Thể chất & thuộc tính
                    st.divider()
                    st.subheader("📊 Physicals & Attributes")
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
                        "Skill list (comma-separated)",
                        value=data.get('Skills', ''),
                        height=100,
                        help="Example: Heading, Man Marking, Interception"
                    )
                    
                    st.divider()
                    st.subheader("🚀 Booster Type")
                    current_booster_type = _normalize_booster_type(data.get('Booster Type', 'National' if data.get('National Booster', False) else 'None'))
                    booster_type = st.selectbox(
                        "Booster Type",
                        ["None", "National", "Club", "League"],
                        index=["None", "National", "Club", "League"].index(current_booster_type),
                        help="Choose the booster scope. Only one type can be active at a time. The ratings apply for the selected group."
                    )
                    booster_enabled = booster_type != 'None'
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        booster_1_7 = st.number_input(
                            "Boosted Rating (1–7 team mates)",
                            min_value=1, max_value=150,
                            value=int(data.get('Booster Rating 1-7', 0) or data.get('Rating', 90)),
                            help="Effective boosted Rating when you own 1–7 players in the selected group"
                        )
                    with col2:
                        booster_8_10 = st.number_input(
                            "Boosted Rating (8–10 team mates)",
                            min_value=1, max_value=150,
                            value=int(data.get('Booster Rating 8-10', 0) or data.get('Rating', 90)),
                            help="Effective boosted Rating when you own 8–10 players in the selected group"
                        )
                    with col3:
                        booster_11_23 = st.number_input(
                            "Boosted Rating (11–23 team mates)",
                            min_value=1, max_value=150,
                            value=int(data.get('Booster Rating 11-23', 0) or data.get('Rating', 90)),
                            help="Effective boosted Rating when you own 11–23 players in the selected group"
                        )

                    st.divider()
                    
                    # Buttons
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col2:
                        cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                    with col3:
                        save_btn = st.form_submit_button("💾 Save player", type="primary", use_container_width=True)
                    
                    # Xử lý buttons
                    if cancel_btn:
                        st.session_state.add_preview_data = None
                        st.session_state.add_show_form = False
                        st.rerun()
                    
                    if save_btn:
                        if not player_name:
                            st.error("❌ Please enter a player name!")
                        elif not position:
                            st.error("❌ Please select a position!")
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
                                    for field in PESDATA_BODY_MODEL_FIELDS:
                                        new_df.at[old_idx, field] = data.get(field, '')
                                    new_df.at[old_idx, 'Epic_Priority'] = 0 if player_type_norm == "EPIC" else 1
                                    new_df.at[old_idx, 'National Booster'] = booster_type == 'National'
                                    new_df.at[old_idx, 'Booster Type'] = booster_type
                                    new_df.at[old_idx, 'Booster Rating 1-7'] = booster_1_7 if booster_enabled else 0
                                    new_df.at[old_idx, 'Booster Rating 8-10'] = booster_8_10 if booster_enabled else 0
                                    new_df.at[old_idx, 'Booster Rating 11-23'] = booster_11_23 if booster_enabled else 0
                                    
                                    try:
                                        if save_data_to_gsheet(new_df):
                                            rating_diff = int(rating) - old_rating
                                            st.success(f"✅ Upgraded **{player_name}**: {old_rating} ({old_type}) → {rating} ({player_type}) ({rating_diff:+d})")
                                            st.info(f"📍 {club} | {nation} | {league}")
                                            
                                            st.session_state.add_preview_data = None
                                            st.session_state.add_show_form = False
                                            st.cache_data.clear()
                                            st.balloons()
                                            
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error("❌ Could not save data!")
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")
                                else:
                                    st.warning(f"⚠️ No existing card found with this Club/Nation/League")
                                    st.info("💡 Will add a new version instead of upgrading")
                                    
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
                                        **{field: data.get(field, '') for field in PESDATA_BODY_MODEL_FIELDS},
                                        "Epic_Priority": 0 if player_type_norm == "EPIC" else 1,
                                        "National Booster": booster_type == 'National',
                                        "Booster Type": booster_type,
                                        "Booster Rating 1-7": booster_1_7 if booster_enabled else 0,
                                        "Booster Rating 8-10": booster_8_10 if booster_enabled else 0,
                                        "Booster Rating 11-23": booster_11_23 if booster_enabled else 0,
                                    }
                                    
                                    new_df = pd.concat([new_df, pd.DataFrame([new_player])], ignore_index=True)
                                    
                                    try:
                                        if save_data_to_gsheet(new_df):
                                            st.success(f"✅ Successfully added player **{player_name}**!")

                                            st.session_state.add_preview_data = None
                                            st.session_state.add_show_form = False
                                            st.cache_data.clear()
                                            st.balloons()

                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ Could not save data to Google Sheets!")
                                    except Exception as e:
                                        st.error(f"❌ Error saving: {e}")
                            else:
                                new_player = {
                                    "Player": player_name,
                                    "Rating": int(rating),
                                    "Position": position,
                                    "Position Style": position_style,
                                    "Secondary Positions": secondary_pos,
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
                                    **{field: data.get(field, '') for field in PESDATA_BODY_MODEL_FIELDS},
                                    "Epic_Priority": 0 if player_type_norm == "EPIC" else 1,
                                    "National Booster": booster_type == 'National',
                                    "Booster Type": booster_type,
                                    "Booster Rating 1-7": booster_1_7 if booster_enabled else 0,
                                    "Booster Rating 8-10": booster_8_10 if booster_enabled else 0,
                                    "Booster Rating 11-23": booster_11_23 if booster_enabled else 0,
                                }

                                new_df = pd.concat([df, pd.DataFrame([new_player])], ignore_index=True)

                                try:
                                    if save_data_to_gsheet(new_df):
                                        st.success(f"✅ Successfully added player **{player_name}**!")

                                        st.session_state.add_preview_data = None
                                        st.session_state.add_show_form = False
                                        st.cache_data.clear()
                                        st.balloons()

                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ Could not save data to Google Sheets!")
                                except Exception as e:
                                    st.error(f"❌ Error saving: {e}")
            
    elif current_tab == 'inventory':
        st.header("📦 Skill Inventory Management")

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
        inv_type = st.radio("📂 Choose Kho:", ["🏃 Player (Field)", "🧤 Goalkeeper (GK)"], horizontal=True)
        is_gk_mode = "Goalkeeper (GK)" in inv_type

        # --- 3. LOAD DATA TƯƠNG ỨNG ---
        if is_gk_mode:
            inventory = get_gk_inventory_from_gsheet()
            # GK chỉ dùng đúng list priority đã định nghĩa, không có category phức tạp
            target_skills = GK_SKILLS_PRIORITY_LIST
            # Gom tất cả vào 1 nhóm duy nhất cho gọn
            grouped_skills = {"🧤 Goalkeeper Skills": target_skills}
            st.info("💡 This is a separate GK inventory. Skills here are not shared with regular players.")
        else:
            inventory = get_inventory()
            all_skills = get_all_known_skills()
            # Logic phân loại cũ cho Field Players
            STRICT_CATEGORIES = {
                "🎮 Dribbling": ["Sole Control", "Scissors Feint", "Double Touch", "Flip Flap", "Marseille Turn", "Sombrero", "Chop Turn", "Cut Behind & Turn", "Scotch Move", "Rabona"],
                "⚽ Passing": ["Weighted Pass", "Pinpoint Crossing", "One-touch Pass", "Through Passing", "No Look Pass", "Low Lofted Pass", "Long Throw"],
                "🎯 Shooting": ["First-time Shot", "Long Range Shooting", "Long-Range Curler", "Outside Curler", "Chip Shot Control", "Knuckle Shot", "Dipping Shot", "Rising Shot", "Acrobatic Finishing"],
                "🛡️ Defense": ["Man Marking", "Track Back", "Acrobatic Clearance", "Interception", "Blocker", "Heading", "Aerial Superiority", "Sliding Tackle"],
                "✨ Other": ["Captaincy", "Super Sub", "Fighting Spirit", "Gamesmanship", "Penalty Specialist", "Heel Trick"]
            }
            # Gom skill GK ra khỏi list Field (nếu muốn ẩn GK skills ở kho thường)
            # Tuy nhiên code cũ bạn đang gộp chung, giờ ta chỉ hiển thị những gì không phải GK specific hoặc cứ để full
            # Để đơn giản và đúng logic cũ: Field Inventory chứa tất cả skill (trừ những cái thuần GK nếu muốn lọc)
            
            grouped_skills = {k: [] for k in STRICT_CATEGORIES.keys()}
            grouped_skills["❓ Unsorted"] = []
            
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
                if not found: grouped_skills["❓ Unsorted"].append(skill)
            
            grouped_skills = {k: v for k, v in grouped_skills.items() if v}

        # --- 4. SUMMARY ---
        total_items = sum(inventory.values())
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"### 🎒 Inventory ({'GK' if is_gk_mode else 'Field'}): <span style='color:#4ade80'>{total_items}</span> cards", unsafe_allow_html=True)
            with c2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            with c3:
                if 'confirm_delete_inventory' not in st.session_state:
                    st.session_state['confirm_delete_inventory'] = False

                if st.button("🗑️ Delete this inventory", type="primary"):
                    st.session_state['confirm_delete_inventory'] = True

                if st.session_state.get('confirm_delete_inventory'):
                    st.warning("⚠️ This will delete all inventory data. This action is irreversible.")
                    col_yes, col_no = st.columns([1,1])
                    with col_yes:
                        if st.button("⚠️ Yes, delete everything", key="confirm_delete_yes", type="primary"):
                            if is_gk_mode:
                                save_gk_inventory_to_gsheet({k:0 for k in GK_SKILLS_PRIORITY_LIST})
                            else:
                                save_skill_inventory_to_gsheet({})
                            st.session_state['confirm_delete_inventory'] = False
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", key="confirm_delete_cancel"):
                            st.session_state['confirm_delete_inventory'] = False
                            st.rerun()

        st.write("") 

        # --- 5. FORM EDIT ---
        with st.form("inventory_form"):
            tabs = st.tabs(list(grouped_skills.keys()))
            new_values = {}

            for tab_idx, (cat_name, skills_in_cat) in enumerate(grouped_skills.items()):
                with tabs[tab_idx]:
                    cols = st.columns(4)
                    # Preserve explicit priority order for GK inventory; alphabetical for Field
                    if is_gk_mode:
                        skills_iter = skills_in_cat
                    else:
                        skills_iter = sorted(skills_in_cat)
                    for i, skill in enumerate(skills_iter):
                        current_qty = inventory.get(skill, 0)
                        
                        icon = "🧤" if is_gk_mode else "✨"
                        if "Dribbling" in cat_name: icon = "🎮"
                        elif "Passing" in cat_name: icon = "⚽"
                        elif "Shooting" in cat_name: icon = "🎯"
                        elif "Defense" in cat_name: icon = "🛡️"
                        
                        stock_class = "has-stock" if current_qty > 0 else "no-stock"
                        stock_text = "In stock" if current_qty > 0 else "Out of stock"
                        
                        with cols[i % 4]:
                            st.markdown(f"""
                            <div class="skill-card">
                                <div class="skill-icon">{icon}</div>
                                <div class="skill-name">{skill}</div>
                                <div class="quantity-badge {stock_class}">{stock_text}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            widget_key = f"inv_{'gk' if is_gk_mode else 'field'}_{skill}"
                            val = st.number_input(
                                f"{skill}", min_value=0, max_value=999, 
                                value=int(current_qty), step=1, key=widget_key, 
                                label_visibility="collapsed"
                            )
                            new_values[skill] = val
                            st.write("") 

            st.divider()
            col_submit, col_info = st.columns([1, 3])
            with col_submit:
                submitted = st.form_submit_button("💾 UPDATE INVENTORY", type="primary", use_container_width=True)
            with col_info:
                st.caption("💡 You are editing the **" + ("GK" if is_gk_mode else "PLAYER") + " inventory. Please review carefully before saving.")

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
                with st.spinner("Saving..."):
                    success = False
                    if is_gk_mode: success = save_gk_inventory_to_gsheet(final_inventory)
                    else: success = save_skill_inventory_to_gsheet(final_inventory)
                    
                    if success:
                        st.toast("✅ Saved successfully!", icon="💾")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Error saving.")
            else:
                st.toast("⚠️ No changes detected.", icon="ℹ️")


if __name__ == "__main__":
    main()