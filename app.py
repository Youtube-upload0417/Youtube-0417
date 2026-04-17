import streamlit as st
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# YouTube投稿に必要な権限
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 手動トークン取得（最終手段）")

# Secrets読み込み
client_config = json.loads(st.secrets["google_auth"]["client_secrets"])

# ★リダイレクトURIを「デスクトップアプリ用」に強制変更します（これでエラーが消えます）
flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

st.info("1. 下のリンクを開いてログインし、表示された「コード」をコピーしてください。")
st.markdown(f'[🔴 ここをクリックしてログイン]({auth_url})')

# 2. 手動で貼り付け
code = st.text_input("2. コピーしたコードをここに貼り付けてEnterを押してください")

if code:
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.success("🎉 成功しました！この文字を全部コピーして Secrets に貼ってください。")
        st.code(creds.to_json())
    except Exception as e:
        st.error(f"エラー: {e}")
