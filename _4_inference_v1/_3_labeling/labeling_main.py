import pandas as pd
from sklearn.model_selection import train_test_split
from _0_infra.hdfs_client import get_client
from _4_inference_v1._3_labeling.common_labeling import label_dataframe
import os

# 환경변수에서 종목명 받아오기
stock_name = os.environ.get("STOCK_NAME")
client = get_client()

# HDFS 경로
input_path = f"/project-root/data/_1_preprocess/{stock_name}_filtered.csv"
fear_path = f"/project-root/data/_0_raw/fear_keywords.txt"
greed_path = f"/project-root/data/_0_raw/greed_keywords.txt"

labeled_output_path = f"/project-root/data/_2_labeling/{stock_name}_labeled_3class.csv"
train_output_path = f"/project-root/data/_2_labeling/{stock_name}_train_3class.csv"
valid_output_path = f"/project-root/data/_2_labeling/{stock_name}_valid_3class.csv"

# HDFS → Pandas
with client.read(input_path, encoding="utf-8-sig") as reader:
    df = pd.read_csv(
        reader,
        quotechar='"',
        escapechar='\\',
        doublequote=True,
        sep=',',
        encoding="utf-8-sig",
        engine='python',  # ← 핵심
        on_bad_lines='skip'  # ← 문제 줄 무시
    )

# 라벨링
labeled_df = label_dataframe(df, fear_path, greed_path)

# 전체 라벨링 결과 저장
with client.write(labeled_output_path, encoding="utf-8-sig", overwrite=True) as writer:
    labeled_df.to_csv(writer, index=False)

# 라벨 분포 확인
print("✅ 전체 라벨 분포 (0=공포, 1=중립, 2=탐욕):")
print(labeled_df["label"].value_counts().sort_index())

# train/valid 분리
train_df, valid_df = train_test_split(
    labeled_df, test_size=0.2, stratify=labeled_df["label"], random_state=42
)

# Pandas → HDFS
with client.write(train_output_path, encoding="utf-8-sig", overwrite=True) as writer:
    train_df.to_csv(writer, index=False)

with client.write(valid_output_path, encoding="utf-8-sig", overwrite=True) as writer:
    valid_df.to_csv(writer, index=False)

print(f"✅ {stock_name} 라벨링 완료! (train: {len(train_df)}, valid: {len(valid_df)})")
