import os
import sys
import subprocess
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Ensure console output is in UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

st.set_page_config(
    page_title="IT & 과학 정책 뉴스 큐레이터",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set base path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "cleaned_policy_news.csv")
RECOMMENDED_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "recommended_policy_news.csv")
HTML_PREVIEW_PATH = os.path.join(BASE_DIR, "reports", "email_preview.html")
LOG_CSV_PATH = os.path.join(BASE_DIR, "reports", "resend_send_log.csv")

# Sidebar - Settings and Actions
st.sidebar.title("⚙️ 시스템 제어실")
st.sidebar.markdown("---")

def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            st.sidebar.success(f"✔ {script_name} 실행 성공!")
            return result.stdout
        else:
            st.sidebar.error(f"❌ {script_name} 실행 실패!")
            return result.stderr
    except Exception as e:
        st.sidebar.error(f"오류 발생: {str(e)}")
        return str(e)

st.sidebar.subheader("🔄 데이터 파이프라인 수동 실행")
if st.sidebar.button("1. 뉴스 크롤링 실행 (crawler.py)"):
    with st.spinner("뉴스 피드 크롤링 중... (10~20초 소요)"):
        out = run_script("crawler.py")
        st.sidebar.text_area("크롤러 출력 로그", out, height=150)

if st.sidebar.button("2. 데이터 정제 실행 (cleaner.py)"):
    with st.spinner("데이터 정제 및 중복 제거 중..."):
        out = run_script("cleaner.py")
        st.sidebar.text_area("정제 로그", out, height=150)

if st.sidebar.button("3. 추천 점수 계산 (recommender.py)"):
    with st.spinner("가중치 점수 계산 및 추천 랭킹 중..."):
        out = run_script("recommender.py")
        st.sidebar.text_area("추천기 로그", out, height=150)

if st.sidebar.button("4. 이메일 템플릿 빌드 (email_report_builder.py)"):
    with st.spinner("HTML 이메일 미리보기 파일 빌드 중..."):
        out = run_script("email_report_builder.py")
        st.sidebar.text_area("빌더 로그", out, height=150)

st.sidebar.markdown("---")
st.sidebar.subheader("📧 Resend 메일 전송 제어")
if st.sidebar.button("🚀 실제 이메일 발송 실행 (send_resend_email.py)"):
    with st.spinner("Resend API 연계 발송 시도 중..."):
        out = run_script("send_resend_email.py")
        st.sidebar.text_area("발송 결과 로그", out, height=150)

# Main Screen Layout
st.title("🚀 IT & 과학 정책 뉴스 자동 큐레이션 대시보드")
st.markdown("수집된 정부 및 매체 뉴스 데이터를 분석하고 큐레이션하여 이메일 발송까지 제어하는 종합 웹앱입니다.")
st.markdown("---")

# Layout Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📰 오늘의 추천 뉴스 (Top 20)",
    "📊 전체 수집 및 카테고리 분석",
    "📧 이메일 레터 미리보기 (HTML)",
    "📜 이메일 발송 기록 (Log)"
])

# Tab 1: Top 20 Recommended News
with tab1:
    st.subheader("🏆 키워드 가중치 기반 추천 랭킹 (Top 20)")
    st.markdown("인공지능, 빅데이터, 클라우드, 보안, 디지털전환 등의 가중치 합산 점수가 가장 높은 최신 기사목록입니다.")
    
    if os.path.exists(RECOMMENDED_CSV_PATH):
        try:
            df_rec = pd.read_csv(RECOMMENDED_CSV_PATH, encoding="utf-8")
            
            for idx, row in df_rec.iterrows():
                # Score & Badges
                score = row.get('recommend_score', 0)
                source = row.get('source_name', '알수없음')
                date = row.get('date', '')
                title = row.get('title', '')
                url = row.get('source_url', '#')
                categories = row.get('matched_categories', '')
                summary = row.get('summary', '상세 본문을 통해 전체 기사를 만나보실 수 있습니다.')
                
                with st.expander(f"**#{idx+1}위** [ {source} ] 🔥 **{score}점** | {title}"):
                    st.write(f"**🗓️ 발행 일자:** {date}")
                    st.write(f"**🏷️ 매칭 키워드:** {categories}")
                    st.markdown(f"**📝 내용 요약:**\n{summary}")
                    st.markdown(f"[🔗 원본 뉴스 링크 바로가기 ↗]({url})")
        except Exception as e:
            st.error(f"데이터를 불러오는 데 실패했습니다: {str(e)}")
    else:
        st.info("💡 추천 데이터 파일(`recommended_policy_news.csv`)이 없습니다. 사이드바의 파이프라인 버튼을 순서대로 실행해 주세요!")

# Tab 2: General Collection & Analytics
with tab2:
    st.subheader("📊 수집 기사 데이터 분석")
    
    if os.path.exists(CLEANED_CSV_PATH):
        try:
            df_clean = pd.read_csv(CLEANED_CSV_PATH, encoding="utf-8")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 정제 기사 수", f"{len(df_clean)} 건")
            with col2:
                sources = df_clean['source_name'].value_counts()
                st.metric("과학기술정보통신부 기사", f"{sources.get('과학기술정보통신부', 0)} 건")
            with col3:
                st.metric("전자신문 기사", f"{sources.get('전자신문', 0)} 건")
                
            st.markdown("---")
            st.subheader("📰 수집 출처별 통계")
            st.bar_chart(sources)
            
            st.subheader("🔍 전체 정제 기사 목록 데이터 테이블")
            st.dataframe(df_clean[['date', 'source_name', 'title', 'source_url']], use_container_width=True)
            
        except Exception as e:
            st.error(f"데이터 분석 오류: {str(e)}")
    else:
        st.info("💡 정제된 기사 데이터 파일(`cleaned_policy_news.csv`)이 존재하지 않습니다.")

# Tab 3: HTML Email Preview
with tab3:
    st.subheader("📧 실제 전송될 이메일 레이아웃 템플릿")
    st.markdown("반응형으로 빌드된 이메일 템플릿의 완성 디자인입니다.")
    
    if os.path.exists(HTML_PREVIEW_PATH):
        try:
            with open(HTML_PREVIEW_PATH, "r", encoding="utf-8") as f:
                html_content = f.read()
            # Render HTML safely
            components.html(html_content, height=750, scrolling=True)
        except Exception as e:
            st.error(f"HTML 템플릿 로딩 실패: {str(e)}")
    else:
        st.info("💡 빌드된 이메일 HTML 미리보기 파일이 없습니다. 사이드바 4번 단계를 실행하여 리포트 파일을 생성해 주세요!")

# Tab 4: Send Log History
with tab4:
    st.subheader("📜 이메일 자동 발송 및 시도 히스토리")
    st.markdown("중복 발송 방지 로그 및 실제 발송 시도 성공/실패 내역을 실시간으로 확인합니다.")
    
    if os.path.exists(LOG_CSV_PATH):
        try:
            df_log = pd.read_csv(LOG_CSV_PATH, encoding="utf-8")
            # Sort by newest first
            df_log_sorted = df_log.iloc[::-1]
            st.dataframe(df_log_sorted, use_container_width=True)
        except Exception as e:
            st.error(f"로그를 불러오는 과정에서 오류가 발생했습니다: {str(e)}")
    else:
        st.info("💡 아직 발송 이력 로그(`resend_send_log.csv`)가 존재하지 않습니다.")
