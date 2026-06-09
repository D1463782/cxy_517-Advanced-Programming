from flask import Blueprint, render_template
from app.models.history import History

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
def index():
    """起床歷史統計控制器：讀取 SQLite 歷史統計，提供圖表與明細展示，渲染 dashboard.html。"""
    stats = History.get_stats()
    records = History.get_all()
    return render_template('dashboard.html', stats=stats, records=records)
