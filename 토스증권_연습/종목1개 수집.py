import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import os

# 웹드라이버 설정
def setting():
    global driver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://tossinvest.com/stocks/A005930/community")
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
    except Exception as e:
        print(f"soting 과정 오류 발생: {e}")


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
                # data_index 2이후 부터 수집, 중복 index 수집 X
                if data_index < 2:
                    continue
                if data_index in collected_data_index:
                    continue

                # post_id 가져오기
                try:
                    article = comment.find_element(By.CSS_SELECTOR, "article.comment")
                    post_id = str(article.get_attribute("data-post-anchor-id"))
                except:
                    continue
                
                if post_id in collected_ids: # post_id 중복 확인
                    continue

                # 댓글 제목, 내용, 작성 시간 수집
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

                # 중복 방지 목록에 추가 (다음 스크롤에서도 중복 방지)
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
        
        # 스크롤 실행
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 새로운 댓글 로딩 대기
        WebDriverWait(driver, 10).until(
            lambda d: any(int(el.get_attribute("data-index")) > prev_max_index
                         for el in d.find_elements(By.CSS_SELECTOR, "[data-index]")))
        new_comments = collect_comments(driver)
        


# 데이터 저장
def save_comments(file_path):
    if not collected_comments:
        print("저장할 새 댓글 없음")
        return

    df_new = pd.DataFrame(collected_comments, columns=["post_id", "data_index", "title", "comment", "timestamp"])
    df_new["post_id"] = df_new["post_id"].astype(str)
    df_new["platform"] = "토스증권"
    df_new["stock_name"] = "삼성전자" #추후 url list에 따라 for문으로 링크에 따라 순차적으로 종목명 선택하여 저장
    df_new = df_new[["platform", "stock_name", "timestamp", "post_id", "data_index", "title", "comment"]]


    # 기존 파일이 있으면 기존 데이터 로드 후 중복 제거
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
def run_scraper(repeat_count, file_path):
    load_existing_ids(file_path)
    scroll_and_collect(driver, repeat_count)
    save_comments(file_path)


# 실행
setting()
sorting()
run_scraper(repeat_count=5, file_path="test_comments_2.csv")
driver.quit()


