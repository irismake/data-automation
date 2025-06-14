import pandas as pd
import os

def center_coordinates(file_path, output_path=None):
    df = pd.read_csv(file_path)

    if 'x' not in df.columns or 'y' not in df.columns:
        raise ValueError("CSV에 'x', 'y' 컬럼이 존재하지 않습니다.")

    min_x, max_x = df['x'].min(), df['x'].max()
    min_y, max_y = df['y'].min(), df['y'].max()

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    shift_x = (25 - width) // 2 - min_x
    shift_y = (25 - height) // 2 - min_y

    df['x'] = df['x'] + shift_x
    df['y'] = df['y'] + shift_y

    if not output_path:
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_centered{ext}"

    df.to_csv(output_path, index=False)
    return output_path
