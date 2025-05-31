import os
import textwrap
from openai import OpenAI

def get_summary(caption_txt):
    """OpenAPI へ字幕情報を渡し、要約情報を得る"""

    message = textwrap.dedent(f"""\
        あなたは優秀な日本語の長文要約エキスパートです。
        以下にようやくのフォーマットと条件を提示します。これらに基づいて後で提供される字幕の内容を丁寧に要約してください。

        【必須条件】
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

    # OpenAPIのエンドポイントURLとAPIキーを設定
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": message,
        }]
    )

    response = completion.choices[0].message.content

    print("要約結果:", response)

    return response
