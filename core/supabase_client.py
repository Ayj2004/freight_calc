import streamlit as st
from supabase import create_client

@st.cache_resource
def sb_client():
    """统一客户端，anon账号，可读可写"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)
