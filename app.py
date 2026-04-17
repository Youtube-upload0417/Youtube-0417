import streamlit as st
import json
from google_auth_oauthlib.flow import Flow

# YouTube投稿の権限
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 トークン取得（最終解決版）")

# 1. Secrets読み込み
if "google_auth" not in st.secrets:
    st.error("Secretsの設定が不足しています。")
    st.stop()

client_config = json.loads(st.secrets["google_auth"]["client_secrets"])

# 2. 【最重要】Google Cloud側に登録されているはずの正確なURLをここで固定します
# もしこれでもエラーが出る場合は、下のURLの末尾の「/」を消してください
redirect_uri = "https://my-youtube-tool.streamlit.app/"

# 3. 認証フローの作成（セッションで固定してエラー回避）
if "auth_flow" not in st.session_state:
    st.session_state.auth_flow = Flow.from_client_config(
        client_config, 
        scopes=SCOPES, 
        redirect_uri=redirect_uri
    )

auth_url, _ = st.session_state.auth_flow.authorization_url(prompt='consent', access_type='offline')

query_params = st.query_params

if "code" not in query_params:
    st.info("下のボタンからログインしてください。")
    # target="_self" で今のタブで開き、不一致エラーを徹底回避
    st.markdown(f'''
        <a href="{auth_url}" target="_self">
            <button style="background-color:#FF0000;color:white;border:none;padding:15px 30px;border-radius:10px;cursor:pointer;font-weight:bold;">
                🔴 Googleログインを開始
            </button>
        </a>
    ''', unsafe_allow_html=True)
else:
    # 戻ってきた時
    try:
        # URLにあるcodeを使ってトークンを確定
        st.session_state.auth_flow.fetch_token(code=query_params["code"])
        creds = st.session_state.auth_flow.credentials
        
        st.success("🎉 ついに成功しました！")
        st.write("この JSON をすべてコピーして Secrets に貼ってください。")
        st.code(creds.to_json())
        st.balloons()
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
