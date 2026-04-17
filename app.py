import streamlit as st
import os
import datetime
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# 5GB制限解除
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000" 
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

st.set_page_config(page_title="YouTube投稿マネージャー Pro", layout="centered")
st.title("🎥 YouTubeアップローダー")

# --- 認証処理（セッションで管理） ---
if "youtube" not in st.session_state:
    st.session_state.youtube = None

if st.session_state.youtube is None:
    st.subheader("ステップ1: YouTubeと連携する")
    
    if "google_auth" in st.secrets:
        client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
        flow = InstalledAppFlow.from_client_config(
            client_config, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
    else:
        st.error("Secretsにgoogle_authが設定されていません。")
        st.stop()

    auth_url, _ = flow.authorization_url(prompt='consent')
    st.info("下のリンクからGoogleログインを行い、発行されたコードを貼り付けてください。")
    st.markdown(f'[👉 Googleログインを開始する]({auth_url})')
    
    auth_code = st.text_input("認証コードを入力してEnter")
    
    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            st.session_state.youtube = build('youtube', 'v3', credentials=flow.credentials)
            st.success("認証に成功しました！投稿フォームを表示します。")
            st.rerun()
        except Exception as e:
            st.error(f"認証エラー: {e}")
    st.stop() # 認証されるまでここで止める

# --- ここからメインの投稿フォーム（認証済みの時だけ表示される） ---
youtube = st.session_state.youtube
st.success("✅ YouTube連携済み")

with st.container():
    title = st.text_input("動画タイトル")
    description = st.text_area("概要欄")
    tag_input = st.text_input("タグ (カンマ区切り)")
    
    col1, col2 = st.columns(2)
    with col1:
        status_display = st.selectbox("公開設定", ["限定公開", "非公開", "公開"])
        status_map = {"限定公開": "unlisted", "非公開": "private", "公開": "public"}
    with col2:
        category = st.selectbox("カテゴリ", ["17 (スポーツ)", "22 (ブログ)", "20 (ゲーム)"])

    st.markdown("---")
    video_file = st.file_uploader("動画を選択", type=["mp4", "mov"])
    thumb_file = st.file_uploader("サムネイル画像", type=["jpg", "png"])

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
                'status': {'privacyStatus': status_map[status_display], 'selfDeclaredMadeForKids': False}
            }
            
            media = MediaFileUpload(temp_video, chunksize=1024*1024*10, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            
            bar = st.progress(0)
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status: bar.progress(int(status.progress() * 100))
            
            st.success("投稿完了！")
            st.balloons()
            os.remove(temp_video)
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("タイトルと動画は必須です。")
