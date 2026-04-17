import streamlit as st
import json
from google_auth_oauthlib.flow import Flow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 最終トークン取得")

if "google_auth" not in st.secrets:
    st.error("Secretsの設定が漏れています")
    st.stop()

# 認証設定の読み込み
client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
redirect_uri = "https://my-youtube-tool.streamlit.app/"

# この Flow オブジェクトをセッションで固定するのが解決の鍵
if "auth_flow" not in st.session_state:
    st.session_state.auth_flow = Flow.from_client_config(
        client_config, scopes=SCOPES, redirect_uri=redirect_uri
    )

query_params = st.query_params

if "code" not in query_params:
    # 1. ログインURLを作る（ここで合言葉が生成される）
    auth_url, _ = st.session_state.auth_flow.authorization_url(prompt='consent', access_type='offline')
    st.info("下のリンクを【右クリック】して【新しいタブで開く】で進んでください。")
    st.markdown(f'<a href="{auth_url}" target="_blank">🔴 ここを右クリックして新しいタブで開く</a>', unsafe_allow_html=True)
else:
    # 2. 戻ってきたら、セッションに保存しておいた Flow で認証する
    try:
        st.session_state.auth_flow.fetch_token(code=query_params["code"])
        creds = st.session_state.auth_flow.credentials
        st.success("🎉 ついに成功しました！下の文字を全部コピーしてください。")
        st.code(creds.to_json())
        st.balloons()
    except Exception as e:
        st.error(f"エラー: {e}")
        if st.button("最初からやり直す"):
            st.query_params.clear()
            st.rerun()
