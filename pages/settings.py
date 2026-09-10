import streamlit as st
import pandas as pd
from core.supabase_client import sb_client
from core.rules import load_all_data

sb = sb_client()

st.title("⚙️ 基础数据设置")
st.warning("⚠️ 修改价格立即生效，会影响后续每一次运费计算，请谨慎操作！")

tab_goods, tab_dest, tab_rates, tab_surcharge = st.tabs(["货物品类", "目的地", "报价规则", "附加费规则"])

# -------------------------- Tab1 货物品类 --------------------------
with tab_goods:
    st.subheader("货物品类维护")
    df_goods, _, _, _ = load_all_data()
    edited_goods = st.data_editor(
        df_goods,
        num_rows="dynamic",
        disabled=["id", "created_at"],
        column_config={
            "name": st.column_config.TextColumn("名称", required=True),
            "default_uom": st.column_config.SelectboxColumn("默认计费单位", options=["台", "方", "吨", "件"], required=True),
            "is_active": st.column_config.CheckboxColumn("启用"),
            "sort_order": st.column_config.NumberColumn("排序", min_value=0, step=1)
        },
        use_container_width=True,
        hide_index=True
    )
    if st.button("保存品类数据", key="save_goods"):
        if edited_goods["name"].duplicated().any():
            st.error("品类名称不能重复！")
        elif edited_goods["name"].isna().any():
            st.error("品类名称不能为空！")
        else:
            sb.table("goods").upsert(edited_goods.to_dict("records")).execute()
            st.cache_data.clear()
            st.success("品类保存成功！")
            st.rerun()

# -------------------------- Tab2 目的地 --------------------------
with tab_dest:
    st.subheader("目的地维护")
    _, df_dest, _, _ = load_all_data()
    edited_dest = st.data_editor(
        df_dest,
        num_rows="dynamic",
        disabled=["id"],
        column_config={
            "name": st.column_config.TextColumn("名称", required=True),
            "is_active": st.column_config.CheckboxColumn("启用"),
            "sort_order": st.column_config.NumberColumn("排序", min_value=0, step=1)
        },
        use_container_width=True,
        hide_index=True
    )
    if st.button("保存目的地数据", key="save_dest"):
        if edited_dest["name"].duplicated().any():
            st.error("目的地名称不能重复！")
        elif edited_dest["name"].isna().any():
            st.error("目的地名称不能为空！")
        else:
            sb.table("destinations").upsert(edited_dest.to_dict("records")).execute()
            st.cache_data.clear()
            st.success("目的地保存成功！")
            st.rerun()

# -------------------------- Tab3 报价规则 --------------------------
with tab_rates:
    st.subheader("报价规则维护")
    df_goods, df_dest, df_rates, _ = load_all_data()
    goods_map = dict(zip(df_goods["id"], df_goods["name"]))
    dest_map = dict(zip(df_dest["id"], df_dest["name"]))
    df_rates_display = df_rates.copy()
    df_rates_display["goods_name"] = df_rates_display["goods_id"].map(goods_map)
    df_rates_display["dest_name"] = df_rates_display["dest_id"].map(dest_map)

    edited_rates = st.data_editor(
        df_rates_display,
        num_rows="dynamic",
        disabled=["id", "created_at"],
        column_config={
            "goods_id": st.column_config.SelectboxColumn("货物品类", options=df_goods["id"].tolist(), format_func=lambda x: goods_map[x], required=True),
            "dest_id": st.column_config.SelectboxColumn("目的地", options=df_dest["id"].tolist(), format_func=lambda x: dest_map[x], required=True),
            "uom": st.column_config.SelectboxColumn("计费单位", options=["台", "方", "吨", "件"], required=True),
            "unit_price": st.column_config.NumberColumn("单价（元/单位）", min_value=0, step=0.01, required=True),
            "pickup_fee": st.column_config.NumberColumn("提送费（元/票）", min_value=0, step=0.01),
            "effective_from": st.column_config.DateColumn("生效开始", required=True),
            "effective_to": st.column_config.DateColumn("生效结束（空=长期有效）"),
            "is_active": st.column_config.CheckboxColumn("启用"),
            "remark": st.column_config.TextColumn("备注"),
            "goods_name": None,
            "dest_name": None
        },
        use_container_width=True,
        hide_index=True
    )
    if st.button("保存报价规则", key="save_rates"):
        save_df = edited_rates.drop(["goods_name", "dest_name"], axis=1, errors="ignore")

        # =========关键处理：datetime -> YYYY-MM-DD字符串存入Supabase=========
        def fmt_date(d):
            if pd.isna(d):
                return None
            return d.strftime("%Y-%m-%d")

        save_df["effective_from"] = save_df["effective_from"].apply(fmt_date)
        save_df["effective_to"] = save_df["effective_to"].apply(fmt_date)

        sb.table("freight_rates").upsert(save_df.to_dict("records")).execute()
        st.cache_data.clear()
        st.success("报价规则保存成功！")
        st.rerun()

    # 矩阵速览（只读）
    st.divider()
    st.subheader("报价矩阵速览（只读）")
    df_view = df_rates[df_rates["is_active"]].copy()
    df_view["goods_name"] = df_view["goods_id"].map(goods_map)
    df_view["dest_name"] = df_view["dest_id"].map(dest_map)

    # 按行生成展示文字
    df_view["display_text"] = df_view.apply(
        lambda row: f"{row['unit_price']}元/{row['uom']} | 提送{row['pickup_fee']}",
        axis=1
    )
    pivot = df_view.pivot(index="goods_name", columns="dest_name", values="display_text")
    st.dataframe(pivot.fillna("—"), use_container_width=True)


# -------------------------- Tab4 附加费规则 --------------------------
with tab_surcharge:
    st.subheader("附加费规则维护")
    _, _, _, df_surcharge = load_all_data()
    edited_surcharge = st.data_editor(
        df_surcharge,
        num_rows="dynamic",
        disabled=["id"],
        column_config={
            "code": st.column_config.TextColumn("规则编码", required=True),
            "name": st.column_config.TextColumn("名称", required=True),
            "threshold": st.column_config.NumberColumn("阈值", step=0.001),
            "threshold_uom": st.column_config.TextColumn("阈值单位（m/kg等）"),
            "default_fee": st.column_config.NumberColumn("默认费用", min_value=0, step=0.01),
            "max_fee": st.column_config.NumberColumn("费用上限", min_value=0, step=0.01),
            "is_active": st.column_config.CheckboxColumn("启用"),
        },
        use_container_width=True,
        hide_index=True
    )
    if st.button("保存附加费规则", key="save_surcharge"):
        sb.table("surcharge_rules").upsert(edited_surcharge.to_dict("records")).execute()
        st.cache_data.clear()
        st.success("附加费规则保存成功！")
        st.rerun()
