"""MathAlarm — 數學極致醒腦鬧鐘系統
系統啟動入口點：建立 Flask 應用程式並啟動開發伺服器。
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
