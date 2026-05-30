from flask import Blueprint, render_template, redirect, url_for, session
from app.models.alarm import Alarm
from app.models.history import History

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首頁控制器：顯示音效開關、新增表單與所有鬧鐘卡片。
    若 Session 中有當前正在響鈴的 alarm_id，則強制跳轉至對應的鎖定作答頁。
    """
    # 防逃避：若有響鈴中的鬧鐘，攔截器 (before_request) 已處理重導向
    alarms = Alarm.get_all()
    stats = History.get_stats()
    return render_template('index.html', alarms=alarms, stats=stats)
