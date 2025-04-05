
def compare_data(db_data, new_data):
    """2つのデータセットを比較し、新しいデータを抽出する関数"""
    formatted_db_data, formatted_new_data = format_data(db_data, new_data)
    new_data = []
    for video in formatted_new_data:
        if video not in formatted_db_data:
            new_data.append(video)
    return new_data


def format_data(db_data, new_data):
    """取得したデータとDBのデータを整形して返す"""
    formatted_db_data = []
    for row in db_data:
        formatted_db_data.append({
            "video_id": row[0],
            "title": row[1],
            "published": str(row[3]),
            "link": row[4]
        })
    formatted_new_data = []
    for video in new_data:
        formatted_new_data.append({
            "video_id": video['video_id'],
            "title": video['title'],
            "published": video['published'][:10],
            "link": video['link']
        })

    # リストに戻す
    return formatted_db_data, formatted_new_data
