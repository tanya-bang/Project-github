import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

# ✅ 1. 모델 및 토크나이저 로드
model_path = "../0_model/kcbert_3class_test_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# ✅ 디바이스 설정 (GPU 가능 시 CUDA, 아니면 CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"✅ 모델 실행 디바이스: {device}")

model.eval()

# ✅ 2. 배치 예측 함수
def batch_predict_3class(df, text_column="text", batch_size=64):
    results = {
        "공포 확률": [],
        "중립 확률": [],
        "탐욕 확률": [],
        "공포탐욕지수": []
    }

    model.eval()

    for i in tqdm(range(0, len(df), batch_size)):
        batch_texts = df[text_column].iloc[i:i+batch_size].tolist()

        inputs = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        ).to(model.device)

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)

        results["공포 확률"].extend([round(f, 4) for f in probs[:, 0].tolist()])
        results["중립 확률"].extend([round(n, 4) for n in probs[:, 1].tolist()])
        results["탐욕 확률"].extend([round(g, 4) for g in probs[:, 2].tolist()])
        results["공포탐욕지수"].extend([
            round(float(n) * 50 + float(g) * 100, 2) for n, g in zip(probs[:, 1], probs[:, 2])
        ])


    return pd.DataFrame(results)

# ✅ 3. 실행
if __name__ == "__main__":
    # 전처리된 데이터 로드 (text_bert 포함)
    filtered_df = pd.read_csv("../0_data/1_preprocess/삼성전자_filtered.csv")
    filtered_df = filtered_df[filtered_df["text_bert"].notnull()]
    
    # ✅ 예측 실행 (text_bert 기준)
    pred_df = batch_predict_3class(filtered_df, text_column="text_bert")

    # ✅ 댓글 + 예측 결과 병합
    final_df = pd.concat([
        filtered_df[["text_bert"]].reset_index(drop=True),
        pred_df.reset_index(drop=True)
    ], axis=1)

    # ✅ 저장
    final_df.to_csv("../0_data/3_predict/삼성전자_predict_bert.csv", index=False, encoding="utf-8-sig")
    print("✅ 예측 결과 저장 완료: ../0_data/3_predict/삼성전자_predict_bert.csv")

    # ✅ 상위 5개 확인
    print(final_df.head())
