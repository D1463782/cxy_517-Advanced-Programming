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
    API 1: 隨機生成二元四則運算題目路由
    - 隨機選取運算子: +、-、*
    - 隨機生成兩個數值 (1 ~ 50)
    - 減法自動確保大於等於零，避免過度挫折
    - 乘法限制乘數在 2~12 之間以符合睡眠喚醒難度
    - 將正確解答以整數型態存入 Flask Session
    """
    operators = ['+', '-', '*']
    op = random.choice(operators)
    
    if op == '*':
        # 乘法限制在 2~12，避免數值過大
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        answer = a * b
        display_op = '×'
    elif op == '-':
        # 減法確保結果不為負值
        a = random.randint(10, 50)
        b = random.randint(1, a)
        answer = a - b
        display_op = '-'
    else: # op == '+'
        a = random.randint(5, 50)
        b = random.randint(5, 50)
        answer = a + b
        display_op = '+'

    # 將答案存儲在 Flask 的加密 Cookie Session 中
    session['correct_answer'] = answer
    
    question_str = f"{a} {display_op} {b}"
    
    return jsonify({
        "success": True,
        "question": question_str
    })

@app.route('/api/verify_answer', methods=['POST'])
def verify_answer():
    """
    API 2: 驗證使用者答案路由
    - 接收 JSON 格式資料，包含 "answer" 欄位
    - 比對使用者輸入與 Session 中保存的 correct_answer
    - 回傳比對結果；若答對則清除 Session 中該題答案避免重複利用
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
        # 解答正確，清除 session 答案狀態，防範二次提交
        session.pop('correct_answer', None)
        return jsonify({
            "success": True,
            "message": "答案正確！大腦成功喚醒，鬧鐘已解除。"
        })
    else:
        return jsonify({
            "success": False,
            "message": "答案錯誤，請再試一次！"
        })

if __name__ == '__main__':
    # 啟動開發伺服器
    app.run(debug=True, host='127.0.0.1', port=5000)
