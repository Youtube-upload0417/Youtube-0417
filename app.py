import streamlit as st
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# 認証設定
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 トークン取得専用モード")

# Secretsの確認
if "google_auth" not in st.secrets:
    st.error("Secrets に 'google_auth' がありません")
    st.stop()

client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
redirect_uri = "https://my-youtube-tool.streamlit.app/"
flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri=redirect_uri)

# URLパラメータ取得
query_params = st.query_params

if "code" not in query_params:
    st.info("下のボタンからログインして、戻ってきたらトークンを表示します。")
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    # target="_self" で同じタブで開く
    st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#FF0000;color:white;border:none;padding:12px 24px;border-radius:5px;cursor:pointer;">🔴 Googleログインを開始する</button></a>', unsafe_allow_html=True)
else:
    # URLにcodeがある場合、一回だけトークン取得を試みる
    try:
        # fetch_token を一回だけ実行
        flow.fetch_token(code=query_params["code"])
        creds = flow.credentials
        
        st.success("🎉 トークンの取得に成功しました！これをコピーして Secrets に貼ってください。")
        # これを表示してコピーしてもらう
        st.code(creds.to_json())
        
        # パラメータを消してリセットするボタン
        if st.button("終わったらここを押してURLをきれいにしてください"):
            st.query_params.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.write("URLの末尾に古い ?code=... が残っていないか確認し、もう一度最初からやり直してください。")
        if st.button("最初からやり直す"):
            st.query_params.clear()
            st.rerun()
