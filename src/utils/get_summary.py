import os
import textwrap
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)


def _build_client():
    """SUMMARY_PROVIDER に応じた OpenAI クライアントとモデル名を返す"""
    provider = os.getenv('SUMMARY_PROVIDER', 'lmstudio')

    if provider == 'lmstudio':
        client = OpenAI(
            base_url=os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1'),
            api_key='lm-studio',
        )
        model = os.getenv('LM_STUDIO_MODEL', 'local-model')
    else:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        model = 'gpt-4o'

    return client, model


def get_summary(caption_txt):
    """字幕情報を渡し、要約情報を得る"""

    message = textwrap.dedent(f"""\
        あなたは優秀な日本語の長文要約エキスパートです。
        以下にようやくのフォーマットと条件を提示します。これらに基づいて後で提供される字幕の内容を丁寧に要約してください。

        【必須条件】
        - 字幕が英語で提供されている場合でも、必ず日本語で要約してください。
        - 書き起こしの中で話者が特に強調している主張やメッセージを中心に要約してください。
        - 細かすぎるエピソードや繰り返される表現は省略または簡潔化し、要点が明確に伝わるようにしてください。
        - 元の文脈やニュアンスを損なわないよう注意し、話者の意図や感情も適切に表現してください。

        【出力構成】
        # 要約内容
        要約した内容をタイトルとして記載します。

        ## はじめに
        - 話者が視聴者に伝えたいこと、話し始めた動機、背景を整理します。

        ## 主なメッセージと重要なアドバイス
        - 話者が具体的に語っている内容を整理し、項目ごとに適切な小見出しを付けてください。
        - ポイントごとに簡潔かつ明快に5000文字程度に要約してください。

        ## おわりに
        - 話者が視聴者に最後に伝えたいことをまとめます。

        以下の字幕を要約してください。

        {caption_txt}
    """)

    client, model = _build_client()

    completion = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": message,
        }]
    )

    response = completion.choices[0].message.content
    logger.info(f"要約生成完了 (model={model}, chars={len(response)})")
    return response
