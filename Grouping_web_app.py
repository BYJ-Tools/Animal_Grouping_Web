import streamlit as st
import pandas as pd
import numpy as np
import random
import math
import io
import datetime
from scipy import stats

# ================= 页面基础设置 =================
st.set_page_config(page_title="实验动物均衡分组系统", page_icon="🐾", layout="wide")
st.title("🐾 实验动物均衡分组系统 (Web版)")
st.markdown("上传包含动物指标的 Excel 表格，系统将自动进行随机且均衡的分组。")


# ================= 核心计算逻辑 =================
def evaluate_balance(df, indicators, weights):
    scores = []
    for idx, ind in enumerate(indicators):
        means = df.groupby('group')[ind].mean()
        std_all = df[ind].std()
        if std_all == 0 or pd.isna(std_all): std_all = 1
        weight = weights[idx] if idx < len(weights) else 1.0
        weight = max(0.0, min(1.0, weight))
        if weight == 0:
            scores.append(0)
        else:
            score = ((means.max() - means.min()) / std_all) * weight
            scores.append(score)
    return sum(scores)


def random_assign(df, n_groups):
    df = df.sample(frac=1).reset_index(drop=True)
    df['group'] = [i % n_groups + 1 for i in range(len(df))]
    return df


def optimize_balance(df, n_groups, indicators, weights):
    global_best_score = float('inf')
    global_best_df = None
    n_restarts = 3  # 网页版为了响应速度，重启次数稍微调低，也可以自己改大
    for _ in range(n_restarts):
        current_df = random_assign(df, n_groups)
        current_score = evaluate_balance(current_df, indicators, weights)
        iter_count = max(2000, len(df) * 100)
        temperature = current_score * 0.1 + 0.1
        for i in range(iter_count):
            g1, g2 = random.sample(range(1, n_groups + 1), 2)
            if len(current_df[current_df['group'] == g1]) == 0 or len(
                current_df[current_df['group'] == g2]) == 0: continue
            idx1 = current_df[current_df['group'] == g1].sample(1).index[0]
            idx2 = current_df[current_df['group'] == g2].sample(1).index[0]
            current_df.loc[idx1, 'group'], current_df.loc[idx2, 'group'] = g2, g1
            new_score = evaluate_balance(current_df, indicators, weights)
            if new_score <= current_score:
                current_score = new_score
            else:
                temp_now = temperature * (1 - i / iter_count)
                if temp_now > 1e-5:
                    diff = (current_score - new_score) / temp_now
                    if diff > -50 and random.random() < math.exp(diff):
                        current_score = new_score
                    else:
                        current_df.loc[idx1, 'group'], current_df.loc[idx2, 'group'] = g1, g2
                else:
                    current_df.loc[idx1, 'group'], current_df.loc[idx2, 'group'] = g1, g2
        if current_score < global_best_score:
            global_best_score = current_score
            global_best_df = current_df.copy()
    return global_best_df


# ================= 网页交互布局 =================
# 1. 文件上传区
uploaded_file = st.file_uploader("1. 请上传数据文件 (Excel 格式)", type=["xlsx", "xls"])

if uploaded_file is not None:
    # 读取数据
    data = pd.read_excel(uploaded_file)
    if 'animal_id' not in data.columns:
        data.insert(0, 'animal_id', range(1, len(data) + 1))

    cols = list(data.columns)
    # 自动排除第一列编号
    if cols and ('id' in str(cols[0]).lower() or '编号' in str(cols[0])):
        all_indicators = cols[1:]
    else:
        all_indicators = cols

    st.success(f"成功读取数据，共 {len(data)} 只动物，识别到指标：{', '.join(all_indicators)}")

    # 2. 参数设置区
    st.markdown("### 2. 分组参数设置")
    col1, col2 = st.columns(2)
    with col1:
        n_groups = st.number_input("分组数量 (组)", min_value=2, max_value=20, value=4)
    with col2:
        n_indicators = st.number_input("参与平衡的指标数", min_value=1, max_value=len(all_indicators),
                                       value=len(all_indicators))

    active_indicators = all_indicators[:n_indicators]

    # 3. 权重设置区
    st.markdown("### 3. 指标权重设置 (1 为最重要，0 为不考虑)")
    weights = []
    # 把输入框横向排列
    weight_cols = st.columns(min(n_indicators, 5))  # 最多一行放5个
    for i, ind_name in enumerate(active_indicators):
        with weight_cols[i % len(weight_cols)]:
            w = st.number_input(f"{ind_name} 权重", min_value=0.0, max_value=1.0, value=1.0, step=0.1, key=f"w_{i}")
            weights.append(w)

    # 4. 执行分组
    st.markdown("---")
    if st.button("🚀 开始均衡分组", use_container_width=True, type="primary"):
        with st.spinner("正在计算最优分配方案，请稍候..."):
            # 运行算法
            np.random.seed(42)
            random.seed(42)
            df_final = optimize_balance(data, n_groups, active_indicators, weights)

            # 整理结果
            final_table = df_final[['group', 'animal_id'] + active_indicators].copy()
            final_table = final_table.sort_values(by=['group', 'animal_id']).reset_index(drop=True)
            group_means = final_table.groupby('group')[active_indicators].mean().round(2)

            # 显示结果表格 (网页上直接展示)
            st.markdown("### 🎉 分组结果预览")
            st.dataframe(final_table, use_container_width=True)

            st.markdown("### 📊 各组均值对比")
            st.dataframe(group_means, use_container_width=True)

            # 生成下载文件
            mean_rows_list = []
            for g in range(1, n_groups + 1):
                if g in group_means.index:
                    row_values = [f'第{g}组均值', ''] + [f"{val:.2f}" for val in group_means.loc[g]]
                    mean_rows_list.append(row_values)
            mean_df = pd.DataFrame(mean_rows_list, columns=final_table.columns)
            final_output = pd.concat([final_table, mean_df], ignore_index=True)

            # 将 DataFrame 转换为 Excel 字节流以便下载
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_output.to_excel(writer, index=False)
            processed_data = output.getvalue()

            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            # 提供下载按钮
            st.download_button(
                label="📥 下载完整分组结果 (Excel)",
                data=processed_data,
                file_name=f"分组结果_{now_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
