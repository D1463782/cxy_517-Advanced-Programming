import sqlite3
import os

DATABASE_PATH = os.path.join('instance', 'database.db')

def get_db_connection():
    """建立並取得 SQLite 資料庫連線，設定 row_factory 為 sqlite3.Row 以便用欄位名稱存取。"""
    # 確保 instance 資料夾存在
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # 啟用外鍵支援
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

class Alarm:
    def __init__(self, id, time, repeat_days, difficulty, task_count, is_active, note, snooze_count, next_ring_time):
        self.id = id
        self.time = time
        self.repeat_days = repeat_days
        self.difficulty = difficulty
        self.task_count = task_count
        self.is_active = is_active
        self.note = note
        self.snooze_count = snooze_count
        self.next_ring_time = next_ring_time

    @staticmethod
    def create(time, repeat_days=None, difficulty='easy', task_count=1, note=None):
        """建立一筆新的鬧鐘設定，寫入資料庫並返回新鬧鐘的 ID。"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO alarms (time, repeat_days, difficulty, task_count, is_active, note, snooze_count, next_ring_time)
                   VALUES (?, ?, ?, ?, 1, ?, 0, NULL)''',
                (time, repeat_days, difficulty, task_count, note)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return new_id
        except sqlite3.Error as e:
            print(f"Database error in Alarm.create: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all():
        """取得所有鬧鐘設定，依時間 (time) 升序排列。"""
        conn = get_db_connection()
        try:
            rows = conn.execute('SELECT * FROM alarms ORDER BY time ASC').fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Database error in Alarm.get_all: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_by_id(alarm_id):
        """根據 ID 取得單筆鬧鐘設定，找不到則返回 None。"""
        conn = get_db_connection()
        try:
            row = conn.execute('SELECT * FROM alarms WHERE id = ?', (alarm_id,)).fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Database error in Alarm.get_by_id: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def update(alarm_id, time, repeat_days=None, difficulty='easy', task_count=1, note=None, is_active=1):
        """更新指定 ID 的鬧鐘設定。"""
        conn = get_db_connection()
        try:
            conn.execute(
                '''UPDATE alarms 
                   SET time = ?, repeat_days = ?, difficulty = ?, task_count = ?, is_active = ?, note = ?
                   WHERE id = ?''',
                (time, repeat_days, difficulty, task_count, is_active, note, alarm_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in Alarm.update: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def toggle_status(alarm_id):
        """切換指定鬧鐘的啟用與停用狀態 (1 <=> 0)。返回切換後的新狀態 (0 或 1)。"""
        conn = get_db_connection()
        try:
            alarm = conn.execute('SELECT is_active FROM alarms WHERE id = ?', (alarm_id,)).fetchone()
            if alarm is None:
                return None
            new_status = 0 if alarm['is_active'] == 1 else 1
            conn.execute('UPDATE alarms SET is_active = ? WHERE id = ?', (new_status, alarm_id))
            conn.commit()
            return new_status
        except sqlite3.Error as e:
            print(f"Database error in Alarm.toggle_status: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def update_snooze(alarm_id, snooze_count, next_ring_time):
        """更新指定鬧鐘的貪睡次數與下次響鈴的精確 ISO 時間。"""
        conn = get_db_connection()
        try:
            conn.execute(
                'UPDATE alarms SET snooze_count = ?, next_ring_time = ? WHERE id = ?',
                (snooze_count, next_ring_time, alarm_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in Alarm.update_snooze: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def reset_snooze(alarm_id):
        """重設指定鬧鐘的貪睡次數與下次響鈴時間。"""
        conn = get_db_connection()
        try:
            conn.execute(
                'UPDATE alarms SET snooze_count = 0, next_ring_time = NULL WHERE id = ?',
                (alarm_id,)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in Alarm.reset_snooze: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def delete(alarm_id):
        """刪除指定 ID 的鬧鐘設定。"""
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM alarms WHERE id = ?', (alarm_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in Alarm.delete: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
