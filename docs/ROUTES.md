# 路由與頁面設計文件 (ROUTES) — MathAlarm

本文件詳細規劃了「數學極致醒腦鬧鐘系統 (MathAlarm)」的 Flask 路由、HTTP 方法、表單輸入/輸出、錯誤處理機制，以及 Jinja2 模板結構。

---

## 1. 路由總覽表

本系統包含三大核心模組路由，所有操作皆符合 RESTful 精神與 HTML 表單規範：

| 模組名稱 | 功能說明 | HTTP 方法 | URL 路徑 | 對應 Jinja2 模板 | 輸出說明 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **通用模組** | 系統首頁與鬧鐘列表 | `GET` | `/` | `index.html` | 顯示音效授權開關、新增表單與所有鬧鐘卡片。 |
| **鬧鐘管理** | 建立新鬧鐘 | `POST` | `/alarms/new` | — | 接收表單並寫入 DB，完成後重導向至 `/`。 |
| | 切換啟用狀態 | `POST` | `/alarms/<int:id>/toggle` | — (AJAX JSON) | AJAX 切換鬧鐘 is_active 狀態，返回 JSON 結果。 |
| | 刪除鬧鐘 | `POST` | `/alarms/<int:id>/delete` | — | 接收 ID 從 DB 刪除鬧鐘，完成後重導向至 `/`。 |
| **警報與鎖定** | 鬧鐘到期背景輪詢 | `GET` | `/alarms/active-check` | — (AJAX JSON) | AJAX 每秒輪詢，檢查當前是否有鬧鐘到期。 |
| | 滿版響鈴鎖定作答 | `GET` | `/alarms/active/<int:id>` | `alarm_active.html` | 播放急促警報聲，鎖定螢幕，顯示數學題。 |
| | 數學解答比對驗證 | `POST` | `/alarms/active/<int:id>/verify` | — (AJAX JSON) | 驗證使用者輸入的數學答案。返回成功或失敗 JSON。 |
| | 按下貪睡按鈕 | `POST` | `/alarms/active/<int:id>/snooze` | — (AJAX JSON) | 暫停響鈴 5 分鐘，下次響起時附加貪睡懲罰。 |
| **數據統計** | 起床歷史數據儀表板 | `GET` | `/dashboard` | `dashboard.html` | 呈現起床歷史的統計與 Canvas 圖表。 |

---

## 2. 每個路由的詳細說明

### 2.1 系統首頁 (`GET /`)
- **輸入**：無。
- **處理邏輯**：
  1. 呼叫 `Alarm.get_all()` 獲取所有鬧鐘。
  2. 檢查 Session 中是否存有當前正在響鈴的 `ringing_alarm_id`。如果有，強制重導向至該鬧鐘的作答頁面 `/alarms/active/<id>`。
- **輸出**：渲染 `index.html`。
- **錯誤與異常處理**：資料庫無資料時，傳遞空陣列給前端，前端顯示「目前尚無鬧鐘，請點擊右下角新增！」提示。

### 2.2 建立新鬧鐘 (`POST /alarms/new`)
- **輸入**：表單欄位：`time` (時間，例如 `"08:00"`)、`repeat_days` (重複星期陣列)、`difficulty` (`'easy'/'medium'/'hard'`)、`task_count` (目標答對題數)、`note` (備註)。
- **處理邏輯**：
  1. 驗證 `time` 是否為空。若為空，設定 Flash Error 訊息並重導向回首頁。
  2. 將 `repeat_days` 陣列以逗號連結成字串（例如 `"1,2,3,4,5"`）。
  3. 呼叫 `Alarm.create(time, repeat_days, difficulty, task_count, note)`。
- **輸出**：重導向至首頁 `/`，並發送 Flash Success 訊息 "鬧鐘建立成功！"。

### 2.3 切換啟用狀態 (`POST /alarms/<id>/toggle`)
- **輸入**：URL 參數 `id`。
- **處理邏輯**：呼叫 `Alarm.toggle_status(id)`。
- **輸出**：回傳 JSON `{"success": true, "new_status": 1}` 或 `{"success": false, "message": "找不到該鬧鐘"}`。

### 2.4 刪除鬧鐘 (`POST /alarms/<id>/delete`)
- **輸入**：URL 參數 `id`。
- **處理邏輯**：呼叫 `Alarm.delete(id)`。
- **輸出**：重導向至 `/`，並發送 Flash Success 訊息 "鬧鐘已成功刪除"。

### 2.5 鬧鐘到期輪詢 (`GET /alarms/active-check`)
- **輸入**：無。
- **處理邏輯**：
  - 檢查當前時間與星期，比對啟用中的鬧鐘。
  - 若有鬧鐘的時間與目前系統時間精確相符（且重複星期符合或為單次鬧鐘），或有處於貪睡時間到期的鬧鐘，則將該鬧鐘的 ID 寫入 Session (`session['ringing_alarm_id'] = alarm_id`)。
- **輸出**：回傳 JSON `{"active": true, "alarm_id": id}`。若無則回傳 `{"active": false}`。

### 2.6 滿版響鈴鎖定作答 (`GET /alarms/active/<id>`)
- **輸入**：URL 參數 `id`。
- **處理邏輯**：
  1. 呼叫 `Alarm.get_by_id(id)`，若鬧鐘不存在，回傳 404。
  2. 若 Session 中沒有此 `ringing_alarm_id`，或鬧鐘已被停用，則不允許進入作答頁，重導向回首頁。
  3. 在 Session 中隨機產生題目並存入解答。例如：產生算式 `"35 + 18 - 9"`，計算出結果 `44`，存入 `session['math_answer'] = 44`，題目字串存入 `session['math_question'] = "35 + 18 - 9"`。
- **輸出**：渲染 `alarm_active.html`，傳遞題目字串及答題進度。

### 2.7 數學解答驗證 (`POST /alarms/active/<id>/verify`)
- **輸入**：JSON 表單：`answer` (使用者填寫的整數答案)。
- **處理邏輯**：
  1. 比對 `session['math_answer']` 與使用者輸入的值。
  2. **若答案正確**：
     - 使用者的答對題目數進度加 1。
     - 若答對題數達到鬧鐘設定的 `task_count`：
       - 呼叫 `History.create` 寫入歷史統計。
       - 清除 Session 中的鬧鐘響鈴狀態及算式緩存。
       - 呼叫 `Alarm.reset_snooze(id)` 重設貪睡與懲罰。
       - 返回 JSON `{"success": true, "finished": true}`。
     - 若答對題數未達到 `task_count`：
       - 在 Session 產生下一道數學題。
       - 返回 JSON `{"success": true, "finished": false, "next_question": new_question_string}`。
  3. **若答案錯誤**：
     - 將答錯次數加 1。
     - 產生下一道新題目以防使用者死背答案。
     - 返回 JSON `{"success": false, "finished": false, "message": "計算錯誤，題目已更新！", "next_question": new_question_string}`。

### 2.8 按下貪睡按鈕 (`POST /alarms/active/<id>/snooze`)
- **輸入**：URL 參數 `id`。
- **處理邏輯**：
  1. 呼叫 `Alarm.get_by_id(id)` 獲取資料。
  2. 將鬧鐘的 `snooze_count` 加 1。
  3. 計算下次響鈴時間（目前時間 + 5 分鐘），並寫入 `next_ring_time`。
  4. 清除 Session 的響鈴狀態 `session.pop('ringing_alarm_id')`。
- **輸出**：返回 JSON `{"success": true, "message": "鬧鐘已貪睡，大腦休息 5 分鐘！"}`。

---

## 3. Jinja2 模板清單

前端使用 Bootstrap 5 與 自訂 `css/style.css`，共有 4 個 Jinja2 HTML 模板：

1. **`base.html` (基礎布局模板)**
   - **繼承關係**：最頂層基礎模板。
   - **內容**：包含 HTML 標頭、載入 Google Fonts (Outfit / Inter) 與 Bootstrap 5 CSS、全域背景漸層、頂部導覽列（Logo、鬧鐘首頁、統計數據連結）、Flash 訊息顯示區域、以及 `{% block content %}{% endblock %}` 內容區塊。
2. **`index.html` (鬧鐘列表與設定)**
   - **繼承關係**：繼承自 `base.html`。
   - **內容**：
     - 頂部音效與感測器監聽的「啟動醒腦鬧鐘系統」玻璃開關。
     - 磨砂玻璃 (Glassmorphism) 卡片式鬧鐘列表，帶有啟用開關 (Switch) 與刪除按鈕，開關切換伴隨流暢 AJAX 不刷新頁面。
     - 右下角精美浮動新增按鈕 (Floating Action Button, FAB)，點擊開啟新增鬧鐘的 Modal 彈窗表單。
3. **`alarm_active.html` (全螢幕鎖定響鈴與作答頁)**
   - **繼承關係**：獨立渲染，不顯示 `base.html` 的頂部導覽列（防止使用者點選導覽列逃避作答）。
   - **內容**：
     - 滿版紅紫霓虹呼吸燈背景。
     - 醒目的倒數計時與進行中的警報動畫。
     - 題目區塊：大字體呈現數學算式，輸入答案框，提交按鈕。
     - 進度條：顯示目前答對題數 / 目標題數。
     - 貪睡按鈕：小字體，降低點擊誘因，並標註「貪睡將加重計算處罰」。
4. **`dashboard.html` (起床統計儀表板)**
   - **繼承關係**：繼承自 `base.html`。
   - **內容**：
     - 三個核心統計卡片：總起床次數、平均醒腦時間（秒）、總計算答錯次數。
     - 折線圖 (Line Chart)：以 Canvas 繪製最近 7 次起床作答時間趨勢。
     - 起床歷史紀錄的詳細資料表格。
