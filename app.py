import streamlit as st
import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# 5GB制限解除
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000" 
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.set_page_config(page_title="YouTube投稿マネージャー Pro", layout="centered")
st.title("🎥 YouTubeアップローダー")

# --- 認証フローのキャッシュ化（ここが解決の鍵） ---
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

# URLパラメータ取得
query_params = st.query_params

if st.session_state.youtube is None:
    if flow is None:
        st.error("Secretsの設定を確認してください。")
        st.stop()

    if "code" not in query_params:
        # authorization_urlを1回だけ生成するようにし、verifierを固定する
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.info("YouTubeと連携してください")
        st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#FF0000;color:white;border:none;padding:12px 24px;border-radius:5px;cursor:pointer;">🔴 Googleログインを開始する</button></a>', unsafe_allow_html=True)
        st.stop()
    else:
        try:
            # キャッシュされたflowを使ってトークンを取得
            flow.fetch_token(code=query_params["code"])
            st.session_state.youtube = build('youtube', 'v3', credentials=flow.credentials)
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"認証エラー: {e}")
            if st.button("リセットしてやり直す"):
                st.cache_resource.clear()
                st.query_params.clear()
                st.rerun()
            st.stop()

# --- 認証成功後のメイン画面 ---
st.success("✅ YouTube連携済み")
# (以下、投稿フォームのコードを続ける)
