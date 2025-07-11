import pandas as pd

def process_pnu_csv(input_csv_path: str, output_csv_path: str, invalid_output_path: str):
    # CSV 읽기
    df = pd.read_csv(input_csv_path, dtype=str)

    # 1. A3 또는 A2_list가 None인 행 제거
    df = df.dropna(subset=["A3", "A2_list"])

    # 중복 경고, 불일치 항목 저장용
    duplicate_warning = []
    invalid_entries = []

    # 2. A2_list 컬럼을 리스트[int]로 변환하며 검사
    def process_row(row):
        row_index = str(row["row_index"]).strip()
        col_index = str(row["col_index"]).strip()
        a3_prefix = str(row["A3"]).strip()

        try:
            a2_raw = row["A2_list"].split(",")
            a2_list = [int(x.strip()) for x in a2_raw if x.strip().isdigit()]
        except Exception as e:
            print(f"⚠️ 변환 실패: ({row_index}, {col_index}) → {e}")
            return []

        # 2-1. 중복 확인
        if len(a2_list) != len(set(a2_list)):
            duplicate_warning.append((row_index, col_index))

        # 3. A3와 앞 10자리 불일치 검사
        for a2 in a2_list:
            if str(a2).zfill(19)[:10] != a3_prefix:
                invalid_entries.append((row_index, col_index, a2))

        return a2_list

    # A2_list를 정수 리스트로 변환
    df["A2_list"] = df.apply(process_row, axis=1)

    # 4. 총 A2 정수 개수 계산
    try:
        total_count = sum(len(a2_list) for a2_list in df["A2_list"] if isinstance(a2_list, list))
    except Exception as e:
        print("총 A2 정수 개수 계산 중 오류:", e)
        total_count = 0
    print(f"✅ 총 A2 정수 개수: {total_count}")

    # 5. 중복 경고 출력
    if duplicate_warning:
        print("\n⚠️ 중복된 A2가 존재하는 셀:")
        for row, col in duplicate_warning:
            print(f" - row_index: {row}, col_index: {col}")

    # 6. A3와 일치하지 않는 A2 저장
    with open(invalid_output_path, "w") as f:
        for row, col, a2 in invalid_entries:
            f.write(f"{row},{col},{a2}\n")
    print(f"❌ A3와 일치하지 않는 A2 총 {len(invalid_entries)}건 → '{invalid_output_path}'에 저장됨")

    # 7. CSV 저장을 위한 컬럼명 및 데이터 변환
    df_export = df.copy()
    df_export["y"] = df_export["row_index"]
    df_export["x"] = df_export["col_index"]
    df_export["zone_code"] = df_export["A3"]
    df_export["pnus"] = df_export["A2_list"].apply(lambda lst: str(lst) if isinstance(lst, list) else "[]")

    # 필요한 컬럼만 저장
    df_export[["y", "x", "zone_code", "pnus"]].to_csv(output_csv_path, index=False)
    print(f"📄 정제된 결과 → '{output_csv_path}'에 저장 완료")
