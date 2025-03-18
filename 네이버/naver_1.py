import pandas as pd
import time
import re
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os


# 수집시간 (3/17 오전09시 이전 작성 댓글은 수집 X)
stocks = {'096770':'SK이노베이션'}
until_when = datetime(2025, 3, 17, 14, 9, 0, tzinfo=timezone(timedelta(hours=9)))

def setting():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def title_list(driver, stock_code, current_page):
    url = f"https://finance.naver.com/item/board.naver?code={stock_code}&page={current_page}"
    driver.get(url)
    time.sleep(3)
    
    rows = driver.find_elements(By.CSS_SELECTOR, 'table.type2 > tbody > tr')
    page_data = []
   
    # 게시글 목록 수집
    for row in rows:
        try:
            timestamp_text = row.find_element(By.CSS_SELECTOR, 'td > span.tah.p10.gray03').text.strip()
            timestamp = datetime.strptime(timestamp_text, '%Y.%m.%d %H:%M')
            timestamp = timestamp.replace(tzinfo=timezone(timedelta(hours=9)))
            
            title_tag = row.find_element(By.CSS_SELECTOR, 'td.title > a')
            title = title_tag.text.strip()
            post_url = title_tag.get_attribute('href')
            post_id = re.search(r'nid=(\d+)', post_url).group(1)
            page_data.append({
                'timestamp': timestamp,
                'title': title,
                'post_url': post_url,
                'post_id': post_id
            })
        except Exception as e:
            print(f"게시글 타이틀 수집 중 오류: {e}")
            continue
    return page_data

# 게시글 상세 내용 크롤링 함수
def post_content(driver, post_url):
    driver.get(post_url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#body")))
        content = driver.find_element(By.CSS_SELECTOR, 'div#body').text.strip()
        return content
    except Exception as e:
        print(f"게시글 내용 수집 중 오류: {e}")
        return ""


# 페이지 전환 함수
def go_to_next_page(driver, current_page):
    # 페이지가 10의 배수일 경우 '다음' 버튼 클릭
    if current_page % 10 == 0:
        try:
            next_button = driver.find_element(By.LINK_TEXT, '다음')
            next_button.click()
            return current_page + 10
        except:
            return None  # 더 이상 다음 페이지가 없으면 None 리턴
    else:
        # 현재 페이지 번호를 클릭하여 다음 페이지로 이동
        try:
            next_page_button = driver.find_element(By.LINK_TEXT, str(current_page + 1))
            next_page_button.click()
            return current_page + 1
        except:
            return None   
    
def crawl_and_save(driver, stock_code, until_when):
    current_page = 1
    all_data = []
    
    while True:
        print(f"Fetching page {current_page}...")
        page_data = title_list(driver, stock_code, current_page)
        
        # 각 게시글에 대한 상세 내용 크롤링
        for data in page_data:
            if data['timestamp'] >= until_when:
                content = post_content(driver, data['post_url'])
                all_data.append({
                    'platform': '네이버증권',
                    'stock_name': stocks.get(stock_code, 'Unknown'),
                    'timestamp': data['timestamp'].strftime('%Y-%m-%dT%H:%M:%S+09:00'),
                    'post_id': data['post_id'],
                    'title': data['title'],
                    'content': content
                })
            else:
                continue
        
        # 페이지 전환
        current_page = go_to_next_page(driver, current_page)
        if not current_page:
            break  # 더 이상 페이지가 없으면 종료
    
    return all_data
    
# 실행 함수
def main(stock_code, until_when):
    driver = setting()
    data = crawl_and_save(driver, stock_code, until_when)
    
    # DataFrame으로 저장
    df = pd.DataFrame(data)
    print(df.head())
    
    # CSV로 저장 (원하는 경우)
    df.to_csv(f"naver_{stocks[stock_code]}.csv", index=False)

main(list(stocks.keys())[0], until_when)
