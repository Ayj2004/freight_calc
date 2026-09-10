import streamlit as st
import pandas as pd
from core.supabase_client import sb_client

@st.cache_data(ttl=300, show_spinner="加载基础数据...")
def load_all_data():
    sb = sb_client()
    # 货物品类
    res_goods = sb.table("goods").select("*").order("sort_order").execute()
    df_goods = pd.DataFrame(res_goods.data)
    # 目的地
    res_dest = sb.table("destinations").select("*").order("sort_order").execute()
    df_dest = pd.DataFrame(res_dest.data)
    # 报价规则：重点把日期字符串转为datetime
    res_rates = sb.table("freight_rates").select("*").execute()
    df_rates = pd.DataFrame(res_rates.data)
    # 转换日期列，自动识别空值
    df_rates["effective_from"] = pd.to_datetime(df_rates["effective_from"], errors="coerce")
    df_rates["effective_to"] = pd.to_datetime(df_rates["effective_to"], errors="coerce")

    # 附加费规则
    res_surcharge = sb.table("surcharge_rules").select("*").execute()
    df_surcharge = pd.DataFrame(res_surcharge.data)
    return df_goods, df_dest, df_rates, df_surcharge


def get_active_rate(goods_id: int, dest_id: int, today):
    """today 传 date 对象，统一转 Timestamp 对比"""
    df_goods, df_dest, df_rates, df_surcharge = load_all_data()
    today_ts = pd.Timestamp(today)
    mask = (
        (df_rates["goods_id"] == goods_id)
        & (df_rates["dest_id"] == dest_id)
        & (df_rates["is_active"] == True)
        & (df_rates["effective_from"] <= today_ts)
        & (
            (df_rates["effective_to"].isna())
            | (df_rates["effective_to"] >= today_ts)
        )
    )
    candidates = df_rates.loc[mask].sort_values("effective_from", ascending=False)
    if candidates.empty:
        return None
    row = candidates.iloc[0]
    return {
        "rate_id": row["id"],
        "uom": row["uom"],
        "unit_price": row["unit_price"],
        "pickup_fee": row["pickup_fee"],
    }

def get_surcharge_dict():
    """附加费规则转为字典，用于P1自动计算"""
    df_goods, df_dest, df_rates, df_surcharge = load_all_data()
    d = {}
    for _, r in df_surcharge.iterrows():
        d[r["code"]] = {
            "name": r["name"],
            "threshold": r["threshold"],
            "threshold_uom": r["threshold_uom"],
            "default_fee": r["default_fee"],
            "max_fee": r["max_fee"],
            "is_active": r["is_active"],
        }
    return d
