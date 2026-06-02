# MathWake 智力喚醒鬧鐘 — 產品需求文件 (PRD)

本文件詳細規劃「MathWake 智力喚醒鬧鐘」的產品需求，並針對 **F-01 動態數學解題功能** 進行深入的技術架構與邏輯設計，旨在提供開發團隊一套清晰、嚴謹且易於實作的規格指南。

---

## 1. 專案概述

### 1.1 背景與動機
現代人普遍面臨賴床、無意識關閉鬧鐘後繼續陷入睡眠（Snooze loop）的問題。傳統鬧鐘的關閉難度極低，用戶只需輕輕一滑或按壓按鈕即可關閉，此時大腦尚未完全醒轉。  
**MathWake 智力喚醒鬧鐘** 透過在鬧鐘響起時強制用戶進行「數學解題挑戰」來解決此痛點。藉由即時、動態且不可輕易跳過的數學運算，刺激用戶的前額葉皮質（Prefrontal Cortex），強制活化大腦思考，從而達到快速且清醒起床的目的。

### 1.2 目標用戶
- **重度賴床者**：有多次貪睡習慣、經常無意識關閉鬧鐘而遲到的人群。
- **晨型人培育者**：希望在早晨第一時間讓大腦開機、進入高效工作/學習狀態的學生與上班族。
- **科技與自我管理者**：喜愛透過數字與統計管理生活作息的效率達人。

### 1.3 核心價值主張
- **物理與心智雙重喚醒**：聲音與智力挑戰雙管齊下，不解開題目，鬧鐘絕不罷休。
- **無縫互動體驗**：專為半夢半醒狀態設計的超大觸控按鍵與防呆介面。
- **安全防弊機制**：核心解題邏輯與答案驗證完全在後端運行，防止用戶透過前端重新整理或修改網頁原始碼繞過挑戰。

---

## 2. 功能需求

以下為 MathWake 的五大核心功能模組與其對應的使用者故事：

### F-01: 動態數學解題 (核心功能)
- **使用者故事**：作為一名「重度賴床者」，我希望在鬧鐘響起時，螢幕會鎖定並隨機生成一組四則運算題目，以便我必須集中精神解出正確答案才能關閉鬧鐘，防止我無意識地關閉鬧鐘。
- **主要規格**：
  - 支援「加、減、乘、除」四則運算。
  - 題目必須在後端動態生成，嚴格禁止前端產生或儲存解答。
  - 除法運算必須保證能夠整除，避免出現無限小數。

### F-02: 階梯音量懲罰功能 (核心功能)
- **使用者故事**：作為一名「睡眠極沉的用戶」，我希望鬧鐘在響起後若我遲遲沒有解出題目，鈴聲音量會每隔 30 秒自動放大 20%，以便透過逐漸增強的聽覺與壓力刺激強迫我加快解題，防止我聽著鈴聲繼續睡。
- **主要規格**：
  - 後端必須精確記錄鬧鐘開始響鈴的時間戳記（以 Session 保持）。
  - 每過 30 秒若挑戰未解除，音量放大 20%，直到達到最大硬體/軟體上限 (100%)。
  - 提供動態查詢 API，供前端定時同步最新的音量狀態與懲罰層級。

### F-03: 難度與題型自訂
- **使用者故事**：作為一名「數學不擅長但想強迫起床的用戶」，我希望可以自由調整鬧鐘的解題難度與運算子類型，以便我能以適合自己的心智負擔逐漸建立起床習慣。
- **主要規格**：
  - **簡單 (Easy)**：2 個個位數/雙位數的加減法（如 `12 + 7`）。
  - **中等 (Medium)**：3 個數值（雙位數）的混合加減乘（如 `25 - 4 * 3`）。
  - **困難 (Hard)**：3-4 個數值的混合加減乘除，包含括號（如 `(48 / 6) * 12 - 15`），且答案保證為整數。

### F-04: 歷史紀錄與喚醒統計
- **使用者故事**：作為一名「自我管理者」，我希望在解題成功後，系統能記錄我花費的解題秒數與正確率，並以圖表呈現，以便我追蹤自己大腦每日清醒的速度與進步趨勢。
- **主要規格**：
  - 記錄每次鬧鐘響起時間、實際解題完成時間、嘗試次數。
  - 計算平均「喚醒秒數」。

### F-05: 智能貪睡 (Snooze) 限制與懲罰機制
- **使用者故事**：作為一名「極度想賴床的用戶」，我希望在實在無法立即解題時能有短暫的貪睡喘息機會，但系統必須限制貪睡次數，且每次貪睡後題目難度應逐漸增加，以便防止我無限期賴床。
- **主要規格**：
  - 每次鬧鐘最多允許貪睡 2 次。
  - 貪睡間隔隨次數遞減（例如：第一次 5 分鐘，第二次 3 分鐘）。
  - 每貪睡一次，下一次響鈴的題目難度自動提升一階（例如：簡單 $\rightarrow$ 中等）。

---

## 3. 非功能需求

### 3.1 技術限制與架構
- **後端技術**：使用 Python (Flask) 作為 Web 服務框架，搭配 SQLite 作為輕量化關聯式資料庫。
- **前端技術**：採用 HTML5、Vanilla CSS（純 CSS，無 Tailwind）與 Vanilla JavaScript 進行 DOM 操縱與互動。
- **頁面渲染**：使用 Flask 內建的 Jinja2 模板引擎進行動態頁面渲染。

### 3.2 效能與響應考量
- **超低延遲**：鬧鐘觸發與解題提交的 API 反應時間必須小於 200ms，確保流暢度。
- **輕量化資源**：前端解題介面需保持極簡，確保在移動端或低效能裝置上亦能秒開。

### 3.3 安全性與防作弊
- **後端狀態保持**：每次生成題目時，後端將題目文本與唯一解（答案）加密或寫入資料庫/Session，前端只接收題目文本與一個隨機生成的挑戰 ID（Challenge ID）。
- **答案防窺**：禁止在網頁原始碼、Cookie 或 LocalStorage 中洩漏答案。
- **關閉防禦**：前端介面採用全螢幕遮罩，攔截常用鍵盤快捷鍵（如 Escape、Space），並在響鈴時循環播放音訊，防止用戶直接無視介面。

---

## 4. F-01 動態數學解題功能規劃

本章節為 F-01 功能的詳細核心設計，包含後端算法、API 路由與前端互動規格。

### 4.1 後端 Python (Flask) 隨機題目生成算法邏輯

為確保題目具有挑戰性且答案皆為整數，算法需根據難度採取不同的生成策略：

#### A. 算法規則設計
1. **加減法 (Addition/Subtraction)**：
   - 簡單難度下，數值介於 `1 ~ 30`。
   - 減法運算時，若為簡單難度，應確保被減數大於減數，避免出現負數導致用戶清晨挫折感過重。
2. **乘法 (Multiplication)**：
   - 簡單難度不包含乘法。
   - 中等難度包含單個乘法，乘數介於 `2 ~ 9`，被乘數 `2 ~ 15`。
3. **除法 (Division) — 整除保證算法**：
   - **核心邏輯**：要生成 $A \div B = C$ 且 $C$ 為整數，算法應**先隨機生成除數 $B$ 與商 $C$，再計算出被除數 $A = B \times C$**。最後將題目呈現為 $A \div B$。
   - 如此可 $100\%$ 保證整除，且運算難度完全可控。

#### B. 題目生成器程式碼邏輯實作預想
後端將設計一個 `MathProblemGenerator` 類別：

```python
import random

class MathProblemGenerator:
    @staticmethod
    def generate(difficulty="easy"):
        """
        根據難度生成題目與答案
        回傳格式: (formula_string, integer_answer)
        """
        if difficulty == "easy":
            # 簡單：2 個數字的加減法 (1~20)
            a = random.randint(5, 20)
            b = random.randint(1, a)  # 確保相減為正數
            operator = random.choice(["+", "-"])
            
            if operator == "+":
                return f"{a} + {b}", a + b
            else:
                return f"{a} - {b}", a - b

        elif difficulty == "medium":
            # 中等：3 個數字的加減乘混合運算
            # 範例結構：a + b * c 或 a * b - c
            a = random.randint(10, 50)
            b = random.randint(2, 9)
            c = random.randint(2, 9)
            
            op1, op2 = random.choice([("+", "*"), ("-", "*"), ("*", "+"), ("*", "-")])
            
            if op1 == "*":
                formula = f"{a} * {b} {op2} {c}"
                ans = eval(formula)
            else:
                formula = f"{a} {op1} {b} * {c}"
                ans = eval(formula)
                
            return formula.replace("*", "×"), int(ans)

        elif difficulty == "hard":
            # 困難：3-4 個數，包含加減乘除與括號
            # 為了保證除法整除，我們先構建一個整除對
            b_div = random.randint(2, 12)  # 除數
            c_div = random.randint(2, 12)  # 商
            a_div = b_div * c_div          # 被除數 (a_div / b_div = c_div)
            
            # 再加上一個加減或乘法項
            d = random.randint(15, 100)
            operator = random.choice(["+", "-", "*"])
            
            if operator == "+":
                # 形如: (A / B) + D
                formula = f"({a_div} / {b_div}) + {d}"
                ans = c_div + d
            elif operator == "-":
                # 形如: D - (A / B)
                formula = f"{d} - ({a_div} / {b_div})"
                ans = d - c_div
            else:
                # 形如: (A / B) * D，限制 D 較小以免數值爆大
                d_small = random.randint(2, 6)
                formula = f"({a_div} / {b_div}) * {d_small}"
                ans = c_div * d_small
                
            # 將除號與乘號轉換為網頁友好顯示字元
            display_formula = formula.replace("/", "÷").replace("*", "×")
            return display_formula, int(ans)
```

---

### 4.2 API 路由設計

為確保前後端邏輯對齊，API 設計需具備高度安全性。所有運算皆在後端驗證，並透過 Session 機制綁定當前挑戰。

| API 端點 | HTTP 方法 | 說明 | 請求參數 (JSON) | 回傳參數 (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| `/api/alarms/active-challenge` | `GET` | 獲取當前響鈴中鬧鐘的解題挑戰題目 | 無 | `{"challenge_id": "uuid...", "formula": "12 × 4 - 8"}` |
| `/api/alarms/verify` | `POST` | 驗證使用者輸入的數學答案 | `{"challenge_id": "uuid...", "answer": 40}` | `{"success": true, "message": "解題成功，鬧鐘關閉"}` 或 `{"success": false, "message": "解答錯誤，請重試！"}` |
| `/api/alarms/snooze` | `POST` | 申請鬧鐘進入貪睡模式 | `{"challenge_id": "uuid..."}` | `{"success": true, "snooze_count": 1, "next_ring": "07:15"}` 或 `{"success": false, "message": "已達貪睡上限，必須解題！"}` |

#### 驗證流程圖 (邏輯流)
1. 鬧鐘觸發 $\rightarrow$ 瀏覽器跳轉至解題頁面 `/alarm/ring`。
2. 頁面載入時，前端發送請求至 `GET /api/alarms/active-challenge`。
3. 後端隨機生成題目，將其 `(formula, answer)` 與產生的 `challenge_id` 寫入後端 Session，並將 `challenge_id` 與 `formula` 回傳前端。
4. 使用者在前端解題介面輸入答案，按下送出 $\rightarrow$ `POST /api/alarms/verify`。
5. 後端從 Session 中比對該 `challenge_id` 的正確答案：
   - **正確**：清除 Session 挑戰狀態、停止鬧鐘響鈴狀態，回傳 `{"success": true}`。
   - **錯誤**：增加嘗試次數，回傳 `{"success": false}`，前端觸發錯誤動畫並清空輸入框。

---

### 4.3 前端 HTML/CSS 解題互動介面需求

前端頁面是直接喚醒大腦的視覺載體，必須滿足以下「強互動、極簡、高對比」的設計要求：

#### A. 介面佈局與視覺美學 (UI/UX)
- **色彩計畫**：
  - 採用高品質暗黑模式（Sleek Dark Mode），背景以深邃的灰黑藍（如 `#0d0f12`）為主，搭配霓虹漸層（如藍紫色 `#6366f1` 到 `#a855f7`）作為主題點綴色。
  - 當警報響起時，頂部或背景可呈現微妙的紅色呼吸燈光影效果（Pulse Animation），加強緊迫感。
- **字型與排版**：
  - 導入 Google Fonts (例如 `Outfit` 或 `Plus Jakarta Sans`)，提供極具未來感的無襯線字體。
  - 數學算式必須以極大的字級（如 `3rem` 以上）顯示於畫面正中央，字體加粗，具備微發光效果。
- **解題互動鍵盤 (Virtual Keypad)**：
  - 半夢半醒下手指無法精準敲擊小鍵盤，因此頁面必須提供一組**大型網格虛擬按鍵**（數字 0-9、退格鍵 Backspace、清除鍵 Clear、確認鍵 Enter）。
  - 虛擬按鍵需有明顯的懸停（Hover）與點擊（Active）動態縮放與陰影變化。

#### B. 互動邏輯與 JS 行為
- **自動聚焦與音訊鎖定**：
  - 進入頁面後，立即以對話框提示或點擊事件「解鎖」瀏覽器音訊播放限制，隨即循環播放極具喚醒效果的電子鬧鈴聲。
  - 直到 `/verify` 回傳 `success: true`，音訊方可暫停播放，且頁面展示「早安！大腦已成功喚醒」的漸變動畫，隨後導回首頁。
- **防作弊與干擾限制**：
  - 使用 JS 攔截 `beforeunload` 事件，若用戶試圖關閉或重新整理網頁，提示「鬧鐘仍在運行，請完成解題！」
  - 監聽 `keydown` 事件，阻止 `Escape` 鍵的預設動作。
- **錯誤視覺回饋**：
  - 當提交錯誤答案時，算式顯示區域觸發**左右劇烈搖晃動畫（Shake Animation）**，且輸入框與外框閃爍紅色光暈，並提供短促的低頻錯誤音效。

---

## 5. F-02 階梯音量懲罰功能規劃

本章節為 F-02 功能的詳細核心設計，包含後端時間戳記紀錄、階梯增益演算法、新增的 API 路由，以及前端 Web Audio API 定時器音量更新規格。

### 5.1 後端 Python (Flask) 鬧鐘計時與音量懲罰演算法

後端主要負責時間狀態的可靠記錄與公式計算，防止前端時間被惡意篡改或因網頁重整而重置計時。

#### A. 鬧鐘響起計時邏輯
1. 當用戶點擊開始按鈕進入解題挑戰時，前端發送請求初始化計時。
2. 後端將當前 Unix 時間戳記（時間戳）寫入 Flask 的加密 Session 中：`session['alarm_start_time'] = time.time()`。
3. 此時間戳記一旦設定，直到成功答對題目呼叫 `/api/verify_answer` 通過後，才會伴隨正確答案一同被清除。網頁即使重新整理，計時也不會被重設。

#### B. 階梯音量懲罰演算法
* **初始音量**：$20\%$ (0.2)
* **增益間隔**：每過 $30$ 秒，音量放大 $20\%$ (0.2)
* **最大上限**：$100\%$ (1.0)
* **公式計算**：
  $$\text{Volume Ratio} = \min\left(1.0,\ 0.2 + \left\lfloor \frac{\text{Elapsed Seconds}}{30} \right\rfloor \times 0.2\right)$$
* **懲罰等級 (Penalty Level)**：
  $$\text{Penalty Level} = \min\left(4,\ \left\lfloor \frac{\text{Elapsed Seconds}}{30} \right\rfloor\right)$$
  *(Level 0 = 20% 音量, Level 1 = 40% 音量, ..., Level 4 = 100% 音量)*

#### C. 後端 Python 程式碼邏輯預想
```python
import time

def calculate_volume_penalty(start_time):
    """
    計算自鬧鐘響起後流逝的時間與對應的音量比例
    """
    elapsed_seconds = int(time.time() - start_time)
    
    # 階梯音量計算 (每 30 秒提升 20%，最低 20%，最高 100%)
    penalty_steps = elapsed_seconds // 30
    volume_percentage = min(100.0, 20.0 + (penalty_steps * 20.0))
    penalty_level = min(4, penalty_steps)
    
    return {
        "elapsed_seconds": elapsed_seconds,
        "volume_percentage": volume_percentage,
        "penalty_level": penalty_level
    }
```

---

### 5.2 新增 API 路由設計

配合 F-02 的運作，新增以下兩個 API 端點：

| API 端點 | HTTP 方法 | 說明 | 請求參數 (JSON) | 回傳參數 (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| `/api/alarms/start` | `POST` | 初始化鬧鐘開始時間，啟動後端計時 | 無 | `{"success": true, "start_time": 1780453200}` |
| `/api/alarms/check-penalty` | `GET` | 查詢當前流逝秒數、應達音量百分比與懲罰等級 | 無 | `{"success": true, "elapsed_seconds": 65, "volume_percentage": 60.0, "penalty_level": 2}` |

#### 詳細驗證流程：
1. 用戶點擊進入解題 $\rightarrow$ 前端呼叫 `POST /api/alarms/start` $\rightarrow$ 後端建立 `session['alarm_start_time']`。
2. 前端透過 JavaScript `setInterval` 定時器（例如每 5 秒）呼叫 `GET /api/alarms/check-penalty`。
3. 後端讀取 Session 計算，回傳最新的音量比例 `volume_percentage`（如 `60.0`）與 `penalty_level`（如 `2`）。
4. 成功解題呼叫 `POST /api/verify_answer` 後，後端呼叫 `session.pop('alarm_start_time', None)` 完整清除計時狀態。

---

### 5.3 前端 JS 與 Web Audio API 配合更新音量機制

前端採用 Vanilla JS 配合 HTML5 的 Web Audio API 實現平滑、漸進的音量調整：

#### A. Web Audio API 架構設計
前端在初始化音訊時，需在 `OscillatorNode`（聲音產生器）與 `AudioDestinationNode`（喇叭輸出）之間插入一個 **`GainNode`（音量增益節點）**。

```
[OscillatorNode] ---> [GainNode (控制音量)] ---> [audioCtx.destination]
```

#### B. 前端 JS 定時輪詢與平滑音量控制代碼預想
```javascript
let gainNode = null;
let penaltyIntervalId = null;

// 在初始化音效時綁定 GainNode
function initAlarmSoundWithGain() {
    audioCtx = new AudioContext();
    gainNode = audioCtx.createGain();
    
    // 初始音量設定為 20%
    gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gainNode.connect(audioCtx.destination);
    
    // 定時播放鬧鈴
    alarmIntervalId = setInterval(() => {
        playBeepWithGain(880, 0.15);
    }, 1000);
}

function playBeepWithGain(frequency, duration) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    osc.type = "sine";
    osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
    
    // 連接至 gainNode 而非直接連 destination
    osc.connect(gainNode);
    
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
}

// 啟動定時輪詢懲罰 API
function startPenaltyPolling() {
    // 每 5 秒與後端同步一次最新的懲罰狀態
    penaltyIntervalId = setInterval(async () => {
        try {
            const response = await fetch('/api/alarms/check-penalty');
            const data = await response.json();
            
            if (data.success && gainNode) {
                const volRatio = data.volume_percentage / 100;
                
                // 使用 linearRampToValueAtTime 讓音量在 1 秒內平滑漸變，避免爆音
                gainNode.gain.linearRampToValueAtTime(volRatio, audioCtx.currentTime + 1.0);
                
                // 動態更新前端 UI：呈現當前懲罰秒數與警示狀態
                updatePenaltyUI(data.elapsed_seconds, data.volume_percentage, data.penalty_level);
            }
        } catch (e) {
            console.error("同步音量懲罰狀態失敗:", e);
        }
    }, 5000);
}

function updatePenaltyUI(elapsed, volPercent, level) {
    const subtitle = document.getElementById('statusSubtitle');
    subtitle.innerHTML = `已響鈴 <span style="color:var(--danger-color); font-weight:800;">${elapsed}</span> 秒 | 當前音量：<span style="color:var(--danger-color); font-weight:800;">${volPercent}%</span>`;
    
    // 依據懲罰等級 level (0~4) 調整背景紅色呼吸燈的閃爍速度與強度
    const overlay = document.querySelector('.alarm-pulse-overlay');
    if (overlay) {
        const speed = Math.max(0.5, 3 - level * 0.6); // level 越高，呼吸頻率越快
        overlay.style.animationDuration = `${speed}s`;
    }
}
```

---

## 6. MVP 範圍規劃

我們更新功能優先級層次如下：

```mermaid
kanban
  Must_Have["Must Have (第一階段核心)"]
    F-01_動態數學解題功能
    F-02_階梯音量懲罰功能 (後端計時與 volume 路由)
    後端_Session_安全答案與時間驗證
    基礎網頁解題與音量控制介面
  Should_Have["Should Have (第二階段優化)"]
    F-03_簡單/中等/困難三段難度切換
    Web_Audio_API_GainNode_音量平滑漸變
    實體虛擬大按鍵鍵盤與輸入動畫
  Nice_to_Have["Nice to Have (第三階段加分)"]
    F-04_解題時間與正確率歷史統計圖表
    F-05_貪睡限制與每貪睡一次難度升級機制
```

---

## 7. 專案成員與分工

本專案由開發團隊協同合作，具體分工如下表所示：

| 角色 / 職責 | 負責人 | 預估時數 | 交付產出物 | 備註 |
| :--- | :--- | :--- | :--- | :--- |
| **產品經理 (PM)** | 待指派 | | 產品需求文件 (PRD)、功能驗收規格 | |
| **後端工程師 (Backend)** | 待指派 | | Flask 路由、動態數學生成演算法、後端時間戳與音量演算法 API | |
| **前端工程師 (Frontend)** | 待指派 | | HTML 解題挑戰頁面、虛擬鍵盤、Web Audio API GainNode 控制、輪詢邏輯 | |
| **測試工程師 (QA)** | 待指派 | | 功能測試案例、音量漸強驗收報告 | |

---

*文件版本：v1.1 | 規劃日期：2026-06-02*
