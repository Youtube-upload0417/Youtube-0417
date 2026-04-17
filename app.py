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
    # --- 【重要】すでに認証済みの場合は、その情報を再利用する ---
    if "youtube_creds" in st.session_state:
        return build('youtube', 'v3', credentials=st.session_state.youtube_creds)

    # Streamlit CloudのSecretsから認証情報を取得
    if "google_auth" in st.secrets:
        client_config = json.loads(st.secrets["google_auth"]["client_secrets"])
        flow = InstalledAppFlow.from_client_config(
            client_config, 
            SCOPES, 
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
    else:
        # ローカル環境用
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)

    # 認証用URLの生成
    auth_url, _ = flow.authorization_url(prompt='consent')

    # 画面に認証案内を表示
    st.info("🔑 YouTubeへのアクセス許可が必要です")
    st.markdown(f'1. [こちらをクリックしてGoogleログインを完了してください]({auth_url})')
    st.write("2. 表示されたコードをコピーして下の欄に貼り付けてEnterを押してください。")
    
    # ユーザーが認証コードを入力する欄
    auth_code = st.text_input("認証コードを入力してください", key="youtube_auth_code")

    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            # --- 【重要】取得した認証情報をセッションに保存する ---
            st.session_state.youtube_creds = flow.credentials
            # 認証が完了したので、一度画面をリセットして次の処理（投稿）を動かす
            st.rerun()
        except Exception as e:
            st.error(f"認証に失敗しました: {e}")
            st.stop()
    else:
        st.warning("認証コードが入力されるまで待機中です...")
        st.stop()

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
            # ここで get_service() を呼ぶ
            youtube = get_service()
            
            tags = [t.strip() for t in tag_input.split(",")] if tag_input else []

            # 予約設定がある場合は status を調整
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
