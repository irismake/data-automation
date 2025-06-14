import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import pandas as pd
import cleaner
import comparer
import extractor

class ExcelAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV 자동화 도구")
        self.root.geometry("500x350")

        self.csv_path = ""
        # ✅ 기본 txt 경로 지정
        self.txt_path = os.path.join(os.path.dirname(__file__), "legal_zone_code_data.txt")
        self.selected_region = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        tk.Button(self.root, text="CSV 파일 선택", command=self.load_csv).pack(pady=10)

        tk.Label(self.root, text="시/도 선택").pack()
        region_combo = ttk.Combobox(self.root, textvariable=self.selected_region, values=[
            "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
            "경기도", "강원특별자치도", "충청북도", "충청남도", "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도"
        ])
        region_combo.pack(pady=5)

        tk.Button(self.root, text="실행 (정리 + 비교)", command=self.run_processing).pack(pady=20)

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
        filtered_df = extractor.filter_txt(self.txt_path, self.selected_region.get(), filtered_path)

        cleaned_df = cleaner.clean_csv(self.csv_path)
        missing_csv, missing_txt = comparer.compare_bidirectional(cleaned_df, filtered_df)

        pd.DataFrame({"누락된 법정동코드": missing_csv}).to_csv("누락_from_csv.csv", index=False)
        pd.DataFrame({"누락된 법정동코드": missing_txt}).to_csv("누락_from_txt.csv", index=False)

        messagebox.showinfo("완료", f"처리 완료!\n{filtered_path}\n누락_from_csv.csv\n누락_from_txt.csv")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelAutomationApp(root)
    root.mainloop()
