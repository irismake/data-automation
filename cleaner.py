import pandas as pd

def clean_csv(file_path):
    df = pd.read_csv(file_path)

    # 1. 컬럼 이름 정리 (공백 제거)
    df.columns = [col.strip() for col in df.columns]

    # 2. 모든 문자열 컬럼 strip
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()

    # 3. 이상치 제거: 모든 값이 NA인 행 제거
    df.dropna(how='all', inplace=True)

    # 4. 중복 제거
    df.drop_duplicates(inplace=True)

    return df
