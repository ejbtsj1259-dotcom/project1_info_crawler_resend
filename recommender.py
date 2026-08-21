import os
import sys
import pandas as pd

# Ensure console output is in UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "cleaned_policy_news.csv")
RECOMMENDED_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "recommended_policy_news.csv")

# Recommendations keyword criteria
TECH_KEYWORDS = {
    "AI / 생성형 AI": ["AI", "인공지능", "생성형", "GPT", "LLM", "머신러닝", "딥러닝", "거대언어", "대화형"],
    "자동화": ["자동화", "로봇", "RPA", "매크로", "업무자동화"],
    "클라우드": ["클라우드", "SaaS", "PaaS", "IaaS", "AWS", "애저"],
    "데이터": ["데이터", "빅데이터", "데이터베이스", "가명정보", "마이데이터"],
    "보안": ["보안", "랜섬웨어", "해킹", "시큐리티", "해커", "악성코드", "침해"],
    "디지털 전환": ["디지털 전환", "디지털 혁신", "DX", "DT", "디지털 플랫폼", "디지털전환", "디지털혁신"]
}

def calculate_score(row):
    title = str(row['title']).lower()
    content = str(row['content']).lower()
    
    score = 0
    matched_categories = set()
    
    for category, kws in TECH_KEYWORDS.items():
        cat_matched = False
        for kw in kws:
            kw_lower = kw.lower()
            # Title occurrences (Weighted 10x)
            title_matches = title.count(kw_lower)
            if title_matches > 0:
                score += title_matches * 10
                cat_matched = True
                
            # Content occurrences (Weighted 1x)
            content_matches = content.count(kw_lower)
            if content_matches > 0:
                score += content_matches * 1
                cat_matched = True
                
        if cat_matched:
            matched_categories.add(category)
            
    return score, ", ".join(matched_categories)

def main():
    print("==========================================")
    print("        🚀 기사 추천 알고리즘 시작        ")
    print("==========================================\n")
    
    if not os.path.exists(CLEANED_CSV_PATH):
        print(f"❌ 정제 데이터 파일이 존재하지 않습니다: {CLEANED_CSV_PATH}")
        sys.exit(1)
        
    df = pd.read_csv(CLEANED_CSV_PATH, encoding="utf-8")
    
    # Calculate score and matching categories for each article
    scores_categories = df.apply(calculate_score, axis=1)
    df['recommend_score'] = [sc[0] for sc in scores_categories]
    df['matched_categories'] = [sc[1] for sc in scores_categories]
    
    # Sort by recommendation score (descending) and date (newer first)
    df_sorted = df.sort_values(by=['recommend_score', 'date'], ascending=[False, False])
    
    # Extract top 20 recommendations
    top_20 = df_sorted.head(20).copy()
    
    # Print Top 5 Recommended Articles for evaluation
    print("🏆 추천 상위 5건 목록:")
    print("-" * 80)
    for idx, (_, row) in enumerate(top_20.head(5).iterrows(), 1):
        print(f"  {idx}등. 점수: {row['recommend_score']}점 | 출처: {row['source_name']}")
        print(f"     제목: {row['title']}")
        print(f"     매칭 테마: {row['matched_categories']}")
        print("-" * 80)
        
    # Save recommended articles to CSV
    top_20.to_csv(RECOMMENDED_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"\n📁 추천 상위 20건 저장 완료: {RECOMMENDED_CSV_PATH}")
    print("==========================================")

if __name__ == "__main__":
    main()
