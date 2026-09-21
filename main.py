import streamlit as st

st.set_page_config(
    page_title="运费计算器 v1",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

DOWNLOAD_URL = "https://github.com/Ayj2004/freight_calc/releases/download/v1/freight_calc_desktop_v1.exe"
button_html = f'''
<style>
div[data-testid="stAppViewContainer"] {{
    position:relative;
}}
.download-btn {{
    position: fixed;
    top: 18px;
    right: 30px;
    z-index:99999 !important;
}}
.download-btn a {{
    background-color: #2563eb;
    color: white !important;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight:bold;
    font-size:14px;
}}
.download-btn a:hover {{
    background-color: #1d4ed8;
}}
</style>
<div class="download-btn">
    <a href="{DOWNLOAD_URL}" target="_blank">💻 下载桌面版</a>
</div>
'''
# 高度改成 80，不要写0，避免渲染失效
st.components.v1.html(button_html, height=80)

# 侧边导航
pg = st.navigation([
    st.Page("pages/freight_calc.py", title="运费计算", icon="🧮"),
    st.Page("pages/settings.py", title="基础数据设置", icon="⚙️"),
])
pg.run()
