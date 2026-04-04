import pandas as pd
import numpy as np
from scipy.stats import friedmanchisquare, ttest_rel
from itertools import combinations

# === 配置 ===
filename = "平均值.xlsx"  # ← 请替换为你的文件路径
group_col = "ρ组"
stage_cols = ["a", "b", "c", "d", "e"]
metrics = ["平均心率", "HRV"]

# === 读取数据 ===
df = pd.read_excel(filename)
df.columns = [col.strip() for col in df.columns]
df["Group"] = df[group_col].replace({"ρ小": "低密度", "ρ大": "高密度"}).ffill()

# === 分析函数 ===
def analyze_group_stage_differences(df_metric, group_name, metric_label):
    df_group = df_metric[df_metric["Group"] == group_name]
    if df_group.shape[0] < 3:
        print(f"\n⚠️ {group_name}组 - {metric_label} 样本不足，跳过分析。")
        return

    data = df_group[stage_cols].astype(float)
    print(f"\n📊 Friedman 检验结果（{group_name}组 - {metric_label}）:")

    stat, p = friedmanchisquare(*[data[stage] for stage in stage_cols])
    print(f"χ² = {stat:.3f}, p = {p:.3f}")

    if p < 0.05:
        print("阶段间差异显著，进行两两比较：")
        for comb in combinations(stage_cols, 2):
            t_val, p_val = ttest_rel(data[comb[0]], data[comb[1]])
            print(f"{comb[0]} vs {comb[1]}: t = {t_val:.2f}, p = {p_val:.3f}")
    else:
        print("阶段间无显著差异。")

# === 主循环：分别分析每组 × 每指标 ===
for metric_label in metrics:
    df_metric = df[df["实验阶段"].str.contains(metric_label)].copy()
    for group in ["低密度", "高密度"]:
        analyze_group_stage_differences(df_metric, group, metric_label)
