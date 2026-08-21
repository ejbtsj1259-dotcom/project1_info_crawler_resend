import os
import sys
import hashlib
import datetime
import time
import random
import requests
import feedparser
from bs4 import BeautifulSoup
import pandas as pd
import urllib3

# Suppress insecure request warnings for government portals with self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure console output is in UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

ERROR_LOG_PATH = os.path.join(LOGS_DIR, "crawler_error_log.txt")
CSV_PATH = os.path.join(DATA_RAW_DIR, "crawled_policy_news.csv")

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Define RSS Feed List
RSS_FEEDS = {
    "전자신문_IT": "http://rss.etnews.com/03.xml",
    "전자신문_SW": "http://rss.etnews.com/04.xml",
    "전자신문_AI": "http://rss.etnews.com/04046.xml",
    "전자신문_보안": "http://rss.etnews.com/04045.xml",
    "과기정통부_보도자료": "https://www.msit.go.kr/user/rss/rss.do?bbsSeqNo=94",
    "과기정통부_정보통신": "https://www.msit.go.kr/user/rss/rss.do?bbsSeqNo=67",
    "과기정통부_네트워크": "https://www.msit.go.kr/user/rss/rss.do?bbsSeqNo=68",
    "과기정통부_정책": "https://www.msit.go.kr/user/rss/rss.do?bbsSeqNo=70",
    "KISA_공지사항": "https://kisa.or.kr/rss/401",
    "KISA_보도자료": "https://kisa.or.kr/rss/402"
}

# Key Tech Keywords for Filtering (AI, Automation, Cloud, Data, Security, DX)
TECH_KEYWORDS = [
    # 인공지능 (AI)
    "인공지능", "AI", "머신러닝", "딥러닝", "생성형", "GPT", "거대언어", "LLM",
    # 자동화 (Automation)
    "자동화", "RPA", "로봇", "매크로", "업무자동화",
    # 클라우드 (Cloud)
    "클라우드", "SaaS", "PaaS", "IaaS", "AWS", "애저", "클라우드형",
    # 데이터 (Data)
    "데이터", "빅데이터", "DB", "데이터베이스", "마이데이터",
    # 보안 (Security)
    "보안", "랜섬웨어", "해킹", "KISA", "해커", "공격", "백신", "시큐리티", "침해사고", "악성코드", "피싱",
    # 디지털 전환 (Digital Transformation)
    "디지털 전환", "디지털 혁신", "DX", "DT", "디지털 플랫폼", "디지털전환", "디지털혁신"
]

def log_error(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def fetch_rss_entries():
    all_entries = []
    print("▶ STEP 1: RSS 피드 목록 수집 중...")
    
    for source_name, url in RSS_FEEDS.items():
        try:
            print(f"  - {source_name} 가져오는 중: {url}")
            # Use requests to fetch XML to bypass default feedparser User-Agent block
            res = requests.get(url, headers=HEADERS, timeout=15, verify=False)
            if res.status_code == 200:
                feed = feedparser.parse(res.content)
                entries_added = 0
                for entry in feed.entries:
                    # Parse publication date
                    pub_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if pub_parsed:
                        date_str = datetime.datetime(*pub_parsed[:6]).strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
                    
                    all_entries.append({
                        "title": entry.get("title", "").strip(),
                        "source_url": entry.get("link", "").strip(),
                        "source_name": "전자신문" if "전자신문" in source_name else ("과학기술정보통신부" if "과기정통부" in source_name else "한국인터넷진흥원"),
                        "date": date_str,
                        "rss_summary": entry.get("description", "").strip()
                    })
                    entries_added += 1
                print(f"    ✔ {entries_added}건 발견")
            else:
                msg = f"피드 가져오기 실패 ({source_name}): HTTP {res.status_code}"
                print(f"    ❌ {msg}")
                log_error(msg)
        except Exception as e:
            msg = f"피드 파싱 에러 ({source_name}): {str(e)}"
            print(f"    ❌ {msg}")
            log_error(msg)
            
    # Remove duplicates based on URL
    df_temp = pd.DataFrame(all_entries)
    if not df_temp.empty:
        df_temp = df_temp.drop_duplicates(subset=["source_url"])
        all_entries = df_temp.to_dict("records")
        
    print(f"▶ 중복 제거 후 총 {len(all_entries)}개의 고유 기사 링크를 확보했습니다.\n")
    return all_entries

def clean_html_and_get_text(soup, url):
    # Remove unneeded layout/nav/script tags
    for elem in soup(["script", "style", "header", "footer", "nav", "aside", "noscript", "iframe"]):
        elem.decompose()
        
    text = ""
    # Domain-specific selectors
    if "etnews.com" in url:
        for selector in ["div.article_body", "div#articleBody", "article"]:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text("\n", strip=True)
                break
    elif "msit.go.kr" in url:
        for selector in ["div.board_view", "div.board-view", "div.view-cont"]:
            elem = soup.select_one(selector)
            if elem:
                # Remove file downloads or nav links
                for extra in elem.select("div.view_file, div.view_nav, div.share_box"):
                    extra.decompose()
                text = elem.get_text("\n", strip=True)
                break
    elif "kisa.or.kr" in url:
        for selector in ["div.sub_container", "div.board_detail", "table"]:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text("\n", strip=True)
                break
                
    # Heuristic fallback if text is too short
    if len(text) < 100:
        all_divs = soup.find_all("div")
        best_div = None
        max_len = 0
        for d in all_divs:
            sub_div_count = len(d.find_all("div"))
            if sub_div_count < 10:
                d_text = d.get_text(strip=True)
                if len(d_text) > max_len:
                    max_len = len(d_text)
                    best_div = d
        if best_div:
            text = best_div.get_text("\n", strip=True)
            
    # Absolute fallback
    if len(text) < 50 and soup.body:
        text = soup.body.get_text("\n", strip=True)
        
    return text.strip()

def matches_tech_keywords(title, description):
    combined = (title + " " + description).lower()
    for kw in TECH_KEYWORDS:
        if kw.lower() in combined:
            return True
    return False

def crawl_articles(entries):
    print("▶ STEP 2: 상세 기사 본문 수집 시작...")
    crawled_data = []
    
    # 1. First attempt with keyword filtering to get relevant tech articles
    filtered_entries = [e for e in entries if matches_tech_keywords(e["title"], e["rss_summary"])]
    print(f"  - 테마 키워드 매칭 기사: {len(filtered_entries)}건 / 전체 기사: {len(entries)}건")
    
    # Check if keyword-filtered count is sufficient (>= 200)
    # If not, we relax the filter and include non-filtered items as fallback
    if len(filtered_entries) >= 200:
        target_entries = filtered_entries
        print("  - 키워드 매칭 기사가 200건 이상이므로, 필터링된 기사들로만 수집을 진행합니다.")
    else:
        target_entries = entries
        print("  - 키워드 매칭 기사가 200건 미만이므로, 수집량 200건을 달성하기 위해 전체 수집으로 완화하여 진행합니다.")
        
    total_to_crawl = len(target_entries)
    print(f"  - 총 {total_to_crawl}건의 수집 대상 확정.\n")
    
    for idx, entry in enumerate(target_entries, 1):
        url = entry["source_url"]
        print(f"  [{idx}/{total_to_crawl}] 본문 수집 중: {entry['title'][:30]}...")
        
        content = ""
        try:
            # Random delay between 1.0 to 1.8 seconds to respect servers (robots.txt)
            time.sleep(random.uniform(1.0, 1.8))
            
            res = requests.get(url, headers=HEADERS, timeout=12, verify=False)
            if res.status_code == 200:
                # Resolve encoding issues (EUC-KR fallback)
                if "etnews.com" in url:
                    res.encoding = 'utf-8'
                elif "kisa.or.kr" in url or "msit.go.kr" in url:
                    res.encoding = 'utf-8'
                else:
                    res.encoding = res.apparent_encoding
                    
                soup = BeautifulSoup(res.text, 'html.parser')
                content = clean_html_and_get_text(soup, url)
            else:
                msg = f"본문 요청 실패 ({url}): HTTP {res.status_code}"
                log_error(msg)
        except Exception as e:
            msg = f"본문 수집 에러 ({url}): {str(e)}"
            log_error(msg)
            
        # Prepare final columns
        article_id = hashlib.md5(url.encode('utf-8')).hexdigest()
        collected_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Strip HTML from RSS summary to use as text summary
        summary_clean = BeautifulSoup(entry["rss_summary"], 'html.parser').get_text(strip=True) if entry["rss_summary"] else ""
        
        # Check if any mandatory field is missing (title, date, content, source_url, source_name)
        has_null = not (bool(entry["title"]) and bool(entry["date"]) and bool(content) and bool(url) and bool(entry["source_name"]))
        
        crawled_data.append({
            "article_id": article_id,
            "title": entry["title"],
            "date": entry["date"],
            "content": content,
            "summary": summary_clean,
            "source_url": url,
            "source_name": entry["source_name"],
            "collected_at": collected_at,
            "has_null": has_null
        })
        
    return crawled_data

def evaluate_and_save(data):
    print("\n▶ STEP 3: 수집 결과 검증 및 저장...")
    df = pd.DataFrame(data)
    
    total_count = len(df)
    null_title = df['title'].isna().sum() + (df['title'] == "").sum()
    null_content = df['content'].isna().sum() + (df['content'] == "").sum()
    
    source_counts = df['source_name'].value_counts().to_dict()
    
    print("=" * 50)
    print("             📊 수집 결과 요약             ")
    print("=" * 50)
    print(f"  • 총 수집된 건수   : {total_count}건")
    print(f"  • 제목 결측 건수   : {null_title}건")
    print(f"  • 본문 결측 건수   : {null_content}건")
    print(f"  • 출처(소스)별 건수:")
    for src, count in source_counts.items():
        print(f"    - {src}: {count}건")
    print("=" * 50)
    
    # Hard requirement verification
    if total_count < 200:
        print(f"🚨 [경고] 수집된 데이터가 {total_count}건으로 목표치인 200건 미만입니다.")
        print("대체 소스 수집이 필요한 상황입니다.")
        return False
    else:
        print(f"✔ [성공] 총 {total_count}건 수집을 성공하여 목표(200건 이상)를 완벽히 달성했습니다.")
        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
        print(f"📁 데이터가 성공적으로 저장되었습니다: {CSV_PATH}")
        return True

def main():
    start_time = time.time()
    print("==========================================")
    print("  🚀 IT/정책 뉴스 및 보도자료 크롤러 실행  ")
    print("==========================================\n")
    
    # 1. Fetch RSS feed items
    entries = fetch_rss_entries()
    if not entries:
        print("❌ 수집된 RSS 링크가 전혀 없습니다. 크롤러를 종료합니다.")
        return
        
    # 2. Extract article bodies
    crawled_data = crawl_articles(entries)
    
    # 3. Save & Evaluate
    success = evaluate_and_save(crawled_data)
    
    duration = time.time() - start_time
    print(f"\n⏱ 총 소요 시간: {duration:.2f}초")
    print("==========================================")

if __name__ == "__main__":
    main()
