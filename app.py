import streamlit as st
import os
import datetime
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# 5GB制限解除の設定
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000" 

# YouTube操作権限
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

def get_service():
    # --- ここを修正：Secretsから鍵を読み込む ---
    if "google_auth" in st.secrets:
        # Secretsに保存したJSON文字列を辞書形式に変換
        client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    else:
        # ローカル実行用（一応残しておきます）
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
    
    # Web上ではブラウザで認証を行うため、引数を調整
    creds = flow.run_local_server(port=0, open_browser=False)
    return build('youtube', 'v3', credentials=creds)

st.set_page_config(page_title="YouTube投稿マネージャー Pro", layout="centered")
st.title("🎥 YouTubeアップローダー (公開予約対応)")

# --- 入力フォーム ---
with st.container():
    title = st.text_input("動画タイトル")
    description = st.text_area("概要欄")
    tag_input = st.text_input("タグ (カンマ区切り)", placeholder="スポーツ, サッカー")

    col1, col2 = st.columns(2)
    with col1:
        status_display = st.selectbox("公開設定", ["限定公開", "非公開", "公開"], index=0)
        status_map = {"限定公開": "unlisted", "非公開": "private", "公開": "public"}
        status_api = status_map[status_display]
    with col2:
        category = st.selectbox("カテゴリ", ["17 (スポーツ)", "22 (ブログ)", "20 (ゲーム)"])

    # --- 公開予約設定 ---
    st.markdown("---")
    is_scheduled = st.checkbox("公開予約を設定する")
    publish_at_iso = None

    if is_scheduled:
        st.info("※予約投稿の場合、公開設定は自動的に『非公開』として送信されます。")
        col_d, col_t = st.columns(2)
        with col_d:
            d = st.date_input("公開日", datetime.date.today())
        with col_t:
            t = st.time_input("公開時刻", datetime.time(18, 0))
        
        dt = datetime.datetime.combine(d, t)
        publish_at_iso = dt.strftime('%Y-%m-%dT%H:%M:%S+09:00')

    st.markdown("---")
    video_file = st.file_uploader("動画を選択 (最大5GB)", type=["mp4", "mov"])
    thumb_file = st.file_uploader("サムネイル画像 (任意)", type=["jpg", "png", "jpeg"])

if st.button("🚀 YouTubeへ投稿開始"):
    if video_file and title:
        temp_video = "temp_video.mp4"
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with open(temp_video, "wb") as f:
            f.write(video_file.read())
        
        temp_thumb = None
        if thumb_file:
            temp_thumb = f"temp_thumb.{thumb_file.name.split('.')[-1]}"
            with open(temp_thumb, "wb") as f:
                f.write(thumb_file.read())

        try:
            youtube = get_service()
            tags = [t.strip() for t in tag_input.split(",")] if tag_input else []

            final_status = "private" if is_scheduled else status_api
            
            body = {
                'snippet': {
                    'title': title, 
                    'description': description, 
                    'tags': tags, 
                    'categoryId': category.split(' ')[0]
                },
                'status': {
                    'privacyStatus': final_status,
                    'selfDeclaredMadeForKids': False
                }
            }

            if is_scheduled:
                body['status']['publishAt'] = publish_at_iso

            media = MediaFileUpload(temp_video, chunksize=1024*1024*10, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            status_text.text("YouTubeへ転送中...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress_bar.progress(int(status.progress() * 100))
            
            if temp_thumb:
                status_text.text("サムネイルを設定中...")
                youtube.thumbnails().set(videoId=response['id'], media_body=MediaFileUpload(temp_thumb)).execute()

            st.success(f"投稿完了！ {'予約完了: ' + publish_at_iso if is_scheduled else '公開完了'}")
            st.balloons()
            os.remove(temp_video)
            if temp_thumb: os.remove(temp_thumb)

        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("タイトルと動画は必須です。")
