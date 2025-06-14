import pandas as pd
import os

def convert_to_swift(file_path, region_code=None, output_path=None):
    df = pd.read_csv(file_path)

    # 필요한 컬럼이 있는지 확인
    if 'x' not in df.columns or 'y' not in df.columns or 'zone_code' not in df.columns:
        raise ValueError("CSV에 'x', 'y', 'zone_code' 컬럼이 모두 존재해야 합니다.")

    # Swift 변수 시작
    key = region_code if region_code else 9999999999

    lines = [f"let zoneMap: [Int: [Zone]] = ["]
    lines.append(f"    {key}: [")

    for _, row in df.iterrows():
        try:
            x = int(row["x"])
            y = int(row["y"])
            zone_code = int(row["zone_code"])
            lines.append(f"        Zone(x: {x}, y: {y}, zoneCode: {zone_code}),")
        except Exception:
            continue

    lines.append("    ],")
    lines.append("]")

    swift_code = "\n".join(lines)

    # 기본 파일 경로 설정
    if not output_path:
        base, _ = os.path.splitext(file_path)
        output_path = f"{base}.swift"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(swift_code)

    return output_path
