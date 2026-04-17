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
        # code_verifierの不一致を防ぐため、敢えて古い認証方式（OOB）を固定
        flow = InstalledAppFlow.from_client_config(
            client_config, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
    else:
        st.error("Secretsにgoogle_authが設定されていません。")
        st.stop()

    # ★重要：このURLを一度生成したらセッションに保存して、画面がリフレッシュされても変わらないようにする
    if "auth_url" not in st.session_state:
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.session_state.auth_url = auth_url

    st.info("下のリンクからGoogleログインを行い、発行されたコードを貼り付けてください。")
    st.markdown(f'[👉 Googleログインを開始する]({st.session_state.auth_url})')
    
    # ユーザーがコードを入力する場所
    auth_code = st.text_input("認証コードを入力してEnter", key="auth_input_field")
    
    if auth_code:
        try:
            # flowオブジェクトを再作成せず、セッションを維持してトークンを取得
            flow.fetch_token(code=auth_code)
            st.session_state.youtube = build('youtube', 'v3', credentials=flow.credentials)
            st.success("認証に成功しました！")
            st.rerun()
        except Exception as e:
            st.error(f"認証エラー: {e}")
            # エラーが出たらURLを再生成できるようにリセットボタンを出す
            if st.button("認証をやり直す"):
                del st.session_state.auth_url
                st.rerun()
    st.stop()

# --- 以降、認証成功後のみ表示 ---
youtube = st.session_state.youtube
st.success("✅ YouTube連携済み")

# 動画投稿フォームのコード...（以下略、前回の後半部分と同じ）
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
