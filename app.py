# app.py – Efootball Team Builder (Google Sheets version)
import os
import shutil
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
        
        # Ensure required columns
        required_cols = [
            "Player", "Rating", "Position", "Position Style", "Player Type",
            "Nation", "Club", "League", "Player URL", "Player ID", "Skills", "Added Skills",
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
        
        for col in ["Player", "Position", "Position Style", "Player Type", "Nation", "Club", "League", "Player URL", "Player ID", "Skills", "Added Skills"]:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).replace(['nan', 'None', 'NaN', '<NA>'], '').str.strip()
        
        df["Epic_Priority"] = df["Player Type"].apply(lambda x: 0 if str(x).strip().upper() == "EPIC" else 1)
        
        return df
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc dữ liệu: {e}")
        return pd.DataFrame()

def save_data_to_gsheet(df):
    """Lưu dữ liệu lên Google Sheets"""
    try:
        client = get_gsheet_connection()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        
        # Remove Epic_Priority column before saving
        df_save = df.drop(columns=['Epic_Priority'], errors='ignore')
        
        # Clear and update
        sheet.clear()
        sheet.update([df_save.columns.values.tolist()] + df_save.values.tolist())
        return True
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu dữ liệu: {e}")
        return False

# --- SKILLS PRIORITY SYSTEM ---
POSITION_SKILLS_PRIORITY = {
    "CF": [
        "First Time Shot", "Acrobatic Finishing", "Long Range Drive", 
        "Long Range Shooting", "Outside Curler", "Heading", 
        "Aerial Superiority", "One Touch Pass", "Through Passing",
        "Weighted Pass", "Fighting Spirit", "Cut Behind & Turn",
        "Step On Skill Control", "Heel Trick", "Track Back"
    ],
    "SS": [
        "One Touch Pass", "Through Passing", "First Time Shot",
        "Acrobatic Finishing", "Fighting Spirit", "Outside Curler",
        "Long Range Shooting", "Weighted Pass", "Step On Skill Control",
        "Long Range Drive", "Cut Behind & Turn", "Double Touch",
        "Pinpoint Crossing", "Heel Trick", "Super Sub"
    ],
    "LWF": [
        "Pinpoint Crossing", "One Touch Pass", "Through Passing",
        "Weighted Pass", "Outside Curler", "Fighting Spirit",
        "Step On Skill Control", "Long Range Drive", "Long Range Shooting",
        "Cut Behind & Turn", "First Time Shot", "Heel Trick",
        "Double Touch", "Acrobatic Finishing", "Super Sub"
    ],
    "RWF": [
        "Pinpoint Crossing", "One Touch Pass", "Through Passing",
        "Weighted Pass", "Outside Curler", "Fighting Spirit",
        "Step On Skill Control", "Long Range Drive", "Long Range Shooting",
        "Cut Behind & Turn", "First Time Shot", "Heel Trick",
        "Double Touch", "Acrobatic Finishing", "Super Sub"
    ],
    "AMF": [
        "One Touch Pass", "Through Passing", "Weighted Pass",
        "Long Range Drive", "Fighting Spirit", "First Time Shot",
        "Long Range Shooting", "Outside Curler", "Pinpoint Crossing",
        "Cut Behind & Turn", "Step On Skill Control", "Heel Trick",
        "Acrobatic Finishing", "Double Touch", "Low Lofted Pass"
    ],
    "CMF": [
        "One Touch Pass", "Through Passing", "Interception",
        "Weighted Pass", "Fighting Spirit", "Track Back",
        "Step On Skill Control", "Cut Behind & Turn", "Pinpoint Crossing","Outside Curler", "Heel Trick", "Low Lofted Pass",
        "Blocker", "Long Range Shooting", "Double Touch"
    ],
    "DMF": [
        "Interception", "Blocker", "One Touch Pass",
        "Through Passing", "Weighted Pass", "Man Marking",
        "Fighting Spirit", "Step On Skill Control", "Aerial Superiority",
        "Sliding Tackle", "Heading", "Low Lofted Pass",
        "Cut Behind & Turn", "Outside Curler", "Acrobatic Clear"
    ],
    "LMF": [
        "Pinpoint Crossing", "One Touch Pass", "Through Passing",
        "Fighting Spirit", "Cut Behind & Turn", "Weighted Pass",
        "Outside Curler", "Long Range Drive", "Step On Skill Control",
        "Heel Trick", "Track Back", "Long Range Shooting",
        "First Time Shot", "Acrobatic Finishing", "Double Touch"
    ],
    "RMF": [
        "Pinpoint Crossing", "One Touch Pass", "Through Passing",
        "Fighting Spirit", "Cut Behind & Turn", "Weighted Pass",
        "Outside Curler", "Long Range Drive", "Step On Skill Control",
        "Heel Trick", "Track Back", "Long Range Shooting",
        "First Time Shot", "Acrobatic Finishing", "Double Touch"
    ],
    "LB": [
        "Track Back", "Blocker", "Interception",
        "Man Marking", "Pinpoint Crossing", "Fighting Spirit",
        "Sliding Tackle", "Acrobatic Clear", "Aerial Superiority",
        "One Touch Pass", "Through Passing", "Weighted Pass",
        "Outside Curler", "Step On Skill Control", "Low Lofted Pass"
    ],
    "RB": [
        "Track Back", "Blocker", "Interception",
        "Man Marking", "Pinpoint Crossing", "Fighting Spirit",
        "Sliding Tackle", "Acrobatic Clear", "Aerial Superiority",
        "One Touch Pass", "Through Passing", "Weighted Pass",
        "Outside Curler", "Step On Skill Control", "Low Lofted Pass"
    ],
    "CB": [
        "Interception", "Blocker", "Man Marking",
        "Aerial Superiority", "Heading", "Sliding Tackle",
        "Acrobatic Clear", "Fighting Spirit", "One Touch Pass",
        "Through Passing", "Weighted Pass", "Low Lofted Pass",
        "Step On Skill Control", "Outside Curler", "Track Back"
    ],
    "GK": [
        "GK Low Punt", "GK High Punt", "GK Long Throw",
        "GK Penalty Saver", "Fighting Spirit", "Low Lofted Pass",
        "One Touch Pass", "Through Passing", "Weighted Pass",
        "Outside Curler", "Step On Skill Control", "Heel Trick",
        "Captaincy"
    ]
}

def normalize_skill_name(skill: str) -> str:
    """Chuẩn hóa tên skill để so sánh - loại bỏ mọi whitespace thừa"""
    normalized = re.sub(r'\s+', ' ', str(skill).strip())
    return normalized.lower()

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

# --- SKILL INVENTORY MANAGEMENT ---
APP_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = APP_DIR / "skill_inventory.json"

def load_skill_inventory():
    """Load skill inventory from JSON file"""
    if INVENTORY_FILE.exists():
        try:
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_skill_inventory(inventory):
    """Save skill inventory to JSON file"""
    try:
        with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def get_all_known_skills():
    """Get all skills from POSITION_SKILLS_PRIORITY"""
    all_skills = set()
    for skills_list in POSITION_SKILLS_PRIORITY.values():
        all_skills.update(skills_list)
    return sorted(list(all_skills))

def update_inventory_count(skill_name, delta):
    """Update skill count in inventory by delta (+1 or -1)"""
    inventory = load_skill_inventory()
    current = inventory.get(skill_name, 0)
    new_count = max(0, current + delta)
    
    if new_count == 0 and skill_name in inventory:
        del inventory[skill_name]
    else:
        inventory[skill_name] = new_count
    
    save_skill_inventory(inventory)
    return new_count

def check_inventory_availability(skill_name):
    """Check if skill is available in inventory"""
    inventory = load_skill_inventory()
    return inventory.get(skill_name, 0) > 0

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

# Scraper config
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
}

EFOOTBALLHUB_PLAYER_URL_BASE = "https://efootballhub.net/efootball23/player/"

# --- UTILITIES ---

def extract_ehub_player_id(value: str) -> str:
    """Extract numeric player id from an efootballhub URL or a raw id string."""
    if not value:
        return ""
    s = str(value).strip()
    m = re.search(r"(\d{6,})", s)
    return m.group(1) if m else ""

def make_ehub_player_url(player_id: str) -> str:
    pid = extract_ehub_player_id(player_id)
    return f"{EFOOTBALLHUB_PLAYER_URL_BASE}{pid}" if pid else ""

@st.cache_data(ttl=86400)
def fetch_ehub_raw_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def extract_player_skills(player_url: str) -> str:
    """Trích xuất Skills từ eFootballHub player page"""
    try:
        if not player_url or not str(player_url).startswith('http'):
            return ""
        html = fetch_ehub_raw_html(player_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        skill_container = soup.find('div', class_='player-skill-container')
        if not skill_container:
            return ""
        
        skill_labels = skill_container.find_all('label', class_='lbl-block', hidden=False)
        
        skills = []
        for label in skill_labels:
            skill_name = label.get_text(strip=True)
            if skill_name and skill_name.lower() != 'skills':
                skills.append(skill_name)
        
        skills = sorted(list(set(x for x in skills if x)))
        return ', '.join(skills)
    except Exception:
        return ""

def get_unique_values(df: pd.DataFrame, column: str) -> list:
    if column in df.columns:
        vals = [str(x) for x in df[column].unique() if pd.notna(x) and str(x).strip()]
        return sorted(vals)
    return []

def initialize_session_state():
    defaults = {
        'manual_reload_triggered': False,
        'selected_player_detail': None,
        'editing_player': None,
        'current_tab': 'overview',
        'checkbox_reset_counter': 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --- MAIN APP ---
def main():
    initialize_session_state()

    st.title("⚽ Efootball Team Builder – Google Sheets")

    with st.sidebar:
        st.header("⚙️ Điều khiển")
        if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.manual_reload_triggered = True
            st.rerun()
        
        st.divider()
        
        st.subheader("📑 Điều hướng")
        
        if st.button("📊 Tổng quan", use_container_width=True, type="secondary" if st.session_state.current_tab != 'overview' else "primary"):
            st.session_state.current_tab = 'overview'
            st.rerun()
        
        if st.button("👥 Cầu thủ", use_container_width=True, type="secondary" if st.session_state.current_tab != 'players' else "primary"):
            st.session_state.current_tab = 'players'
            st.rerun()
        
        if st.button("🎮 Quản lý Skills", use_container_width=True, type="secondary" if st.session_state.current_tab != 'skills' else "primary"):
            st.session_state.current_tab = 'skills'
            st.rerun()
        
        if st.button("📦 Kho Skills", use_container_width=True, type="secondary" if st.session_state.current_tab != 'inventory' else "primary"):
            st.session_state.current_tab = 'inventory'
            st.rerun()
        
        if st.button("⚽ Đội hình", use_container_width=True, type="secondary" if st.session_state.current_tab != 'squad' else "primary"):
            st.session_state.current_tab = 'squad'
            st.rerun()
        
        if st.button("➕ Thêm cầu thủ", use_container_width=True, type="secondary" if st.session_state.current_tab != 'add' else "primary"):
            st.session_state.current_tab = 'add'
            st.rerun()
        
        st.divider()
        st.caption(f"☁️ Google Sheets • Max Squad: {MAX_SQUAD_SIZE}")

    with st.spinner("⏳ Đang tải dữ liệu từ Google Sheets..."):
        df = load_data_from_gsheet()
    
    if df.empty:
        st.error("Không có dữ liệu cầu thủ!")
        return

    needs_extraction = df[
        (df['Player URL'].astype(str).str.startswith('http')) & 
        ((df['Skills'].astype(str).str.strip() == '') | (df['Skills'].isna()))
    ]
    
    if not needs_extraction.empty and not st.session_state.get('auto_extracting', False):
        st.session_state['auto_extracting'] = True
        updated = False
        
        for i, row in needs_extraction.iterrows():
            skills = extract_player_skills(row['Player URL'])
            if skills:
                df.at[i, 'Skills'] = skills
                updated = True
        
        if updated:
            save_data_to_gsheet(df)
            st.cache_data.clear()
        
        st.session_state['auto_extracting'] = False

    current_tab = st.session_state.current_tab

    if current_tab == 'overview':
        st.header("📊 Tổng quan")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Tổng cầu thủ", len(df))
        with c2:
            st.metric("Rating TB", f"{df['Rating'].mean():.1f}")
        with c3:
            st.metric("Epic", int((df['Player Type'].astype(str).str.upper() == 'EPIC').sum()))
        with c4:
            st.metric("POTW", int((df['Player Type'].astype(str).str.upper() == 'POTW').sum()))

        st.divider()

        # Phân bố theo vị trí
        st.subheader("📍 Phân bố theo vị trí")
        pos_counts = df['Position'].value_counts().reset_index(name='Count')
        pos_counts.columns = ['Position', 'Count']
        pos_counts = pos_counts.sort_values('Count', ascending=False)
        pos_counts.insert(0, 'STT', range(1, len(pos_counts) + 1))
        st.dataframe(pos_counts, 
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small"),
                "Position": st.column_config.TextColumn("Vị trí", width="small"),
                "Count": st.column_config.NumberColumn("Số lượng", width="small"),
            },
            use_container_width=True, 
            hide_index=True)

        st.divider()

        # Phân bố theo loại
        st.subheader("🏷️ Phân bố theo loại")
        type_counts = df['Player Type'].value_counts().reset_index(name='Count')
        type_counts.columns = ['Player Type', 'Count']
        type_counts = type_counts.sort_values('Count', ascending=False)
        type_counts.insert(0, 'STT', range(1, len(type_counts) + 1))
        st.dataframe(type_counts, 
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small"),
                "Player Type": st.column_config.TextColumn("Loại", width="small"),
                "Count": st.column_config.NumberColumn("Số lượng", width="small"),
            },
            use_container_width=True, 
            hide_index=True)

        st.divider()

        # Top Leagues
        st.subheader("🏆 Top 10 Leagues")
        league_counts = df['League'].value_counts().reset_index(name='Count')
        league_counts.columns = ['League', 'Count']
        league_counts = league_counts.head(10)
        league_counts.insert(0, 'STT', range(1, len(league_counts) + 1))
        st.dataframe(league_counts, 
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small"),
                "League": st.column_config.TextColumn("Giải đấu", width="small"),
                "Count": st.column_config.NumberColumn("Số lượng", width="small"),
            },
            use_container_width=True, 
            hide_index=True)

        st.divider()

        # Top Clubs
        st.subheader("⚽ Top 10 Clubs")
        club_counts = df['Club'].value_counts().reset_index(name='Count')
        club_counts.columns = ['Club', 'Count']
        club_counts = club_counts.head(10)
        club_counts.insert(0, 'STT', range(1, len(club_counts) + 1))
        st.dataframe(club_counts, 
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small"),
                "Club": st.column_config.TextColumn("Câu lạc bộ", width="small"),
                "Count": st.column_config.NumberColumn("Số lượng", width="small"),
            },
            use_container_width=True, 
            hide_index=True)

        st.divider()

        # Top Nations
        st.subheader("🌍 Top 10 Nations")
        nation_counts = df['Nation'].value_counts().reset_index(name='Count')
        nation_counts.columns = ['Nation', 'Count']
        nation_counts = nation_counts.head(10)
        nation_counts.insert(0, 'STT', range(1, len(nation_counts) + 1))
        st.dataframe(nation_counts, 
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small"),
                "Nation": st.column_config.TextColumn("Quốc gia", width="small"),
                "Count": st.column_config.NumberColumn("Số lượng", width="small"),
            },
            use_container_width=True, 
            hide_index=True)

    elif current_tab == 'players':
        st.header("👥 Cầu thủ")
        
        target_clubs = [
            "Real Madrid", "Munich", "Inter", "Manchester City", "Liverpool", "PSG", "Dortmund",
            "Leverkusen", "Atletico Madrid", "Arsenal", "Chelsea", "Man United", "Atalanta",
            "AC Milan", "Tottenham", "Juventus", "Naples",
        ]
        target_nations = [
            "Spain", "France", "Argentina", "England", "Portugal", "Brazil", "Netherlands",
            "Belgium", "Italy", "Germany", "Uruguay", "Japan", "Sweden",
        ]
        target_leagues = ["LaLiga", "EPL", "Serie A", "Bundesliga"]
        
        def quick_suggest_action(row):
            club = str(row.get('Club', ''))
            nation = str(row.get('Nation', ''))
            league = str(row.get('League', ''))
            
            if club in target_clubs or nation in target_nations or league in target_leagues:
                return 'GIỮ'
            return '❌ BÁN'
        
        quick_rec = df.apply(lambda r: quick_suggest_action(r), axis=1)
        quick_sell_count = (quick_rec == '❌ BÁN').sum()
        
        if quick_sell_count == 0:
            st.info("✅ Không có cầu thủ đề xuất bán")
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.warning(f"⚠️ Có **{quick_sell_count}** cầu thủ đề xuất bán")
        
        st.divider()
        
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            search_query = st.text_input("🔍 Tìm kiếm", placeholder="Nhập tên cầu thủ...")
        with f2:
            position_filter = st.selectbox("Vị trí", ["Tất cả"] + get_unique_values(df, 'Position'))
        with f3:
            type_filter = st.selectbox("Loại", ["Tất cả"] + get_unique_values(df, 'Player Type'))
        with f4:
            league_filter = st.selectbox("League", ["Tất cả"] + get_unique_values(df, 'League'))

        g1, g2 = st.columns(2)
        with g1:
            club_filter = st.selectbox("Club", ["Tất cả"] + get_unique_values(df, 'Club'))
        with g2:
            nation_filter = st.selectbox("Nation", ["Tất cả"] + get_unique_values(df, 'Nation'))

        h1, h2, h3 = st.columns(3)
        with h1:
            rmin, rmax = int(df['Rating'].min()), int(df['Rating'].max())
            rating_range = st.slider("Khoảng Rating", rmin, rmax, (rmin, rmax))
        with h2:
            pos_style = st.selectbox("Nhóm vị trí", ["Tất cả"] + get_unique_values(df, 'Position Style'))
        with h3:
            epic_only = st.toggle("Chỉ EPIC", value=False)

        skill_query = st.text_input("Tìm trong Skills (chứa)", placeholder="vd: Long Range Shooting")

        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['Player'].str.contains(search_query, case=False, na=False)]
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
        filtered_df = filtered_df[(filtered_df['Rating'] >= rating_range[0]) & (filtered_df['Rating'] <= rating_range[1])]
        if pos_style != "Tất cả":
            filtered_df = filtered_df[filtered_df['Position Style'] == pos_style]
        if epic_only:
            filtered_df = filtered_df[filtered_df['Player Type'].astype(str).str.upper() == 'EPIC']
        if skill_query:
            filtered_df = filtered_df[filtered_df['Skills'].astype(str).str.contains(re.escape(skill_query), case=False, na=False)]

        st.caption(f"Hiển thị {len(filtered_df)}/{len(df)} cầu thủ")

        sort_col = st.selectbox("Sắp xếp theo", options=[
            'Rating','Player','Position','Player Type','Club','Nation','League'
        ], index=0)
        sort_order = st.radio("Thứ tự", ["Giảm dần","Tăng dần"], horizontal=True, index=0)
        
        if sort_col == 'Position':
            filtered_df['_pos_order'] = filtered_df['Position'].map(POSITION_ORDER)
            filtered_df = filtered_df.sort_values(by='_pos_order', ascending=(sort_order=="Tăng dần"), kind='mergesort')
            filtered_df = filtered_df.drop(columns=['_pos_order'])
        else:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=(sort_order=="Tăng dần"), kind='mergesort')

        view_cols = [
            'Player', 'Rating', 'Position', 'Position Style', 'Player Type',
            'Club', 'Nation', 'League', 'Skills',
        ]
        view_cols = [c for c in view_cols if c in filtered_df.columns]

        display_df = filtered_df[view_cols].copy()
        display_df.insert(0, 'STT', range(1, len(display_df) + 1))
        display_df['_Position_Order'] = display_df['Position'].map(POSITION_ORDER).fillna(999)

        st.dataframe(
            display_df,
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small", help="Số thứ tự"),
                "Player": st.column_config.TextColumn("Player", width="small", help="Tên cầu thủ"),
                "Rating": st.column_config.NumberColumn("Rating", width="small", help="Chỉ số"),
                "Position": st.column_config.TextColumn("Position", width="small", help="Vị trí"),
                "Position Style": st.column_config.TextColumn("Position Style", width="small", help="Phong cách"),
                "Player Type": st.column_config.TextColumn("Player Type", width="small", help="Loại"),
                "Club": st.column_config.TextColumn("Club", width="medium", help="Câu lạc bộ"),
                "Nation": st.column_config.TextColumn("Nation", width="small", help="Quốc gia"),
                "League": st.column_config.TextColumn("League", width="small", help="Giải đấu"),
                "Skills": st.column_config.TextColumn("Skills", width="large", help="Kỹ năng"),
                "_Position_Order": None,
            },
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("🧠 Gợi ý bán", expanded=st.session_state.get('scroll_to_sell', False)):
            st.info("💡 Gợi ý BÁN: Cầu thủ KHÔNG thuộc Club/Nation/League mục tiêu")

            rec_df = df.copy()
            def suggest_action(row):
                club = str(row.get('Club', ''))
                nation = str(row.get('Nation', ''))
                league = str(row.get('League', ''))
                reasons = []
                
                if club in target_clubs:
                    reasons.append('Club mục tiêu')
                if nation in target_nations:
                    reasons.append('Nation mục tiêu')
                if league in target_leagues:
                    reasons.append('League mục tiêu')
                
                action = '✅ GIỮ' if reasons else '❌ BÁN'
                return action, ", ".join(reasons) if reasons else "Không thuộc mục tiêu"
            
            recs = rec_df.apply(lambda r: suggest_action(r), axis=1)
            rec_df['Action'], rec_df['Reasons'] = zip(*recs)
            sell_df = rec_df[rec_df['Action'] == '❌ BÁN']
            st.caption(f"Gợi ý bán: {len(sell_df)} cầu thủ")
            
            sell_display = sell_df[['Player','Rating','Position','Player Type','Club','Nation','League','Reasons']].copy()
            sell_display.insert(0, 'STT', range(1, len(sell_display) + 1))
            st.dataframe(sell_display, 
                column_config={
                    "STT": st.column_config.NumberColumn("STT", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="small"),
                    "Rating": st.column_config.NumberColumn("Rating", width="small"),
                    "Position": st.column_config.TextColumn("Position", width="small"),
                    "Player Type": st.column_config.TextColumn("Type", width="small"),
                    "Club": st.column_config.TextColumn("Club", width="small"),
                    "Nation": st.column_config.TextColumn("Nation", width="small"),
                    "League": st.column_config.TextColumn("League", width="small"),
                    "Reasons": st.column_config.TextColumn("Lý do", width="medium"),
                },
                use_container_width=True, 
                hide_index=True)

            idx_options = sell_df.index.tolist()
            labels = {i: f"{sell_df.loc[i, 'Player']} ({sell_df.loc[i, 'Position']}) – {sell_df.loc[i, 'Rating']}" for i in idx_options}
            to_sell = st.multiselect("Chọn cầu thủ để bán (xóa)", options=idx_options, format_func=lambda x: labels.get(x, str(x)))
            if st.button("Bán (xóa khỏi dữ liệu)", disabled=len(to_sell) == 0):
                try:
                    new_df = df.drop(index=to_sell, errors='ignore')
                    if save_data_to_gsheet(new_df):
                        st.success("Đã bán (xóa) các cầu thủ đã chọn")
                        st.session_state['scroll_to_sell'] = False
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi bán: {e}")

        with st.expander("📈 Thống kê 23+"):
            threshold = st.slider("Ngưỡng tối thiểu", 1, 50, 23, key="stats23_threshold")
            def show_table(title, series):
                st.subheader(title)
                counts = series.value_counts()
                enough = counts[counts >= threshold]
                if enough.empty:
                    st.info("Chưa có nhóm nào đủ ngưỡng")
                else:
                    out = enough.rename_axis(title).reset_index(name='Count')
                    out.insert(0, 'STT', range(1, len(out) + 1))
                    st.dataframe(out, 
                        column_config={
                            "STT": st.column_config.NumberColumn("STT", width="small"),
                            title: st.column_config.TextColumn(title, width="large"),
                            "Count": st.column_config.NumberColumn("Số lượng", width="small"),
                        },
                        use_container_width=True, 
                        hide_index=True)
            show_table("Club", df['Club'].astype(str))
            show_table("Nation", df['Nation'].astype(str))
            show_table("League", df['League'].astype(str))

    elif current_tab == 'skills':
        st.header("🎮 Quản lý Skills")
        
        with st.expander("🔍 Tìm kiếm nâng cao", expanded=False):
            search_col1, search_col2, search_col3 = st.columns(3)
            with search_col1:
                sm_player_search = st.text_input("Tên cầu thủ", placeholder="Nhập tên...", key="sm_player_search")
                sm_position = st.multiselect("Vị trí", sorted(df['Position'].unique().tolist()), key="sm_position")
            with search_col2:
                sm_player_type = st.multiselect("Loại cầu thủ", ["EPIC", "POTW", "NON-EPIC"], key="sm_player_type")
                sm_club = st.multiselect("Club", sorted([x for x in df['Club'].unique() if str(x).strip()]), key="sm_club")
            with search_col3:
                sm_nation = st.multiselect("Quốc gia", sorted([x for x in df['Nation'].unique() if str(x).strip()]), key="sm_nation")
                sm_league = st.multiselect("League", sorted([x for x in df['League'].unique() if str(x).strip()]), key="sm_league")
            
            rating_col1, rating_col2, filter_col = st.columns([2, 2, 2])
            with rating_col1:
                rating_min = st.number_input("Rating từ", min_value=1, max_value=150, value=1, key="sm_rating_min")
            with rating_col2:
                rating_max = st.number_input("Rating đến", min_value=1, max_value=150, value=150, key="sm_rating_max")
            with filter_col:
                sm_filter = st.selectbox("Trạng thái Skills", ["Tất cả", "Có gợi ý", "Không thể thêm skills", "Đã đủ skills"], key="sm_filter")
        
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
        
        if sm_filter == "Không thể thêm skills":
            sm_df = sm_df[sm_df['Player Type'].astype(str).str.upper() == 'POTW']
        elif sm_filter == "Có gợi ý":
            sm_df = sm_df[sm_df['Position'].isin(POSITION_SKILLS_PRIORITY.keys())]
            sm_df = sm_df[sm_df['Player Type'].astype(str).str.upper() != 'POTW']
            def has_recommendations(row):
                base = str(row['Skills']).strip()
                added = str(row['Added Skills']).strip()
                position = row['Position']
                recs = get_recommended_skills(position, base, added, 15)
                return len(recs) > 0
            sm_df = sm_df[sm_df.apply(has_recommendations, axis=1)]
        elif sm_filter == "Đã đủ skills":
            sm_df = sm_df[sm_df['Player Type'].astype(str).str.upper() != 'POTW']
            def has_no_recommendations(row):
                base = str(row['Skills']).strip()
                added = str(row['Added Skills']).strip()
                position = row['Position']
                all_skills = get_all_skills(base, added)
                if not all_skills:
                    return False
                recs = get_recommended_skills(position, base, added, 15)
                return len(recs) == 0
            sm_df = sm_df[sm_df.apply(has_no_recommendations, axis=1)]
        
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
            MAX_SKILLS = 15
            MAX_ADDED_SKILLS = 5
            
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
                        inventory = load_skill_inventory()
                        
                        for i, skill in enumerate(recommended):
                            with cols[i % num_cols]:
                                stock_count = inventory.get(skill, 0)
                                stock_display = f"({stock_count})" if stock_count > 0 else "(❌)"
                                label = f"**#{i+1}** {skill} {stock_display}"
                                
                                if st.checkbox(label, key=f"skill_{idx}_{i}_{reset_key}", label_visibility="visible"):
                                    selected_skills.append(skill)
                        
                        if selected_skills:
                            new_total = total_count + len(selected_skills)
                            
                            if new_total > MAX_SKILLS:
                                st.error(f"⚠️ Không thể thêm {len(selected_skills)} skills! (Vượt giới hạn {MAX_SKILLS})")
                            else:
                                inventory = load_skill_inventory()
                                unavailable_skills = []
                                for skill in selected_skills:
                                    if inventory.get(skill, 0) <= 0:
                                        unavailable_skills.append(skill)
                                
                                if unavailable_skills:
                                    st.error(f"⚠️ Kho không đủ skills: {', '.join(unavailable_skills)}")
                                    st.info("💡 Vui lòng kiểm tra tab 'Kho Skills' để thêm skills cần thiết")
                                else:
                                    if st.button(f"➕ Thêm {len(selected_skills)} skill → Tổng: {new_total}/{MAX_SKILLS}", key=f"add_{idx}_{reset_key}", type="primary", use_container_width=True):
                                        new_added_skills = added_skills_list + selected_skills
                                        new_added_skills_str = ', '.join(new_added_skills)
                                        df.at[idx, 'Added Skills'] = new_added_skills_str
                                        
                                        try:
                                            with st.spinner("💾 Đang lưu..."):
                                                for skill in selected_skills:
                                                    update_inventory_count(skill, -1)
                                                
                                                if save_data_to_gsheet(df):
                                                    st.cache_data.clear()
                                            
                                            st.toast(f"✅ Đã thêm {len(selected_skills)} skills cho {player_name}!", icon="✅")
                                            st.session_state.checkbox_reset_counter += 1
                                            st.session_state.current_tab = 'skills'
                                            
                                            import time
                                            time.sleep(0.5)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Lỗi: {e}")
                    else:
                        if total_count < MAX_SKILLS:
                            st.info(f"ℹ️ Không có gợi ý thêm cho vị trí {position} (Hiện có {total_count}/{MAX_SKILLS} skills)")
                        else:
                            st.success(f"✅ Đã đạt giới hạn tối đa {MAX_SKILLS} skills!")

    elif current_tab == 'squad':
        st.header("⚽ Đội hình")
        g1, g2 = st.columns(2)
        with g1:
            group_by = st.selectbox("Theo", ["Club", "Nation", "League"], index=0)
        with g2:
            group_counts = df[group_by].value_counts().to_dict()
            group_options = sorted([x for x in df[group_by].astype(str).unique() if str(x).strip()])
            
            formatted_options = ["(Tất cả)"] + [f"{opt} ({group_counts.get(opt, 0)})" for opt in group_options]
            
            selected_display = st.selectbox(f"Chọn {group_by}", formatted_options)
            
            if selected_display == "(Tất cả)":
                group_value = "(Tất cả)"
            else:
                group_value = selected_display.rsplit(" (", 1)[0]

        df_src = df.copy()
        if group_value != "(Tất cả)":
            df_src = df_src[df_src[group_by].astype(str) == group_value]
        
        if df_src.empty:
            st.warning("Không có cầu thủ cho lựa chọn này.")
        else:
            total_available = len(df_src)
            squad_size = min(23, total_available)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tổng cầu thủ", total_available)
            with col2:
                st.metric("Chọn vào đội hình", squad_size)
            with col3:
                if total_available >= 23:
                    st.metric("Trạng thái", "✅ Đủ đội hình")
                else:
                    st.metric("Trạng thái", f"⚠️ Thiếu {23 - total_available}")
            
            st.caption(f"Lấy {squad_size} cầu thủ rating cao nhất")
            squad = df_src.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(23)
            st.subheader("Đội hình 23 – Top rating")
            show_cols = ['Player','Rating','Position','Player Type','Club','Nation','League','Skills']
            show_cols = [c for c in show_cols if c in squad.columns]
            
            squad_display = squad[show_cols].copy()
            squad_display.insert(0, 'STT', range(1, len(squad_display) + 1))
            st.dataframe(squad_display, 
                column_config={
                    "STT": st.column_config.NumberColumn("STT", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="small"),
                    "Rating": st.column_config.NumberColumn("Rating", width="small"),
                    "Position": st.column_config.TextColumn("Position", width="small"),
                    "Player Type": st.column_config.TextColumn("Type", width="small"),
                    "Club": st.column_config.TextColumn("Club", width="small"),
                    "Nation": st.column_config.TextColumn("Nation", width="small"),
                    "League": st.column_config.TextColumn("League", width="small"),
                    "Skills": st.column_config.TextColumn("Skills", width="large"),
                },
                use_container_width=True, 
                hide_index=True)

    elif current_tab == 'add':
        st.header("➕ Thêm cầu thủ")
        
        existing_nations = [""] + sorted([x for x in df['Nation'].astype(str).unique() if str(x).strip()])
        existing_clubs = [""] + sorted([x for x in df['Club'].astype(str).unique() if str(x).strip()])
        existing_leagues = [""] + sorted([x for x in df['League'].astype(str).unique() if str(x).strip()])
        existing_positions = sorted(df['Position'].unique().tolist())
        
        with st.form("add_player_form"):
            c1, c2 = st.columns(2)
            with c1:
                player_name = st.text_input("Tên cầu thủ", placeholder="Nhập tên cầu thủ...")
                rating = st.number_input("Rating", min_value=1, max_value=150, value=80)
                position = st.selectbox("Vị trí", existing_positions)
                position_style = st.selectbox("Nhóm vị trí", POSITION_STYLES)
            with c2:
                player_type = st.selectbox("Loại", ["EPIC", "POTW", "NON-EPIC"])
                
                nation = st.selectbox("Quốc gia", existing_nations, help="Chọn từ danh sách có sẵn")
                if nation == "":
                    nation_custom = st.text_input("Hoặc nhập quốc gia mới", key="nation_custom")
                    if nation_custom:
                        nation = nation_custom
                
                club = st.selectbox("CLB", existing_clubs, help="Chọn từ danh sách có sẵn")
                if club == "":
                    club_custom = st.text_input("Hoặc nhập CLB mới", key="club_custom")
                    if club_custom:
                        club = club_custom
                
                league = st.selectbox("Giải đấu", existing_leagues, help="Chọn từ danh sách có sẵn")
                if league == "":
                    league_custom = st.text_input("Hoặc nhập giải đấu mới", key="league_custom")
                    if league_custom:
                        league = league_custom
            
            player_url = st.text_input("URL eFootballHub (tùy chọn)", placeholder="https://efootballhub.net/efootball23/player/...")
            
            st.caption("💡 Skills sẽ được tự động trích xuất nếu có URL")
            
            submitted = st.form_submit_button("➕ Thêm cầu thủ", use_container_width=True)

            if submitted:
                if player_name and rating and position:
                    new_player = {
                        "Player": player_name,
                        "Rating": int(rating),
                        "Position": position,
                        "Position Style": position_style,
                        "Player Type": player_type,
                        "Nation": nation,
                        "Club": club,
                        "League": league,
                        "Player URL": player_url,
                        "Player ID": extract_ehub_player_id(player_url) if player_url else "",
                        "Skills": "",
                        "Added Skills": "",
                        "Epic_Priority": 0 if player_type == "EPIC" else 1,
                    }
                    
                    if player_url:
                        with st.spinner("Đang trích xuất skills..."):
                            new_player["Skills"] = extract_player_skills(player_url)

                    new_df = pd.concat([df, pd.DataFrame([new_player])], ignore_index=True)
                    try:
                        if save_data_to_gsheet(new_df):
                            st.success(f"✅ Đã thêm cầu thủ {player_name} thành công!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi lưu: {e}")
                else:
                    st.error("Vui lòng điền đầy đủ thông tin bắt buộc!")

    elif current_tab == 'inventory':
        st.header("📦 Kho Skills")
        
        inventory = load_skill_inventory()
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
                        save_skill_inventory(imported_data)
                        st.success("✅ Đã nhập kho thành công!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi khi đọc file: {e}")
            
            st.divider()
            
            st.subheader("⚠️ Xóa kho")
            if st.button("🗑️ Xóa toàn bộ kho", type="secondary", use_container_width=True):
                if st.checkbox("Xác nhận xóa toàn bộ kho skills"):
                    save_skill_inventory({})
                    st.success("✅ Đã xóa toàn bộ kho")
                    st.rerun()


if __name__ == "__main__":
    main()