import streamlit as st
from datetime import date
from decimal import Decimal
from core.rules import load_all_data, get_active_rate, get_surcharge_dict
from core.calc import compute_item
import pandas as pd

st.title("🧮 运费计算器")
df_goods, df_dest, df_rates, df_surcharge = load_all_data()
surcharge_dict = get_surcharge_dict()
BUFFER_LIMIT = Decimal(str(st.secrets.get("BUFFER_LIMIT", "500")))

# 筛选启用的品类、目的地
goods_active = df_goods[df_goods["is_active"]].copy()
dest_active = df_dest[df_dest["is_active"]].copy()

# 下拉选择
col1, col2 = st.columns(2)
with col1:
    goods_name = st.selectbox(
        "货物品类",
        options=goods_active["name"].tolist(),
        index=0
    )
with col2:
    dest_name = st.selectbox(
        "目的地",
        options=dest_active["name"].tolist(),
        index=0
    )

# 获取ID
goods_row = goods_active[goods_active["name"] == goods_name].iloc[0]
dest_row = dest_active[dest_active["name"] == dest_name].iloc[0]
goods_id = goods_row["id"]
dest_id = dest_row["id"]

# 获取报价规则
rate_info = get_active_rate(goods_id, dest_id, date.today())

# 只读展示区域
if rate_info:
    uom = rate_info["uom"]
    unit_price = Decimal(str(rate_info["unit_price"]))
    pickup_fee = Decimal(str(rate_info["pickup_fee"]))
    st.info(f"""
    计费单位：**{uom}**｜单价：**{unit_price} 元/{uom}**
    提送费：**{pickup_fee} 元/票** {"（割草机未另加提送费）" if pickup_fee == 0 else ""}
    """)
else:
    st.warning("该品类+目的地暂无生效报价规则，填写数量无法计算，请前往【基础数据设置】添加报价规则。")
    uom = None

# 数量输入提示文案
help_text_map = {
    "台": "填台数，多台按单台报价累乘",
    "方": "填总方数",
    "吨": "填总吨数",
    "件": "填总件数"
}
help_text = help_text_map.get(uom, "") if uom else ""

# 表单
with st.form("calc_form"):
    if uom in ["台"]:
        qty = st.number_input("计费数量", min_value=0, step=1, format="%d", help=help_text)
    else:
        qty = st.number_input("计费数量", min_value=0.0, step=0.001, format="%.3f", help=help_text)

    with st.expander("⚙️ 高级选项（可选）"):
        surcharge_input = st.number_input("附加费（元/票）", min_value=0.0, value=0.0, step=1.0)
        buffer_input = st.number_input("容错金额（元/票）", min_value=0.0, value=0.0, step=1.0,
                                       help=f"不含容错的价格为运输底价，无降价空间；容错上限配置为 {BUFFER_LIMIT} 元")
        # P1 超长/异形，注释放开启用
        # length_m = st.number_input("货物长度(米)", min_value=0.0, value=0.0, step=0.1)
        # is_irregular = st.checkbox("是否异形件")

    submitted = st.form_submit_button("计算")

# 计算逻辑
if submitted:
    if not rate_info:
        st.error("无法计算：该线路尚未配置报价，请前往【设置】-【报价规则】添加")
    else:
        qty_dec = Decimal(str(qty))
        surcharge_dec = Decimal(str(surcharge_input))
        buffer_dec = Decimal(str(buffer_input))

        if buffer_dec > BUFFER_LIMIT:
            st.warning(f"⚠️ 容错金额 {buffer_dec} 超过配置上限 {BUFFER_LIMIT}，可继续计算，请留意报价风险")

        base_frt, lowest_frt, total_frt = compute_item(
            quantity=qty_dec,
            unit_price=unit_price,
            pickup_fee=pickup_fee,
            surcharge=surcharge_dec,
            buffer=buffer_dec
        )

        # 结果指标卡
        st.divider()
        st.subheader("📊 计算结果")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("最低运费（底价）", f"{lowest_frt} 元")
        with c2:
            st.metric("容错金额", f"{buffer_dec} 元")
        with c3:
            st.metric("运费合计（对外报价）", f"{total_frt} 元")

        # 明细表格
        result_df = pd.DataFrame([{
            "货物品类": goods_name,
            "目的地": dest_name,
            "单位": uom,
            "单价(元)": float(unit_price),
            "计费数量": float(qty_dec),
            "基础运费(元)": float(base_frt),
            "提送费(元)": float(pickup_fee),
            "附加费(元)": float(surcharge_dec),
            "容错金额(元)": float(buffer_dec),
            "运费合计(元)": float(total_frt)
        }])
        st.dataframe(result_df, hide_index=True, use_container_width=True)

        # 公式文本
        st.code(f"""基础运费 = {unit_price} 元/{uom} × {qty_dec} {uom} = {base_frt} 元
最低运费 = {base_frt} + 提送费 {pickup_fee} + 附加费 {surcharge_dec} = {lowest_frt} 元
运费合计 = {lowest_frt} + 容错 {buffer_dec} = {total_frt} 元""", language="text")

        if qty_dec == Decimal("0"):
            st.info("✅ 数量为0，本票按不发货计，不收取提送费")
