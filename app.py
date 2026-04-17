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

# --- 認証処理 ---
if "youtube" not in st.session_state:
    st.session_state.youtube = None

# URLのパラメータ（認証後の戻りコード）を取得
query_params = st.query_params

if st.session_state.youtube is None:
    if "google_auth" in st.secrets:
        # SecretsからJSONを読み込む
        client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
        # リダイレクトURIを自分のアプリのURLに設定（末尾の/を忘れずに）
        redirect_uri = "https://my-youtube-tool.streamlit.app/"
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri=redirect_uri)
    else:
        st.error("Secretsにgoogle_authが正しく設定されていません。")
        st.stop()

    # URLに認証コード("code")が含まれていない場合、ログインボタンを表示
    if "code" not in query_params:
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.info("ステップ1: YouTubeと連携してください")
        # リンクをクリックするとGoogleログイン画面へ飛びます
        st.markdown(f'''
            <a href="{auth_url}" target="_self">
                <button style="background-color:#FF0000;color:white;border:none;padding:12px 24px;border-radius:5px;cursor:pointer;font-size:16px;">
                    🔴 Googleログインを開始する
                </button>
            </a>
            ''', unsafe_allow_html=True)
        st.stop()
    else:
        # URLに含まれる"code"を使ってYouTubeとの通信を開始
        try:
            flow.fetch_token(code=query_params["code"])
            st.session_state.youtube = build('youtube', 'v3', credentials=flow.credentials)
            # URLを綺麗にするためにパラメータをクリアして再起動
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"認証に失敗しました: {e}")
            if st.button("もう一度やり直す"):
                st.query_params.clear()
                st.rerun()
            st.stop()

# --- 認証成功後のメイン画面 ---
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
    video_file = st.file_uploader("動画を選択 (最大5GB)", type=["mp4", "mov"])
    thumb_file = st.file_uploader("サムネイル画像 (任意)", type=["jpg", "png"])

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
            status_msg = st.empty()
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    bar.progress(int(status.progress() * 100))
                    status_msg.text(f"アップロード中... {int(status.progress() * 100)}%")
            
            st.success("🎉 投稿完了！")
            st.balloons()
            os.remove(temp_video)
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("タイトルと動画は必須です。")
