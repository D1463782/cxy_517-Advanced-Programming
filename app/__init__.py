import os
import sqlite3
from flask import Flask, session, redirect, url_for, request


def create_app():
    """Flask 應用程式工廠：初始化 Flask、註冊 Blueprint、設定 Session 與資料庫。"""
    app = Flask(__name__)

    # 安全金鑰（用於 Session 簽署與 Flash 訊息）
    app.secret_key = os.environ.get('SECRET_KEY', 'mathalarm-dev-secret-key-2026')

    # 確保 instance 資料夾存在
    os.makedirs(app.instance_path, exist_ok=True)

    # 初始化資料庫
    init_db(app)

    # 註冊 Blueprint
    from app.routes.main import main_bp
    from app.routes.alarm import alarm_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(alarm_bp)
    app.register_blueprint(dashboard_bp)

    # ─── 全域攔截器：防逃避機制 ───
    @app.before_request
    def enforce_ringing_lock():
        """若 Session 中存有正在響鈴的鬧鐘 ID，
        且使用者嘗試瀏覽除「作答頁與驗證 API」以外的路由，
        一律強制重導向回鎖定作答頁面。
        """
        ringing_id = session.get('ringing_alarm_id')
        if ringing_id is not None:
            # 允許通過的路由清單
            allowed_endpoints = [
                'alarm.active_alarm',
                'alarm.verify_answer',
                'alarm.snooze_alarm',
                'static',
            ]
            if request.endpoint not in allowed_endpoints:
                return redirect(url_for('alarm.active_alarm', alarm_id=ringing_id))

    return app


def init_db(app=None):
    """初始化 SQLite 資料庫：讀取 database/schema.sql 並執行建表語法。"""
    db_path = os.path.join('instance', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    schema_path = os.path.join('database', 'schema.sql')

    if not os.path.exists(schema_path):
        print(f"[WARN] Schema file not found: {schema_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        print("[INFO] Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"[ERROR] Database initialization failed: {e}")
    finally:
        conn.close()
