import pandas as pd
from _0_infra.util import load_keyword_file

def weak_label_by_count(text: str, fear_keywords: set, greed_keywords: set) -> int:
    text = str(text)
    fear_count = sum(1 for word in fear_keywords if word in text)
    greed_count = sum(1 for word in greed_keywords if word in text)

    if fear_count > greed_count:
        return 0  # 공포
    elif greed_count > fear_count:
        return 2  # 탐욕
    else:
        return 1  # 중립

def label_dataframe(df: pd.DataFrame, fear_path: str, greed_path: str) -> pd.DataFrame:
    df = df.copy()

    fear_keywords = load_keyword_file(fear_path, as_set=True)
    greed_keywords = load_keyword_file(greed_path, as_set=True)

    df["label"] = df["text_tfidf"].apply(
        lambda x: weak_label_by_count(x, fear_keywords, greed_keywords)
    )

    return df
