import pandas as pd

def compare_bidirectional(csv_df, filtered_df):
    # 1. CSV 안의 pnus 필드에서 모든 숫자 꺼내기
    csv_pnus = set()
    for pnus_list in csv_df['pnus']:
        try:
            pnus = eval(pnus_list)  # 문자열 리스트 -> 실제 리스트
            csv_pnus.update(int(p) for p in pnus)
        except:
            continue

    # 2. TXT의 법정동코드
    txt_pnus = set(filtered_df['법정동코드'].astype(int))

    # 3. 누락 비교
    missing_in_csv = sorted(txt_pnus - csv_pnus)
    missing_in_txt = sorted(csv_pnus - txt_pnus)

    return missing_in_csv, missing_in_txt