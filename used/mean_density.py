import pandas as pd
import numpy as np
import scipy.stats as stats

# === 配置 ===
filename = "平均值.xlsx"  # 替换为你的路径
group_col = "ρ组"  # 替换为你的组别列名，如：ρ组, 速度组, 条件组等
stage_cols = ["a", "b", "c", "d", "e"]
metric_names = ["平均心率", "HRV"]

# === 读取数据 ===
df = pd.read_excel(filename)
df.columns = [col.strip() for col in df.columns]  # 去除列名空格
df[group_col] = df[group_col].replace({"ρ小": "其他", "ρ大": "ADHD"}).ffill()
df["Group"] = df[group_col].ffill()

# === 拆分指标 ===
results = {}
for metric in metric_names:
    df_metric = df[df["实验阶段"].str.contains(metric)].copy()
    df_metric["Group"] = df_metric["Group"].astype(str)

    results[metric] = {}

    for stage in stage_cols:
        group_labels = df_metric["Group"].unique()
        if len(group_labels) != 2:
            continue  # 必须两组比较

        g1, g2 = group_labels
        data1 = pd.to_numeric(df_metric[df_metric["Group"] == g1][stage], errors='coerce').dropna()
        data2 = pd.to_numeric(df_metric[df_metric["Group"] == g2][stage], errors='coerce').dropna()

        # 如果任一组没数据，跳过
        if len(data1) == 0 or len(data2) == 0:
            continue

        # 均值 & 标准差
        mean1, std1 = data1.mean(), data1.std()
        mean2, std2 = data2.mean(), data2.std()

        # F检验（ANOVA）
        f_val, p_val = stats.f_oneway(data1, data2)

        # η²
        grand_mean = np.mean(np.concatenate([data1, data2]))
        ss_total = np.sum((np.concatenate([data1, data2]) - grand_mean) ** 2)
        ss_between = len(data1) * (data1.mean() - grand_mean) ** 2 + len(data2) * (data2.mean() - grand_mean) ** 2
        eta_sq = ss_between / ss_total if ss_total != 0 else np.nan

        # t检验
        t_stat, p_t = stats.ttest_ind(data1, data2, equal_var=False)

        # 效应量 d
        pooled_std = np.sqrt((np.var(data1, ddof=1) + np.var(data2, ddof=1)) / 2)
        d = (data1.mean() - data2.mean()) / pooled_std if pooled_std != 0 else np.nan

        results[metric][stage] = {
            "组1": g1, "均值1": mean1, "标准差1": std1,
            "组2": g2, "均值2": mean2, "标准差2": std2,
            "F": f_val, "p_F": p_val, "η²": eta_sq,
            "t": t_stat, "p_t": p_t, "d": d
        }

# === 输出结果 ===
for metric in results:
    print(f"\n===== {metric} =====")
    for stage, res in results[metric].items():
        print(f"{stage}阶段：")
        print(f"{res['组1']}组 {res['均值1']:.2f}±{res['标准差1']:.2f}，"
              f"{res['组2']}组 {res['均值2']:.2f}±{res['标准差2']:.2f}")
        print(f"F(1,{len(data1)+len(data2)-2})={res['F']:.3f}, p={res['p_F']:.3f}, η²={res['η²']:.3f}；"
              f"t={res['t']:.2f}, p={res['p_t']:.3f}, d={res['d']:.2f}\n")

