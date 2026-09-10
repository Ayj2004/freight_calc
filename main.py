import streamlit as st

st.set_page_config(
    page_title="运费计算器 v1",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 侧边导航
pg = st.navigation([
    st.Page("pages/freight_calc.py", title="运费计算", icon="🧮"),
    st.Page("pages/settings.py", title="基础数据设置", icon="⚙️"),
])

pg.run()
