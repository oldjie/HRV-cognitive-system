import pandas as pd
import numpy as np
import scipy.stats as stats

# 读取数据
df = pd.read_excel("速度平均值.xlsx")
df.columns = ["姓名", "指标", "a", "b", "c", "d", "e"]

# 定义阶段及顺序
stages = ["a", "b", "e", "c", "d"]
stage_labels = {"a": "基线期", "b": "唤醒期", "e": "平复期", "c": "慢速期", "d": "快速期"}
metrics = df["指标"].unique()

# 显著性标记
def get_significance(p):
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return 'ns'

# η² 计算
def calculate_eta_squared(a, b):
    grand_mean = np.mean(np.concatenate([a, b]))
    ss_total = np.sum((np.concatenate([a, b]) - grand_mean) ** 2)
    ss_between = len(a) * np.mean(a - grand_mean) ** 2 + len(b) * np.mean(b - grand_mean) ** 2
    return ss_between / ss_total

# 初始化结果容器
anova_results = {metric: {} for metric in metrics}
posthoc_results = {metric: {} for metric in metrics}
summary_dict = {metric: {} for metric in metrics}

# 分析每个指标
for metric in metrics:
    df_metric = df[df["指标"] == metric]

    for stage in stages:
        values = df_metric[stage].astype(float)

        # 均值±标准差
        summary_dict[metric][stage] = {
            "mean": values.mean(),
            "std": values.std()
        }

    # 特别针对“慢速 vs 快速”阶段进行统计
    slow = df_metric["c"].astype(float)
    fast = df_metric["d"].astype(float)

    # ANOVA（虽然两组其实可以直接看 t）
    F_val, p_val = stats.f_oneway(slow, fast)
    eta2 = calculate_eta_squared(slow, fast)

    # t 检验（配对）
    t_stat, p_t = stats.ttest_rel(slow, fast)
    pooled_std = np.sqrt(((slow - slow.mean())**2).sum() + ((fast - fast.mean())**2).sum()) / (2 * len(slow) - 2)
    d_val = (slow.mean() - fast.mean()) / pooled_std

    # 保存结果
    anova_results[metric]["c_vs_d"] = {
        "F": F_val,
        "p": p_val,
        "eta²": eta2,
        "df": (1, len(slow)*2 - 2)
    }
    posthoc_results[metric]["c_vs_d"] = {
        "t": t_stat,
        "p": p_t,
        "d": d_val
    }

# 输出所有内容
pd.set_option('display.float_format', '{:.3f}'.format)

print("\n\n=== 各阶段均值 ± 标准差 ===")
for metric in metrics:
    print(f"\n◆ {metric} ◆")
    for stage in stages:
        m = summary_dict[metric][stage]["mean"]
        s = summary_dict[metric][stage]["std"]
        print(f"{stage_labels[stage]}: {m:.2f} ± {s:.2f}")

print("\n\n=== 方差分析 + t检验（慢速 vs 快速） ===")
for metric in metrics:
    print(f"\n◆ {metric} ◆")
    anova = anova_results[metric]["c_vs_d"]
    ph = posthoc_results[metric]["c_vs_d"]
    print(
        f"慢速 vs 快速: F({anova['df'][0]},{anova['df'][1]})={anova['F']:.3f}, "
        f"p={anova['p']:.3f}{get_significance(anova['p'])}, η²={anova['eta²']:.3f}； "
        f"t={ph['t']:.2f}, p={ph['p']:.3f}, d={ph['d']:.2f}, {get_significance(ph['p'])}"
    )
