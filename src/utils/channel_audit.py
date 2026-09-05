"""YouTube の取得結果と DB の登録状況を比較する純粋な監査ロジック。"""

from typing import Any, Iterable


def _sort_videos(videos: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        videos,
        key=lambda video: (
            str(video.get("published") or ""),
            str(video.get("video_id") or ""),
        ),
        reverse=True,
    )


def _status_counts(db_videos: Iterable[dict[str, Any]]) -> dict[str, int]:
    videos = list(db_videos)
    return {
        "caption_ready": sum(video.get("caption") is not None for video in videos),
        "caption_unavailable": sum(
            bool(video.get("caption_unavailable")) for video in videos
        ),
        "caption_pending": sum(
            video.get("caption") is None
            and not bool(video.get("caption_unavailable"))
            for video in videos
        ),
        "summary_ready": sum(video.get("summary") is not None for video in videos),
        "summary_pending": sum(video.get("summary") is None for video in videos),
        "discord_sent": sum(bool(video.get("summary_send_flag")) for video in videos),
        "discord_pending": sum(
            not bool(video.get("summary_send_flag")) for video in videos
        ),
    }


def build_channel_audit(
    *,
    channel_id: str,
    channel_name: str,
    remote_videos: Iterable[dict[str, Any]],
    db_videos: Iterable[dict[str, Any]],
    remote_video_count: int | None = None,
    scan_limit: int | None = None,
    full_scan: bool | None = None,
    scan_description: str | None = None,
    remote_channel_name: str | None = None,
) -> dict[str, Any]:
    """1チャンネル分の比較結果を返す。

    ``scan_limit`` が None の場合はアップロード一覧を全件比較する。
    件数制限時は、DB側の古い動画を「YouTubeに存在しない」と誤判定しないよう、
    ``db_only`` には入れず ``outside_scan`` として扱う。
    """
    is_full_scan = scan_limit is None if full_scan is None else full_scan
    remote_by_id = {
        str(video["video_id"]): dict(video)
        for video in remote_videos
        if video.get("video_id")
    }
    db_by_id = {
        str(video["video_id"]): dict(video)
        for video in db_videos
        if video.get("video_id")
    }

    remote_only = [
        remote_by_id[video_id]
        for video_id in remote_by_id.keys() - db_by_id.keys()
    ]
    not_in_scan = [
        db_by_id[video_id]
        for video_id in db_by_id.keys() - remote_by_id.keys()
    ]

    return {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "remote_channel_name": remote_channel_name,
        "remote_video_count": remote_video_count,
        "scanned_video_count": len(remote_by_id),
        "scan_limit": scan_limit,
        "full_scan": is_full_scan,
        "scan_description": scan_description,
        "db_video_count": len(db_by_id),
        "matched_count": len(remote_by_id.keys() & db_by_id.keys()),
        "missing_in_db": _sort_videos(remote_only),
        "db_only": _sort_videos(not_in_scan) if is_full_scan else [],
        "outside_scan": _sort_videos(not_in_scan) if not is_full_scan else [],
        "status_counts": _status_counts(db_by_id.values()),
    }


def _format_video(video: dict[str, Any]) -> str:
    video_id = video.get("video_id", "?")
    published = video.get("published") or "日付不明"
    title = video.get("title") or "(タイトル不明)"
    link = video.get("link") or f"https://www.youtube.com/watch?v={video_id}"
    return f"  - {published} {video_id} {title}\n    {link}"


def format_audit_report(reports: Iterable[dict[str, Any]]) -> str:
    """監査結果を人間向けの日本語テキストにする。"""
    lines: list[str] = []
    for index, report in enumerate(reports):
        if index:
            lines.append("")

        channel_name = report.get("channel_name") or "(名称不明)"
        channel_id = report.get("channel_id") or "?"
        lines.extend([f"## {channel_name} ({channel_id})"])

        if report.get("error"):
            lines.append(f"エラー: {report['error']}")
            if "status_counts" in report:
                lines.append(f"DB登録動画数: {report['db_video_count']} 件")
                counts = report["status_counts"]
                lines.extend(
                    [
                        "DB内の処理状況（YouTube取得失敗のため差分は未判定）:",
                        f"  字幕取得済み {counts['caption_ready']} / 字幕取得不可 {counts['caption_unavailable']} / 字幕待ち {counts['caption_pending']}",
                        f"  要約済み {counts['summary_ready']} / 要約待ち {counts['summary_pending']}",
                        f"  Discord送信済み {counts['discord_sent']} / 送信待ち {counts['discord_pending']}",
                    ]
                )
            continue

        remote_name = report.get("remote_channel_name")
        if remote_name and remote_name != channel_name:
            lines.append(f"YouTube上の名称: {remote_name}")

        remote_count = report.get("remote_video_count")
        remote_count_text = "不明" if remote_count is None else str(remote_count)
        scan_limit = report.get("scan_limit")
        scan_text = report.get("scan_description")
        if not scan_text:
            is_full_scan = report.get("full_scan", scan_limit is None)
            scan_text = "全件" if is_full_scan else f"最新 {scan_limit} 件"
        lines.extend(
            [
                f"YouTube公開動画数: {remote_count_text}",
                f"今回の比較範囲: {scan_text}（{report['scanned_video_count']} 件取得）",
                f"DB登録動画数: {report['db_video_count']} 件",
                f"一致: {report['matched_count']} 件",
                f"未取得候補（YouTubeにあり / DBになし）: {len(report['missing_in_db'])} 件",
            ]
        )

        counts = report["status_counts"]
        lines.extend(
            [
                "DB内の処理状況:",
                f"  字幕取得済み {counts['caption_ready']} / 字幕取得不可 {counts['caption_unavailable']} / 字幕待ち {counts['caption_pending']}",
                f"  要約済み {counts['summary_ready']} / 要約待ち {counts['summary_pending']}",
                f"  Discord送信済み {counts['discord_sent']} / 送信待ち {counts['discord_pending']}",
            ]
        )

        if report["missing_in_db"]:
            lines.append("未取得候補の一覧:")
            lines.extend(
                _format_video(video) for video in report["missing_in_db"]
            )

        if report["db_only"]:
            lines.append("YouTubeから確認できなかったDB動画（削除・非公開等の可能性）:")
            lines.extend(_format_video(video) for video in report["db_only"])

        if report["outside_scan"]:
            lines.append(
                "今回の最新件数範囲外にあるDB動画（削除とは判定しない）: "
                f"{len(report['outside_scan'])} 件"
            )

    return "\n".join(lines)
