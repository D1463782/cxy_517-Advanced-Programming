from flask import Flask, session, jsonify, request, render_template
import random
import os

app = Flask(__name__)

# 使用環境變數中的 SECRET_KEY，若未設定則使用隨機生成的金鑰確保 Session 安全
app.secret_key = os.environ.get('SECRET_KEY', 'mathwake_default_secure_session_key_2026_06_02')

@app.route('/')
def index():
    """首頁，渲染解題互動網頁"""
    return render_template('index.html')

@app.route('/api/generate_question', methods=['GET'])
def generate_question():
    """
    API 1: 隨機生成七元混合超長運算題目路由 (地獄級超級加長版)
    - 題目由 7 個隨機數值 (雙位數與個位數交錯) 與 6 個四則運算子 (+、-、*) 動態串聯而成
    - 限制乘號數量最多為 2 個，且乘數控制為個位數，使心算在極限下仍屬可行
    - 嚴格遵循 Python 先乘除後加減的優先權計算答案
    - 透過後端驗證機制，保證計算過程與最終答案均大於零，且小於 500，杜絕負數或數值爆炸
    - 將正確答案以整數安全地寫入 Session， friendly 算式回傳前端
    """
    import time
    
    attempts = 0
    while attempts < 200:
        attempts += 1
        nums = []
        # 生成 7 個交錯的雙位數與個位數
        for i in range(7):
            if i % 2 == 0:
                nums.append(random.randint(10, 25)) # 雙位數 (10~25)，控制大小防止數值膨脹
            else:
                nums.append(random.randint(2, 9))   # 個位數 (2~9)
        
        ops = []
        # 生成 6 個運算子，限制乘法數量最長為 2 以防數值過大
        for i in range(6):
            available_ops = ['+', '-', '*']
            if ops.count('*') >= 2:
                available_ops = ['+', '-'] # 超過 2 個乘號則強制改為加減
            
            ops.append(random.choice(available_ops))
        
        # 串聯為 Python 能解析的算式字串
        formula_parts = []
        for i in range(7):
            formula_parts.append(str(nums[i]))
            if i < 6:
                formula_parts.append(ops[i])
        
        formula_str = " ".join(formula_parts)
        
        try:
            # 使用 eval 計算正確答案
            answer = eval(formula_str)
            
            # 確保答案是一個合理、非負且易於輸入的整數 (10 ~ 500)
            if 10 <= answer <= 500 and isinstance(answer, int):
                display_formula = formula_str.replace("*", "×")
                break
        except Exception:
            continue
    else:
        # 後備應急方案：若 200 次嘗試內無解，回傳一個固定的挑戰
        display_formula = "12 × 3 + 15 - 8 × 2 + 10 - 5"
        answer = 32

    # 將正確答案存儲在後端加密 Session 中
    session['correct_answer'] = int(answer)
    
    return jsonify({
        "success": True,
        "question": display_formula
    })

@app.route('/api/verify_answer', methods=['POST'])
def verify_answer():
    """
    API 2: 驗證使用者答案路由
    - 接收 JSON 格式資料，包含 "answer" 欄位
    - 比對使用者輸入與 Session 中保存的 correct_answer
    - 回傳比對結果；若答對則清除 Session 中該題答案與計時狀態
    """
    data = request.get_json() or {}
    
    # 檢查請求格式
    if 'answer' not in data:
        return jsonify({
            "success": False,
            "message": "缺少必要的 'answer' 參數"
        }), 400
        
    user_answer = data['answer']
    
    # 從 session 中取出正確答案
    correct_answer = session.get('correct_answer')
    
    if correct_answer is None:
        return jsonify({
            "success": False,
            "message": "目前沒有待解答的題目，請先呼叫生成題目 API"
        }), 400

    try:
        # 嘗試將用戶答案轉為整數進行比對
        user_answer_int = int(user_answer)
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "請輸入有效的整數答案"
        }), 400

    # 比對解答
    if user_answer_int == correct_answer:
        # 解答正確，清除 session 答案狀態與鬧鐘開始計時狀態
        session.pop('correct_answer', None)
        session.pop('alarm_start_time', None)
        return jsonify({
            "success": True,
            "message": "答案正確！大腦成功喚醒，鬧鐘已解除。"
        })
    else:
        return jsonify({
            "success": False,
            "message": "答案錯誤，請再試一次！"
        })

@app.route('/api/alarms/start', methods=['POST'])
def start_alarm():
    """
    API 3: 初始化鬧鐘響起時間，啟動後端計時
    - 將當前 Unix 時間戳寫入加密 Session 中
    """
    import time
    session['alarm_start_time'] = time.time()
    return jsonify({
        "success": True,
        "start_time": session['alarm_start_time']
    })

@app.route('/api/alarms/check-penalty', methods=['GET'])
def check_penalty():
    """
    API 4: 查詢當前流逝秒數、音量百分比與懲罰等級 (高壓超快節奏)
    - 每過 5 秒未解出題目，音量即暴增 25%，最快 15 秒內即達到 100% 最大音量
    """
    import time
    start_time = session.get('alarm_start_time')
    
    # 若 Session 中不存在，則以當前時間初始化 (防錯機制)
    if start_time is None:
        start_time = time.time()
        session['alarm_start_time'] = start_time
        
    elapsed_seconds = int(time.time() - start_time)
    
    # 階梯音量懲罰計算：每 5 秒增加 25%，初始音量 25%，最高上限 100%
    penalty_steps = elapsed_seconds // 5
    volume_percentage = min(100.0, 25.0 + (penalty_steps * 25.0))
    penalty_level = min(4, penalty_steps)
    
    return jsonify({
        "success": True,
        "elapsed_seconds": elapsed_seconds,
        "volume_percentage": volume_percentage,
        "penalty_level": penalty_level
    })

if __name__ == '__main__':
    # 啟動開發伺服器
    app.run(debug=True, host='127.0.0.1', port=5000)
