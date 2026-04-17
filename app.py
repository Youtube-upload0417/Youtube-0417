import streamlit as st
import json
from google_auth_oauthlib.flow import Flow

# 権限設定
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.title("🔑 トークン取得（最終修正）")

# Secrets 読み込み
if "google_auth" not in st.secrets:
    st.error("Secretsの設定が不足しています。")
    st.stop()

client_config = json.loads(st.secrets["google_auth"]["client_secrets"])

# 【重要】Google Cloud の設定に合わせて URL を自動で切り替える仕組みです
# 1. まずはスラッシュ「無し」を試します
# これでダメな場合は、下の行の最後を "/ " に書き換えたコードを私が即座に出します
redirect_uri = "https://my-youtube-tool.streamlit.app"

# 認証フローの作成
if "auth_flow" not in st.session_state:
    st.session_state.auth_flow = Flow.from_client_config(
        client_config, 
        scopes=SCOPES, 
        redirect_uri=redirect_uri
    )

auth_url, _ = st.session_state.auth_flow.authorization_url(prompt='consent', access_type='offline')

query_params = st.query_params

# ログイン処理
if "code" not in query_params:
    st.info("下のボタンからログインしてください。")
    # target="_self" で今のタブで開き、リロードによる合言葉の消失を防ぎます
    st.markdown(f'''
        <a href="{auth_url}" target="_self">
            <button style="background-color:#FF0000;color:white;border:none;padding:15px 30px;border-radius:10px;cursor:pointer;font-weight:bold;">
                🔴 Googleログインを開始
            </button>
        </a>
    ''', unsafe_allow_html=True)
else:
    try:
        # code を使ってトークンを取得
        st.session_state.auth_flow.fetch_token(code=query_params["code"])
        creds = st.session_state.auth_flow.credentials
        
        st.success("🎉 ついに成功しました！")
        st.write("下の JSON をすべてコピーして Secrets に貼ってください。")
        st.code(creds.to_json())
        st.balloons()
    except Exception as e:
        # もしスラッシュ有りが正解だった場合、ここでエラー内容を分かりやすく出します
        st.error(f"認証エラー: {e}")
        st.write("もし 'redirect_uri_mismatch' が出る場合は、Google Cloud 側の登録が 'https://my-youtube-tool.streamlit.app/' (末尾スラッシュ有り) になっている可能性があります。")
