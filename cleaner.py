import os
import sys
import re
import pandas as pd
from bs4 import BeautifulSoup

# Ensure console output is in UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV_PATH = os.path.join(BASE_DIR, "data", "raw", "crawled_policy_news.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CLEANED_CSV_PATH = os.path.join(PROCESSED_DIR, "cleaned_policy_news.csv")

os.makedirs(PROCESSED_DIR, exist_ok=True)

# Common advertising, copyright, or footer boilerplates to clean from content
BOILERPLATES = [
    r"무단전재\s*및\s*재배포\s*금지",
    r"저작권자\s*ⓒ.*금지",
    r"Copyrights\s*ⓒ.*All\s*rights\s*reserved",
    r"All\s*rights\s*reserved",
    r"이메일\s*무단수집\s*거부",
    r"관련\s*보도자료\s*내용입니다",
    r"자세한\s*내용은\s*첨부파일을\s*참고하시기\s*바랍니다",
    r"\[\s*공유\s*\]"
]

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # 1. Clean HTML tags just in case
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)
    
    # 2. Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # 3. Clean common boilerplates/ad copy
    for pattern in BOILERPLATES:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
    return text.strip()

def main():
    print("==========================================")
    print("        🧹 데이터 정제 작업 시작          ")
    print("==========================================\n")
    
    if not os.path.exists(RAW_CSV_PATH):
        print(f"❌ 원본 데이터 파일이 존재하지 않습니다: {RAW_CSV_PATH}")
        sys.exit(1)
        
    # Read raw data
    df = pd.read_csv(RAW_CSV_PATH, encoding="utf-8")
    initial_rows = len(df)
    print(f"• 불러온 원본 데이터: {initial_rows}건")
    
    # 1. Remove rows with empty/null title or content
    df_cleaned = df.copy()
    
    # Track missing titles and content
    null_titles = df_cleaned['title'].isna() | (df_cleaned['title'].str.strip() == "")
    null_content = df_cleaned['content'].isna() | (df_cleaned['content'].str.strip() == "")
    
    df_cleaned = df_cleaned[~null_titles & ~null_content]
    after_null_removal = len(df_cleaned)
    removed_nulls = initial_rows - after_null_removal
    print(f"• 결측치 제거: {removed_nulls}건 제거 완료 (남은 데이터: {after_null_removal}건)")
    
    # 2. Apply text cleaning (HTML removal, boilerplate removal)
    df_cleaned['title'] = df_cleaned['title'].apply(lambda x: clean_text(x))
    df_cleaned['content'] = df_cleaned['content'].apply(lambda x: clean_text(x))
    
    # 3. Filter out too short contents (e.g. less than 100 characters)
    too_short = df_cleaned['content'].str.len() < 100
    removed_short = too_short.sum()
    df_cleaned = df_cleaned[~too_short]
    after_short_removal = len(df_cleaned)
    print(f"• 너무 짧은 본문 제거 (< 100자): {removed_short}건 제거 완료 (남은 데이터: {after_short_removal}건)")
    
    # 4. Remove duplicate articles (based on title or content)
    duplicate_titles = df_cleaned.duplicated(subset=['title'], keep='first')
    removed_dup_titles = duplicate_titles.sum()
    df_cleaned = df_cleaned[~duplicate_titles]
    
    duplicate_contents = df_cleaned.duplicated(subset=['content'], keep='first')
    removed_dup_contents = duplicate_contents.sum()
    df_cleaned = df_cleaned[~duplicate_contents]
    
    total_duplicates_removed = removed_dup_titles + removed_dup_contents
    final_count = len(df_cleaned)
    
    print(f"• 중복 기사 제거: {total_duplicates_removed}건 제거 완료 (제목 중복 {removed_dup_titles}건, 본문 중복 {removed_dup_contents}건)")
    print(f"• 최종 정제 완료된 데이터: {final_count}건 (남은 데이터: {final_count}건)\n")
    
    # Save cleaned data
    df_cleaned.to_csv(CLEANED_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"📁 정제 완료 파일 저장 성공: {CLEANED_CSV_PATH}")
    print("==========================================")

if __name__ == "__main__":
    main()
