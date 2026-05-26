import random
from datetime import datetime, timedelta

from flask import Blueprint, request, redirect, url_for, flash, session, jsonify, render_template
from app.models.alarm import Alarm
from app.models.history import History

alarm_bp = Blueprint('alarm', __name__)


# ═══════════════════════════════════════════════
# 鬧鐘 CRUD 路由
# ═══════════════════════════════════════════════

@alarm_bp.route('/alarms/new', methods=['POST'])
def create():
    """新增鬧鐘控制器：接收表單資料，寫入 SQLite 後重導向回首頁。"""
    time_val = request.form.get('time', '').strip()
    if not time_val:
        flash('錯誤：請選擇有效時間！', 'error')
        return redirect(url_for('main.index'))

    # 重複星期：表單傳來 checkbox 陣列
    repeat_days_list = request.form.getlist('repeat_days')
    repeat_days = ','.join(repeat_days_list) if repeat_days_list else None

    difficulty = request.form.get('difficulty', 'easy')
    task_count = int(request.form.get('task_count', 1))
    note = request.form.get('note', '').strip() or None

    try:
        Alarm.create(time_val, repeat_days, difficulty, task_count, note)
        flash('鬧鐘建立成功！', 'success')
    except Exception as e:
        flash(f'建立失敗：{e}', 'error')

    return redirect(url_for('main.index'))


@alarm_bp.route('/alarms/<int:alarm_id>/toggle', methods=['POST'])
def toggle(alarm_id):
    """切換開關狀態控制器：變更指定鬧鐘啟用/關閉狀態，並回傳 AJAX JSON。"""
    new_status = Alarm.toggle_status(alarm_id)
    if new_status is not None:
        return jsonify({'success': True, 'new_status': new_status})
    return jsonify({'success': False, 'message': '找不到該鬧鐘'}), 404


@alarm_bp.route('/alarms/<int:alarm_id>/delete', methods=['POST'])
def delete_alarm(alarm_id):
    """刪除鬧鐘控制器：將指定鬧鐘自資料庫移除，完成後重導向回首頁。"""
    Alarm.delete(alarm_id)
    flash('鬧鐘已成功刪除', 'success')
    return redirect(url_for('main.index'))


# ═══════════════════════════════════════════════
# 鬧鐘輪詢與警報鎖定路由
# ═══════════════════════════════════════════════

@alarm_bp.route('/alarms/active-check', methods=['GET'])
def active_check():
    """鬧鐘到期輪詢控制器：背景 JS 每秒輪詢以偵測是否有鬧鐘時間到。回傳 AJAX JSON。"""
    # 若已有鬧鐘在響鈴中
    ringing_id = session.get('ringing_alarm_id')
    if ringing_id is not None:
        return jsonify({'active': True, 'alarm_id': ringing_id})

    now = datetime.now()
    current_time_str = now.strftime('%H:%M')
    # 星期：Python isoweekday() → 1=Mon…7=Sun，系統定義 1=Mon…0=Sun
    current_weekday = str(now.isoweekday() % 7)  # 轉換為 0=Sun, 1=Mon...6=Sat

    alarms = Alarm.get_all()
    for alarm in alarms:
        if not alarm['is_active']:
            continue

        # 檢查貪睡鬧鐘的下次響鈴時間
        if alarm['next_ring_time']:
            try:
                next_ring = datetime.fromisoformat(alarm['next_ring_time'])
                if now >= next_ring:
                    _trigger_alarm(alarm['id'])
                    return jsonify({'active': True, 'alarm_id': alarm['id']})
            except ValueError:
                pass
            continue

        # 一般鬧鐘：比對時間與星期
        if alarm['time'] == current_time_str:
            repeat_days = alarm['repeat_days']
            if repeat_days:
                # 有設定重複日，檢查今天星期是否在清單中
                days_list = repeat_days.split(',')
                if current_weekday in days_list:
                    _trigger_alarm(alarm['id'])
                    return jsonify({'active': True, 'alarm_id': alarm['id']})
            else:
                # 單次鬧鐘
                _trigger_alarm(alarm['id'])
                return jsonify({'active': True, 'alarm_id': alarm['id']})

    return jsonify({'active': False})


def _trigger_alarm(alarm_id):
    """將鬧鐘寫入 Session 為響鈴狀態，並初始化答題進度。"""
    session['ringing_alarm_id'] = alarm_id
    session['ring_start_time'] = datetime.now().isoformat()
    session['correct_count'] = 0
    session['wrong_count'] = 0


@alarm_bp.route('/alarms/active/<int:alarm_id>', methods=['GET'])
def active_alarm(alarm_id):
    """滿版響鈴鎖定作答控制器：強制鎖定畫面，動態產生數學題並儲存於 Session 中，渲染鎖定頁面。"""
    alarm = Alarm.get_by_id(alarm_id)
    if not alarm:
        flash('找不到該鬧鐘', 'error')
        return redirect(url_for('main.index'))

    # 若 Session 中沒有此鬧鐘的響鈴記錄，不允許進入
    ringing_id = session.get('ringing_alarm_id')
    if ringing_id != alarm_id:
        return redirect(url_for('main.index'))

    # 計算實際難度（含貪睡懲罰升級）
    actual_difficulty = _get_punished_difficulty(alarm['difficulty'], alarm['snooze_count'])
    actual_task_count = alarm['task_count'] + alarm['snooze_count']  # 每次貪睡多 1 題

    # 產生數學題（若 Session 中尚無題目）
    if 'math_question' not in session:
        question, answer = _generate_math_question(actual_difficulty)
        session['math_question'] = question
        session['math_answer'] = answer

    correct_count = session.get('correct_count', 0)

    return render_template(
        'alarm_active.html',
        alarm=alarm,
        question=session['math_question'],
        correct_count=correct_count,
        task_count=actual_task_count,
        difficulty=actual_difficulty
    )


@alarm_bp.route('/alarms/active/<int:alarm_id>/verify', methods=['POST'])
def verify_answer(alarm_id):
    """數學解答驗證控制器：接收使用者輸入的答案與 Session 比對。"""
    alarm = Alarm.get_by_id(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '找不到該鬧鐘'}), 404

    data = request.get_json(silent=True) or {}
    user_answer_str = str(data.get('answer', '')).strip()

    try:
        user_answer = int(user_answer_str)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'finished': False, 'message': '請輸入有效的整數答案！'})

    correct_answer = session.get('math_answer')
    actual_difficulty = _get_punished_difficulty(alarm['difficulty'], alarm['snooze_count'])
    actual_task_count = alarm['task_count'] + alarm['snooze_count']

    if user_answer == correct_answer:
        # 答對
        session['correct_count'] = session.get('correct_count', 0) + 1
        correct_count = session['correct_count']

        if correct_count >= actual_task_count:
            # 達標：寫入歷史、解鎖鬧鐘
            ring_start = session.get('ring_start_time', datetime.now().isoformat())
            unlock_time = datetime.now().isoformat()
            try:
                time_taken = int((datetime.now() - datetime.fromisoformat(ring_start)).total_seconds())
            except Exception:
                time_taken = 0
            wrong_count = session.get('wrong_count', 0)

            History.create(
                alarm_id=alarm_id,
                ring_time=ring_start,
                unlock_time=unlock_time,
                time_taken=time_taken,
                wrong_attempts=wrong_count,
                difficulty_faced=actual_difficulty
            )

            # 重設貪睡狀態
            Alarm.reset_snooze(alarm_id)

            # 單次鬧鐘自動關閉
            if not alarm['repeat_days']:
                Alarm.toggle_status(alarm_id)

            # 清除 Session 響鈴狀態
            _clear_ringing_session()

            return jsonify({'success': True, 'finished': True})
        else:
            # 未達標：產生下一題
            question, answer = _generate_math_question(actual_difficulty)
            session['math_question'] = question
            session['math_answer'] = answer
            return jsonify({
                'success': True,
                'finished': False,
                'next_question': question,
                'correct_count': correct_count,
                'task_count': actual_task_count
            })
    else:
        # 答錯
        session['wrong_count'] = session.get('wrong_count', 0) + 1
        # 產生新題目防止死背
        question, answer = _generate_math_question(actual_difficulty)
        session['math_question'] = question
        session['math_answer'] = answer
        return jsonify({
            'success': False,
            'finished': False,
            'message': '計算錯誤，題目已更新！',
            'next_question': question,
            'correct_count': session.get('correct_count', 0),
            'task_count': actual_task_count
        })


@alarm_bp.route('/alarms/active/<int:alarm_id>/snooze', methods=['POST'])
def snooze_alarm(alarm_id):
    """貪睡控制器：暫停警報，設定 5 分鐘後再次響起，並更新 snooze_count 以觸發懲罰。"""
    alarm = Alarm.get_by_id(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '找不到該鬧鐘'}), 404

    new_snooze_count = alarm['snooze_count'] + 1
    next_ring = (datetime.now() + timedelta(minutes=5)).isoformat()

    Alarm.update_snooze(alarm_id, new_snooze_count, next_ring)

    # 清除 Session 響鈴狀態
    _clear_ringing_session()

    return jsonify({
        'success': True,
        'message': f'鬧鐘已貪睡，大腦休息 5 分鐘！（第 {new_snooze_count} 次貪睡，下次難度將加重）'
    })


# ═══════════════════════════════════════════════
# 輔助函式
# ═══════════════════════════════════════════════

def _clear_ringing_session():
    """清除 Session 中所有與當前響鈴相關的資料。"""
    keys_to_remove = ['ringing_alarm_id', 'ring_start_time', 'math_question',
                      'math_answer', 'correct_count', 'wrong_count']
    for key in keys_to_remove:
        session.pop(key, None)


def _get_punished_difficulty(base_difficulty, snooze_count):
    """根據貪睡次數升級難度。每次貪睡提升一個難度等級。"""
    levels = ['easy', 'medium', 'hard']
    try:
        base_index = levels.index(base_difficulty)
    except ValueError:
        base_index = 0
    new_index = min(base_index + snooze_count, len(levels) - 1)
    return levels[new_index]


def _generate_math_question(difficulty):
    """根據難度等級隨機產生數學題目與正確答案。

    - easy: 兩個兩位數的加減法
    - medium: 兩位數乘法 ± 一位數
    - hard: 帶括號的三元混合運算
    """
    if difficulty == 'easy':
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        op = random.choice(['+', '-'])
        question = f"{a} {op} {b}"
        answer = a + b if op == '+' else a - b

    elif difficulty == 'medium':
        a = random.randint(11, 49)
        b = random.randint(2, 9)
        c = random.randint(1, 30)
        op = random.choice(['+', '-'])
        question = f"{a} × {b} {op} {c}"
        answer = (a * b + c) if op == '+' else (a * b - c)

    else:  # hard
        a = random.randint(10, 50)
        b = random.randint(2, 20)
        c = random.randint(2, 9)
        inner_op = random.choice(['+', '-'])
        question = f"({a} {inner_op} {b}) × {c}"
        inner = (a + b) if inner_op == '+' else (a - b)
        answer = inner * c

    return question, answer
