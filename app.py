import streamlit as st
import os
import json
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# 5GB制限解除
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000" 
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.set_page_config(page_title="YouTube投稿マネージャー Pro", layout="centered")
st.title("🎥 YouTubeアップローダー")

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

query_params = st.query_params

if st.session_state.youtube is None:
    if "code" not in query_params:
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.info("YouTubeと連携してください")
        st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#FF0000;color:white;border:none;padding:12px 24px;border-radius:5px;cursor:pointer;">🔴 Googleログインを開始する</button></a>', unsafe_allow_html=True)
        st.stop()
    else:
        try:
            flow.fetch_token(code=query_params["code"])
            st.session_state.youtube = build('youtube', 'v3', credentials=flow.credentials)
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"認証エラー: {e}")
            st.stop()

# --- 認証成功後のメイン画面 ---
youtube = st.session_state.youtube
st.success("✅ YouTube連携済み")

# 1. 入力セクション
title = st.text_input("動画タイトル")
description = st.text_area("概要欄")
tag_input = st.text_input("タグ (カンマ区切り)")

col1, col2 = st.columns(2)
with col1:
    status_display = st.selectbox("公開設定", ["限定公開", "非公開", "公開", "予約投稿"])
    status_map = {"限定公開": "unlisted", "非公開": "private", "公開": "public", "予約投稿": "private"}
with col2:
    category = st.selectbox("カテゴリ", ["17 (スポーツ)", "22 (ブログ)", "20 (ゲーム)", "1 (映画/アニメ)", "10 (音楽)"])

# 予約投稿の設定
publish_at = None
if status_display == "予約投稿":
    st.markdown("#### 📅 予約投稿の詳細設定")
    d_col, t_col = st.columns(2)
    with d_col:
        d = st.date_input("公開日", datetime.date.today())
    with t_col:
        t = st.time_input("公開時間", datetime.time(19, 0))
    
    # 日本時間の日時を結合
    local_dt = datetime.datetime.combine(d, t)
    # 日本時間(JST)からUTCに変換するために9時間を引く
    utc_dt = local_dt - datetime.timedelta(hours=9)
    # YouTube API専用の形式に変換
    publish_at = utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    st.info(f"🇯🇵 日本時間 **{local_dt.strftime('%Y/%m/%d %H:%M')}** に予約します")
    
    if local_dt <= datetime.datetime.now():
        st.warning("⚠️ 現在より未来の時間を設定してください。")

st.markdown("---")
video_file = st.file_uploader("動画を選択 (最大5GB)", type=["mp4", "mov"])
thumb_file = st.file_uploader("サムネイル画像 (任意)", type=["jpg", "png"])

# 2. 投稿アクション
if st.button("🚀 YouTubeへ投稿開始"):
    if video_file and title:
        temp_video = "temp_video.mp4"
        with open(temp_video, "wb") as f:
            f.write(video_file.read())
        
        try:
            body = {
                'snippet': {
                    'title': title, 
                    'description': description, 
                    'tags': [t.strip() for t in tag_input.split(",")] if tag_input else [],
                    'categoryId': category.split(' ')[0]
                },
                'status': {
                    'privacyStatus': status_map[status_display],
                    'selfDeclaredMadeForKids': False
                }
            }
            
            if publish_at:
                body['status']['publishAt'] = publish_at

            media = MediaFileUpload(temp_video, chunksize=1024*1024*10, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            
            bar = st.progress(0)
            status_msg = st.empty()
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    bar.progress(int(status.progress() * 100))
                    status_msg.text(f"動画をアップロード中... {int(status.progress() * 100)}%")
            
            video_id = response['id']
            
            if thumb_file:
                status_msg.text("サムネイルを設定中...")
                temp_thumb = "temp_thumb.png"
                with open(temp_thumb, "wb") as f:
                    f.write(thumb_file.read())
                youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(temp_thumb)).execute()
                os.remove(temp_thumb)

            st.success(f"🎉 投稿完了！ 動画ID: {video_id}")
            st.balloons()
            os.remove(temp_video)
            
        except Exception as e:
            st.error(f"エラー発生: {e}")
    else:
        st.warning("タイトルと動画ファイルを選択してください。")
