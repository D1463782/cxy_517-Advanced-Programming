/* MathAlarm — 全域 JavaScript 邏輯 */

const MathAlarm = {
  audioCtx: null,
  alarmInterval: null,
  elapsedSeconds: 0,
  elapsedTimer: null,
  game: {
    canvas: null,
    ctx: null,
    dot: { x: 0, y: 0, radius: 15, vx: 3, vy: 3 },
    hits: 0,
    requiredHits: 5,
    timeLeft: 5.0,
    gameInterval: null,
    active: false
  },

  // ─── 音效授權與合成系統 ───
  
  // 初始化/啟用音效（首頁點擊按鈕觸發）
  enableAudio: function() {
    try {
      if (!this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
      
      // 播放一聲超短的正弦波作為授權提示與暖機
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, this.audioCtx.currentTime);
      gain.gain.setValueAtTime(0.1, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.1);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + 0.1);
      
      // 紀錄授權狀態到 LocalStorage
      localStorage.setItem('audioAuthorized', 'true');
      this.updateAudioAuthUI(true);
      
      console.log("[INFO] Audio Context authorized and initialized.");
    } catch(e) {
      console.error("[ERROR] Failed to enable Audio Context: ", e);
    }
  },

  // 更新音效授權 UI 狀態
  updateAudioAuthUI: function(isAuthorized) {
    const card = document.getElementById('audioAuthCard');
    const statusText = document.querySelector('#authStatus .status-text');
    const btn = document.getElementById('audioAuthBtn');
    const icon = document.getElementById('authIcon');
    
    if (isAuthorized) {
      if (card) card.classList.add('authorized');
      if (statusText) statusText.innerText = "音效已授權監聽";
      if (icon) icon.innerText = "🔊";
      if (btn) {
        btn.disabled = true;
        btn.innerText = "已啟用";
        // 移除呼吸閃爍小點的 CSS pulse 動態
        const pulse = btn.querySelector('.btn-pulse');
        if (pulse) pulse.remove();
      }
    } else {
      if (card) card.classList.remove('authorized');
      if (statusText) statusText.innerText = "音效尚未授權";
      if (icon) icon.innerText = "🔇";
    }
  },

  // 播放急促警報鈴聲 (F-02: 隨時間階梯懲罰調升音量與頻率)
  playAlarm: function() {
    if (this.alarmInterval) return;
    
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    this.alarmInterval = setInterval(() => {
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
      
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      
      // F-02 懲罰機制：隨時間增加頻率 (250ms ~ 150ms 變快) 與音調 (600Hz ~ 1500Hz)
      const elapsed = this.elapsedSeconds;
      const baseFreq = 750 + Math.min(elapsed * 8, 850);  // 最高到 1600Hz
      const vol = 0.2 + Math.min(elapsed * 0.015, 0.65);  // 最大音量放大到 0.85
      
      osc.type = 'sawtooth'; // 急促刺耳鋸齒波
      osc.frequency.setValueAtTime(baseFreq, this.audioCtx.currentTime);
      
      // 雙音警報：交替高低音
      const isEven = Math.floor(Date.now() / 250) % 2 === 0;
      if (isEven) {
        osc.frequency.setValueAtTime(baseFreq * 0.8, this.audioCtx.currentTime);
      }
      
      gain.gain.setValueAtTime(vol, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.16);
      
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      
      osc.start();
      osc.stop(this.audioCtx.currentTime + 0.16);
    }, 280); // 每 280ms 響一聲
  },

  // 停止警報鈴聲
  stopAlarm: function() {
    if (this.alarmInterval) {
      clearInterval(this.alarmInterval);
      this.alarmInterval = null;
    }
  },

  // 播放答對成功音效 (上升和弦)
  playSuccessSound: function() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const now = this.audioCtx.currentTime;
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5 -> E5 -> G5 -> C6
    
    notes.forEach((freq, idx) => {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now + idx * 0.1);
      
      gain.gain.setValueAtTime(0.25, now + idx * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.1 + 0.22);
      
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      
      osc.start(now + idx * 0.1);
      osc.stop(now + idx * 0.1 + 0.22);
    });
  },

  // 播放答錯音效 (下降悲傷音效)
  playWrongSound: function() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const now = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(220, now);
    osc.frequency.linearRampToValueAtTime(110, now + 0.35); // 頻率迅速下降
    
    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
    
    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    
    osc.start(now);
    osc.stop(now + 0.35);
  },

  // ─── 鬧鐘新增與列表控制 (首頁) ───

  // 開啟 Modal
  openModal: function() {
    const modal = document.getElementById('alarmModal');
    if (modal) {
      // 重設標題與 action
      const title = modal.querySelector('.modal-header h2');
      if (title) title.innerText = "⏰ 新增鬧鐘";
      const form = modal.querySelector('.alarm-form');
      if (form) form.action = "/alarms/new";
      
      // 重設預設值
      const presetSelect = document.getElementById('alarmPreset');
      if (presetSelect) presetSelect.value = "custom";
      const noteInput = document.getElementById('alarmNote');
      if (noteInput) noteInput.value = "";
      const taskCountInput = document.getElementById('alarmTaskCount');
      if (taskCountInput) taskCountInput.value = "1";
      
      const weekdays = document.querySelectorAll('.weekday-chip input');
      weekdays.forEach(w => w.checked = false);
      
      const diffInputs = document.querySelectorAll('.difficulty-selector input');
      diffInputs.forEach(i => {
        if (i.value === 'easy') i.checked = true;
      });

      modal.classList.add('open');
      // 自動設定預設時間為當前時間的下一分鐘
      const now = new Date();
      now.setMinutes(now.getMinutes() + 1);
      const hours = String(now.getHours()).padStart(2, '0');
      const mins = String(now.getMinutes()).padStart(2, '0');
      document.getElementById('alarmTime').value = `${hours}:${mins}`;
    }
  },

  // 關閉 Modal
  closeModal: function() {
    const modal = document.getElementById('alarmModal');
    if (modal) modal.classList.remove('open');
  },

  // 開啟編輯 Modal
  openEditModal: function(alarm) {
    const modal = document.getElementById('alarmModal');
    if (!modal) return;
    
    // 變更標題與表單 action
    const title = modal.querySelector('.modal-header h2');
    if (title) title.innerText = "⏰ 編輯鬧鐘";
    const form = modal.querySelector('.alarm-form');
    if (form) form.action = `/alarms/${alarm.id}/edit`;
    
    // 設定預設情境下拉選單為「自訂模式」
    const presetSelect = document.getElementById('alarmPreset');
    if (presetSelect) presetSelect.value = "custom";
    
    // 填入時間
    const timeInput = document.getElementById('alarmTime');
    if (timeInput) timeInput.value = alarm.time;
    
    // 填入備註
    const noteInput = document.getElementById('alarmNote');
    if (noteInput) noteInput.value = alarm.note || "";
    
    // 填入答對題數
    const taskCountInput = document.getElementById('alarmTaskCount');
    if (taskCountInput) taskCountInput.value = alarm.task_count;
    
    // 填入重複日
    const weekdays = document.querySelectorAll('.weekday-chip input');
    const repeatDaysList = alarm.repeat_days ? alarm.repeat_days.split(',') : [];
    weekdays.forEach(w => {
      w.checked = repeatDaysList.includes(w.value);
    });
    
    // 填入難度
    const diffInputs = document.querySelectorAll('.difficulty-selector input');
    diffInputs.forEach(i => {
      i.checked = (i.value === alarm.difficulty);
    });
    
    // 開啟 Modal
    modal.classList.add('open');
  },

  // 調整答對題數限制
  adjustCount: function(change) {
    const input = document.getElementById('alarmTaskCount');
    if (!input) return;
    let val = parseInt(input.value) + change;
    if (val < 1) val = 1;
    if (val > 10) val = 10;
    input.value = val;
  },

  // 切換啟用/停用鬧鐘 (AJAX)
  toggleAlarm: function(alarmId) {
    fetch(`/alarms/${alarmId}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const card = document.querySelector(`.alarm-card[data-alarm-id="${alarmId}"]`);
        if (card) {
          if (data.new_status === 1) {
            card.classList.remove('inactive');
          } else {
            card.classList.add('inactive');
          }
        }
        console.log(`[INFO] Alarm ${alarmId} active state toggled to ${data.new_status}`);
      } else {
        alert(data.message || '切換鬧鐘狀態失敗！');
      }
    })
    .catch(err => {
      console.error(err);
      alert('無法通訊與伺服器連接！');
    });
  },

  // 套用情境預設模式 (F-09)
  applyPreset: function(preset) {
    const timeInput = document.getElementById('alarmTime');
    const taskCountInput = document.getElementById('alarmTaskCount');
    const noteInput = document.getElementById('alarmNote');
    const weekdays = document.querySelectorAll('.weekday-chip input');
    const diffInputs = document.querySelectorAll('.difficulty-selector input');

    if (preset === 'exam') {
      // 考試地獄：困難 (hard) / 5題 / 禁用貪睡 (備註寫入禁貪睡)
      taskCountInput.value = 5;
      noteInput.value = "🔥 考試地獄模式！禁起用貪睡！";
      
      // 選擇 hard
      diffInputs.forEach(i => {
        if (i.value === 'hard') i.checked = true;
      });
      // 自動勾選週一到週五
      weekdays.forEach(w => {
        const val = w.value;
        w.checked = (val !== '6' && val !== '0');
      });
    } else if (preset === 'weekday') {
      // 平日上課：中等 (medium) / 2題 / 可貪睡 / 自動週一到週五
      taskCountInput.value = 2;
      noteInput.value = "🏫 平日上課，加油起床";
      
      diffInputs.forEach(i => {
        if (i.value === 'medium') i.checked = true;
      });
      weekdays.forEach(w => {
        const val = w.value;
        w.checked = (val !== '6' && val !== '0');
      });
    } else if (preset === 'weekend') {
      // 週末溫和：簡單 (easy) / 1題 / 自動週六、週日
      taskCountInput.value = 1;
      noteInput.value = "😊 週末溫和喚醒";
      
      diffInputs.forEach(i => {
        if (i.value === 'easy') i.checked = true;
      });
      weekdays.forEach(w => {
        const val = w.value;
        w.checked = (val === '6' || val === '0');
      });
    } else {
      // 自訂模式：不做變更，清空備註與星期
      noteInput.value = "";
      weekdays.forEach(w => w.checked = false);
      diffInputs.forEach(i => {
        if (i.value === 'easy') i.checked = true;
      });
      taskCountInput.value = 1;
    }
  },

  // ─── 背景監聽定時器 (首頁輪詢) ───
  startBackgroundCheck: function() {
    // 檢查 localStorage 狀態，更新首頁授權狀態
    if (localStorage.getItem('audioAuthorized') === 'true') {
      this.updateAudioAuthUI(true);
      // 設定滑鼠/觸控事件來啟動 AudioContext
      const unlockAudio = () => {
        this.enableAudio();
        document.removeEventListener('click', unlockAudio);
        document.removeEventListener('touchstart', unlockAudio);
      };
      document.addEventListener('click', unlockAudio);
      document.addEventListener('touchstart', unlockAudio);
    }
    
    // 背景定時器：每秒輪詢
    setInterval(() => {
      fetch('/alarms/active-check')
      .then(res => res.json())
      .then(data => {
        if (data.active) {
          console.log("[INFO] Active alarm detected! Redirecting...");
          // 前往鎖定頁
          window.location.href = `/alarms/active/${data.alarm_id}`;
        }
      })
      .catch(err => console.error("Polling error: ", err));
    }, 1000);
  },

  // ─── 滿版鎖定頁面控制 (Active Lock Screen) ───
  initLockScreen: function() {
    this.elapsedSeconds = 0;
    
    // 1. 每秒更新時間與定時累加秒數 (F-02 懲罰依據)
    const timeEl = document.getElementById('currentTime');
    const timerEl = document.getElementById('elapsedTime');
    
    this.elapsedTimer = setInterval(() => {
      this.elapsedSeconds++;
      if (timerEl) timerEl.innerText = this.elapsedSeconds;
      
      const now = new Date();
      if (timeEl) {
        timeEl.innerText = now.toTimeString().split(' ')[0];
      }
    }, 1000);

    // 2. 播放警報聲
    this.playAlarm();

    // 3. 防弊機制：阻斷鍵盤 Backspace 與 Escape 等快捷鍵
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' || e.key === 'Escape') {
        e.preventDefault();
      }
    });

    // 4. 重整防規避：綁定 beforeunload
    window.onbeforeunload = function() {
      return "請勿關閉網頁！鬧鐘仍在響鈴中！";
    };
  },

  // 提交數學題答案 (AJAX)
  submitAnswer: function(alarmId) {
    const input = document.getElementById('answerInput');
    const feedback = document.getElementById('feedbackMsg');
    if (!input) return;
    
    const ans = input.value.trim();
    if (!ans) {
      feedback.className = "feedback-message";
      feedback.innerText = "請輸入有效的數學答案！";
      return;
    }

    fetch(`/alarms/active/${alarmId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: ans })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        input.value = "";
        
        if (data.finished) {
          // 解鎖成功 (無 Canvas 遊戲的傳統回退，或完成解題)
          this.handleUnlockSuccess();
        } else if (data.show_game) {
          // 進入 F-07 快速反應點擊遊戲
          this.playSuccessSound();
          feedback.className = "feedback-message success";
          feedback.innerText = "數學關卡通過！準備雙重清醒測試...";
          setTimeout(() => {
            this.startCanvasGame(alarmId);
          }, 1000);
        } else {
          // 答對但尚未滿題：更新下一題
          this.playSuccessSound();
          feedback.className = "feedback-message success";
          feedback.innerText = "答對了！繼續下一題";
          
          document.getElementById('questionText').innerText = data.next_question;
          document.getElementById('correctCount').innerText = data.correct_count;
          document.getElementById('progressBar').style.width = `${(data.correct_count / data.task_count) * 100}%`;
          input.focus();
        }
      } else {
        // 答錯
        this.playWrongSound();
        feedback.className = "feedback-message";
        feedback.innerText = data.message || "計算錯誤！";
        
        // 搖晃輸入框特效
        input.classList.add('shake');
        setTimeout(() => input.classList.remove('shake'), 500);

        if (data.next_question) {
          document.getElementById('questionText').innerText = data.next_question;
        }
        input.value = "";
        input.focus();
      }
    })
    .catch(err => {
      console.error(err);
      feedback.innerText = "驗證出錯，請重試！";
    });
  },

  // 貪睡鬧鐘 (AJAX)
  snoozeAlarm: function(alarmId) {
    if (!confirm('按下貪睡會加倍下次的題目難度與數量，確定要大腦偷懶 5 分鐘嗎？')) {
      return;
    }

    fetch(`/alarms/active/${alarmId}/snooze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        this.stopAlarm();
        clearInterval(this.elapsedTimer);
        window.onbeforeunload = null; // 解除重整警告
        alert(data.message);
        window.location.href = "/";
      } else {
        alert(data.message || "貪睡失敗！");
      }
    })
    .catch(err => {
      console.error(err);
      alert("無法通訊與伺服器連接！");
    });
  },

  // 解鎖成功後續處理 (帶早安語錄與連續早起天數展示)
  handleUnlockSuccess: function(streak) {
    this.stopAlarm();
    this.playSuccessSound();
    clearInterval(this.elapsedTimer);
    window.onbeforeunload = null; // 解除警告

    // 隨機早安語錄清單 (F-06)
    const quotes = [
      "早安！大腦已經完全甦醒，今天也要朝著夢想前進！🚀",
      "今天的你，比昨天的你更早起了一點點，這就是進步！💪",
      "起床吧！今天的太陽很溫暖，而你的期末專題也一定會順利通過！🎓",
      "聽說早起的人會有好運，但如果不起來，好運就只能在夢裡見了 😴",
      "大腦已開機，邏輯已上線。今天又是充滿代碼與活力的一天！💻",
      "成功就是每天早上起床，決定今天要做一個比昨天更好的人 ✨",
      "早起的人有蟲吃，晚起的人就只能被鬧鐘轟炸了 🐛",
      "大腦清醒度 100%，恭喜你成功戰勝睡魔！出發征服今天吧！🏆"
    ];
    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    
    // 更新語錄與連續天數
    const quoteText = document.getElementById('quoteText');
    if (quoteText) quoteText.innerText = randomQuote;
    
    const quoteSub = document.querySelector('.quote-sub');
    if (quoteSub && streak !== undefined) {
      quoteSub.innerHTML = `🔥 您已連續早起 <strong>${streak}</strong> 天！養成良好的早起習慣，今天也要加油哦！`;
    }

    // 顯示早安語錄 modal
    const quoteModal = document.getElementById('quoteModal');
    if (quoteModal) {
      quoteModal.classList.add('open');
    } else {
      // 回退機制 (如果 modal 不存在)
      const feedback = document.getElementById('feedbackMsg');
      if (feedback) {
        feedback.className = "feedback-message success";
        feedback.innerText = `🎉 挑戰成功！連續早起 ${streak || 0} 天！3 秒後回首頁。`;
      }
      setTimeout(() => {
        window.location.href = "/";
      }, 3000);
    }
  },

  // ─── F-07 快速反應點擊 Canvas 遊戲實作 ───
  startCanvasGame: function(alarmId) {
    // 隱藏數學卡片、答題與貪睡區
    document.getElementById('questionCard').style.display = 'none';
    document.querySelector('.answer-section').style.display = 'none';
    document.querySelector('.snooze-section').style.display = 'none';
    document.getElementById('feedbackMsg').innerText = "";

    // 顯示遊戲容器
    const gameContainer = document.getElementById('gameContainer');
    if (gameContainer) gameContainer.style.display = 'block';

    const canvas = document.getElementById('gameCanvas');
    if (!canvas) return;

    this.game.canvas = canvas;
    this.game.ctx = canvas.getContext('2d');
    this.game.hits = 0;
    this.game.timeLeft = 5.0;
    this.game.active = true;

    // 重設紅點座標
    this.resetDot();

    // 更新點擊進度 UI
    document.getElementById('gameHitsText').innerText = `${this.game.hits} / ${this.game.requiredHits}`;
    document.getElementById('gameTimeText').innerText = `${this.game.timeLeft.toFixed(1)}s`;

    // 監聽畫布點擊事件
    canvas.onclick = (e) => {
      if (!this.game.active) return;

      // 取得相對於 canvas 的點擊座標
      const rect = canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      // 計算點擊距離
      const dist = Math.sqrt((clickX - this.game.dot.x)**2 + (clickY - this.game.dot.y)**2);
      if (dist <= this.game.dot.radius + 8) { // 加上 8px 緩衝區增加手勢靈敏度
        this.game.hits++;
        document.getElementById('gameHitsText').innerText = `${this.game.hits} / ${this.game.requiredHits}`;
        this.playSuccessSound(); // 點對提示

        if (this.game.hits >= this.game.requiredHits) {
          this.endCanvasGame(alarmId, true);
        } else {
          this.resetDot(); // 點對之後隨機生成新紅點
        }
      } else {
        this.playWrongSound(); // 點錯提示，球會加快
        this.game.dot.vx *= 1.2;
        this.game.dot.vy *= 1.2;
      }
    };

    // 啟動遊戲迴圈：繪製與倒數計時
    let lastTime = performance.now();
    const gameLoop = (timestamp) => {
      if (!this.game.active) return;

      const dt = (timestamp - lastTime) / 1000;
      lastTime = timestamp;

      // 更新倒數時間
      this.game.timeLeft -= dt;
      if (this.game.timeLeft <= 0) {
        this.game.timeLeft = 0;
        document.getElementById('gameTimeText').innerText = "0.0s";
        this.endCanvasGame(alarmId, false);
        return;
      }
      document.getElementById('gameTimeText').innerText = `${this.game.timeLeft.toFixed(1)}s`;

      this.updateDot();
      this.drawGame();

      requestAnimationFrame(gameLoop);
    };
    requestAnimationFrame(gameLoop);
  },

  // 更新小紅球移動與碰撞邊框反射
  updateDot: function() {
    const dot = this.game.dot;
    const canvas = this.game.canvas;
    
    dot.x += dot.vx;
    dot.y += dot.vy;

    // 邊界反射 (加上球半徑邊距)
    if (dot.x - dot.radius < 0) {
      dot.x = dot.radius;
      dot.vx = -dot.vx;
    }
    if (dot.x + dot.radius > canvas.width) {
      dot.x = canvas.width - dot.radius;
      dot.vx = -dot.vx;
    }
    if (dot.y - dot.radius < 0) {
      dot.y = dot.radius;
      dot.vy = -dot.vy;
    }
    if (dot.y + dot.radius > canvas.height) {
      dot.y = canvas.height - dot.radius;
      dot.vy = -dot.vy;
    }
  },

  // 繪製紅小球與殘影特效
  drawGame: function() {
    const ctx = this.game.ctx;
    const canvas = this.game.canvas;
    const dot = this.game.dot;

    // 磨砂質感背景半透明刷拭 (形成運動殘影)
    ctx.fillStyle = 'rgba(10, 14, 26, 0.25)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 繪製光暈外圈
    ctx.beginPath();
    ctx.arc(dot.x, dot.y, dot.radius * 1.6, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(244, 63, 94, 0.25)';
    ctx.fill();

    // 繪製主小球 (亮紅)
    ctx.beginPath();
    ctx.arc(dot.x, dot.y, dot.radius, 0, Math.PI * 2);
    ctx.fillStyle = '#f43f5e';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
  },

  // 隨機重設小球位置與隨機速度向量
  resetDot: function() {
    const canvas = this.game.canvas;
    const dot = this.game.dot;
    if (!canvas) return;

    dot.radius = 12 + Math.random() * 6; // 隨機半徑 12 ~ 18
    dot.x = dot.radius + Math.random() * (canvas.width - dot.radius * 2);
    dot.y = dot.radius + Math.random() * (canvas.height - dot.radius * 2);

    // 隨機方向速度 (-4 到 4) 且不為零
    const baseSpeed = 2.5 + Math.min(this.elapsedSeconds * 0.05, 3.5); // 隨已過秒數增加難度
    dot.vx = (Math.random() > 0.5 ? 1 : -1) * (baseSpeed + Math.random() * 2);
    dot.vy = (Math.random() > 0.5 ? 1 : -1) * (baseSpeed + Math.random() * 2);
  },

  // 結束 Canvas 遊戲並向後端發送驗證 (F-07)
  endCanvasGame: function(alarmId, success) {
    this.game.active = false;
    
    if (success) {
      // 成功：向後端解鎖
      fetch(`/alarms/active/${alarmId}/verify-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          document.getElementById('gameContainer').style.display = 'none';
          document.getElementById('feedbackMsg').style.display = 'block';
          this.handleUnlockSuccess(data.streak);
        }
      })
      .catch(err => {
        console.error(err);
        alert("無法傳送解鎖訊號！");
      });
    } else {
      // 失敗 (時間到)：重回數學題目，大腦重罰 (重設計時器)
      this.playWrongSound();
      alert("⚠️ 反應力測試超時！大腦清醒度不足，重回數學加碼題！");
      
      // 更新 math_question
      window.location.reload();
    }
  },

  // ─── F-08 緊急求救罰寫解鎖 ───
  triggerSOSMode: function(alarmId) {
    if (!confirm('🚨 緊急求救：解題卡關？需進行 10 次罰寫確認大腦已活動，此解鎖將記為 SOS 起床歷史。確定要啟用嗎？')) {
      return;
    }

    // 隱藏數學卡片、答題與貪睡區
    document.getElementById('questionCard').style.display = 'none';
    document.querySelector('.answer-section').style.display = 'none';
    document.querySelector('.snooze-section').style.display = 'none';
    document.getElementById('gameContainer').style.display = 'none';
    document.getElementById('feedbackMsg').innerText = "";

    // 取得罰寫句子 (AJAX)
    fetch(`/alarms/active/${alarmId}/sos`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        document.getElementById('sosSentence').innerText = data.sentence;
        document.getElementById('sosHitsText').innerText = `0 / 10`;
        document.getElementById('sosContainer').style.display = 'block';
        document.getElementById('sosInput').focus();
      }
    })
    .catch(err => {
      console.error(err);
      alert("無法連線取得求救內容！");
    });
  },

  // 提交罰寫比對
  submitSOS: function(alarmId) {
    const input = document.getElementById('sosInput');
    const feedback = document.getElementById('feedbackMsg');
    if (!input) return;

    const val = input.value.trim();
    if (!val) return;

    fetch(`/alarms/active/${alarmId}/verify-sos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_text: val })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        input.value = "";
        
        if (data.finished) {
          // 罰寫解鎖成功
          document.getElementById('sosContainer').style.display = 'none';
          document.getElementById('feedbackMsg').style.display = 'block';
          this.handleUnlockSuccess(data.streak);
        } else {
          this.playSuccessSound(); // 正確提醒
          document.getElementById('sosHitsText').innerText = `${data.written_count} / 10`;
          feedback.className = "feedback-message success";
          feedback.innerText = `第 ${data.written_count} 次罰寫正確，請繼續輸入！`;
          input.focus();
        }
      } else {
        this.playWrongSound(); // 錯誤提醒
        feedback.className = "feedback-message";
        feedback.innerText = data.message || "罰寫內容不相符，請核對空白與標點符號！";
        input.classList.add('shake');
        setTimeout(() => input.classList.remove('shake'), 500);
        input.focus();
      }
    })
    .catch(err => {
      console.error(err);
      feedback.innerText = "傳送罰寫時發生錯誤，請重試！";
    });
  }
};
