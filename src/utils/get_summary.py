import requests
import json
import os
import textwrap


def get_summary(caption_txt):
    """Ollama へ字幕情報を渡し、要約情報を得る"""

    message = textwrap.dedent(f"""\
        以下の字幕を要約してください。

        {caption_txt}
    """)

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "youtube-summary-tanuki",
        "stream": True,  # ストリーミングモード
        "num_predict": 2048,
        "messages": [{
            "role": "user",
            "content": message,
        }]
    }

    API_SERVER_URL = os.getenv('API_SERVER_URL')
    response = requests.post(
        API_SERVER_URL, headers=headers, json=payload, stream=True)
    response.raise_for_status()

    full_content = ""

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "message" in data and "content" in data["message"]:
                full_content += data["message"]["content"]

    return full_content
