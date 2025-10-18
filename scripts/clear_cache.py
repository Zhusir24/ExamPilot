"""清除问卷缓存脚本"""
import sqlite3
import sys

def clear_questionnaire_cache(url):
    """清除指定URL的问卷缓存"""
    db_path = "data/database.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查找问卷ID
        cursor.execute("SELECT id, title FROM questionnaires WHERE url LIKE ?", (f"%{url}%",))
        results = cursor.fetchall()

        if not results:
            print(f"❌ 未找到URL包含 '{url}' 的问卷")
            return

        for qid, title in results:
            print(f"\n📝 找到问卷: ID={qid}, 标题='{title}'")

            # 删除题目记录
            cursor.execute("DELETE FROM questions WHERE questionnaire_id = ?", (qid,))
            deleted_questions = cursor.rowcount
            print(f"   删除题目: {deleted_questions} 条")

            # 删除答题会话
            cursor.execute("DELETE FROM answering_sessions WHERE questionnaire_id = ?", (qid,))
            deleted_sessions = cursor.rowcount
            print(f"   删除会话: {deleted_sessions} 条")

            # 删除答案记录
            cursor.execute("DELETE FROM answers WHERE questionnaire_id = ?", (qid,))
            deleted_answers = cursor.rowcount
            print(f"   删除答案: {deleted_answers} 条")

            # 删除问卷
            cursor.execute("DELETE FROM questionnaires WHERE id = ?", (qid,))
            print(f"   删除问卷: 1 条")

        conn.commit()
        print(f"\n✅ 缓存清除成功！现在可以重新解析问卷了。")

    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 清除测试问卷的缓存
    url = "rDTLYkN"  # 或完整URL的一部分
    if len(sys.argv) > 1:
        url = sys.argv[1]

    print(f"🗑️  清除URL包含 '{url}' 的问卷缓存...")
    clear_questionnaire_cache(url)
