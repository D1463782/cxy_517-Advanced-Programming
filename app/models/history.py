import sqlite3
from app.models.alarm import get_db_connection

class History:
    def __init__(self, id, alarm_id, ring_time, unlock_time, time_taken, wrong_attempts, difficulty_faced):
        self.id = id
        self.alarm_id = alarm_id
        self.ring_time = ring_time
        self.unlock_time = unlock_time
        self.time_taken = time_taken
        self.wrong_attempts = wrong_attempts
        self.difficulty_faced = difficulty_faced

    @staticmethod
    def create(alarm_id, ring_time, unlock_time, time_taken, wrong_attempts, difficulty_faced):
        """新增一筆起床歷史數據，記錄使用者解鎖鬧鐘的相關指標。"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO history (alarm_id, ring_time, unlock_time, time_taken, wrong_attempts, difficulty_faced)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (alarm_id, ring_time, unlock_time, time_taken, wrong_attempts, difficulty_faced)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error in History.create: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all():
        """取得所有起床歷史紀錄，依解鎖時間 (unlock_time) 降序排列（最新在最前面）。"""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                '''SELECT h.*, a.note as alarm_note 
                   FROM history h 
                   LEFT JOIN alarms a ON h.alarm_id = a.id 
                   ORDER BY h.unlock_time DESC'''
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Database error in History.get_all: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_stats():
        """獲取儀表板所需的聚合統計數據，包括：
        1. 總起床次數
        2. 平均解鎖秒數
        3. 總答錯次數
        4. 各難度分佈比例
        5. 最近 7 次的起床解鎖秒數趨勢 (用於圖表)
        """
        conn = get_db_connection()
        stats = {
            'total_wakeups': 0,
            'avg_time_taken': 0,
            'total_wrong_attempts': 0,
            'difficulty_distribution': {'easy': 0, 'medium': 0, 'hard': 0},
            'recent_trend': []
        }
        try:
            # 1. 總數與加總
            row = conn.execute(
                '''SELECT COUNT(*) as count, AVG(time_taken) as avg_time, SUM(wrong_attempts) as sum_wrong 
                   FROM history'''
            ).fetchone()
            
            if row and row['count'] > 0:
                stats['total_wakeups'] = row['count']
                stats['avg_time_taken'] = round(row['avg_time'], 1)
                stats['total_wrong_attempts'] = row['sum_wrong'] or 0

            # 2. 各難度分佈
            diff_rows = conn.execute(
                'SELECT difficulty_faced, COUNT(*) as count FROM history GROUP BY difficulty_faced'
            ).fetchall()
            for r in diff_rows:
                diff = r['difficulty_faced']
                if diff in stats['difficulty_distribution']:
                    stats['difficulty_distribution'][diff] = r['count']

            # 3. 最近 7 次的記錄趨勢（按時間升序以利前端繪製折線圖）
            trend_rows = conn.execute(
                '''SELECT unlock_time, time_taken, wrong_attempts 
                   FROM history 
                   ORDER BY unlock_time DESC LIMIT 7'''
            ).fetchall()
            # 翻轉陣列使其符合時間遞增
            stats['recent_trend'] = [dict(r) for r in reversed(trend_rows)]

            return stats
        except sqlite3.Error as e:
            print(f"Database error in History.get_stats: {e}")
            return stats
        finally:
            conn.close()
