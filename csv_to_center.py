import pandas as pd
import os

def coord_to_center(file_path, output_path=None):
    df = pd.read_csv(file_path)

    if 'x' not in df.columns or 'y' not in df.columns:
        raise ValueError("CSV에 'x', 'y' 컬럼이 존재하지 않습니다.")

    min_x, max_x = df['x'].min(), df['x'].max()
    min_y, max_y = df['y'].min(), df['y'].max()

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    shift_x = (22 - width) // 2 - min_x
    shift_y = (22 - height) // 2 - min_y

    # ✅ 이동 후 음수 좌표 방지(사전 체크)
    new_min_x = min_x + shift_x
    new_min_y = min_y + shift_y
    if new_min_x < 0 or new_min_y < 0:
        raise ValueError(f"중앙 정렬 결과 음수 좌표가 발생합니다: "
                         f"new_min_x={new_min_x}, new_min_y={new_min_y}")

    df['x'] = df['x'] + shift_x
    df['y'] = df['y'] + shift_y

    # ✅ 적용 후 이중 확인(예상치 못한 값 대비)
    if (df['x'] < 0).any() or (df['y'] < 0).any():
        raise ValueError("좌표 이동 후 음수 값이 존재합니다.")

    if not output_path:
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_centered{ext}"

    df.to_csv(output_path, index=False)
    return output_path
