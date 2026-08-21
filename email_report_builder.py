import os
import sys
import datetime
import pandas as pd

# Ensure console output is in UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOMMENDED_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "recommended_policy_news.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
HTML_OUT_PATH = os.path.join(REPORTS_DIR, "email_preview.html")
TXT_OUT_PATH = os.path.join(REPORTS_DIR, "email_preview.txt")

os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_html_report(df):
    items_html = []
    
    for idx, row in df.iterrows():
        # Clean matched categories
        categories = str(row['matched_categories']) if pd.notna(row['matched_categories']) and row['matched_categories'] != "" else "일반 IT"
        cat_badges = "".join([f'<span class="badge badge-tech">{cat.strip()}</span>' for cat in categories.split(",")])
        
        # Crop summary if too long
        summary = str(row['summary']) if pd.notna(row['summary']) else "상세보기 링크를 통해 전체 내용을 확인하실 수 있습니다."
        if len(summary) > 200:
            summary = summary[:200] + "..."
            
        item_template = f"""
        <div class="news-card">
            <div class="card-header">
                <span class="rank-num">#{idx + 1}</span>
                <span class="score-badge">🔥 {row['recommend_score']}점</span>
                <span class="source-tag">{row['source_name']}</span>
                <span class="date-tag">{row['date']}</span>
            </div>
            <h3 class="news-title">
                <a href="{row['source_url']}" target="_blank">{row['title']}</a>
            </h3>
            <p class="news-summary">{summary}</p>
            <div class="card-footer">
                <div class="category-list">
                    {cat_badges}
                </div>
                <a href="{row['source_url']}" class="btn-link" target="_blank">본문 바로가기 ↗</a>
            </div>
        </div>
        """
        items_html.append(item_template)
        
    all_cards_html = "\n".join(items_html)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT 및 과학 정책 뉴스 일간 추천 리포트</title>
    <style>
        body {{
            font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
            background-color: #f4f6f9;
            color: #1e293b;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 680px;
            margin: 30px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .hero {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: #ffffff;
            padding: 40px 30px;
            text-align: center;
        }}
        .hero h1 {{
            margin: 0;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .hero p {{
            margin: 10px 0 0 0;
            font-size: 15px;
            opacity: 0.9;
        }}
        .meta-info {{
            background-color: #f8fafc;
            padding: 15px 30px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 13px;
            color: #64748b;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .content {{
            padding: 30px;
        }}
        .news-card {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 22px;
            margin-bottom: 24px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .news-card:hover {{
            box-shadow: 0 6px 12px rgba(0,0,0,0.04);
            border-color: #cbd5e1;
        }}
        .card-header {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
            font-size: 12px;
        }}
        .rank-num {{
            background-color: #1e293b;
            color: #ffffff;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .score-badge {{
            background-color: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .source-tag {{
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .date-tag {{
            color: #94a3b8;
            margin-left: auto;
        }}
        .news-title {{
            margin: 0 0 10px 0;
            font-size: 18px;
            font-weight: 600;
            line-height: 1.4;
        }}
        .news-title a {{
            color: #1e3a8a;
            text-decoration: none;
        }}
        .news-title a:hover {{
            color: #2563eb;
            text-decoration: underline;
        }}
        .news-summary {{
            margin: 0 0 16px 0;
            font-size: 14px;
            color: #475569;
            text-align: justify;
        }}
        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px dashed #e2e8f0;
            padding-top: 12px;
        }}
        .category-list {{
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }}
        .badge {{
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .badge-tech {{
            background-color: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
        }}
        .btn-link {{
            color: #2563eb;
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
        }}
        .btn-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            background-color: #1e293b;
            color: #94a3b8;
            padding: 30px;
            text-align: center;
            font-size: 12px;
            border-top: 1px solid #334155;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .footer a {{
            color: #3b82f6;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Hero Section -->
        <div class="hero">
            <h1>🚀 IT & 과학 정책 뉴스 추천 리포트</h1>
            <p>오늘 수집된 과기정통부, KISA, 전자신문 기사 중 추천 지수가 가장 높은 뉴스들입니다.</p>
        </div>
        
        <!-- Metadata -->
        <div class="meta-info">
            <span>발송 모드: <strong>미리보기(Preview) 모드</strong></span>
            <span>수집 일시: <strong>{datetime.datetime.now().year}년 {datetime.datetime.now().month}월 {datetime.datetime.now().day}일</strong></span>
        </div>
        
        <!-- News List Content -->
        <div class="content">
            {all_cards_html}
        </div>
        
        <!-- Email Footer -->
        <div class="footer">
            <p>본 메일은 수강생 전용 프로젝트 실습을 위한 <strong>일간 자동 뉴스 요약 리포트</strong>입니다.</p>
            <p>수집 출처: 과학기술정보통신부, 한국인터넷진흥원(KISA), 전자신문</p>
            <p>© 2026 IT 뉴스 큐레이터 프로젝트. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content

def generate_txt_report(df):
    lines = []
    lines.append("=" * 70)
    lines.append(" 🚀 IT & 과학 정책 뉴스 일간 추천 리포트 (Plain Text)")
    lines.append(f" 발송 모드: 미리보기 (Preview)")
    lines.append(f" 생성 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    lines.append("")
    
    for idx, row in df.iterrows():
        summary = str(row['summary']) if pd.notna(row['summary']) else "본문 바로가기를 참조해주세요."
        if len(summary) > 150:
            summary = summary[:150] + "..."
            
        lines.append(f"[{idx + 1}등] {row['title']} (추천 점수: {row['recommend_score']}점)")
        lines.append(f"  • 출처: {row['source_name']} | 발행일: {row['date']}")
        lines.append(f"  • 매칭 카테고리: {row['matched_categories']}")
        lines.append(f"  • 요약: {summary}")
        lines.append(f"  • 원본 링크: {row['source_url']}")
        lines.append("-" * 70)
        lines.append("")
        
    lines.append("본 메일은 수강생 실습 프로젝트용 자동 요약 뉴스 메일입니다.")
    return "\n".join(lines)

def main():
    print("==========================================")
    print("        📧 이메일 리포트 미리보기 생성      ")
    print("==========================================\n")
    
    if not os.path.exists(RECOMMENDED_CSV_PATH):
        print(f"❌ 추천 데이터가 존재하지 않습니다: {RECOMMENDED_CSV_PATH}")
        print("recommender.py를 먼저 실행해 주세요.")
        sys.exit(1)
        
    df = pd.read_csv(RECOMMENDED_CSV_PATH, encoding="utf-8")
    print(f"• 불러온 추천 뉴스 기사: {len(df)}건")
    
    # Generate HTML content
    html_content = generate_html_report(df)
    with open(HTML_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✔ HTML 미리보기 생성 성공: {HTML_OUT_PATH}")
    
    # Generate Plain Text content
    txt_content = generate_txt_report(df)
    with open(TXT_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(txt_content)
    print(f"✔ 텍스트 미리보기 생성 성공: {TXT_OUT_PATH}\n")
    
    print("✨ 이메일 미리보기 생성이 모두 성공적으로 완료되었습니다!")
    print("reports 폴더 내의 파일들을 브라우저와 텍스트 에디터로 각각 열어보실 수 있습니다.")
    print("==========================================")

if __name__ == "__main__":
    main()
