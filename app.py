import streamlit as st
import os
import json
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# 5GB制限解除
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000" 
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.set_page_config(page_title="YouTube投稿マネージャー Pro", layout="centered")
st.title("🎥 YouTubeアップローダー")

@st.cache_resource
def get_auth_flow():
    if "google_auth" in st.secrets:
        client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
        redirect_uri = "https://my-youtube-tool.streamlit.app/"
        return InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri=redirect_uri)
    return None

flow = get_auth_flow()

if "youtube" not in st.session_state:
    st.session_state.youtube = None

query_params = st.query_params

if st.session_state.youtube is None:
    if "code" not in query_params:
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.info("YouTubeと連携してください")
        st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#FF0000;color:white;border:none;padding:12px 24px;border-radius:5px;cursor:pointer;">🔴 Googleログインを開始する</button></a>', unsafe_allow_html=True)
        st.stop()
    else:
        try:
            flow.fetch_token(code=query_params["code"])
            st.session_state.youtube = build('youtube', 'v3', credentials=flow.credentials)
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"認証エラー: {e}")
            st.stop()

# --- 認証成功後のメイン画面 ---
youtube = st.session_state.youtube
st.success("✅ YouTube連携済み")

# 1. まず入力をすべて受け付ける
title = st.text_input("動画タイトル")
description = st.text_area("概要欄")
tag_input = st.text_input("タグ (カンマ区切り)")

col1, col2 = st.columns(2)
with col1:
    status_display = st.selectbox("公開設定", ["限定公開", "非公開", "公開", "予約投稿"])
    status_map = {"限定公開": "unlisted", "非公開": "private", "公開": "public", "予約投稿": "private"}
with col2:
    category = st.selectbox("カテゴリ", ["17 (スポーツ)", "22 (ブログ)", "20 (ゲーム)", "1 (映画/アニメ)", "10 (音楽)"])

# 予約投稿の入力欄
publish_at = None
if status_display == "予約投稿":
    st.markdown("#### 📅 予約投稿の詳細設定")
    d_col, t_col = st.columns(2)
    with d_col:
        # デフォルトは今日
        d = st.date_input("公開日", datetime.date.today())
    with t_col:
        # デフォルトは19:00
        t = st.time_input("公開時間", datetime.time(19, 0))
    
    # 日本時間の日時を作成
    local_dt = datetime.datetime.combine(d, t)
    
    # YouTube APIはUTC(世界標準時)が必要なので、日本時間から9時間を引く
    utc_dt =
