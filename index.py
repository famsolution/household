import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. 페이지 기본 설정 (항상 최상단에 위치)
st.set_page_config(page_title="우리집 통합 스마트 가계부", page_icon="💳", layout="wide")

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
        elif name.startswith(brand): # '쿠팡 식비' 등 대응
            # 정규식 없이 간단하게 처리하기 위해 공백이나 대시가 있는 경우만 처리
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
# 🎨 트렌디한 UI/CSS 전면 개편
# ==========================================
st.markdown("""
    <style>
    /* 웹 폰트 (Pretendard) 적용으로 모바일 앱 느낌 극대화 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }

    /* 전체 배경색 살짝 어둡게 (카드들을 돋보이게 함) */
    .stApp { background-color: #f9fafb; }

    /* 탭(Tab) 디자인 - 알약(Pill) 형태의 세그먼트 컨트롤 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f2f4f6;
        padding: 6px;
        border-radius: 16px;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 12px;
        height: 48px;
        padding: 0 24px;
        font-weight: 700;
        color: #8b95a1;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        color: #191f28 !important;
    }

    /* 폼(Form) 컨테이너를 둥근 하얀 카드로 변경 */
    [data-testid="stForm"] {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 24px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.03);
        border: 1px solid #ffffff;
    }

    /* 큼지막한 메인 제출 버튼 (포인트 블루) */
    button[kind="primaryFormSubmit"], button[kind="primary"] {
        background-color: #3182f6 !important;
        color: white !important;
        border-radius: 16px !important;
        height: 60px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(49, 130, 246, 0.25) !important;
        transition: all 0.2s ease;
        margin-top: 15px;
    }
    button[kind="primaryFormSubmit"]:hover, button[kind="primary"]:hover {
        background-color: #1b64da !important;
        transform: translateY(-2px);
    }

    /* 대시보드 카드 디자인 (더 입체적이고 깔끔하게) */
    .toss-card-container { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
    .toss-card {
        flex: 1 1 200px; 
        background-color: #ffffff; 
        border-radius: 20px;
        padding: 24px; 
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.04);
        text-align: center; 
        border: 1px solid #f2f4f6;
    }
    .toss-title { color: #4e5968; font-size: 15px; font-weight: 600; margin-bottom: 8px; }
    .toss-amount { color: #191f28; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .highlight-blue { color: #3182f6; }

    /* 세부 내역 테이블 */
    .detail-table { width: 100%; border-collapse: collapse; font-size: 14px; color: #4e5968; margin-top: 5px; }
    .detail-table tr { border-bottom: 1px solid #f2f4f6; }
    .detail-table td { padding: 12px 4px; }
    
    /* 입력창 폰트 크기 조정 */
    input, select { font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("우리집 가계부 💳")

# 메인 탭 구성
tab_input, tab_dashboard, tab_upload = st.tabs(["✍️ 내역 입력", "📊 대시보드", "📂 파일 가져오기"])

# ==========================================
# ✍️ 탭 1: 직접 입력 (UI 개선)
# ==========================================
with tab_input:
    st.markdown("<h3 style='color: #191f28; font-weight: 800;'>얼마를 쓰셨나요? 💸</h3>", unsafe_allow_html=True)
    
    with st.form("quick_input", clear_on_submit=True):
        # 모바일 앱처럼 라디오 버튼(가로형)을 사용하여 버튼 누르듯 선택하게 변경
        type_v = st.radio("어떤 내역인가요?", ["지출", "수입"], horizontal=True)
        who_v = st.radio("누가 결제했나요?", ["공동", "영민", "지은"], horizontal=True)
        
        st.markdown("<hr style='border:1px dashed #e5e8eb; margin: 15px 0;'>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        date_v = c1.date_input("날짜", datetime.today())
        cat_v = c2.selectbox("어디에 속하나요? (분류)", all_categories)
        
        # 금액과 내역을 큼지막하게
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
# 📈 탭 2: 대시보드 및 관리 (순서 변경)
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
            fig_p.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig_p, use_container_width=True)
        with c_right:
            st.markdown("<h4 style='color: #333d4b;'>일자별 흐름</h4>", unsafe_allow_html=True)
            daily = df_exp.groupby('날짜')['금액'].sum().reset_index()
            fig_b = px.bar(daily, x='날짜', y='금액')
            fig_b.update_traces(marker_color='#3182f6', marker_line_width=0, opacity=0.9)
            fig_b.update_layout(margin=dict(t=0, b=0, l=0, r=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            fig_b.update_yaxes(showgrid=True, gridcolor='#f2f4f6')
            st.plotly_chart(fig_b, use_container_width=True)
            
        # 📋 항목별 지출 요약 (정렬 기능 추가)
        st.markdown("### 📋 항목별 지출 상세 (눌러서 펼치기)")
        
        # 정렬 옵션 선택
        sort_opt = st.selectbox("정렬 기준", ["금액 높은 순 ↓", "금액 낮은 순 ↑", "항목 이름순 (가나다)"], label_visibility="collapsed")
        
        cat_sum = df_exp.groupby('분류')['금액'].sum().reset_index()
        
        if sort_opt == "금액 높은 순 ↓":
            cat_sum = cat_sum.sort_values('금액', ascending=False)
        elif sort_opt == "금액 낮은 순 ↑":
            cat_sum = cat_sum.sort_values('금액', ascending=True)
        else:
            cat_sum = cat_sum.sort_values('분류', ascending=True)
        
        summary_html = '<div style="background-color: #ffffff; border-radius: 20px; padding: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);">'
        for _, row in cat_sum.iterrows():
            cat = row['분류']
            amt = int(row['금액'])
            perc = (amt / total * 100) if total > 0 else 0
            
            details = df_exp[df_exp['분류'] == cat].sort_values('날짜', ascending=False)
            det_html = '<div style="margin-top:12px; padding:12px; background:#f9fafb; border-radius:12px;">'
            det_html += '<table class="detail-table">'
            for _, d in details.iterrows():
                det_html += f'<tr><td style="color:#8b95a1;">{d["날짜"][5:]}</td><td style="font-weight:500;">{d["내역"]}</td><td style="text-align:right; font-weight:600; color:#191f28;">{int(d["금액"]):,}원</td></tr>'
            det_html += '</table></div>'
            
            summary_html += f'<details style="padding:18px 10px; border-bottom:1px solid #f2f4f6; cursor:pointer;">'
            summary_html += f'<summary style="list-style:none; outline:none;">'
            summary_html += f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
            summary_html += f'<span style="font-weight:700; color:#333d4b; font-size:17px;">{cat} <span style="font-size:12px; color:#b0b8c1;">▼</span></span>'
            summary_html += f'<span style="font-weight:800; color:#191f28; font-size:18px;">{amt:,}원</span>'
            summary_html += f'</div>'
            summary_html += f'<div style="background:#f2f4f6; border-radius:8px; height:10px; width:100%; overflow:hidden;">'
            summary_html += f'<div style="background:#3182f6; width:{perc}%; height:100%; border-radius:8px;"></div>'
            summary_html += f'</div>'
            summary_html += f'<div style="text-align:right; font-size:13px; color:#8b95a1; margin-top:6px;">비중 {perc:.1f}%</div>'
            summary_html += f'</summary>{det_html}</details>'
        
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("⚙️ 전체 데이터 편집")
        edited = st.data_editor(master_df, num_rows="dynamic", use_container_width=True)
        
        if st.button("수정 내용 저장", type="primary"):
            save_master_data(edited)
            st.success("업데이트되었습니다.")
            st.rerun()

# ==========================================
# 📂 탭 3: 엑셀 업로드
# ==========================================
with tab_upload:
    st.markdown("### 📥 기존 엑셀/CSV 가져오기")
    st.info("과거 데이터를 업로드하면 기존 장부에 병합됩니다.")
    
    uploaded_file = st.file_uploader("파일 선택", type=['xlsx', 'csv'])
    
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            up_df = pd.read_csv(uploaded_file)
        else:
            up_df = pd.read_excel(uploaded_file)
        
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
        
        if st.button("내 장부에 합치기", type="primary"):
            master_df = pd.concat([master_df, up_df], ignore_index=True).drop_duplicates()
            save_master_data(master_df)
            st.success("통합 완료!")
            st.rerun()