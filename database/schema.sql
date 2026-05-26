-- 數學醒腦鬧鐘資料庫 Schema 設計 (SQLite)

-- 啟用外鍵約束
PRAGMA foreign_keys = ON;

-- 建立 alarms 表
CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT NOT NULL,                  -- 鬧鐘響起時間，格式為 "HH:MM"
    repeat_days TEXT,                    -- 重複星期，例如 "1,2,3,4,5" 代表週一至五
    difficulty TEXT NOT NULL DEFAULT 'easy',  -- 'easy', 'medium', 'hard'
    task_count INTEGER NOT NULL DEFAULT 1,     -- 解鎖需要的答題數量
    is_active INTEGER NOT NULL DEFAULT 1,     -- 1代表啟用，0代表停用
    note TEXT,                           -- 鬧鐘備註
    snooze_count INTEGER NOT NULL DEFAULT 0,  -- 累計貪睡次數 (用於貪睡懲罰)
    next_ring_time TEXT                  -- 下次響鈴時間 (用於貪睡時儲存精確 ISO 時間)
);

-- 建立 history 表
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alarm_id INTEGER,                    -- 關聯鬧鐘 ID
    ring_time TEXT NOT NULL,             -- 響鈴開始的 ISO 時間
    unlock_time TEXT NOT NULL,           -- 解鎖完成的 ISO 時間
    time_taken INTEGER NOT NULL,         -- 解鎖所花費秒數
    wrong_attempts INTEGER NOT NULL DEFAULT 0, -- 答錯題目次數
    difficulty_faced TEXT NOT NULL,      -- 實際面對的題目難度
    FOREIGN KEY(alarm_id) REFERENCES alarms(id) ON DELETE SET NULL
);
