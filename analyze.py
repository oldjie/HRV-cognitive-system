import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('Agg')  # 解决 Matplotlib 后端问题
import matplotlib.pyplot as plt
from scipy import stats

# 定义文件路径
file_paths = {
    "a": "subject_11-19_16-20_a.csv",
    "b": "subject_11-19_16-20_b.csv",
    "c": "subject_11-19_16-20_c.csv",
    "d": "subject_11-19_16-20_d.csv",
    "e": "subject_11-19_16-21_e.csv",
}

# 读取数据并存储完整数据
raw_data = {}

for stage, path in file_paths.items():
    df = pd.read_csv(path)

    # 过滤掉空值
    df.dropna(inplace=True)


    # 处理 R-R 间隔数据（转换成列表并展开）
    def parse_rr(rr_str):
        try:
            if isinstance(rr_str, str):
                rr_list = eval(rr_str)  # 解析字符串列表
                return [float(r) for r in rr_list if isinstance(r, (int, float))]
            return []
        except:
            return []


    df["R-R 间隔 (ms)"] = df["R-R 间隔 (ms)"].apply(parse_rr)

    # **展开 R-R 间隔**
    rr_expanded = []
    for rr_list in df["R-R 间隔 (ms)"]:
        rr_expanded.extend(rr_list)

    # 存储完整数据
    raw_data[stage] = {
        "心率 (bpm)": df["心率 (bpm)"].tolist(),
        "R-R 间隔 (ms)": rr_expanded,  # 已展开列表
        "HRV (RMSSD) (ms)": df["HRV (RMSSD) (ms)"].tolist(),
    }

# 进行统计检验
analysis_results = []
stages = list(raw_data.keys())
metrics = ["心率 (bpm)", "R-R 间隔 (ms)", "HRV (RMSSD) (ms)"]

for i in range(len(stages) - 1):
    stage1, stage2 = stages[i], stages[i + 1]

    for metric in metrics:
        data1 = raw_data[stage1][metric]
        data2 = raw_data[stage2][metric]

        # **对齐数据长度**
        min_length = min(len(data1), len(data2))
        data1, data2 = data1[:min_length], data2[:min_length]

        # 只有当数据点足够时才进行检验
        if len(data1) < 3 or len(data2) < 3:
            p_value, test_type = "数据不足", "跳过"
        else:
            # 正态性检验
            normality_p1 = stats.shapiro(data1).pvalue
            normality_p2 = stats.shapiro(data2).pvalue

            if normality_p1 > 0.05 and normality_p2 > 0.05:
                # 数据服从正态分布，使用配对 t 检验
                t_stat, p_value = stats.ttest_rel(data1, data2)
                test_type = "配对 t 检验"
            else:
                # 数据非正态，使用 Wilcoxon 符号秩检验
                t_stat, p_value = stats.wilcoxon(data1, data2)
                test_type = "Wilcoxon 符号秩检验"

        # 记录结果
        analysis_results.append({
            "对比阶段": f"{stage1} → {stage2}",
            "指标": metric,
            "统计方法": test_type,
            "p 值": p_value,
            "显著性": "显著" if isinstance(p_value, float) and p_value < 0.05 else "不显著"
        })

# 转换为 DataFrame 方便查看
analysis_results_df = pd.DataFrame(analysis_results)

# 显示统计检验结果
print("\n🔍 统计检验结果（显著性分析）")
print(analysis_results_df)

# 绘制趋势图
plt.figure(figsize=(10, 5))

# 绘制心率变化
plt.subplot(1, 3, 1)
plt.plot(stages, [np.mean(raw_data[stage]["心率 (bpm)"]) for stage in stages], marker='o', linestyle='-',
         label="心率 (bpm)")
plt.xlabel("Experinment Stage")
plt.ylabel("Average Heart Rate (bpm)")
plt.title("Heart Rate Trend")
plt.grid(True)

# 绘制 R-R 间隔变化
plt.subplot(1, 3, 2)
plt.plot(stages, [np.mean(raw_data[stage]["R-R 间隔 (ms)"]) for stage in stages], marker='s', linestyle='-',
         color="orange", label="R-R 间隔 (ms)")
plt.xlabel("Experinment Stage")
plt.ylabel("Average R-R Interval (ms)")
plt.title("R-R Interval Trend")
plt.grid(True)

# 绘制 HRV 变化
plt.subplot(1, 3, 3)
plt.plot(stages, [np.mean(raw_data[stage]["HRV (RMSSD) (ms)"]) for stage in stages], marker='^', linestyle='-',
         color="green", label="HRV (RMSSD) (ms)")
plt.xlabel("Experinment Stage")
plt.ylabel("HRV (RMSSD) (ms)")
plt.title("HRV (RMSSD) Trend")
plt.grid(True)

plt.tight_layout()
plt.savefig("trend_analysis.png")  # 保存图像，适用于无 GUI 环境
print("📊 结果趋势图已保存为 trend_analysis.png")
