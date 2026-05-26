from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首頁控制器：顯示音效開關、新增表單與所有鬧鐘卡片。
    若是 Session 中有當前正在響鈴的 alarm_id，則強制跳轉至對應的鎖定作答頁。
    """
    pass
