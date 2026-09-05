import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from openai import OpenAI
from utils.caption_text import prepare_caption_for_storage
from utils.logger import get_logger

logger = get_logger(__name__)

_SUMMARY_FORMAT = textwrap.dedent("""\
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
""")


def _build_openai_client():
    """SUMMARY_PROVIDER=openai|lmstudio 向けのクライアントとモデル名を返す"""
    provider = os.getenv("SUMMARY_PROVIDER", "codex")

    if provider == "lmstudio":
        client = OpenAI(
            base_url=os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key="lm-studio",
        )
        model = os.getenv("LM_STUDIO_MODEL", "local-model")
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = "gpt-4o"

    return client, model


def _build_prompt(caption_txt: str, caption_file_hint: str | None = None) -> str:
    if caption_file_hint:
        body = (
            f"作業ディレクトリ内の字幕ファイル `{caption_file_hint}` を読み、"
            "その内容だけを根拠に要約してください。"
            "シェルでの調査や追加ファイルの作成は不要です。"
            "最終応答には要約本文のみを出力してください。\n"
        )
    else:
        body = f"以下の字幕を要約してください。\n\n{caption_txt}\n"

    return textwrap.dedent(f"""\
        あなたは優秀な日本語の長文要約エキスパートです。
        以下にようやくのフォーマットと条件を提示します。これらに基づいて字幕の内容を丁寧に要約してください。

        {_SUMMARY_FORMAT}

        {body}
    """)


def _get_summary_via_openai_compatible(caption_txt: str) -> str:
    client, model = _build_openai_client()
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": _build_prompt(caption_txt)}],
    )
    response = completion.choices[0].message.content
    logger.info(f"要約生成完了 (provider=openai-compatible, model={model}, chars={len(response)})")
    return response


def _get_summary_via_codex(caption_txt: str) -> str:
    """自宅サーバー等にインストール済みの Codex CLI で要約する。

    字幕は一時ファイルにも残すが、本体は stdin でプロンプトに埋め込む。
    （エージェントのファイル読み取りに依存しない）
    """
    codex_bin = os.getenv("CODEX_BIN", "codex")
    if not shutil.which(codex_bin) and not Path(codex_bin).exists():
        raise FileNotFoundError(
            f"Codex CLI が見つかりません: {codex_bin}。"
            "自宅サーバーに Codex をインストールするか、CODEX_BIN を設定してください。"
        )

    timeout = int(os.getenv("CODEX_TIMEOUT", "600"))
    model = os.getenv("CODEX_MODEL", "").strip() or None

    with tempfile.TemporaryDirectory(prefix="yt_caption_") as tmp:
        workdir = Path(tmp)
        caption_path = workdir / "caption.txt"
        output_path = workdir / "summary_out.txt"
        caption_path.write_text(caption_txt, encoding="utf-8")

        cmd = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color", "never",
            "-s", "read-only",
            "-C", str(workdir),
            "-o", str(output_path),
        ]
        if model:
            cmd.extend(["-m", model])
        # プロンプトは argv ではなく stdin（長文の ARG_MAX 回避 + 確実に本文を渡す）
        cmd.append("-")

        prompt = _build_prompt(caption_txt)
        logger.info(
            f"Codex で要約を開始します (bin={codex_bin}, model={model or 'default'}, "
            f"caption_chars={len(caption_txt)}, timeout={timeout}s, caption_file={caption_path})"
        )
        completed = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            detail = stderr or stdout or f"exit={completed.returncode}"
            raise RuntimeError(f"Codex 要約に失敗しました: {detail}")

        if not output_path.exists():
            raise RuntimeError("Codex の出力ファイルが作成されませんでした")

        response = output_path.read_text(encoding="utf-8").strip()
        if not response:
            raise RuntimeError("Codex の要約結果が空でした")

        logger.info(f"要約生成完了 (provider=codex, chars={len(response)})")
        return response


def get_summary(caption_txt: str) -> str:
    """字幕情報を渡し、要約情報を得る"""
    caption_txt = prepare_caption_for_storage(caption_txt)
    provider = os.getenv("SUMMARY_PROVIDER", "codex").lower()

    if provider == "codex":
        return _get_summary_via_codex(caption_txt)
    if provider in ("openai", "lmstudio"):
        return _get_summary_via_openai_compatible(caption_txt)

    raise ValueError(
        f"未対応の SUMMARY_PROVIDER です: {provider} "
        "(codex / openai / lmstudio のいずれかを指定してください)"
    )
