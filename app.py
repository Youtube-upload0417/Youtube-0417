import streamlit as st
import os
import json
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# 5GB制限解除
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000" 
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.set_page_config(page_title="YouTube投稿マネージャー Pro", layout="centered")
st.title("🎥 YouTubeアップローダー")

# --- 認証処理 ---
def get_youtube_client():
    creds = None
    # 1. すでにセッションにある場合
    if "youtube_creds" in st.session_state:
        creds = st.session_state.youtube_creds

    # 2. セッションにないが、Secretsに保存されたトークンがある場合（自動ログイン）
    if not creds and "youtube_token" in st.secrets:
        token_info = json.loads(st.secrets["youtube_token"])
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # トークンの有効期限が切れていたら更新
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.youtube_creds = creds

    if creds:
        return build('youtube', 'v3', credentials=creds)
    return None

youtube = get_youtube_client()

if youtube is None:
    # ログインが必要な場合のみボタンを表示
    client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
    redirect_uri = "https://my-youtube-tool.streamlit.app/"
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri=redirect_uri)
    
    query_params = st.query_params
    if "code" not in query_params:
        # access_type='offline' で「更新券」をもらう設定にする
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.info("YouTubeと連携してください")
        # target="_self" で今のタブで開く（エラー回避のため）
        st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#FF0000;color:white;border:none;padding:12px 24px;border-radius:5px;cursor:pointer;">🔴 Googleログインを開始する</button></a>', unsafe_allow_html=True)
        st.stop()
    else:
        # 認証完了処理
        flow.fetch_token(code=query_params["code"])
        creds = flow.credentials
        st.session_state.youtube_creds = creds
        
        # ★重要：初回ログイン時に表示される文字をSecretsに貼れば、次から自動ログインできます
        st.write("---")
        st.success("ログイン成功！下の文字をコピーして Secrets の 'youtube_token' に貼ってください：")
        st.code(creds.to_json())
        st.write("---")
        
        st.query_params.clear()
        if st.button("ログインを完了して進む"):
            st.rerun()
        st.stop()

# --- 認証成功後のメイン画面 ---
st.success("✅ YouTube連携済み（自動ログイン中）")

# (以下、これまでのタイトル入力や投稿処理のコードをそのまま続ける)
title = st.text_input("動画タイトル")
description = st.text_area("概要欄")
# ... (中略：これまでのコード)
