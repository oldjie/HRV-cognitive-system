#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量统计 CSV 的平均心率(第3列)与 HRV(第5列)，并生成“姓名 × 阶段(a,b,c,d)”的横向表格，便于复制到模板。
文件名格式假设类似：
    SubjectXXX_04-25_15-05_a.csv   或   SubjectXXX_04-25_15-05_a.csv
即：人名 + 空格 + "协和度" + ... + 阶段字母(a/b/c/d) + .csv

用法：
    python calc_hr_hrv.py --glob "*.csv"                   # 统计当前目录下所有 csv
    python calc_hr_hrv.py --glob "data/*.csv"              # 指定通配
    python calc_hr_hrv.py --out summary.xlsx               # 指定输出文件名（扩展名 .xlsx 或 .csv 均可）
"""
import argparse
import glob
import os
import re
from typing import List, Tuple

import pandas as pd

TARGET_COLS_BY_NAME = ["心率 (bpm)", "HRV (RMSSD) (ms)"]  # 第3列、第5列的理想列名
STAGES_ORDER = ["a", "b", "c", "d"]

def read_csv_robust(path: str) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "gbk", "cp936"]
    last_err = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_err = e
    raise last_err

def get_target_series(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    if all(col in df.columns for col in TARGET_COLS_BY_NAME):
        hr = pd.to_numeric(df[TARGET_COLS_BY_NAME[0]], errors="coerce")
        hrv = pd.to_numeric(df[TARGET_COLS_BY_NAME[1]], errors="coerce")
    else:
        if df.shape[1] < 5:
            raise ValueError("列数不足，无法定位第3、5列。")
        hr = pd.to_numeric(df.iloc[:, 2], errors="coerce")
        hrv = pd.to_numeric(df.iloc[:, 4], errors="coerce")
    return hr, hrv

def parse_name_stage(filename: str) -> Tuple[str, str]:
    """从文件名中解析姓名与阶段字母。"""
    base = os.path.basename(filename)
    stem = os.path.splitext(base)[0]

    # 常见两种写法： ..._a.csv 或 ... a.csv（阶段字母在结尾）
    m = re.search(r'[_\s]([abcdABCD])$', stem)
    stage = m.group(1).lower() if m else ""

    # 姓名在“ 协和度”之前
    name = stem.split(" 协和度")[0].strip()
    if not name:
        # 退化：取前一个空格前的块
        name = stem.split()[0].strip()
    return name, stage

def summarize_files(paths: List[str]):
    rows = []       # 逐文件行（调试/留存）
    long_rows = []  # 用于 pivot 的长表：name, stage, mean_hr, mean_hrv

    for p in paths:
        df = read_csv_robust(p)
        hr, hrv = get_target_series(df)
        name, stage = parse_name_stage(p)

        file_hr = hr.dropna()
        file_hrv = hrv.dropna()
        mean_hr = file_hr.mean() if not file_hr.empty else float('nan')
        mean_hrv = file_hrv.mean() if not file_hrv.empty else float('nan')

        rows.append({
            "file": os.path.basename(p),
            "name": name,
            "stage": stage,
            "rows": len(df),
            "valid_hr": int(file_hr.shape[0]),
            "valid_hrv": int(file_hrv.shape[0]),
            "mean_hr": mean_hr,
            "mean_hrv": mean_hrv,
        })
        if name and stage:
            long_rows.append({"name": name, "stage": stage, "mean_hr": mean_hr, "mean_hrv": mean_hrv})

    per_file = pd.DataFrame(rows).sort_values(["name", "stage", "file"], ignore_index=True)
    long_df = pd.DataFrame(long_rows)

    # 生成横向表（姓名 × 阶段）
    def build_wide(value_col: str, title_first_col: str) -> pd.DataFrame:
        if long_df.empty:
            return pd.DataFrame(columns=[title_first_col] + STAGES_ORDER)
        pivot = long_df.pivot_table(index="name", columns="stage", values=value_col, aggfunc="mean")
        # 强制列顺序 a,b,c,d，并保留缺失为 NaN
        pivot = pivot.reindex(columns=STAGES_ORDER)
        pivot.reset_index(inplace=True)
        pivot.insert(0, title_first_col, pivot.pop("name"))
        return pivot

    hrv_wide = build_wide("mean_hrv", "姓名/协和度阶段HRV数据")
    hr_wide  = build_wide("mean_hr",  "姓名/协和度阶段HR数据")

    return per_file, hrv_wide, hr_wide

def save_outputs(per_file: pd.DataFrame, hrv_wide: pd.DataFrame, hr_wide: pd.DataFrame, out_path: str):
    # 根据扩展名写出
    root, ext = os.path.splitext(out_path)
    if ext.lower() == ".csv":
        # CSV 只写 per_file；另存 Excel 以包含宽表
        per_file.to_csv(out_path, index=False, encoding="utf-8-sig")
        with pd.ExcelWriter(root + ".xlsx") as writer:
            per_file.to_excel(writer, index=False, sheet_name="per_file")
            hrv_wide.to_excel(writer, index=False, sheet_name="HRV_表")
            hr_wide.to_excel(writer, index=False, sheet_name="HR_表")
    else:
        # 默认写 Excel
        with pd.ExcelWriter(out_path if ext else (root + ".xlsx")) as writer:
            per_file.to_excel(writer, index=False, sheet_name="per_file")
            hrv_wide.to_excel(writer, index=False, sheet_name="HRV_表")
            hr_wide.to_excel(writer, index=False, sheet_name="HR_表")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--glob", default="*.csv", help="文件通配，如 data/*.csv")
    parser.add_argument("--out", default="hr_hrv_summary.xlsx", help="输出文件名（.xlsx 或 .csv）")
    args = parser.parse_args()

    paths = sorted(glob.glob(args.glob))
    if not paths:
        print(f"未找到任何文件：{args.glob}")
        return

    per_file, hrv_wide, hr_wide = summarize_files(paths)
    save_outputs(per_file, hrv_wide, hr_wide, args.out)

    print("—— 每个文件 ——")
    print(per_file.to_string(index=False))
    print("\n—— HRV 宽表（可直接复制到模板）——")
    print(hrv_wide.to_string(index=False))
    print("\n—— HR 宽表（可直接复制到模板）——")
    print(hr_wide.to_string(index=False))
    print(f"\n已保存：{args.out if args.out.lower().endswith(('.xlsx','.csv')) else args.out+'.xlsx'}")

if __name__ == "__main__":
    main()
