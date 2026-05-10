import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. 페이지 기본 설정 (항상 최상단)
st.set_page_config(page_title="우리집 통합 스마트 가계부", page_icon="💳", layout="wide")

# ==========================================
# 🔑 앱 접속 비밀번호 설정
# ==========================================
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<br><br><h2 style='text-align: center; color: #191f28;'>우리집 가계부 💳</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b95a1;'>부부 전용 공간입니다. 비밀번호를 입력해주세요.</p>", unsafe_allow_html=True)
        pwd = st.text_input("비밀번호 입력", type="password", label_visibility="collapsed", placeholder="비밀번호를 입력하세요")
        if st.button("가계부 열기", use_container_width=True, type="primary"):
            if pwd == "210327": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("⚠️ 비밀번호가 일치하지 않습니다.")
        st.stop() 

# ==========================================
# 💾 데이터 처리 로직
# ==========================================
DATA_FILE = "my_ledger.csv"

def clean_cat(name):
    if not isinstance(name, str): return name
    for brand in ["쿠팡", "네이버", "쿠팡이츠"]:
        if name.startswith(brand + "-"): return name.replace(brand + "-", "") + "-" + brand
        elif name.startswith(brand):
            for sep in ["-", " ", "/"]:
                if name.startswith(brand + sep): return name.replace(brand + sep, "") + "-" + brand
    return name

def load_master_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce', format='mixed')
            df['날짜'] = df['날짜'].fillna(pd.Timestamp.now())
        if '주체' in df.columns:
            df['주체'] = df['주체'].replace('아내', '지은').replace('남편', '영민')
        if '분류' in df.columns:
            df['분류'] = df['분류'].apply(clean_cat)
        return df
    return pd.DataFrame(columns=['날짜', '구분', '주체', '분류', '내역', '금액'])

def save_master_data(df):
    df_save = df.copy()
    if '날짜' in df_save.columns and pd.api.types.is_datetime64_any_dtype(df_save['날짜']):
        df_save['날짜'] = df_save['날짜'].dt.strftime('%Y-%m-%d')
    df_save.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

master_df = load_master_data()
DEFAULT_CATS = ['식비', '육아', '외식', '생필품', '병원', '주유', '기타']
all_categories = sorted(list(set(DEFAULT_CATS + (master_df['분류'].dropna().unique().tolist() if not master_df.empty else []))))

# ==========================================
# 🎨 전역 CSS (화이트 테마 고정)
# ==========================================
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    :root { color-scheme: light !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp { background-color: #f9fafb !important; color: #191f28 !important; font-family: 'Pretendard', sans-serif !important; }
    h1, h2, h3, h4, p, span, div, label, li, .stMarkdown { color: #191f28 !important; }
    
    /* 버튼 스타일 */
    button[kind="primary"], 
    button[kind="primaryFormSubmit"], 
    button[kind="secondary"],
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-secondary"],
    [data-testid="stFormSubmitButton"] button {
        background-color: #3182f6 !important; 
        color: #ffffff !important; 
        border-radius: 16px !important; 
        border: none !important;
        box-shadow: 0 4px 12px rgba(49, 130, 246, 0.2) !important;
    }
    
    /* 버튼 내부 텍스트 강제 화이트 */
    button p, button span, [data-testid="baseButton-secondary"] p { 
        color: #ffffff !important; 
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* 입력창 및 카드 테두리를 연한 파란색으로 */
    input, select, textarea, [data-testid="stSelectbox"] div, .toss-card, [data-testid="stForm"] {
        border: 1px solid #e8f3ff !important;
    }
    
    /* 카드 그림자 및 강조색 */
    .toss-card { 
        background-color: #ffffff !important; 
        border-radius: 20px; 
        padding: 20px; 
        box-shadow: 0 8px 24px rgba(49, 130, 246, 0.05) !important; 
        text-align: center; 
    }
    .toss-title { color: #4e5968 !important; font-size: 14px; font-weight: 600; margin-bottom: 5px; }
    .toss-amount { color: #191f28 !important; font-size: 24px; font-weight: 800; }
    .highlight-blue { color: #3182f6 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 내비게이션 시스템
# ==========================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"

def go_to(page):
    st.session_state["current_page"] = page
    st.rerun()

# 🏠 홈 메뉴 (2x2 카드형)
if st.session_state["current_page"] == "Home":
    st.title("우리집 가계부 💳")
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    menu_data = [
        ("Input", "✍️ 내역 입력", "오늘 쓴 돈 기록하기"),
        ("Dashboard", "📊 대시보드", "월별 지출 분석하기"),
        ("Edit", "✏️ 내역 수정", "기존 내역 관리하기"),
        ("Upload", "📂 파일 가져오기", "외부 데이터 합치기")
    ]
    
    for i, (page_id, title, desc) in enumerate(menu_data):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown(f"""
                <div style="background: white; padding: 30px 20px; border-radius: 24px; 
                     box-shadow: 0 8px 24px rgba(0,0,0,0.04); margin-bottom: 20px; 
                     border: 1px solid #f2f4f6; text-align: center;">
                    <div style="font-size: 28px; margin-bottom: 10px;">{title.split()[0]}</div>
                    <div style="font-weight: 800; font-size: 18px; color: #191f28; margin-bottom: 5px;">{title.split()[1]}</div>
                    <div style="font-size: 13px; color: #8b95a1;">{desc}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"{title.split()[1]} 열기", key=f"btn_{page_id}", use_container_width=True, type="primary"):
                go_to(page_id)
    st.stop()

# 모든 페이지 상단 뒤로가기
if st.button("⬅️ 메인 메뉴로", key="back_btn"):
    go_to("Home")

# ==========================================
# ✍️ 페이지 1: 내역 입력
# ==========================================
if st.session_state["current_page"] == "Input":
    st.subheader("📝 오늘 얼마나 쓰셨나요?")
    with st.form("input_form", clear_on_submit=True):
        t_type = st.radio("구분", ["지출", "수입"], horizontal=True)
        t_who = st.radio("주체", ["공동", "영민", "지은"], horizontal=True)
        c1, c2 = st.columns(2)
        t_date = c1.date_input("날짜", datetime.today())
        t_cat = c2.selectbox("항목", all_categories)
        t_amt = st.number_input("금액 (원)", min_value=0, step=1000)
        t_desc = st.text_input("상세 내역", placeholder="어디에 사용하셨나요?")
        if st.form_submit_button("기록 완료", use_container_width=True):
            if t_amt > 0:
                new_row = pd.DataFrame([{'날짜': pd.to_datetime(t_date), '구분': t_type, '주체': t_who, '분류': t_cat, '내역': t_desc, '금액': t_amt}])
                master_df = pd.concat([master_df, new_row], ignore_index=True)
                save_master_data(master_df)
                st.success("기록되었습니다!")
                st.rerun()

# ==========================================
# 📊 페이지 2: 대시보드 (월별 필터 포함)
# ==========================================
elif st.session_state["current_page"] == "Dashboard":
    if master_df.empty:
        st.info("데이터가 없습니다.")
    else:
        # 월별 필터
        master_df['날짜'] = pd.to_datetime(master_df['날짜'])
        months = sorted(master_df['날짜'].dt.strftime('%Y-%m').unique().tolist(), reverse=True)
        sel_month = st.selectbox("📅 조회할 월을 선택하세요", months)
        
        df_month = master_df[master_df['날짜'].dt.strftime('%Y-%m') == sel_month].copy()
        df_exp = df_month[df_month['구분'] == '지출'].copy()
        
        total = df_exp['금액'].sum()
        h_sum = df_exp[df_exp['주체'] == '영민']['금액'].sum()
        w_sum = df_exp[df_exp['주체'] == '지은']['금액'].sum()
        
        # 상단 카드
        st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
            <div class="toss-card" style="flex: 1.5; min-width: 200px;">
                <div class="toss-title">{sel_month} 총 지출</div>
                <div class="toss-amount highlight-blue">{int(total):,}원</div>
            </div>
            <div class="toss-card" style="flex: 1;">
                <div class="toss-title">영민</div><div class="toss-amount">{int(h_sum):,}원</div>
            </div>
            <div class="toss-card" style="flex: 1;">
                <div class="toss-title">지은</div><div class="toss-amount">{int(w_sum):,}원</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_p = px.pie(df_exp, values='금액', names='분류', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_p.update_layout(margin=dict(t=30, b=0, l=0, r=0), paper_bgcolor='#f2f4f6', font=dict(color='#191f28'))
            st.plotly_chart(fig_p, use_container_width=True)
        with c2:
            daily = df_exp.groupby(df_exp['날짜'].dt.strftime('%d'))['금액'].sum().reset_index()
            fig_b = px.bar(daily, x='날짜', y='금액')
            fig_b.update_layout(margin=dict(t=30, b=0, l=0, r=0), paper_bgcolor='#f2f4f6', font=dict(color='#191f28'))
            st.plotly_chart(fig_b, use_container_width=True)

        st.markdown("### 📋 상세 내역")
        cat_sum = df_exp.groupby('분류')['금액'].sum().reset_index().sort_values('금액', ascending=False)
        for _, row in cat_sum.iterrows():
            with st.expander(f"{row['분류']} - {int(row['금액']):,}원"):
                details = df_exp[df_exp['분류'] == row['분류']].sort_values('날짜', ascending=False)
                st.table(details[['날짜', '내역', '금액']].assign(날짜=lambda x: x['날짜'].dt.strftime('%m-%d')))

# ==========================================
# ✏️ 페이지 3: 내역 수정
# ==========================================
elif st.session_state["current_page"] == "Edit":
    st.subheader("✏️ 내역 수정 및 삭제")
    edited_df = st.data_editor(master_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
        save_master_data(edited_df)
        st.success("저장 완료!")
        st.rerun()

# ==========================================
# 📂 페이지 4: 파일 업로드
# ==========================================
elif st.session_state["current_page"] == "Upload":
    st.subheader("📂 엑셀/CSV 파일 가져오기")
    up_file = st.file_uploader("파일 선택", type=['xlsx', 'csv'])
    if up_file:
        up_df = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
        # 컬럼 매핑
        col_map = {'항목': '분류', '카테고리': '분류', '구분': '구분', '내용': '내역', '지출액': '금액'}
        up_df = up_df.rename(columns=col_map)
        if st.button("장부에 합치기", use_container_width=True, type="primary"):
            master_df = pd.concat([master_df, up_df], ignore_index=True).drop_duplicates()
            save_master_data(master_df)
            st.success("통합 완료!")
            st.rerun()