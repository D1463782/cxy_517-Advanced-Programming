import sqlite3
from datetime import datetime, timedelta
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
            'recent_trend': [],
            'current_streak': 0,
            'longest_streak': 0
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

            # 融入連續早起天數
            streak_data = History.get_streak_stats()
            stats['current_streak'] = streak_data['current_streak']
            stats['longest_streak'] = streak_data['longest_streak']

            return stats
        except sqlite3.Error as e:
            print(f"Database error in History.get_stats: {e}")
            return stats
        finally:
            conn.close()

    @staticmethod
    def get_streak_stats():
        """動態計算連續早起天數 (Streak) 與歷史最長連續天數。"""
        conn = get_db_connection()
        try:
            # 取得所有解鎖日期，去重並依時間降序排列
            rows = conn.execute(
                "SELECT DISTINCT date(unlock_time) as unlock_date FROM history ORDER BY unlock_date DESC"
            ).fetchall()
            
            dates = []
            for row in rows:
                if row['unlock_date']:
                    try:
                        d = datetime.strptime(row['unlock_date'], '%Y-%m-%d').date()
                        dates.append(d)
                    except ValueError:
                        pass
            
            if not dates:
                return {'current_streak': 0, 'longest_streak': 0}
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # 計算 current_streak (連續早起天數)
            current_streak = 0
            if dates[0] == today or dates[0] == yesterday:
                current_streak = 1
                expected_date = dates[0] - timedelta(days=1)
                for d in dates[1:]:
                    if d == expected_date:
                        current_streak += 1
                        expected_date -= timedelta(days=1)
                    elif d > expected_date:
                        continue
                    else:
                        break
            
            # 計算 longest_streak (最長連續早起天數)
            longest_streak = 0
            if len(dates) > 0:
                temp_streak = 1
                longest_streak = 1
                for i in range(1, len(dates)):
                    if (dates[i-1] - dates[i]).days == 1:
                        temp_streak += 1
                    elif (dates[i-1] - dates[i]).days > 1:
                        longest_streak = max(longest_streak, temp_streak)
                        temp_streak = 1
                longest_streak = max(longest_streak, temp_streak)
            
            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak
            }
        except sqlite3.Error as e:
            print(f"Database error in History.get_streak_stats: {e}")
            return {'current_streak': 0, 'longest_streak': 0}
        finally:
            conn.close()
