import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import pandas as pd

import cleaner
import comparer
import extractor
import csv_to_center
import csv_to_swift
import zone_code_trimmer

class ExcelAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV 자동화 도구")
        self.root.geometry("500x600")

        self.csv_path = ""
        self.txt_path = os.path.join(os.path.dirname(__file__), "legal_zone_code_data.txt")
        self.selected_region = tk.StringVar()

        self.region_code_map = {
            "서울특별시": 11,
            "부산광역시": 26,
            "대구광역시": 27,
            "인천광역시": 28,
            "광주광역시": 29,
            "대전광역시": 30,
            "울산광역시": 31,
            "세종특별자치시": 36,
            "경기도": 41,
            "강원특별자치도": 42,
            "충청북도": 43,
            "충청남도": 44,
            "전북특별자치도": 52,
            "전라남도": 46,
            "경상북도": 47,
            "경상남도": 48,
            "제주특별자치도": 50
        }

        self.create_widgets()

    def create_widgets(self):
        tk.Button(self.root, text="CSV 파일 선택", command=self.load_csv).pack(pady=10)

        tk.Label(self.root, text="시/도 선택").pack()
        region_combo = ttk.Combobox(
            self.root,
            textvariable=self.selected_region,
            values=list(self.region_code_map.keys())
        )
        region_combo.pack(pady=5)

        tk.Button(self.root, text="실행 (정리 + 비교)", command=self.run_processing).pack(pady=10)
        tk.Button(self.root, text="중앙 정렬 CSV 저장", command=self.coord_to_center).pack(pady=10)
        tk.Button(self.root, text="Swift 코드로 저장", command=self.convert_csv_to_swift).pack(pady=10)

        # zone_code 자르기 관련 위젯
        tk.Label(self.root, text="zone_code 앞 몇 자리만 남길지 입력").pack()
        self.trim_digits = tk.Entry(self.root)
        self.trim_digits.pack(pady=5)
        tk.Button(self.root, text="zone_code 자르기 및 저장", command=self.trim_zone_code).pack(pady=10)

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_path = path
            messagebox.showinfo("파일 선택됨", f"CSV 파일: {path}")

    def run_processing(self):
        if not self.csv_path or not self.selected_region.get():
            messagebox.showwarning("경고", "CSV 파일과 시/도를 선택하세요.")
            return

        filtered_path = f"filtered_{self.selected_region.get()}.txt"
        filtered_df = extractor.filter_zone_in_txt(self.txt_path, self.selected_region.get(), filtered_path)

        cleaned_df = cleaner.clean_csv(self.csv_path)
        missing_csv, missing_txt = comparer.compare_bidirectional(cleaned_df, filtered_df)

        pd.DataFrame({"누락된 법정동코드": missing_csv}).to_csv("누락_from_csv.csv", index=False)
        pd.DataFrame({"누락된 법정동코드": missing_txt}).to_csv("누락_from_txt.csv", index=False)

        messagebox.showinfo("완료", f"처리 완료!\n{filtered_path}\n누락_from_csv.csv\n누락_from_txt.csv")

    def coord_to_center(self):
        if not self.csv_path:
            messagebox.showwarning("경고", "CSV 파일을 먼저 선택하세요.")
            return

        try:
            output_path = csv_to_center.coord_to_center(self.csv_path)
            messagebox.showinfo("완료", f"중앙 정렬된 CSV 저장됨:\n{output_path}")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def convert_csv_to_swift(self):
        if not self.csv_path or not self.selected_region.get():
            messagebox.showwarning("경고", "CSV 파일과 시/도를 선택하세요.")
            return

        try:
            region_code = self.region_code_map.get(self.selected_region.get())
            output_path = csv_to_swift.convert_csv_to_swift(self.csv_path, region_code)
            messagebox.showinfo("완료", f"Swift 코드 파일 생성됨:\n{output_path}")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def trim_zone_code(self):
        if not self.csv_path:
            messagebox.showwarning("경고", "CSV 파일을 먼저 선택하세요.")
            return
        try:
            digits = int(self.trim_digits.get())
            output_path = zone_code_trimmer.trim_zone_code(self.csv_path, digits)
            messagebox.showinfo("완료", f"zone_code 자르기 완료!\n{output_path}")
        except Exception as e:
            messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelAutomationApp(root)
    root.mainloop()
