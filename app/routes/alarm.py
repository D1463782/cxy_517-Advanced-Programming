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


@alarm_bp.route('/alarms/<int:alarm_id>/edit', methods=['POST'])
def edit(alarm_id):
    """編輯鬧鐘控制器：接收表單資料，更新 SQLite 中鬧鐘資料後重導向回首頁。"""
    time_val = request.form.get('time', '').strip()
    if not time_val:
        flash('錯誤：請選擇有效時間！', 'error')
        return redirect(url_for('main.index'))

    # 重重複星期
    repeat_days_list = request.form.getlist('repeat_days')
    repeat_days = ','.join(repeat_days_list) if repeat_days_list else None

    difficulty = request.form.get('difficulty', 'easy')
    task_count = int(request.form.get('task_count', 1))
    note = request.form.get('note', '').strip() or None

    try:
        Alarm.update(alarm_id, time_val, repeat_days, difficulty, task_count, note)
        flash('鬧鐘修改成功！', 'success')
    except Exception as e:
        flash(f'修改失敗：{e}', 'error')

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

    # 取得已解除鬧鐘的紀錄（防止同一分鐘重複觸發）
    dismissed = session.get('dismissed_alarms', {})
    # 自動清理過期的解除紀錄（只保留當前分鐘的紀錄）
    dismissed = {k: v for k, v in dismissed.items() if v == current_time_str}
    session['dismissed_alarms'] = dismissed

    alarms = Alarm.get_all()
    for alarm in alarms:
        if not alarm['is_active']:
            continue

        alarm_id_str = str(alarm['id'])

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
            # 跳過已在本分鐘解除過的鬧鐘
            if alarm_id_str in dismissed:
                continue

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
    wrong_count = session.get('wrong_count', 0)

    return render_template(
        'alarm_active.html',
        alarm=alarm,
        question=session['math_question'],
        correct_count=correct_count,
        wrong_count=wrong_count,
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

    actual_difficulty = _get_punished_difficulty(alarm['difficulty'], alarm['snooze_count'])
    actual_task_count = alarm['task_count'] + alarm['snooze_count']

    try:
        user_answer = int(user_answer_str)
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'finished': False,
            'message': '請輸入有效的整數答案！',
            'correct_count': session.get('correct_count', 0),
            'wrong_count': session.get('wrong_count', 0),
            'task_count': actual_task_count
        })

    correct_answer = session.get('math_answer')

    if user_answer == correct_answer:
        # 答對
        session['correct_count'] = session.get('correct_count', 0) + 1
        correct_count = session['correct_count']

        if correct_count >= actual_task_count:
            # 數學挑戰達標，標記為 math_finished 供後續驗證，但不直接解鎖
            session['math_finished'] = True
            return jsonify({
                'success': True,
                'finished': False,
                'show_game': True,
                'correct_count': correct_count,
                'wrong_count': session.get('wrong_count', 0),
                'task_count': actual_task_count
            })
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
                'wrong_count': session.get('wrong_count', 0),
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
            'wrong_count': session.get('wrong_count', 0),
            'task_count': actual_task_count
        })


@alarm_bp.route('/alarms/active/<int:alarm_id>/force-cancel', methods=['POST'])
def force_cancel_alarm(alarm_id):
    """直接取消鬧鐘：當答題數超過設定數量時，允許使用者點擊按鈕直接解除鬧鐘。"""
    alarm = Alarm.get_by_id(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '找不到該鬧鐘'}), 404

    # 重設貪睡狀態
    Alarm.reset_snooze(alarm_id)

    # 單次鬧鐘自動關閉
    if not alarm['repeat_days']:
        Alarm.toggle_status(alarm_id)

    # 清除 Session 響鈴狀態
    _clear_ringing_session()

    return jsonify({'success': True, 'message': '鬧鐘已成功取消！'})


@alarm_bp.route('/alarms/active/<int:alarm_id>/verify-game', methods=['POST'])
def verify_game(alarm_id):
    """反應力測試驗證：當前端完成 Canvas 紅點點擊時發送請求以完成解鎖鬧鐘。"""
    alarm = Alarm.get_by_id(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '找不到該鬧鐘'}), 404

    if not session.get('math_finished'):
        return jsonify({'success': False, 'message': '您尚未通過數學挑戰！'}), 403

    # 順利完成：寫入歷史數據並重設狀態
    ring_start = session.get('ring_start_time', datetime.now().isoformat())
    unlock_time = datetime.now().isoformat()
    try:
        time_taken = int((datetime.now() - datetime.fromisoformat(ring_start)).total_seconds())
    except Exception:
        time_taken = 0
    wrong_count = session.get('wrong_count', 0)
    actual_difficulty = _get_punished_difficulty(alarm['difficulty'], alarm['snooze_count'])

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

    # 取得當前連續早起天數以進行展示
    streak_stats = History.get_streak_stats()
    current_streak = streak_stats['current_streak']

    # 清除 Session 響鈴狀態
    _clear_ringing_session()

    return jsonify({'success': True, 'finished': True, 'streak': current_streak})


@alarm_bp.route('/alarms/active/<int:alarm_id>/sos', methods=['GET'])
def get_sos_sentence(alarm_id):
    """求救罰寫路由：隨機返回一個罰寫句子，並初始化進度到 Session。"""
    sentences = [
        "我保證今晚一定在 11 點前睡覺，絕對不准賴床，明天要精神飽滿！",
        "我承認我今天早上解不出數學題，但我會努力起來，維持良好作息！",
        "早起是一件痛苦但值得堅持的事，我不會再被睡魔打敗，出發吧！",
        "期末專題一定要順利通過，我不賴床、不遲到，一定會準時交卷！",
        "大腦目前運轉有點緩慢，我正在打字罰寫，讓手指跟思緒完全清醒！"
    ]
    sentence = random.choice(sentences)
    session['sos_sentence'] = sentence
    session['sos_written_count'] = 0
    return jsonify({'success': True, 'sentence': sentence})


@alarm_bp.route('/alarms/active/<int:alarm_id>/verify-sos', methods=['POST'])
def verify_sos(alarm_id):
    """罰寫單次提交驗證：核對輸入內容，累計 10 次成功後解鎖。"""
    alarm = Alarm.get_by_id(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '找不到該鬧鐘'}), 404

    data = request.get_json(silent=True) or {}
    user_text = str(data.get('input_text', '')).strip()

    target_sentence = session.get('sos_sentence')
    if not target_sentence:
        return jsonify({'success': False, 'message': '求救流程未正常啟動！'}), 400

    if user_text != target_sentence:
        return jsonify({'success': False, 'message': '罰寫內容不符，請仔細檢查標點與字元！'})

    # 答對一次，累加進度
    session['sos_written_count'] = session.get('sos_written_count', 0) + 1
    written_count = session['sos_written_count']

    if written_count >= 10:
        # 達標 10 次：寫入歷史記錄，難度註記為 'SOS'
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
            difficulty_faced='SOS'
        )

        # 重設貪睡與單次狀態
        Alarm.reset_snooze(alarm_id)
        if not alarm['repeat_days']:
            Alarm.toggle_status(alarm_id)

        # 取得當前連續早起天數以進行展示
        streak_stats = History.get_streak_stats()
        current_streak = streak_stats['current_streak']

        _clear_ringing_session()
        return jsonify({'success': True, 'finished': True, 'streak': current_streak})

    return jsonify({'success': True, 'finished': False, 'written_count': written_count})


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
    """清除 Session 中所有與當前響鈴相關的資料，並記錄已解除的鬧鐘 ID 防止同分鐘重複觸發。"""
    # 記錄已解除的鬧鐘 ID 與解除時的分鐘，防止同分鐘重複觸發
    ringing_id = session.get('ringing_alarm_id')
    if ringing_id is not None:
        dismissed = session.get('dismissed_alarms', {})
        dismissed[str(ringing_id)] = datetime.now().strftime('%H:%M')
        session['dismissed_alarms'] = dismissed

    keys_to_remove = ['ringing_alarm_id', 'ring_start_time', 'math_question',
                      'math_answer', 'correct_count', 'wrong_count', 'math_finished',
                      'sos_sentence', 'sos_written_count']
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
    - medium: 較大的兩位數乘法 ± 兩位數
    - hard: 雙重乘法或巢狀括號混合運算
    """
    if difficulty == 'easy':
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        op = random.choice(['+', '-'])
        question = f"{a} {op} {b}"
        answer = a + b if op == '+' else a - b

    elif difficulty == 'medium':
        a = random.randint(15, 99)
        b = random.randint(3, 9)
        # 確保 c 不會大於 a * b - 5，以防止減法出現負數或零
        max_c = min(99, a * b - 5)
        c = random.randint(10, max_c)
        op = random.choice(['+', '-'])
        question = f"{a} × {b} {op} {c}"
        answer = (a * b + c) if op == '+' else (a * b - c)

    else:  # hard
        mode = random.choice([1, 2, 3])
        if mode == 1:
            # √a × b ± c × d
            root = random.choice([4, 5, 6, 7, 8, 9, 10])
            a = root * root
            b = random.randint(3, 9)
            c = random.randint(5, 20)
            d = random.randint(2, 5)
            op = random.choice(['+', '-'])
            
            term1 = root * b
            term2 = c * d
            if op == '-':
                # 確保結果為正值，如果 term1 < term2 則交換
                if term1 < term2:
                    root, b, c, d = c, d, root, b
                    term1, term2 = term2, term1
                    a = root * root
                question = f"√{a} × {b} - {c} × {d}"
                answer = term1 - term2
            else:
                question = f"√{a} × {b} + {c} × {d}"
                answer = term1 + term2
                
        elif mode == 2:
            # (a² ± b) × c
            a = random.randint(4, 12)
            a_sq = a * a
            b = random.randint(10, 50)
            c = random.randint(2, 5)
            op = random.choice(['+', '-'])
            if op == '-':
                # 確保內層運算不為負數或零
                if a_sq <= b:
                    b = random.randint(5, a_sq - 5) if a_sq > 5 else 1
                question = f"({a}² - {b}) × {c}"
                answer = (a_sq - b) * c
            else:
                question = f"({a}² + {b}) × {c}"
                answer = (a_sq + b) * c
                
        else:
            # √a × b² ± c
            root = random.choice([3, 4, 5, 6, 7, 8, 9, 10])
            a = root * root
            b = random.randint(3, 8)
            b_sq = b * b
            c = random.randint(10, 99)
            op = random.choice(['+', '-'])
            
            term1 = root * b_sq
            if op == '-':
                # 確保結果不為負值
                if term1 <= c:
                    c = random.randint(5, max(10, term1 - 5))
                question = f"√{a} × {b}² - {c}"
                answer = term1 - c
            else:
                question = f"√{a} × {b}² + {c}"
                answer = term1 + c

    return question, answer
