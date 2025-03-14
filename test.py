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
        print("🔹 정렬 상태: 최신순")
    except Exception as e:
        print(f"⚠ 정렬 버튼 클릭 실패: {e}")

# 데이터 저장용 변수
collected_data_index = set()
collected_ids = set()
collected_comments = []

# 기존 ID 로드
def load_existing_ids(file_path="test_comments.csv"):
    global collected_ids
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding="utf-8-sig")

        collected_ids = set(df["post_id"].dropna().astype(str))
        print(f"🔹 기존 post_id 개수: {len(collected_ids)}개 로드 완료!")
    else:
        print("🔹 기존 데이터 없음 (새로 수집 시작)")


# 댓글 수집
def collect_comments():
    global collected_comments, collected_data_index

    try:
        comment_elements = driver.find_elements(By.CSS_SELECTOR, '#stock-content [data-index]')
        print(f'🔍 comment_elements의 길이: {len(comment_elements)}')

        new_comments = 0  

        for comment in comment_elements:
            try:
                data_index = int(comment.get_attribute("data-index"))

                if data_index < 2:
                    continue
                if data_index in collected_data_index:
                    continue

                # ✅ article.comment에서 post_id 가져오기
                try:
                    article = comment.find_element(By.CSS_SELECTOR, "article.comment")
                except:
                    continue

                post_id = article.get_attribute("data-post-anchor-id")

                # ✅ post_id가 None 또는 빈 값이면 건너뛰기
                if not post_id:
                    continue

                # ✅ 중복 방지 (기존 post_id가 있다면 스킵)
                if post_id in collected_ids:
                    print(f"⚠ 중복된 post_id 발견, 스킵: {post_id}")
                    continue

                # ✅ 제목과 본문 가져오기
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

                # ✅ 시간 정보 가져오기
                try:
                    time_element = article.find_element(By.CSS_SELECTOR, "time")
                    timestamp = time_element.get_attribute('datetime')
                except:
                    timestamp = ""

                # ✅ 중복 방지 목록에 추가 (다음 스크롤에서도 중복 방지)
                collected_ids.add(post_id)
                collected_data_index.add(data_index)
                collected_comments.append((post_id, data_index, comment_title, comment_text, timestamp))

                new_comments += 1
                print(f"✅ 수집 완료: post_id={post_id}, index={data_index}")

            except Exception as e:
                print(f"⚠ 댓글 수집 오류: {e}")

        print(f"✅ 현재 화면에서 {new_comments}개 댓글 추가 수집 완료!")
        return new_comments
    except Exception as e:
        print(f"⚠ 댓글 수집 중 오류 발생: {e}")
        return 0


# # 스크롤 및 반복 수집
def scroll_and_collect(repeat_count):
    global collected_data_index

    print("🔹 초기 댓글 수집 시작")
    collect_comments()

    for i in range(repeat_count):
        prev_max_index = max(collected_data_index) if collected_data_index else 0
        print(f"🔽 {i+1}/{repeat_count} 번째 스크롤 진행... (현재 최대 data-index: {prev_max_index})")

        # 스크롤 실행
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 새로운 댓글이 나타날 때까지 기다림
        for _ in range(5):  # 5초 동안 반복 확인
            new_comments = collect_comments()
            if new_comments > 0:
                break
            time.sleep(1)

        if new_comments == 0:
            print("🚨 새로운 댓글이 나타나지 않음. 스크롤 중단.")
            break  # 더 이상 새로운 댓글이 없으면 스크롤 중단

    print("✅ 스크롤 및 댓글 수집 완료!")


# 데이터 저장
def save_comments(file_path="test_comments.csv"):
    if not collected_comments:
        print("⚠ 저장할 새 댓글 없음")
        return

    df_new = pd.DataFrame(collected_comments, columns=["post_id", "data_index", "title", "comment", "timestamp"])

    # ✅ 기존 파일이 있으면 기존 데이터 로드 후 중복 제거
    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path, encoding="utf-8-sig")
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["post_id"], keep="first")  # ✅ 중복 제거
        df_combined.to_csv(file_path, index=False, encoding="utf-8-sig")
    else:
        df_new.to_csv(file_path, index=False, encoding="utf-8-sig")

    print(f"✅ 저장 완료! (최종 저장된 댓글 개수: {len(df_new)}개)")
    collected_comments.clear()

# 실행 함수
def run_scraper(repeat_count=5, file_path="test_comments.csv"):
    load_existing_ids(file_path)
    scroll_and_collect(repeat_count)
    save_comments(file_path)

# # 실행
setting()
sorting()
run_scraper(repeat_count=5, file_path="test_comments.csv")


