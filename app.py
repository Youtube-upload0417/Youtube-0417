import streamlit as st
import os
import json
import datetime
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# --- 設定 ---
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

REDIRECT_URI = "https://my-youtube-tool.streamlit.app/"

st.set_page_config(page_title="YouTube投稿マネージャー", layout="centered")
st.title("🎥 YouTubeアップローダー")

# --- セッション初期化 ---
if "credentials" not in st.session_state:
    st.session_state.credentials = None

if "state" not in st.session_state:
    st.session_state.state = None

# --- Flow生成 ---
def create_flow(state=None):
    client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )

query_params = st.query_params

# --- 認証処理 ---
if st.session_state.credentials:
    creds = st.session_state.credentials

    # トークン更新
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.credentials = creds

else:
    if "code" not in query_params:
        flow = create_flow()

        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

        st.session_state.state = state

        st.info("YouTubeと連携してください")
        st.markdown(
            f'<a href="{auth_url}" target="_self">'
            f'<button style="background-color:#FF0000;color:white;padding:12px 24px;border:none;border-radius:5px;">🔴 Googleログイン</button>'
            f'</a>',
            unsafe_allow_html=True
        )
        st.stop()

    else:
        try:
            flow = create_flow(state=st.session_state.state)
            flow.fetch_token(code=query_params["code"])

            st.session_state.credentials = flow.credentials

            st.query_params.clear()
            st.rerun()

        except Exception:
            st.error("認証エラーが発生しました。再ログインしてください。")

            if st.button("🔄 再ログイン"):
                st.session_state.credentials = None
                st.session_state.state = None
                st.query_params.clear()
                st.rerun()

            st.stop()

# --- YouTubeオブジェクト生成（重要） ---
youtube = None
if st.session_state.credentials:
    youtube = build("youtube", "v3", credentials=st.session_state.credentials)
    st.success("✅ YouTube連携済み")

# --- 投稿画面 ---
title = st.text_input("動画タイトル")
description = st.text_area("概要欄")

col1, col2 = st.columns(2)

with col1:
    status_display = st.selectbox("公開設定", ["限定公開", "非公開", "公開", "予約投稿"])
    status_map = {
        "限定公開": "unlisted",
        "非公開": "private",
        "公開": "public",
        "予約投稿": "private"
    }

with col2:
    category_map = {
        "スポーツ": "17",
        "ブログ": "22",
        "ゲーム": "20",
        "映画/アニメ": "1"
    }
    category_display = st.selectbox("カテゴリ", list(category_map.keys()))
    category = category_map[category_display]

publish_at = None
if status_display == "予約投稿":
    st.markdown("#### 📅 予約投稿の設定")
    d_col, t_col = st.columns(2)

    with d_col:
        d = st.date_input("公開日", datetime.date.today())
    with t_col:
        t = st.time_input("公開時間", datetime.time(19, 0))

    dt = datetime.datetime.combine(d, t)
    utc_dt = dt - datetime.timedelta(hours=9)
    publish_at = utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    st.info(f"🇯🇵 日本時間 {dt.strftime('%Y/%m/%d %H:%M')} に公開されます")

st.markdown("---")

video_file = st.file_uploader("動画を選択", type=["mp4", "mov"])
thumb_file = st.file_uploader("サムネイル画像（任意）", type=["jpg", "png"])

# --- 投稿処理 ---
if st.button("🚀 YouTubeへ投稿開始"):

    if not youtube:
        st.warning("先にGoogleログインしてください")
        st.stop()

    if not video_file or not title:
        st.warning("タイトルと動画は必須です。")
        st.stop()

    # 一時ファイル
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_file.read())
        temp_video = tmp.name

    try:
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': category
            },
            'status': {
                'privacyStatus': status_map[status_display],
                'selfDeclaredMadeForKids': False
            }
        }

        if publish_at:
            body['status']['publishAt'] = publish_at

        media = MediaFileUpload(temp_video, chunksize=1024*1024*10, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        bar = st.progress(0)
        status_msg = st.empty()

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                bar.progress(progress)
                status_msg.text(f"アップロード中... {progress}%")

        video_id = response['id']

        # サムネイル
        if thumb_file:
            status_msg.text("サムネイル設定中...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(thumb_file.read())
                temp_thumb = tmp.name

            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(temp_thumb)
            ).execute()

            os.remove(temp_thumb)

        st.success(f"🎉 投稿完了！ 動画ID: {video_id}")
        st.balloons()

        os.remove(temp_video)

    except Exception as e:
        import traceback
        st.error(traceback.format_exc())
