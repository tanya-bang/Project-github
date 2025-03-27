import requests
import time
import csv
from datetime import datetime
from datetime import datetime, date


# 요청할 URL
url = "https://wts-cert-api.tossinvest.com/api/v3/comments"

# 종목명 변수화
stock_name = "애플"

# 요청 헤더 (쿠키와 XSRF 토큰은 그때그때마다 변경 필요)
headers = {
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko,en-US;q=0.9,en;q=0.8",
    "app-version": "2025-03-19 16:20:12",
    "browser-tab-id": "browser-tab-de1a0d07c24449f2ba4fdad4975d7d62",
    "content-type": "application/json",
    "origin": "https://tossinvest.com",
    "referer": "https://tossinvest.com/stocks/US19801212001/community",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-xsrf-token": "359f6ce0-5793-4a04-95d7-02cf9881919a",
    "cookie": "deviceId=WTS-7b52e417e49e4530b9945b6f0b34c6d0; _ga=GA1.1.757933857.1741746259; x-toss-distribution-id=53; XSRF-TOKEN=359f6ce0-5793-4a04-95d7-02cf9881919a; _browserId=d50c413bcef94076850bbb260218dca3; BTK=Tt1v1mRRkk6lzkm3tmnA5EN2yr1ePUyRI3b6k75cbQ4=; SESSION=OTBiN2Y1OTAtMGMzYi00OTMzLThkMTQtNDVhZmI0NmIwZjAw; _ga_T5907TQ00C=GS1.1.1743037968.13.1.1743037993.0.0.0"
}


# 수집할 날짜 범위 (YYYY-MM-DD)
start_date = "2023-03-27"
end_date = date.today().strftime("%Y-%m-%d")  # 오늘 날짜로 고정

# 파일명
csv_filename = "apple_comments.csv"
cache_filename = "cache_apple_comments.csv"

# 애플
data = {
    "subjectId": "US19801212001",
    "subjectType": "STOCK",
    "commentSortType": "RECENT"
}

# 전체 댓글 저장 리스트
all_comments = []
previous_count = 0

# 날짜 비교 함수
def is_within_date_range(comment_date):
    comment_datetime = datetime.strptime(comment_date[:10], "%Y-%m-%d")
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    return start_datetime <= comment_datetime <= end_datetime

# 캐시 저장 함수
def save_cache(file_path, data):
    with open(file_path, "w", newline="", encoding="utf-8") as cache_file:
        writer = csv.writer(cache_file)
        writer.writerow(["Comment ID", "Message", "Updated At", "Nickname", "Platform", "Stock Name"])
        writer.writerows(data)
    print(f"📝 임시 캐시 저장: {len(data)}개 → {file_path}")
last_seen_id = None  # 마지막 댓글 ID 저장

page_count = 0       # 페이지 수 카운터 추가

while True:
    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 요청 실패: {response.status_code}, {response.text}")
        break

    json_data = response.json()
    comments = json_data.get("result", {}).get("comments", {}).get("body", [])
    has_next = json_data.get("result", {}).get("comments", {}).get("hasNext", False)

    if not comments:
        print("\n🚀 더 이상 댓글이 없으므로 수집을 종료합니다.")
        break

    # 마지막 댓글 날짜가 수집 범위 밖이면 종료
    last_comment_date = comments[-1]["updatedAt"]
    if not is_within_date_range(last_comment_date):
        print(f"\n🛑 마지막 댓글 날짜({last_comment_date})가 범위 밖이므로 종료합니다.")
        break
    
    page_count += 1  # 🔹 페이지 수 증가

    # 중간 요약 로그 출력 (10의 배수일 때만)
    if page_count % 10 == 0:
        print(f"🌀 {page_count}페이지 수집 중... 누적 댓글 수: {len(all_comments)}")

    # 가장 마지막 댓글 ID 추출
    current_last_id = comments[-1]["id"]

    # 이전에 봤던 ID와 동일하면 종료
    if current_last_id == last_seen_id:
        print("\n🚀 더 이상 새로운 댓글이 없어 수집을 종료합니다.")
        break

    last_seen_id = current_last_id

    new_comments = 0
    for comment in comments:
        comment_date = comment["updatedAt"]
        if is_within_date_range(comment_date):
            all_comments.append([
                comment["id"],
                comment["message"],
                comment_date,
                comment["author"]["nickname"],
                "toss",
                stock_name
            ])
            new_comments += 1

    current_count = len(all_comments)
    #print(f"✅ 수집된 댓글 개수: {current_count} (이번 페이지 신규: {new_comments})")

    if current_count - previous_count >= 100:
        save_cache(cache_filename, all_comments)
        previous_count = current_count

    data["commentId"] = current_last_id
    time.sleep(1)

# 최종 저장
with open(csv_filename, "w", newline="", encoding="utf-8") as final_file:
    writer = csv.writer(final_file)
    writer.writerow(["Comment ID", "Message", "Updated At", "Nickname", "Platform", "Stock Name"])
    writer.writerows(all_comments)

print(f"\n🎉 최종적으로 {len(all_comments)}개의 댓글이 {csv_filename} 파일에 저장되었습니다!")
