import requests
import pandas as pd
import os
from datetime import datetime, timedelta

# 저장 폴더 설정
SAVE_PATH = "./data/"
os.makedirs(SAVE_PATH, exist_ok=True)

# 네이버 증권 종목토론 API 기본 URL
DISCUSS_URL = "https://m.stock.naver.com/front-api/discuss"

# HTTP 요청 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# 크롤링할 종목 리스트 및 discussionType(global/local) 구분
stocks = {
    "NVDA.O": {"name": "엔비디아", "type": "globalStock"},
    "000660": {"name": "SK하이닉스", "type": "localStock"},
    "TSLA.O": {"name": "테슬라", "type": "globalStock"},
    "005930": {"name": "삼성전자", "type": "localStock"},
    "068270": {"name": "셀트리온", "type": "localStock"},
    
}

def load_existing_post_ids(stock_code):
    """ 기존 CSV 파일에서 저장된 post_id 목록을 불러오는 함수 """
    stock_name = stocks[stock_code]["name"]
    file_path = os.path.join(SAVE_PATH, f"naver_{stock_name}.csv")

    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path, usecols=["post_id"], dtype={"post_id": str}, encoding="utf-8-sig")
        return set(df_existing["post_id"])  # 중복 검사 최적화
    return set()

def request_discussions(stock_code, discussion_type, rsno=None):
    """ API 요청을 보내고 데이터를 가져오는 함수 """
    params = {
        "discussionType": discussion_type,
        "itemCode": stock_code,
        "size": 20,  # 최신 20개 댓글 가져옴
    }
    if rsno:
        params["rsno"] = rsno  # 이전 댓글 기준으로 다음 데이터를 요청

    response = requests.get(DISCUSS_URL, params=params, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ 요청 실패! 상태 코드: {response.status_code}")
        return []

    data = response.json()
    if not data.get("isSuccess"):
        print("❌ API 응답 오류 발생")
        return []

    return data.get("result", [])

def process_discussions(results, start_datetime, end_datetime, existing_post_ids):
    """ API 응답 데이터를 필터링하여 리스트로 변환하는 함수 """
    discussions = []
    last_rsno = None
    stop_collection = False  # ✅ 중지 조건을 확인하는 변수

    for post in results:
        post_date = datetime.strptime(post.get("date"), "%Y-%m-%d %H:%M:%S.%f")
        post_id = str(post.get("discussionId"))

        # ✅ 지정된 시간 이전 데이터가 나오면 중지 플래그 설정
        if post_date < start_datetime:
            print(f"⏹️ 지정된 시간 이전 데이터 발견, 수집 중지 ({post_date})")
            stop_collection = True
            break

        # ✅ 이미 수집된 데이터가 나오면 중지 플래그 설정
        if post_id in existing_post_ids:
            print(f"🔴 기존 데이터({post_id}) 발견, 수집 중지")
            stop_collection = True
            break

        # ✅ 리스트에 데이터 추가 (즉시 저장 X)
        discussions.append({
            "platform": "네이버증권",
            "stock_name": stocks[post["itemCode"]]["name"],
            "post_id": post_id,
            "title": post.get("title"),
            "content": post.get("contents"),
            "timestamp": post.get("date")
        })

        last_rsno = post.get("rsno")  # 가장 오래된 글의 rsno 저장

    return discussions, last_rsno, stop_collection

def save_to_csv(stock_code, discussions):
    """ 리스트 데이터를 한꺼번에 저장하는 함수 """
    stock_name = stocks[stock_code]["name"]
    file_path = os.path.join(SAVE_PATH, f"naver_{stock_name}.csv")

    # 리스트를 데이터프레임으로 변환
    df = pd.DataFrame(discussions, columns=["platform", "stock_name", "post_id", "title", "content", "timestamp"])
    df = df.sort_values(by="timestamp", ascending=True)

    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path, dtype={"post_id": str}, encoding="utf-8-sig")
        combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=["post_id"]).sort_values(by="timestamp")
    else:
        combined_df = df

    combined_df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ {stock_name} 데이터 저장 완료: {file_path}")

def fetch_and_save_discussions(stock_code, discussion_type, start_datetime, end_datetime):
    """ 특정 종목의 댓글을 수집하고 저장하는 함수 """
    existing_post_ids = load_existing_post_ids(stock_code)
    rsno = None  
    all_discussions = []  # ✅ 데이터를 모아두는 리스트

    while True:
        results = request_discussions(stock_code, discussion_type, rsno)
        if not results:
            print(f"✅ 더 이상 가져올 글이 없습니다. ({stock_code})")
            break

        discussions, rsno, stop_collection = process_discussions(results, start_datetime, end_datetime, existing_post_ids)

        if discussions:
            all_discussions.extend(discussions)  # ✅ 리스트에 데이터 추가

        if stop_collection:  # ✅ 중지 조건을 만족하면 즉시 종료
            break

    if all_discussions:
        save_to_csv(stock_code, all_discussions)  # ✅ 한 번에 저장

def collect_and_save_all_discussions(hours_ago):
    """ 전체 종목에 대해 댓글을 수집하고 저장하는 함수 """
    start_datetime = datetime.now() - timedelta(hours=hours_ago)
    end_datetime = datetime.now()

    for stock_code, info in stocks.items():
        print(f"🔍 {info['name']}({stock_code}) 데이터 수집 중...")
        fetch_and_save_discussions(stock_code, info["type"], start_datetime, end_datetime)

# ✅ 실행
collect_and_save_all_discussions(hours_ago=72)
