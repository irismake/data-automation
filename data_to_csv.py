import pandas as pd
import json

def process_pnu_csv(input_csv_path: str, output_csv_path: str, invalid_output_path: str):
    # CSV 읽기
    df = pd.read_csv(input_csv_path, dtype=str)

    # 1. BGD 또는 PNU_list가 None인 행 제거
    df = df.dropna(subset=["BGD", "PNU_list"])

    # 중복 경고, 불일치 항목 저장용
    duplicate_warning = []
    invalid_entries = []

    # 2. PNU_list 컬럼을 리스트[str]로 변환하며 검사
    def process_row(row):
        row_index = str(row["row_index"]).strip()
        col_index = str(row["col_index"]).strip()
        bgd_prefix = str(row["BGD"]).strip()

        try:
            pnu_raw = row["PNU_list"].split(",")
            pnu_list = []
            for x in pnu_raw:
                x = x.strip()
                if not x:
                    continue
                if x.isdigit():
                    pnu_str = str(int(x)).zfill(19)
                    pnu_list.append(pnu_str)
                    # 3. BGD와 앞 10자리 불일치 검사
                    if pnu_str[:10] != bgd_prefix:
                        invalid_entries.append((row_index, col_index, pnu_str))
                else:
                    # 숫자가 아니면 그대로 보존 + invalid 기록
                    invalid_entries.append((row_index, col_index, x))
                    pnu_list.append(x)
        except Exception as e:
            print(f"⚠️ 변환 실패: ({row_index}, {col_index}) → {e}")
            return []

        # 2-1. 중복 확인
        if len(pnu_list) != len(set(pnu_list)):
            duplicate_warning.append((row_index, col_index))

        return pnu_list

    # PNU_list를 리스트로 변환
    df["PNU_list"] = df.apply(process_row, axis=1)

    # 4. 총 PNU 개수 계산
    try:
        total_count = sum(len(pnu_list) for pnu_list in df["PNU_list"] if isinstance(pnu_list, list))
    except Exception as e:
        print("총 PNU 개수 계산 중 오류:", e)
        total_count = 0
    print(f"✅ 총 PNU 개수: {total_count}")

    # 5. 중복 경고 출력
    if duplicate_warning:
        print("\n⚠️ 중복된 PNU가 존재하는 셀:")
        for row, col in duplicate_warning:
            print(f" - row_index: {row}, col_index: {col}")

    # 6. BGD와 불일치/변환 실패 항목 저장
    with open(invalid_output_path, "w") as f:
        for row, col, pnu in invalid_entries:
            f.write(f"{row},{col},{pnu}\n")
    print(f"❌ BGD와 불일치하거나 변환 실패한 PNU 총 {len(invalid_entries)}건 → '{invalid_output_path}'에 저장됨")

    # 7. CSV 저장을 위한 컬럼명 및 데이터 변환
    df_export = df.copy()
    df_export["y"] = df_export["row_index"]
    df_export["x"] = df_export["col_index"]
    df_export["zone_code"] = df_export["BGD"]     # ✅ zone_code = BGD
    df_export["pnus"] = df_export["PNU_list"].apply(
        lambda lst: json.dumps(lst, ensure_ascii=False) if isinstance(lst, list) else "[]"
    )

    # 필요한 컬럼만 저장
    df_export[["y", "x", "zone_code", "pnus"]].to_csv(output_csv_path, index=False)
    print(f"📄 정제된 결과 → '{output_csv_path}'에 저장 완료")
