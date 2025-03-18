import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os

# 수집할 주식 종목
stocks = {
    '096770': 'SK이노베이션',
    '005490': 'POSCO',
    '000720': '현대건설',
    '005380': '현대차',
    '271560': '오리온',
    '207940': '삼성바이오로직스',
    '105560': 'KB금융',
    '005930': '삼성전자',
    '035420': 'NAVER',
    '015760': '한국전력'}

# 웹드라이버 설정
def setting(stock_code):
    global driver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    url = f"https://tossinvest.com/stocks/A{stock_code}/community"
    driver.get(url)
    time.sleep(5)  # 페이지 로딩 대기

# 정렬을 최신순으로 변경
def sorting():
    try:
        sort_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'section._1m9brd0 > button'))
        )
        if sort_button.text.strip() == "인기순":
            sort_button.click()
            time.sleep(2)  # 정렬 변경 반영 대기
        else:
            pass
    except Exception as e:
        print(f"sorting 과정 오류 발생: {e}")

# 데이터 저장용 변수
collected_data_index = set()
collected_ids = set()
collected_comments = []

# 기존 ID 로드
def load_existing_ids(file_path):
    global collected_ids
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, encoding="utf-8-sig")
            collected_ids = set(df["post_id"].astype(str))
    except:
        pass

# 댓글 수집
def collect_comments(driver):
    global collected_comments, collected_data_index
    new_comments = 0

    try:
        comment_elements = driver.find_elements(By.CSS_SELECTOR, '#stock-content [data-index]')

        for comment in comment_elements:
            try:
                data_index = int(comment.get_attribute("data-index"))
                if data_index < 2:
                    continue
                if data_index in collected_data_index:
                    continue

                try:
                    article = comment.find_element(By.CSS_SELECTOR, "article.comment")
                    post_id = str(article.get_attribute("data-post-anchor-id"))
                except:
                    continue
                
                if post_id in collected_ids:
                    continue

                try:
                    title_element = article.find_element(By.CSS_SELECTOR, "span._1sihfl60")
                    comment_title = title_element.text.strip()
                except:
                    comment_title = ""

                try:
                    text_element = article.find_element(By.CSS_SELECTOR, "span._60z0ev1")
                    comment_text = text_element.text.strip()
                except:
                    comment_text = ""

                try:
                    time_element = article.find_element(By.CSS_SELECTOR, "time")
                    timestamp = time_element.get_attribute('datetime')
                except:
                    timestamp = ""

                collected_ids.add(post_id)
                collected_data_index.add(data_index)
                collected_comments.append((post_id, data_index, comment_title, comment_text, timestamp))
                new_comments += 1

            except Exception as e:
                print(f"댓글 수집 중 오류 발생: {e}")

    except Exception as e:
        print(f"댓글 수집 중 오류 발생: {e}")

    return new_comments

# 스크롤 및 반복 수집
def scroll_and_collect(driver, repeat_count):
    global collected_data_index
    
    new_comments = collect_comments(driver)

    for i in range(repeat_count):
        if new_comments == 0:
            break

        prev_max_index = max(collected_data_index) if collected_data_index else 0
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            lambda d: any(int(el.get_attribute("data-index")) > prev_max_index
                         for el in d.find_elements(By.CSS_SELECTOR, "[data-index]"))
        )
        new_comments = collect_comments(driver)

# 데이터 저장
def save_comments(stock_code):
    if not collected_comments:
        print(f"{stocks[stock_code]}: 저장할 새 댓글 없음")
        return

    df_new = pd.DataFrame(collected_comments, columns=["post_id", "data_index", "title", "comment", "timestamp"])
    df_new["post_id"] = df_new["post_id"].astype(str)
    df_new["platform"] = "토스증권"
    df_new["stock_name"] = stocks[stock_code]
    df_new = df_new[["platform", "stock_name", "timestamp", "post_id", "data_index", "title", "comment"]]
    file_path = f"{stocks[stock_code]}.csv"

    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path, encoding="utf-8-sig")
        df_existing["post_id"] = df_existing["post_id"].astype(str) 
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["post_id"], keep="first")
        df_combined.to_csv(file_path, index=False, encoding="utf-8-sig")
    else:
        df_new.to_csv(file_path, index=False, encoding="utf-8-sig")

    collected_comments.clear()

# 실행 함수
def run_scraper(repeat_count):
    for stock_code in stocks.keys():
        try:
            print(f"{stocks[stock_code]}({stock_code}) 데이터 수집 시작...")
            # 종목마다 수집 리스트 초기화
            global collected_comments, collected_ids, collected_data_index
            collected_comments = []
            collected_ids = set()
            collected_data_index = set()
            
            file_path = f"{stocks[stock_code]}.csv"
            load_existing_ids(file_path)
            setting(stock_code)
            sorting()
            scroll_and_collect(driver, repeat_count)
            save_comments(stock_code)
        except Exception as e:
            print(f"{stocks[stock_code]}({stock_code}) 크롤링 중 오류 발생: {e}")
        finally:
            driver.quit()
            time.sleep(1)  # 다음 종목 수집 전 대기
    print("모든 종목 데이터 수집 완료!")

# 실행
run_scraper(repeat_count=3)
