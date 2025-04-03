from youtube_transcript_api import YouTubeTranscriptApi

def get_caption(video_id):
    """対象のYouTube動画のIDを指定"""

    # 日本語の字幕を取得
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])

    # 字幕テキストを結合して一つの文字列にする
    transcript_text = ' '.join([item['text'] for item in transcript])

    return transcript_text