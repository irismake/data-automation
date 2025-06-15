import pandas as pd

def filter_zone_in_txt(txt_path, selected_region, save_path):
    df = pd.read_csv(txt_path, sep="\t", dtype=str)

    # 조건 필터링: 반드시 각 조건 괄호로 감싸야 함!
    filtered = df[
        (df['폐지여부'] == '존재') &
        (df['법정동명'].str.startswith(selected_region)) &
        (~df['법정동명'].str.endswith("리"))
    ]

    # 저장
    filtered.to_csv(save_path, index=False, sep="\t")
    return filtered
