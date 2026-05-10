import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. 페이지 기본 설정 (가장 최상단)
st.set_page_config(page_title="우리집 통합 스마트 가계부", page_icon="💳", layout="wide")

# ==========================================
# 🔑 앱 접속 비밀번호 설정
# ==========================================
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# 비밀번호가 맞지 않을 때만 로그인 화면을 보여줌
if not st.session_state["password_correct"]:
    # 중앙 정렬을 위한 컬럼 배치
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        st.markdown("<br><br><h2 style='text-align: center; color: #191f28;'>우리집 가계부 💳</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b95a1;'>부부 전용 공간입니다. 비밀번호를 입력해주세요.</p>", unsafe_allow_html=True)
        
        # 비밀번호 입력창
        pwd = st.text_input("비밀번호 입력", type="password", label_visibility="collapsed", placeholder="비밀번호를 입력하세요")
        
        if st.button("가계부 열기", use_container_width=True, type="primary"):
            # 💡 비밀번호를 수정했습니다.
            if pwd == "210327": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("⚠️ 비밀번호가 일치하지 않습니다.")
                
        # 비밀번호가 통과될 때까지 아래의 코드는 실행되지 않음
        st.stop() 

# ==========================================
# 💾 장기 저장 시스템 (Master Database)
# ==========================================
DATA_FILE = "my_ledger.csv"

def clean_cat(name):
    """'쿠팡-식비'를 '식비-쿠팡'으로 변경하는 등 브랜드명을 뒤로 보냅니다."""
    if not isinstance(name, str): return name
    for brand in ["쿠팡", "네이버", "쿠팡이츠"]:
        if name.startswith(brand + "-"):
            return name.replace(brand + "-", "") + "-" + brand
        elif name.startswith(brand): 
            for sep in ["-", " ", "/"]:
                if name.startswith(brand + sep):
                    return name.replace(brand + sep, "") + "-" + brand
    return name

def load_master_data():
    """로컬에 저장된 마스터 가계부 파일을 불러옵니다."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce', format='mixed')
            df['날짜'] = df['날짜'].fillna(pd.Timestamp.now())
            df['날짜'] = df['날짜'].dt.strftime('%Y-%m-%d')
        if '주체' in df.columns:
            df['주체'] = df['주체'].replace('아내', '지은').replace('남편', '영민')
        if '분류' in df.columns:
            df['분류'] = df['분류'].apply(clean_cat)
        return df
    else:
        return pd.DataFrame(columns=['날짜', '구분', '주체', '분류', '내역', '금액'])

def save_master_data(df):
    """마스터 데이터를 파일로 영구 저장합니다."""
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

master_df = load_master_data()

DEFAULT_CATS = ['식비', '육아', '외식', '생필품', '병원', '주유', '기타']
if not master_df.empty and '분류' in master_df.columns:
    existing_cats = master_df['분류'].dropna().unique().tolist()
    all_categories = sorted(list(set(DEFAULT_CATS + existing_cats)))
else:
    all_categories = DEFAULT_CATS

# ==========================================
# 🎨 트렌디한 UI/CSS 전면 개편 (다크모드 강제 화이트 고정)
# ==========================================
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 1. 화이트 테마 고정 및 가독성 확보 */
    :root {
        color-scheme: light;
        --primary-color: #3182f6;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #f9fafb !important;
        color: #191f28 !important;
    }

    /* 모든 기본 텍스트를 검정색 계열로 고정 */
    h1, h2, h3, h4, p, span, div, label, li, .stMarkdown {
        color: #191f28 !important;
    }

    /* 2. 메뉴(Tabs) 대비 강화 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f2f4f6 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8b95a1 !important; /* 비활성 탭: 회색 */
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #3182f6 !important; /* 활성 탭: 파란색 (대비 강조) */
    }

    /* 3. 버튼 대비 수정 (배경색이 있을 때만 화이트 텍스트) */
    button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="baseButton-primary"] {
        background-color: #3182f6 !important;
        color: #ffffff !important; /* 파란 배경엔 흰색 글자 */
    }
    
    /* 일반 버튼 (배경이 흰색에 가까운 경우) */
    [data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        color: #191f28 !important; /* 흰 배경엔 검정 글자 */
        border: 1px solid #e5e8eb !important;
    }
    /* 버튼 내부 텍스트 강제 적용 */
    button[kind="primary"] p, button[kind="primary"] span { color: #ffffff !important; }
    [data-testid="baseButton-secondary"] p, [data-testid="baseButton-secondary"] span { color: #191f28 !important; }

    /* 4. 첫 화면(로그인) 및 카드 대비 */
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e8eb !important;
    }

    /* 드롭다운 메뉴 대비 */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #ffffff !important;
    }
    div[data-baseweb="option"], [role="option"] {
        color: #191f28 !important;
        background-color: #ffffff !important;
    }
    div[data-baseweb="option"]:hover {
        background-color: #f2f4f6 !important;
    }

    /* 텍스트 입력창 및 숫자 입력창 대비 강화 */
    input, textarea, [data-testid="stTextInput"] div, [data-testid="stNumberInput"] div {
        background-color: #ffffff !important;
        color: #191f28 !important;
    }
    /* 입력창 내부 실제 텍스트 강제 */
    input {
        color: #191f28 !important;
        -webkit-text-fill-color: #191f28 !important; /* iOS/Safari 대응 */
    }

    /* 차트 및 기타 요소 */
    .toss-card {
        background-color: #ffffff !important;
    }
    .toss-amount {
        color: #191f28 !important;
    }

    /* 대시보드 카드 */
    .toss-card-container { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
    .toss-card { 
        flex: 1 1 200px; 
        background-color: #ffffff !important; 
        border-radius: 20px; 
        padding: 24px; 
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.04) !important; 
        text-align: center; 
        border: 1px solid #f2f4f6 !important; 
    }
    .toss-title { color: #4e5968 !important; font-size: 15px; font-weight: 600; margin-bottom: 8px; }
    .toss-amount { color: #191f28 !important; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .highlight-blue { color: #3182f6 !important; }

    /* 세부 내역 테이블 */
    .detail-table { width: 100%; border-collapse: collapse; font-size: 14px; color: #4e5968 !important; margin-top: 5px; }
    .detail-table tr { border-bottom: 1px solid #f2f4f6 !important; }
    .detail-table td { padding: 12px 4px; color: #191f28 !important; }
    
    /* 사이드바 등 기타 영역 강제 화이트 */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("우리집 가계부 💳")

tab_input, tab_dashboard, tab_upload = st.tabs(["✍️ 내역 입력", "📊 대시보드", "📂 파일 가져오기"])

# ==========================================
# ✍️ 탭 1: 직접 입력
# ==========================================
with tab_input:
    st.markdown("<h3 style='color: #191f28; font-weight: 800;'>얼마를 쓰셨나요? 💸</h3>", unsafe_allow_html=True)
    with st.form("quick_input", clear_on_submit=True):
        type_v = st.radio("어떤 내역인가요?", ["지출", "수입"], horizontal=True)
        who_v = st.radio("누가 결제했나요?", ["공동", "영민", "지은"], horizontal=True)
        st.markdown("<hr style='border:1px dashed #e5e8eb; margin: 15px 0;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        date_v = c1.date_input("날짜", datetime.today())
        cat_v = c2.selectbox("어디에 속하나요? (분류)", all_categories)
        amount_v = st.number_input("금액을 입력하세요 (원)", min_value=0, step=1000, format="%d")
        desc_v = st.text_input("상세 내역 (어디서 썼나요?)", placeholder="예: 정석소아과 진료비")
        
        if st.form_submit_button("장부에 기록하기", use_container_width=True):
            if amount_v > 0:
                new_entry = pd.DataFrame([{
                    '날짜': date_v.strftime("%Y-%m-%d"),
                    '구분': type_v, '주체': who_v, '분류': cat_v, '내역': desc_v, '금액': amount_v
                }])
                master_df = pd.concat([master_df, new_entry], ignore_index=True)
                save_master_data(master_df)
                st.success("✅ 성공적으로 기록되었습니다!")
                st.rerun()
            else:
                st.error("⚠️ 금액을 0원 이상으로 입력해주세요.")

# ==========================================
# 📈 탭 2: 대시보드 및 관리
# ==========================================
with tab_dashboard:
    if master_df.empty:
        st.info("아직 기록된 내역이 없습니다. 첫 지출을 입력해보세요!")
    else:
        df_exp = master_df[master_df['구분'] == '지출'].copy()
        df_exp['금액'] = pd.to_numeric(df_exp['금액'], errors='coerce').fillna(0)
        total = df_exp['금액'].sum()
        h_sum = df_exp[df_exp['주체'] == '영민']['금액'].sum()
        w_sum = df_exp[df_exp['주체'] == '지은']['금액'].sum()
        
        kpi_html = f"""
        <div class="toss-card-container">
            <div class="toss-card"><div class="toss-title">이번 달 총 지출</div><div class="toss-amount highlight-blue">{int(total):,}원</div></div>
            <div class="toss-card"><div class="toss-title">영민 지출</div><div class="toss-amount">{int(h_sum):,}원</div></div>
            <div class="toss-card"><div class="toss-title">지은 지출</div><div class="toss-amount">{int(w_sum):,}원</div></div>
        </div>
        """
        st.markdown(kpi_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("<h4 style='color: #333d4b;'>항목별 비중</h4>", unsafe_allow_html=True)
            fig_p = px.pie(df_exp, values='금액', names='분류', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_p.update_layout(
                margin=dict(t=20, b=20, l=20, r=20), 
                showlegend=False,
                paper_bgcolor='#f2f4f6',
                plot_bgcolor='#f2f4f6'
            )
            st.plotly_chart(fig_p, use_container_width=True)
        with c_right:
            st.markdown("<h4 style='color: #333d4b;'>일자별 흐름</h4>", unsafe_allow_html=True)
            daily = df_exp.groupby('날짜')['금액'].sum().reset_index()
            fig_b = px.bar(daily, x='날짜', y='금액')
            fig_b.update_traces(marker_color='#3182f6', marker_line_width=0, opacity=0.9)
            fig_b.update_layout(
                margin=dict(t=20, b=20, l=20, r=20), 
                plot_bgcolor='#f2f4f6', 
                paper_bgcolor='#f2f4f6'
            )
            fig_b.update_yaxes(showgrid=True, gridcolor='#ffffff')
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.markdown("### 📋 항목별 상세 (눌러서 펼치기)")
        sort_opt = st.selectbox("정렬 기준", ["금액 높은 순 ↓", "금액 낮은 순 ↑", "항목 이름순 (가나다)"], label_visibility="collapsed")
        cat_sum = df_exp.groupby('분류')['금액'].sum().reset_index()
        if sort_opt == "금액 높은 순 ↓": cat_sum = cat_sum.sort_values('금액', ascending=False)
        elif sort_opt == "금액 낮은 순 ↑": cat_sum = cat_sum.sort_values('금액', ascending=True)
        else: cat_sum = cat_sum.sort_values('분류', ascending=True)
        
        summary_html = '<div style="background-color: #ffffff; border-radius: 20px; padding: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);">'
        for _, row in cat_sum.iterrows():
            cat = row['분류']
            amt = int(row['금액'])
            perc = (amt / total * 100) if total > 0 else 0
            details = df_exp[df_exp['분류'] == cat].sort_values('날짜', ascending=False)
            det_html = '<div style="margin-top:12px; padding:12px; background:#f9fafb; border-radius:12px;"><table class="detail-table">'
            for _, d in details.iterrows():
                det_html += f'<tr><td style="color:#8b95a1;">{d["날짜"][5:]}</td><td style="font-weight:500;">{d["내역"]}</td><td style="text-align:right; font-weight:600; color:#191f28;">{int(d["금액"]):,}원</td></tr>'
            det_html += '</table></div>'
            summary_html += f'<details style="padding:18px 10px; border-bottom:1px solid #f2f4f6; cursor:pointer;"><summary style="list-style:none; outline:none;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span style="font-weight:700; color:#333d4b; font-size:17px;">{cat} <span style="font-size:12px; color:#b0b8c1;">▼</span></span><span style="font-weight:800; color:#191f28; font-size:18px;">{amt:,}원</span></div><div style="background:#f2f4f6; border-radius:8px; height:10px; width:100%; overflow:hidden;"><div style="background:#3182f6; width:{perc}%; height:100%; border-radius:8px;"></div></div><div style="text-align:right; font-size:13px; color:#8b95a1; margin-top:6px;">비중 {perc:.1f}%</div></summary>{det_html}</details>'
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("⚙️ 전체 데이터 관리 (수정/삭제/추가)")
        st.info("💡 **팁**: 표 안의 칸을 클릭해 내용을 수정하거나, 행 왼쪽을 클릭해 선택 후 Delete 키로 삭제할 수 있습니다. 가장 아래 빈 행에 내용을 적으면 항목이 추가됩니다.")
        edited = st.data_editor(master_df, num_rows="dynamic", use_container_width=True)
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("💾 수정 내용 저장", use_container_width=True, type="primary"):
                save_master_data(edited)
                st.success("업데이트되었습니다.")
                st.rerun()
        with col_btn2:
            with st.expander("⚠️ 데이터 전체 초기화"):
                st.warning("이 버튼을 누르면 마스터 가계부의 모든 데이터가 영구적으로 삭제됩니다.")
                if st.button("🔥 모든 데이터 삭제하고 처음부터 시작하기"):
                    empty_df = pd.DataFrame(columns=['날짜', '구분', '주체', '분류', '내역', '금액'])
                    save_master_data(empty_df)
                    st.success("전체 데이터가 성공적으로 초기화되었습니다.")
                    st.rerun()
        st.divider()
        csv = master_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 통합 내역 백업(CSV) 다운로드", csv, "ledger_backup.csv", "text/csv")

# ==========================================
# 📂 탭 3: 엑셀 업로드
# ==========================================
with tab_upload:
    st.markdown("### 📥 기존 엑셀/CSV 가져오기")
    st.info("과거 데이터를 업로드하면 기존 장부에 병합됩니다.")
    uploaded_file = st.file_uploader("파일 선택", type=['xlsx', 'csv'])
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'): up_df = pd.read_csv(uploaded_file)
        else: up_df = pd.read_excel(uploaded_file)
        col_map = {'항목': '분류', '카테고리': '분류', '구분': '구분', '내용': '내역', '상세': '내역', '지출액': '금액'}
        up_df = up_df.rename(columns=col_map)
        for col in ['날짜', '구분', '주체', '분류', '내역', '금액']:
            if col not in up_df.columns:
                if col == '구분': up_df[col] = "지출"
                elif col == '금액': up_df[col] = 0
                else: up_df[col] = "기타" if col == '분류' else "-"
        up_df['구분'] = up_df['구분'].fillna("지출").replace("", "지출").replace("-", "지출")
        up_df['분류'] = up_df['분류'].astype(str).str.strip().apply(clean_cat)
        up_df['날짜'] = pd.to_datetime(up_df['날짜'], errors='coerce', format='mixed').dt.strftime('%Y-%m-%d')
        up_df['날짜'] = up_df['날짜'].fillna(datetime.today().strftime('%Y-%m-%d'))
        up_df['금액'] = pd.to_numeric(up_df['금액'].astype(str).replace({',': ''}, regex=True), errors='coerce').fillna(0)
        st.dataframe(up_df.head(5), use_container_width=True)
        if st.button("내 장부에 합치기", type="primary", use_container_width=True):
            master_df = pd.concat([master_df, up_df], ignore_index=True).drop_duplicates()
            save_master_data(master_df)
            st.success("통합 완료!")
            st.rerun()