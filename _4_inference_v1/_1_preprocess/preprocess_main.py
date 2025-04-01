import pandas as pd
import csv
from _0_infra.hdfs_client import get_client
from _4_inference_v1._1_preprocess.common_preprocess import preprocess_comments
import os

stock_name = os.environ.get("STOCK_NAME")

# HDFS 클라이언트 생성
client = get_client()

# 경로 설정
hdfs_input_path = f"/project-root/data/_0_raw/{stock_name}_comments.csv"
hdfs_output_path = f"/project-root/data/_1_preprocess/{stock_name}_filtered.csv"

# HDFS → Pandas
with client.read(hdfs_input_path, encoding="utf-8-sig") as reader:
    df = pd.read_csv(reader)

# 전처리
filtered_df = preprocess_comments(
    df,
    political_path="/project-root/data/_0_raw/political_keywords.txt",
    text="Message",
    timestamp="Updated At"
)
filtered_df = filtered_df.drop_duplicates(subset=["Message"])

# Pandas → HDFS / csv파싱문제
with client.write(hdfs_output_path, encoding="utf-8-sig", overwrite=True) as writer:
    filtered_df.to_csv(
        writer,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_ALL,
        escapechar='\\'
    )

print(f"✅ {stock_name} 전처리 완료! 남은 댓글 수: {len(filtered_df)}")


# 터미널 실행 명령어
"""
for stock in samsung skhynix apple nvidia
do
    PYTHONPATH=/root/sentix_project_root \
    STOCK_NAME=$stock \
    python /root/sentix_project_root/_4_inference_v1/_1_preprocess/preprocess_main.py
done
"""