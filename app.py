import streamlit as st
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# YouTube投稿に必要な権限
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 最終解決：トークン手動取得")

# Secrets読み込み
client_config = json.loads(st.secrets["google_auth"]["client_secrets"])

# 【重要】リダイレクトURIを「手動コピー用」に固定します
# これにより、URLの不一致エラーを物理的に消します
flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri='http://localhost')

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

st.info("1. 下のリンクからGoogleログインしてください。")
st.markdown(f'[🔴 Googleログインを開始]({auth_url})')

st.warning("⚠️ ログイン後、画面が「接続できません」となりますが、それで正解です。その時のアドレスバーの【URL】をまるごと下に貼ってください。")

# 2. URLを貼り付けて解析する
url_input = st.text_input("2. 接続不可になった画面の「URL全体」をここに貼り付けてEnter")

if url_input:
    if "code=" in url_input:
        code = url_input.split("code=")[1].split("&")[0]
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.success("🎉 ついに成功しました！下のJSONをSecretsに貼ってください。")
            st.code(creds.to_json())
        except Exception as e:
            st.error(f"認証エラー: {e}")
