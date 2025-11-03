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

def get_all_known_skills():
    """Get all unique skills from POSITION_SKILLS_PRIORITY"""
    all_skills = set()
    for skills_list in POSITION_SKILLS_PRIORITY.values():
        all_skills.update(skills_list)
    return sorted(list(all_skills))

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

def make_ehub_player_image_url(player_id: str) -> str:
    """Tạo URL hình ảnh cầu thủ từ player_id"""
    pid = extract_ehub_player_id(player_id)
    return f"https://efootballhub.net/images/efootball24/players/{pid}_l.webp" if pid else ""

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
    
        # Nút tải lại dữ liệu
        if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.manual_reload_triggered = True
            st.rerun()
    
        st.divider()
    
        # Menu chính
        main_menu = st.radio(
            "📑 Điều hướng",
            ["📊 Tổng quan", "👥 Quản lý cầu thủ", "🎮 Quản lý Skills"],
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

        # Căn giữa và hiển thị không scroll
        pos_counts_styled = pos_counts.style.set_properties(**{
            'text-align': 'center'
        }).set_table_styles([{
            'selector': 'th',
            'props': [('text-align', 'center')]
        }])

        st.table(pos_counts_styled)

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

        # ===== CẤU HÌNH TEAMS CẦN BUILD =====
        target_clubs = [
            "Barcelona", "Real Madrid", "Munich", "Inter", "Manchester City", "Liverpool", 
            "PSG", "Dortmund", "Leverkusen", "Atletico Madrid", "Arsenal", 
            "Chelsea", "Man United", "Atalanta", "AC Milan", "Tottenham", 
            "Juventus", "Napoli"
        ]
        
        # Club được miễn trừ (không bao giờ bán)
        PROTECTED_CLUBS = ["Barcelona"]
        
        target_nations = [
            "Spain", "France", "Argentina", "England", "Portugal", 
            "Brazil", "Netherlands", "Belgium", "Italy", "Germany", 
            "Uruguay", "Japan"
        ]
        
        target_leagues = ["LaLiga", "EPL", "Serie A", "Bundesliga", "Ligue 1"]

        SQUAD_SIZE = 23  # Số cầu thủ mỗi team

        # ===== TÍNH TOP 23 CHO MỖI TEAM =====
        def get_top_23_players(df, group_by, values):
            top_players = set()
            for value in values:
                team_df = df[df[group_by].astype(str) == value].copy()
                if not team_df.empty:
                    # Với Nation/League: loại trùng tên
                    if group_by in ['Nation', 'League']:
                        team_df = team_df.sort_values(['Player', 'Rating', 'Epic_Priority'],
                                                      ascending=[True, False, True])
                        team_df = team_df.drop_duplicates(subset=['Player'], keep='first')

                    # Bước 1: chọn GK tốt nhất (nếu có) để đảm bảo có ít nhất 1 GK
                    gk_df = team_df[team_df['Position'] == 'GK']
                    cb_df = team_df[team_df['Position'] == 'CB']
                    squad = pd.DataFrame()
                    remaining_slots = SQUAD_SIZE

                    # Chọn 1 GK tốt nhất
                    if not gk_df.empty:
                        best_gk = gk_df.sort_values(['Rating', 'Epic_Priority'],
                                                    ascending=[False, True]).head(1)
                        squad = pd.concat([squad, best_gk])
                        remaining_slots -= 1

                    # Chọn 2 CB tốt nhất
                    if not cb_df.empty:
                        best_cb = cb_df.sort_values(['Rating', 'Epic_Priority'],
                                                    ascending=[False, True]).head(2)
                        squad = pd.concat([squad, best_cb])
                        remaining_slots -= len(best_cb)

                    # Bước 2: chọn các cầu thủ còn lại (bao gồm cả GK/CB khác nếu đủ mạnh)
                    others = team_df.drop(squad.index)  # bỏ GK và CB đã chọn bắt buộc
                    if not others.empty:
                        top_rest = others.sort_values(['Rating', 'Epic_Priority'],
                                              ascending=[False, True]).head(remaining_slots)
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
            nation = str(row.get('Nation', '')).strip()
            league = str(row.get('League', '')).strip()
            reasons = []
            
            # 0. Kiểm tra club được bảo vệ (BARCELONA)
            if club in PROTECTED_CLUBS:
                return '✅ GIỮ', f"🛡️ {club} - Không bao giờ bán (Fan club)"
            
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

        # ===== THỐNG KÊ TỔNG QUAN =====
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Tổng cầu thủ", len(df))
        with col2:
            protected_count = len(df[df['Club'].isin(PROTECTED_CLUBS)])
            st.metric("🛡️ Barcelona", protected_count)
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
            search_query = st.text_input("🔍 Tìm cầu thủ", placeholder="Nhập tên cầu thủ...")
        with col2:
            action_filter = st.selectbox("Hành động", ["Tất cả", "✅ GIỮ", "❌ BÁN"])
        
        # Row 2: Position, Type, League, Position Style
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            position_filter = st.selectbox("Vị trí", ["Tất cả"] + get_unique_values(df, 'Position'))
        with col2:
            type_filter = st.selectbox("Loại", ["Tất cả"] + get_unique_values(df, 'Player Type'))
        with col3:
            league_filter = st.selectbox("League", ["Tất cả"] + get_unique_values(df, 'League'))
        with col4:
            pos_style = st.selectbox("Phong cách", ["Tất cả"] + get_unique_values(df, 'Position Style'))
        
        # Row 3: Club, Nation, Rating, Epic only
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            club_filter = st.selectbox("Club", ["Tất cả"] + get_unique_values(df, 'Club'))
        with col2:
            nation_filter = st.selectbox("Nation", ["Tất cả"] + get_unique_values(df, 'Nation'))
        with col3:
            rmin, rmax = int(df['Rating'].min()), int(df['Rating'].max())
            rating_range = st.slider("Rating", rmin, rmax, (rmin, rmax))
        with col4:
            epic_only = st.checkbox("Chỉ EPIC", value=False)
        
        # Row 4: Skills search
        skill_query = st.text_input("Tìm trong Skills", placeholder="vd: Long Range Shooting")
        
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
        if pos_style != "Tất cả":
            filtered_df = filtered_df[filtered_df['Position Style'] == pos_style]
        if epic_only:
            filtered_df = filtered_df[filtered_df['Player Type'].astype(str).str.upper() == 'EPIC']
        if skill_query:
            filtered_df = filtered_df[filtered_df['Skills'].astype(str).str.contains(re.escape(skill_query), case=False, na=False)]
        
        filtered_df = filtered_df[(filtered_df['Rating'] >= rating_range[0]) & (filtered_df['Rating'] <= rating_range[1])]
        
        # ===== SORTING =====
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_col = st.selectbox("Sắp xếp theo", options=[
                'Rating', 'Player', 'Position', 'Player Type', 'Club', 'Nation', 'League'
            ], index=0)
        with col2:
            sort_order = st.radio("Thứ tự", ["Giảm dần", "Tăng dần"], horizontal=True, index=0)
        
        if sort_col == 'Position':
            filtered_df['_pos_order'] = filtered_df['Position'].map(POSITION_ORDER)
            filtered_df = filtered_df.sort_values(by='_pos_order', ascending=(sort_order == "Tăng dần"))
            filtered_df = filtered_df.drop(columns=['_pos_order'])
        else:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=(sort_order == "Tăng dần"))
        
        # ===== DISPLAY TABLE =====
        st.info(f"📊 Hiển thị **{len(filtered_df)}** / {len(rec_df)} cầu thủ")

        # ===== ĐỊNH NGHĨA COLUMNS TRƯỚC (ĐỂ DÙNG CHO EXPORT) =====
        display_columns = [
            'Player', 'Rating', 'Position', 'Position Style', 'Player Type',
            'Club', 'Nation', 'League', 'Action', 'Reasons', 'Skills'
        ]
        available_columns = [c for c in display_columns if c in filtered_df.columns]
        
        # ===== NÚT CHUYỂN ĐỔI CHỂ ĐỘ HIỂN THỊ =====
        view_mode = st.radio("Chế độ hiển thị:", ["📋 Bảng", "🎴 Card"], horizontal=True, index=1)
        
        if view_mode == "🎴 Card":
            # ===== CHẾ ĐỘ CARD =====
            for idx, row in filtered_df.iterrows():
                player_name = row['Player']
                rating = row['Rating']
                position = row['Position']
                player_type = row['Player Type']
                club = row.get('Club', '')
                nation = row.get('Nation', '')
                league = row.get('League', '')
                action = row.get('Action', '')
                reasons = row.get('Reasons', '')
                skills = row.get('Skills', '')
                added_skills = row.get('Added Skills', '')
                player_id = row.get('Player ID', '')
                player_url = row.get('Player URL', '')
                
                # Tạo URL hình ảnh
                image_url = make_ehub_player_image_url(player_id if player_id else player_url)
                
                # Màu sắc theo loại thẻ
                if str(player_type).upper() == "EPIC":
                    card_color = "🟡"
                elif str(player_type).upper() == "POTW":
                    card_color = "🟣"
                else:
                    card_color = "🔵"
                
                # Màu action
                if action == "❌ BÁN":
                    action_badge = f'<span style="background:#ffebee;color:#c62828;padding:4px 12px;border-radius:12px;font-weight:bold;">{action}</span>'
                else:
                    action_badge = f'<span style="background:#e8f5e9;color:#2e7d32;padding:4px 12px;border-radius:12px;font-weight:bold;">{action}</span>'
                
                with st.container(border=True):
                    col_img, col_info, col_action = st.columns([1, 3, 2])
                    
                    with col_img:
                        if image_url:
                            st.image(image_url, width=100)
                        else:
                            st.markdown(
                                '<div style="width:100px;height:130px;background:#f0f0f0;'
                                'display:flex;align-items:center;justify-content:center;'
                                'border-radius:8px;font-size:40px;">❓</div>',
                                unsafe_allow_html=True
                            )
                    
                    with col_info:
                        st.markdown(f"### {card_color} {player_name}")
                        
                        info_col1, info_col2 = st.columns(2)
                        with info_col1:
                            st.markdown(f"**Rating:** {rating} | **Vị trí:** {position}")
                            st.markdown(f"**Loại:** {player_type}")
                        with info_col2:
                            st.markdown(f"**CLB:** {club}")
                            st.markdown(f"**Quốc gia:** {nation} | **League:** {league}")
                        
                        # Hiển thị Skills
                        added_skills = row.get('Added Skills', '')
                        base_skills_list = [s.strip() for s in skills.split(',') if s.strip()] if skills else []
                        added_skills_list = [s.strip() for s in added_skills.split(',') if s.strip()] if added_skills else []
                        total_skills = len(base_skills_list) + len(added_skills_list)
                        
                        if base_skills_list or added_skills_list:
                            with st.expander(f"📋 Skills ({total_skills})"):
                                if base_skills_list:
                                    st.caption(f"🎮 Gốc ({len(base_skills_list)}):")
                                    base_html = " ".join([
                                        f'<span style="background:#e3f2fd;color:#1565c0;padding:3px 8px;'
                                        f'border-radius:10px;margin:2px;display:inline-block;font-size:12px;">⭐ {s}</span>'
                                        for s in base_skills_list
                                    ])
                                    st.markdown(base_html, unsafe_allow_html=True)
        
                                if added_skills_list:
                                    st.caption(f"➕ Đã thêm ({len(added_skills_list)}):")
                                    added_html = " ".join([
                                        f'<span style="background:#d4edda;color:#155724;padding:3px 8px;'
                                        f'border-radius:10px;margin:2px;display:inline-block;font-size:12px;">✅ {s}</span>'
                                        for s in added_skills_list
                                    ])
                                    st.markdown(added_html, unsafe_allow_html=True)
                    
                    with col_action:
                        st.markdown(action_badge, unsafe_allow_html=True)
                        st.caption(f"**Lý do:** {reasons}")
        
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
                del_display = del_df[['Player', 'Rating', 'Position', 'Player Type', 'Club', 'Nation', 'League', 'Action', 'Reasons']].copy()
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
                            st.metric("🛡️ Barcelona", protected_count, delta="Được bảo vệ!", delta_color="inverse")
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

        # Tự động sort theo Rating giảm dần
        sm_df = sm_df.sort_values('Rating', ascending=False)
        
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
        st.header("⚽ Đội hình")
        
        # Chọn nhóm theo Club / Nation / League
        g1, g2 = st.columns(2)
        with g1:
            group_by = st.selectbox("Theo", ["Club", "Nation", "League"], index=0)
        with g2:
            # 🔧 FIX: Sort theo số lượng giảm dần (nhiều nhất → ít nhất)
            group_counts = df[group_by].value_counts().to_dict()
            
            # Lấy danh sách unique values
            group_options = [x for x in df[group_by].astype(str).unique() if str(x).strip()]
            
            # Sort theo COUNT giảm dần (nhiều → ít)
            group_options_sorted = sorted(
                group_options, 
                key=lambda x: group_counts.get(x, 0),  # Sort theo count
                reverse=True  # Giảm dần (nhiều nhất trên cùng)
            )
            
            # Format hiển thị: "Barcelona (45)"
            formatted_options = ["(Tất cả)"] + [
                f"{opt} ({group_counts.get(opt, 0)})" 
                for opt in group_options_sorted
            ]
            
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
            return
    
    # ... (phần còn lại giữ nguyên)

        # Nếu nhóm là Nation hoặc League thì loại trùng tên giữ rating cao nhất
        if group_by in ['Nation', 'League']:
            df_src = df_src.sort_values(['Player', 'Rating', 'Epic_Priority'], ascending=[True, False, True])
            df_src = df_src.drop_duplicates(subset=['Player'], keep='first')

        # Loại trùng cùng Player+Rating: ưu tiên Protected Club nếu có, ngẫu nhiên nếu không
        import random
        # đảm bảo PROTECTED_CLUBS tồn tại khi vào tab squad
        if 'PROTECTED_CLUBS' not in globals():
            PROTECTED_CLUBS = ["Barcelona"]
        duplicates = df_src[df_src.duplicated(subset=['Player','Rating'], keep=False)]
        for player in duplicates['Player'].unique():
            same_cards = duplicates[duplicates['Player'] == player]
            if len(same_cards) > 1:
                protected_cards = same_cards[same_cards['Club'].isin(PROTECTED_CLUBS)]
                if not protected_cards.empty:
                    chosen_idx = protected_cards.index[0]
                else:
                    chosen_idx = random.choice(same_cards.index.tolist())
                df_src = df_src.drop(same_cards.index.difference([chosen_idx]))

        # Tổng quan GK và CB trong nguồn dữ liệu
        total_available = len(df_src)
        gk_all_count = len(df_src[df_src['Position'] == 'GK'])
        cb_all_count = len(df_src[df_src['Position'] == 'CB'])

        # Xây đội hình top 23: bắt buộc 1 GK và 2 CB nếu có
        MAX_SQUAD = 23
        squad = pd.DataFrame()
        remaining_slots = MAX_SQUAD

        # Chọn 1 GK tốt nhất nếu có
        gk_df = df_src[df_src['Position'] == 'GK']
        if not gk_df.empty:
            best_gk = gk_df.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(1)
            squad = pd.concat([squad, best_gk])
            remaining_slots -= 1
        # Chọn 2 CB tốt nhất nếu có
        cb_df = df_src[df_src['Position'] == 'CB']
        best_cb = pd.DataFrame()
        if not cb_df.empty:
            best_cb = cb_df.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(2)
            squad = pd.concat([squad, best_cb])
            remaining_slots -= len(best_cb)
        # Chọn phần còn lại theo rating
        others = df_src.drop(squad.index, errors='ignore')
        if not others.empty and remaining_slots > 0:
            top_rest = others.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True]).head(remaining_slots)
            squad = pd.concat([squad, top_rest])
    
        squad = squad.sort_values(['Rating', 'Epic_Priority'], ascending=[False, True])
        squad_size = len(squad)
    
        # Số GK và CB trong đội hình đã chọn
        gk_in_squad = len(squad[squad['Position'] == 'GK'])
        cb_in_squad = len(squad[squad['Position'] == 'CB'])
    
        # Hiển thị metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tổng cầu thủ nguồn", total_available)
        with col2:
            st.metric("GK/CB", f"{gk_all_count} GK | {cb_all_count} CB")
        with col3:
            st.metric("Chọn vào đội hình", squad_size)
        with col4:
            st.metric("Đội hình mục tiêu", f"{MAX_SQUAD} người")
    
        st.divider()
    
        # Kiểm tra trạng thái chi tiết
        has_gk = gk_in_squad >= 1
        cb_ok = cb_in_squad >= 2
        cb_count_text = f"{cb_in_squad}/2"
    
        # Trạng thái tổng quan
        if has_gk and cb_ok and squad_size >= MAX_SQUAD:
            st.success("✅ Đủ đội hình: Có ít nhất 1 GK, 2 CB và đủ 23 người")
        else:
            # Cảnh báo chi tiết cho GK
            if not has_gk:
                st.warning("⚠️ Thiếu GK: Đội hình không có thủ môn")
            # Cảnh báo chi tiết cho CB
            if cb_in_squad == 0:
                st.warning("⚠️ Thiếu CB: 0/2 CB")
            elif cb_in_squad == 1:
                st.warning("⚠️ Thiếu CB: 1/2 CB")
            # Cảnh báo thiếu người
            if squad_size < MAX_SQUAD:
                st.warning(f"⚠️ Thiếu người: Hiện có {squad_size} / {MAX_SQUAD}")
    
        # Caption mô tả logic
        if has_gk and cb_ok:
            caption_text = "Lưu ý: Lấy 1 GK rating cao nhất và 2 CB rating cao nhất rồi chọn các cầu thủ có rating cao nhất cho các vị trí còn lại"
        elif has_gk and not cb_ok:
            caption_text = "Lưu ý: Có thủ môn nhưng không đủ CB, sẽ ưu tiên lấy CB rating cao nếu có"
        elif not has_gk and cb_ok:
            caption_text = "Lưu ý: Có đủ CB nhưng thiếu thủ môn, đội hình sẽ thiếu tính hợp lệ"
        else:
            caption_text = "Lưu ý: Thiếu cả GK và CB, đội hình sẽ không hợp lệ để thi đấu"
    
        st.caption(caption_text)
    
        st.divider()
    
        # Chế độ hiển thị
        squad_view = st.radio("Chế độ hiển thị:", ["📋 Bảng", "🎴 Card"], horizontal=True, index=1, key="squad_view")
        
        if squad_view == "🎴 Card":
            # Hiển thị dạng card với hình ảnh
            st.caption(f"Hiển thị {len(squad)} cầu thủ trong đội hình")
            
            # Nhóm theo vị trí
            positions_order = ['GK', 'CB', 'LB', 'RB', 'DMF', 'CMF', 'AMF', 'LMF', 'RMF', 'LWF', 'RWF', 'SS', 'CF']
            
            for pos in positions_order:
                pos_players = squad[squad['Position'] == pos]
                if not pos_players.empty:
                    st.subheader(f"📍 {pos} ({len(pos_players)})")
                    
                    for idx, row in pos_players.iterrows():
                        player_name = row['Player']
                        rating = row['Rating']
                        player_type = row['Player Type']
                        club = row.get('Club', '')
                        nation = row.get('Nation', '')
                        league = row.get('League', '')
                        skills = row.get('Skills', '')
                        added_skills = row.get('Added Skills', '')
                        player_id = row.get('Player ID', '')
                        player_url = row.get('Player URL', '')
                        
                        # Tạo URL hình ảnh
                        image_url = make_ehub_player_image_url(player_id if player_id else player_url)
                        
                        # Màu sắc theo loại thẻ
                        if str(player_type).upper() == "EPIC":
                            card_color = "🟡"
                        elif str(player_type).upper() == "POTW":
                            card_color = "🟣"
                        else:
                            card_color = "🔵"
                        
                        with st.container(border=True):
                            col_img, col_info = st.columns([1, 4])
                            
                            with col_img:
                                if image_url:
                                    st.image(image_url, width=100)
                                else:
                                    st.markdown(
                                        '<div style="width:100px;height:130px;background:#f0f0f0;'
                                        'display:flex;align-items:center;justify-content:center;'
                                        'border-radius:8px;font-size:40px;">❓</div>',
                                        unsafe_allow_html=True
                                    )
                            
                            with col_info:
                                st.markdown(f"### {card_color} {player_name}")
                                
                                info_col1, info_col2, info_col3 = st.columns(3)
                                with info_col1:
                                    st.markdown(f"**Rating:** {rating}")
                                    st.markdown(f"**Loại:** {player_type}")
                                with info_col2:
                                    st.markdown(f"**CLB:** {club}")
                                    st.markdown(f"**Quốc gia:** {nation}")
                                with info_col3:
                                    st.markdown(f"**League:** {league}")
                                
                                # Hiển thị Skills giống tab players
                                base_skills_list = [s.strip() for s in skills.split(',') if s.strip()] if skills else []
                                added_skills_list = [s.strip() for s in added_skills.split(',') if s.strip()] if added_skills else []
                                total_skills = len(base_skills_list) + len(added_skills_list)
                                
                                if base_skills_list or added_skills_list:
                                    with st.expander(f"📋 Skills ({total_skills})", expanded=False):
                                        if base_skills_list:
                                            st.caption(f"🎮 Gốc ({len(base_skills_list)}):")
                                            base_html = " ".join([
                                                f'<span style="background:#e3f2fd;color:#1565c0;padding:3px 8px;'
                                                f'border-radius:10px;margin:2px;display:inline-block;font-size:12px;">⭐ {s}</span>'
                                                for s in base_skills_list
                                            ])
                                            st.markdown(base_html, unsafe_allow_html=True)
                                        
                                        if added_skills_list:
                                            st.caption(f"➕ Đã thêm ({len(added_skills_list)}):")
                                            added_html = " ".join([
                                                f'<span style="background:#d4edda;color:#155724;padding:3px 8px;'
                                                f'border-radius:10px;margin:2px;display:inline-block;font-size:12px;">✅ {s}</span>'
                                                for s in added_skills_list
                                            ])
                                            st.markdown(added_html, unsafe_allow_html=True)
        else:
            # Hiển thị dạng bảng (CODE CŨ - GIỮ NGUYÊN)
            show_cols = ['Player','Rating','Position','Player Type','Club','Nation','League','Skills']
            show_cols = [c for c in show_cols if c in squad.columns]
            squad_display = squad[show_cols].copy()
            squad_display.insert(0, 'STT', range(1, len(squad_display) + 1))
            st.dataframe(
                squad_display,
                column_config={
                    "STT": st.column_config.NumberColumn("STT", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Rating": st.column_config.NumberColumn("Rating", width="small"),
                    "Position": st.column_config.TextColumn("Position", width="small"),
                    "Player Type": st.column_config.TextColumn("Type", width="small"),
                    "Club": st.column_config.TextColumn("Club", width="medium"),
                    "Nation": st.column_config.TextColumn("Nation", width="small"),
                    "League": st.column_config.TextColumn("League", width="small"),
                    "Skills": st.column_config.TextColumn("Skills", width="large"),
                },
                use_container_width=True,
                hide_index=True
            )
    
        # Phân tích đội hình
        with st.expander("📊 Phân tích đội hình"):
            analysis_col1, analysis_col2 = st.columns(2)
            with analysis_col1:
                st.subheader("Phân bố vị trí")
                pos_counts = squad['Position'].value_counts().reset_index()
                pos_counts.columns = ['Position', 'Count']
                pos_counts.insert(0, 'STT', range(1, len(pos_counts) + 1))
                st.dataframe(pos_counts, use_container_width=True, hide_index=True)
            with analysis_col2:
                st.subheader("Phân bố loại thẻ")
                type_counts = squad['Player Type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                type_counts.insert(0, 'STT', range(1, len(type_counts) + 1))
                st.dataframe(type_counts, use_container_width=True, hide_index=True)
    
        st.divider()
    
        # Thống kê cuối
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            avg_rating = squad['Rating'].mean() if not squad.empty else 0
            st.metric("Rating trung bình", f"{avg_rating:.1f}")
        with stat_col2:
            max_rating = squad['Rating'].max() if not squad.empty else 0
            st.metric("Rating cao nhất", int(max_rating))
        with stat_col3:
            min_rating = squad['Rating'].min() if not squad.empty else 0
            st.metric("Rating thấp nhất", int(min_rating))
        with stat_col4:
            epic_count = (squad['Player Type'].astype(str).str.upper() == 'EPIC').sum() if not squad.empty else 0
            st.metric("Số EPIC", int(epic_count))

    elif current_tab == 'add':
        st.header("➕ Thêm cầu thủ")
        
        # Chọn chế độ
        mode = st.radio(
            "Chọn chế độ",
            ["➕ Thêm mới", "🔄 Upgrade cầu thủ có sẵn"],
            horizontal=True
        )
        
        existing_nations = [""] + sorted([x for x in df['Nation'].astype(str).unique() if str(x).strip()])
        existing_clubs = [""] + sorted([x for x in df['Club'].astype(str).unique() if str(x).strip()])
        existing_leagues = [""] + sorted([x for x in df['League'].astype(str).unique() if str(x).strip()])
        existing_positions = sorted(
            df['Position'].unique().tolist(),
            key=lambda x: POSITION_ORDER.get(x, 999)
        )
        existing_players = sorted(df['Player'].astype(str).unique().tolist())
        
        if mode == "➕ Thêm mới":
            st.info("💡 Chế độ này thêm cầu thủ hoàn toàn mới, không kiểm tra trùng lặp")
            
            with st.form("add_player_form"):
                c1, c2 = st.columns(2)
                with c1:
                    player_name = st.selectbox(
                        "Tên cầu thủ (gõ để tìm)", 
                        options=[""] + existing_players
                    )
                    if not player_name:
                        player_name = st.text_input("Hoặc nhập tên mới", placeholder="Ví dụ: Lionel Messi")
                    rating = st.number_input("Rating", min_value=1, max_value=150, value=90)
                    position = st.selectbox("Vị trí", existing_positions)
                    position_style = st.selectbox("Nhóm vị trí", POSITION_STYLES)
                with c2:
                    player_type = st.selectbox("Loại", ["NON-EPIC", "POTW", "EPIC"])
                    
                    nation = st.selectbox("Quốc gia", existing_nations, help="Chọn từ danh sách có sẵn")
                    if nation == "":
                        nation_custom = st.text_input("Hoặc nhập quốc gia mới", key="nation_custom", placeholder="Ví dụ: Vietnam")
                        if nation_custom:
                            nation = nation_custom
                    
                    club = st.selectbox("CLB", existing_clubs, help="Chọn từ danh sách có sẵn")
                    if club == "":
                        club_custom = st.text_input("Hoặc nhập CLB mới", key="club_custom", placeholder="Ví dụ: HAGL")
                        if club_custom:
                            club = club_custom
                    
                    league = st.selectbox("Giải đấu", existing_leagues, help="Chọn từ danh sách có sẵn")
                    if league == "":
                        league_custom = st.text_input("Hoặc nhập giải đấu mới", key="league_custom", placeholder="Ví dụ: VLeague")
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
        
        else:  # Chế độ Upgrade
            st.info("💡 Chế độ này tự động phát hiện và thay thế thẻ cũ (cùng tên + club + nation + league)")
            
            # Bước 1: Chọn cầu thủ
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
                version_display = player_versions[['Rating', 'Position', 'Player Type', 'Club', 'Nation', 'League', 'Skills']].copy()
                version_display.insert(0, 'STT', range(1, len(version_display) + 1))
                st.dataframe(version_display, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Form nhập thông tin mới
                with st.form("upgrade_player_form"):
                    st.subheader("2️⃣ Nhập thông tin phiên bản mới")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        new_rating = st.number_input("Rating mới", min_value=1, max_value=150, value=90)
                        new_position = st.selectbox("Vị trí", existing_positions)
                        new_position_style = st.selectbox("Nhóm vị trí", POSITION_STYLES)
                    with c2:
                        new_player_type = st.selectbox("Loại", ["NON-EPIC", "POTW", "EPIC"])
                        
                        new_nation = st.selectbox("Quốc gia", existing_nations, key="upgrade_nation")
                        if new_nation == "":
                            new_nation = st.text_input("Nhập quốc gia mới", key="upgrade_nation_custom")
                        
                        new_club = st.selectbox("CLB", existing_clubs, key="upgrade_club")
                        if new_club == "":
                            new_club = st.text_input("Nhập CLB mới", key="upgrade_club_custom")
                        
                        new_league = st.selectbox("Giải đấu", existing_leagues, key="upgrade_league")
                        if new_league == "":
                            new_league = st.text_input("Nhập giải đấu mới", key="upgrade_league_custom")
                    
                    new_player_url = st.text_input("URL eFootballHub (bắt buộc)", placeholder="https://efootballhub.net/efootball23/player/...", key="upgrade_url")
                    
                    st.caption("💡 Skills sẽ được tự động trích xuất từ URL")
                    
                    # Preview upgrade
                    if new_club and new_nation and new_league:
                        matching_card = player_versions[
                            (player_versions['Club'].astype(str) == new_club) &
                            (player_versions['Nation'].astype(str) == new_nation) &
                            (player_versions['League'].astype(str) == new_league)
                        ]
                        
                        if not matching_card.empty:
                            old_rating = matching_card.iloc[0]['Rating']
                            old_type = matching_card.iloc[0]['Player Type']
                            rating_diff = new_rating - old_rating
                            
                            st.success(f"✅ Tìm thấy thẻ cũ: {selected_player} {old_rating} ({old_type}) | {new_club} | {new_nation} | {new_league}")
                            
                            if rating_diff > 0:
                                st.info(f"📈 Upgrade: Rating **{old_rating} → {new_rating}** (+{rating_diff})")
                            elif rating_diff < 0:
                                st.warning(f"📉 Downgrade: Rating **{old_rating} → {new_rating}** ({rating_diff})")
                            else:
                                st.info(f"🔄 Cập nhật: Rating giữ nguyên **{new_rating}**")
                            
                            st.caption("⚠️ Added Skills sẽ bị reset vì skills gốc thay đổi")
                        else:
                            st.warning(f"⚠️ Không tìm thấy thẻ cũ với Club/Nation/League này → Sẽ thêm mới thay vì upgrade")
                    
                    submitted_upgrade = st.form_submit_button("🔄 Xác nhận Upgrade", use_container_width=True, type="primary")
                    
                    if submitted_upgrade:
                        if not new_player_url:
                            st.error("❌ Vui lòng nhập URL eFootballHub!")
                        elif not new_club or not new_nation or not new_league:
                            st.error("❌ Vui lòng điền đầy đủ Club, Nation, League!")
                        else:
                            with st.spinner("Đang xử lý..."):
                                # Trích xuất skills mới
                                new_skills = extract_player_skills(new_player_url) if new_player_url else ""
                                
                                # Tìm thẻ cũ
                                matching_card = player_versions[
                                    (player_versions['Club'].astype(str) == new_club) &
                                    (player_versions['Nation'].astype(str) == new_nation) &
                                    (player_versions['League'].astype(str) == new_league)
                                ]
                                
                                new_df = df.copy()
                                
                                if not matching_card.empty:
                                    # UPGRADE: Thay thế thẻ cũ
                                    old_idx = matching_card.index[0]
                                    old_rating = matching_card.iloc[0]['Rating']
                                    
                                    new_df.at[old_idx, 'Rating'] = int(new_rating)
                                    new_df.at[old_idx, 'Position'] = new_position
                                    new_df.at[old_idx, 'Position Style'] = new_position_style
                                    new_df.at[old_idx, 'Player Type'] = new_player_type
                                    new_df.at[old_idx, 'Player URL'] = new_player_url
                                    new_df.at[old_idx, 'Player ID'] = extract_ehub_player_id(new_player_url)
                                    new_df.at[old_idx, 'Skills'] = new_skills
                                    new_df.at[old_idx, 'Added Skills'] = ""  # Reset Added Skills
                                    new_df.at[old_idx, 'Epic_Priority'] = 0 if new_player_type == "EPIC" else 1
                                    
                                    try:
                                        if save_data_to_gsheet(new_df):
                                            rating_diff = new_rating - old_rating
                                            st.success(f"✅ Đã upgrade {selected_player}: {old_rating} → {new_rating} ({rating_diff:+d})")
                                            st.cache_data.clear()
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Lỗi khi lưu: {e}")
                                else:
                                    # THÊM MỚI: Không tìm thấy thẻ cũ
                                    new_player_data = {
                                        "Player": selected_player,
                                        "Rating": int(new_rating),
                                        "Position": new_position,
                                        "Position Style": new_position_style,
                                        "Player Type": new_player_type,
                                        "Nation": new_nation,
                                        "Club": new_club,
                                        "League": new_league,
                                        "Player URL": new_player_url,
                                        "Player ID": extract_ehub_player_id(new_player_url),
                                        "Skills": new_skills,
                                        "Added Skills": "",
                                        "Epic_Priority": 0 if new_player_type == "EPIC" else 1,
                                    }
                                    
                                    new_df = pd.concat([new_df, pd.DataFrame([new_player_data])], ignore_index=True)
                                    
                                    try:
                                        if save_data_to_gsheet(new_df):
                                            st.success(f"✅ Đã thêm phiên bản mới: {selected_player} {new_rating} | {new_club} | {new_nation} | {new_league}")
                                            st.cache_data.clear()
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Lỗi khi lưu: {e}")

    elif current_tab == 'inventory':
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