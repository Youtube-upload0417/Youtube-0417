import streamlit as st
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 トークン取得（最終手順）")

client_config = json.loads(st.secrets["google_auth"]["client_secrets"])

# ステップ1で登録した 'http://localhost' を使います
flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri='http://localhost')

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

st.info("1. 下のリンクをクリックしてログインしてください。")
st.markdown(f'<a href="{auth_url}" target="_blank">🔴 Googleログインを開始</a>', unsafe_allow_html=True)

st.warning("⚠️ ログイン後、画面が「接続できません」となりますが正常です。その時の【アドレスバーのURL】をまるごとコピーして下に貼ってください。")

# 2. URLを貼り付けて解析する
url_input = st.text_input("2. ログイン後に移動した先の「URL全体」をここに貼り付けてEnter")

if url_input:
    if "code=" in url_input:
        # URLからコード部分だけを抜き出す
        code = url_input.split("code=")[1].split("&")[0]
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.success("🎉 ついに成功しました！下のJSONをSecretsに貼ってください。")
            st.code(creds.to_json())
        except Exception as e:
            st.error(f"認証エラー: {e}")
    else:
        st.error("URLが正しくありません。code= を含むURLを貼り付けてください。")
