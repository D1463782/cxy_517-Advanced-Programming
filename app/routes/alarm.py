from flask import Blueprint

alarm_bp = Blueprint('alarm', __name__)

@alarm_bp.route('/alarms/new', methods=['POST'])
def create():
    """新增鬧鐘控制器：接收表單資料，寫入 SQLite 後重導向回首頁。"""
    pass

@alarm_bp.route('/alarms/<int:alarm_id>/toggle', methods=['POST'])
def toggle(alarm_id):
    """切換開關狀態控制器：變更指定鬧鐘啟用/關閉狀態，並回傳 AJAX JSON。"""
    pass

@alarm_bp.route('/alarms/<int:alarm_id>/delete', methods=['POST'])
def delete_alarm(alarm_id):
    """刪除鬧鐘控制器：將指定鬧鐘自資料庫移除，完成後重導向回首頁。"""
    pass

@alarm_bp.route('/alarms/active-check', methods=['GET'])
def active_check():
    """鬧鐘到期輪詢控制器：背景 JS 每秒輪詢以偵測是否有鬧鐘時間到。回傳 AJAX JSON。"""
    pass

@alarm_bp.route('/alarms/active/<int:alarm_id>', methods=['GET'])
def active_alarm(alarm_id):
    """滿版響鈴鎖定作答控制器：強制鎖定畫面，動態產生數學題並儲存於 Session 中，渲染鎖定頁面。"""
    pass

@alarm_bp.route('/alarms/active/<int:alarm_id>/verify', methods=['POST'])
def verify_answer(alarm_id):
    """數學解答驗證控制器：接收使用者輸入的答案與 Session 比對。
    答對則更新答對進度，若達標則寫入歷史統計、解鎖鬧鐘並回傳成功 JSON；
    答錯或未達標則產生下一題新題目並回傳 JSON。
    """
    pass

@alarm_bp.route('/alarms/active/<int:alarm_id>/snooze', methods=['POST'])
def snooze_alarm(alarm_id):
    """貪睡控制器：暫停警報，設定 5 分鐘後再次響起，並更新 snooze_count 以觸發懲罰。"""
    pass
