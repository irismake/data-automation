import pandas as pd

def trim_zone_code(csv_path, digits):
    df = pd.read_csv(csv_path)

    if 'zone_code' not in df.columns:
        raise ValueError("zone_code 컬럼이 존재하지 않습니다.")

    # 문자열로 변환 → 앞 digits자리만 추출 → 정수로 변환
    df['zone_code'] = df['zone_code'].astype(str).str[:digits].astype(int)

    # 새 파일로 저장
    new_path = csv_path.replace(".csv", f"_trimmed_{digits}.csv")
    df.to_csv(new_path, index=False)

    return new_path
