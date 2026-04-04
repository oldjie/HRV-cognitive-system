import pandas as pd
import scipy.stats as stats

file_A = "A.csv"
file_B = "B.csv"

df_A = pd.read_csv(file_A)
df_B = pd.read_csv(file_B)

# 合并数据并添加组别信息
df_A["Group"] = "A"
df_B["Group"] = "B"
df = pd.concat([df_A, df_B])

# 定义阶段
stages = ["a", "b", "c", "d"]
metrics = ["平均心率 (bpm)", "HRV (RMSSD) (ms)"]

# 计算均值和标准差
summary_dict = {}

for metric in metrics:
    df_metric = df[df["实验阶段"] == metric]

    # 确保数据为数值类型
    for stage in stages:
        df_metric[stage] = pd.to_numeric(df_metric[stage])

    # 计算均值和标准差
    summary_dict[metric] = df_metric.groupby("Group")[stages].agg(["mean", "std"])

# 设置 Pandas 选项，完整显示列
pd.set_option('display.max_columns', None)

# 输出均值和标准差
for metric, summary in summary_dict.items():
    print(f"\n各组各阶段的 {metric} 均值和标准差：")
    print(summary)

# 进行方差分析
anova_results = {metric: {} for metric in metrics}

for metric in metrics:
    df_metric = df[df["实验阶段"] == metric]

    for stage in stages:
        group_A = pd.to_numeric(df_metric[df_metric["Group"] == "A"][stage])
        group_B = pd.to_numeric(df_metric[df_metric["Group"] == "B"][stage])

        f_val, p_val = stats.f_oneway(group_A, group_B)
        anova_results[metric][stage] = {"F": f_val, "p": p_val}

# 输出方差分析结果
for metric, results in anova_results.items():
    print(f"\n方差分析（ANOVA）结果 ({metric})：")
    for stage, res in results.items():
        print(f"{stage}阶段: F = {res['F']:.3f}, p = {res['p']:.3f}")

import numpy as np
from statsmodels.stats.multitest import multipletests


def calculate_eta_squared(a, b):
    grand_mean = np.mean(np.concatenate([a, b]))
    ss_total = np.sum((np.concatenate([a, b]) - grand_mean) ** 2)
    ss_between = len(a) * np.mean(a - grand_mean) ** 2 + len(b) * np.mean(b - grand_mean) ** 2
    return ss_between / ss_total


anova_results = {metric: {} for metric in metrics}
for metric in metrics:
    df_metric = df[df["实验阶段"] == metric]
    for stage in stages:
        group_A = pd.to_numeric(df_metric[df_metric["Group"] == "A"][stage])
        group_B = pd.to_numeric(df_metric[df_metric["Group"] == "B"][stage])

        f_val, p_val = stats.f_oneway(group_A, group_B)

        eta_sq = calculate_eta_squared(group_A, group_B)

        df_between = 1  # 组数-1（AB两组）
        df_within = len(group_A) + len(group_B) - 2

        anova_results[metric][stage] = {
            "F": f_val,
            "p": p_val,
            "eta²": eta_sq,
            "df": (df_between, df_within)
        }

posthoc_results = {metric: {} for metric in metrics}
for metric in metrics:
    df_metric = df[df["实验阶段"] == metric]
    for stage in stages:
        group_A = pd.to_numeric(df_metric[df_metric["Group"] == "A"][stage])
        group_B = pd.to_numeric(df_metric[df_metric["Group"] == "B"][stage])

        t_stat, p_val = stats.ttest_ind(group_A, group_B, equal_var=False)

        pooled_std = np.sqrt((np.var(group_A, ddof=1) + np.var(group_B, ddof=1)) / 2)
        cohen_d = (np.mean(group_A) - np.mean(group_B)) / pooled_std

        posthoc_results[metric][stage] = {
            "t": t_stat,
            "p": p_val,
            "d": cohen_d
        }


def get_significance(p):
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return 'ns'


print("\n\n=== 最终分析结果 ===")
for metric in metrics:
    print(f"\n◆ {metric} ◆")
    for stage in stages:
        # ANOVA结果
        anova = anova_results[metric][stage]
        # 两两比较结果
        ph = posthoc_results[metric][stage]

        # 生成报告语句
        report = (
            f"{stage}阶段: F({anova['df'][0]},{anova['df'][1]})={anova['F']:.3f}, "
            f"p={anova['p']:.3f}{get_significance(anova['p'])}, "
            f"η²={anova['eta²']:.3f}；"
            f"两两比较t={ph['t']:.2f}(d={ph['d']:.2f}), {get_significance(ph['p'])}"
        )
        print(report)

"""
◆ 平均心率 (bpm) ◆
a阶段: F(1,18)=0.407, p=0.528ns, η²=0.023；两两比较t=-0.64(d=-0.28), ns
b阶段: F(1,18)=0.345, p=0.561ns, η²=0.019；两两比较t=-0.59(d=-0.25), ns
...
◆ HRV (RMSSD) (ms) ◆
a阶段: F(1,18)=5.407, p=0.027*, η²=0.231；两两比较t=2.33(d=0.85)*
...
"""