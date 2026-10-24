/**
 * Main Application Logic for "Maosh va Xarajatlar" Telegram Mini App
 */

document.addEventListener("DOMContentLoaded", () => {
  const user = TelegramHelper.user;
  const API_BASE = window.location.origin;

  // --- State Variables ---
  let currentTab = "tab-calculator";
  let activeType = "expense"; // "expense" or "income"
  let selectedCategory = "food";
  let currentExpression = "";
  let calculatedAmount = 0;
  let activeLoans = [];
  let userGoals = [];

  // --- UI Elements ---
  const userAvatar = document.getElementById("user-avatar");
  const userName = document.getElementById("user-name");
  const currentDate = document.getElementById("current-date");
  const liveFreeSum = document.getElementById("live-free-sum");
  const stripIncome = document.getElementById("strip-income");
  const stripExpense = document.getElementById("strip-expense");
  const stripReserve = document.getElementById("strip-reserve");
  const calcExpr = document.getElementById("calc-expr");
  const calcVal = document.getElementById("calc-val");
  const toggleExpense = document.getElementById("toggle-expense");
  const toggleIncome = document.getElementById("toggle-income");
  const btnSubmitAction = document.getElementById("btn-submit-action");
  const expenseCategories = document.getElementById("expense-categories");
  const toastMsg = document.getElementById("toast-msg");

  // --- Init Profile & Date ---
  function initHeader() {
    if (user.first_name) {
      userName.textContent = user.first_name;
      userAvatar.textContent = user.first_name.charAt(0).toUpperCase();
    }
    
    // Uzbek date format
    const now = new Date();
    const days = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];
    const months = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktyabr", "Noyabr", "Dekabr"];
    currentDate.textContent = `${days[now.getDay()]}, ${now.getDate()}-${months[now.getMonth()]}`;
  }

  // --- Toast Helper ---
  function showToast(msg, duration = 2500) {
    toastMsg.textContent = msg;
    toastMsg.classList.add("show");
    setTimeout(() => {
      toastMsg.classList.remove("show");
    }, duration);
  }

  // --- Format Currency (UZS) ---
  function formatMoney(amount) {
    if (amount === undefined || amount === null || isNaN(amount)) return "0";
    return Math.round(amount).toLocaleString("uz-UZ");
  }

  // --- Tab Navigation ---
  const navTabs = document.querySelectorAll(".nav-tab");
  navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      TelegramHelper.triggerHaptic("light");
      const target = tab.dataset.tab;
      switchTab(target);
    });
  });

  function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll(".tab-screen").forEach(s => s.classList.remove("active"));
    document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));

    const activeScreen = document.getElementById(tabId);
    if (activeScreen) activeScreen.classList.add("active");

    const activeNav = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    if (activeNav) activeNav.classList.add("active");

    // Refresh specific tab data
    if (tabId === "tab-calculator") refreshBalance();
    if (tabId === "tab-loans") loadLoans();
    if (tabId === "tab-analytics") loadAnalytics();
    if (tabId === "tab-history") {
      loadTransactions();
      loadGoals();
    }
  }

  // --- Calculator Logic ---
  const numpadButtons = document.querySelectorAll(".num-btn[data-key]");
  numpadButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.key;
      handleKeyInput(key);
    });
  });

  function handleKeyInput(key) {
    TelegramHelper.triggerHaptic("light");

    if (key === "clear") {
      currentExpression = "";
      calculatedAmount = 0;
      updateCalcDisplay();
      return;
    }

    if (key === "backspace") {
      if (currentExpression.length > 0) {
        currentExpression = currentExpression.trimEnd();
        currentExpression = currentExpression.slice(0, -1).trimEnd();
      }
      evaluateExpression();
      updateCalcDisplay();
      return;
    }

    if (key === "+") {
      if (currentExpression.length > 0 && !currentExpression.endsWith("+")) {
        currentExpression += " + ";
      }
      updateCalcDisplay();
      return;
    }

    // Numbers & 00
    if (currentExpression === "0" && key !== "+") {
      currentExpression = key;
    } else {
      currentExpression += key;
    }

    evaluateExpression();
    updateCalcDisplay();
  }

  function evaluateExpression() {
    if (!currentExpression.trim()) {
      calculatedAmount = 0;
      return;
    }
    try {
      // Clean and split by '+' safely
      const parts = currentExpression.split("+").map(p => p.trim()).filter(Boolean);
      let sum = 0;
      for (const p of parts) {
        const val = parseFloat(p.replace(/[^0-9.]/g, ""));
        if (!isNaN(val)) sum += val;
      }
      calculatedAmount = sum;
    } catch {
      calculatedAmount = 0;
    }
  }

  function updateCalcDisplay() {
    calcExpr.textContent = currentExpression || " ";
    calcVal.textContent = formatMoney(calculatedAmount);
  }

  // --- Type Toggle (Xarajat vs Daromad) ---
  toggleExpense.addEventListener("click", () => {
    TelegramHelper.triggerHaptic("medium");
    activeType = "expense";
    toggleExpense.classList.add("active");
    toggleIncome.classList.remove("active");
    expenseCategories.style.display = "flex";
    btnSubmitAction.className = "num-btn action-btn submit-expense";
    btnSubmitAction.innerHTML = "<span>Xarajat ✓</span>";
  });

  toggleIncome.addEventListener("click", () => {
    TelegramHelper.triggerHaptic("medium");
    activeType = "income";
    toggleIncome.classList.add("active");
    toggleExpense.classList.remove("active");
    expenseCategories.style.display = "none";
    btnSubmitAction.className = "num-btn action-btn submit-income";
    btnSubmitAction.innerHTML = "<span>Daromad ✓</span>";
  });

  // Category Selection
  document.querySelectorAll(".cat-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      TelegramHelper.triggerHaptic("light");
      document.querySelectorAll(".cat-chip").forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
      selectedCategory = chip.dataset.cat;
    });
  });

  // Submit Action (Enter Expense / Income)
  btnSubmitAction.addEventListener("click", async () => {
    evaluateExpression();
    if (calculatedAmount <= 0) {
      TelegramHelper.triggerHaptic("warning");
      showToast("Iltimos, summani kiriting!");
      return;
    }

    const payload = {
      user_id: user.id,
      type: activeType,
      category: activeType === "income" ? "salary" : selectedCategory,
      amount: calculatedAmount,
      raw_expression: currentExpression || null,
      note: null
    };

    try {
      const res = await fetch(`${API_BASE}/api/transactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        TelegramHelper.triggerHaptic("success");
        showToast(activeType === "income" ? `+${formatMoney(calculatedAmount)} so'm daromad yozildi!` : `-${formatMoney(calculatedAmount)} so'm xarajat yozildi!`);
        currentExpression = "";
        calculatedAmount = 0;
        updateCalcDisplay();
        refreshBalance();
      } else {
        throw new Error("Xatolik yuz berdi");
      }
    } catch (err) {
      TelegramHelper.triggerHaptic("error");
      showToast("Server bilan bog'lanishda xatolik!");
      console.error(err);
    }
  });

  // --- Balance Refresh ---
  async function refreshBalance() {
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/balance`);
      if (res.ok) {
        const data = await res.json();
        liveFreeSum.textContent = formatMoney(data.safe_free_balance);
        stripIncome.textContent = `+${formatMoney(data.today_income)}`;
        stripExpense.textContent = `-${formatMoney(data.today_expense)}`;
        stripReserve.textContent = `-${formatMoney(data.daily_loan_reserve)}`;
      }
    } catch (err) {
      console.error("Balance refresh error:", err);
    }
  }

  // --- Loans & Debts Management ---
  async function loadLoans() {
    const container = document.getElementById("loans-list-container");
    const reserveBadge = document.getElementById("daily-reserve-badge");
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/loans`);
      if (res.ok) {
        activeLoans = await res.json();
        
        // Calculate daily reserve
        const monthlySum = activeLoans.filter(l => l.is_active).reduce((sum, l) => sum + l.monthly_payment, 0);
        const dailyReserve = Math.round(monthlySum / 30);
        reserveBadge.textContent = `${formatMoney(dailyReserve)} so'm/kun`;

        if (activeLoans.length === 0) {
          container.innerHTML = `
            <div style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 13px;">
              Hozircha kredit yoki qarzlaringiz yo'q. Baraka topsin!
            </div>`;
          return;
        }

        container.innerHTML = activeLoans.map(loan => {
          const paid = loan.total_amount - loan.remaining_amount;
          const pct = Math.min(100, Math.max(0, Math.round((paid / loan.total_amount) * 100)));
          return `
            <div class="loan-item-card">
              <div class="loan-header">
                <span class="loan-name">${loan.title}</span>
                <span class="loan-remaining">${formatMoney(loan.remaining_amount)} so'm</span>
              </div>
              <div class="progress-track">
                <div class="progress-bar" style="width: ${pct}%;"></div>
              </div>
              <div class="loan-footer">
                <span>Oylik: <b>${formatMoney(loan.monthly_payment)} so'm</b> (${loan.due_day}-sana)</span>
                ${loan.is_active ? `<button class="pay-btn-sm" onclick="window.openPayModal(${loan.id}, '${loan.title}')">To'lash</button>` : `<span class="badge green">To'langan</span>`}
              </div>
            </div>`;
        }).join("");
      }
    } catch (err) {
      console.error("Load loans error:", err);
    }
  }

  // Add Loan Form
  const modalAddLoan = document.getElementById("modal-add-loan");
  document.getElementById("btn-open-add-loan").addEventListener("click", () => {
    TelegramHelper.triggerHaptic("medium");
    modalAddLoan.classList.add("active");
  });
  document.getElementById("close-add-loan").addEventListener("click", () => {
    modalAddLoan.classList.remove("active");
  });

  document.getElementById("form-add-loan").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("loan-title").value.trim();
    const total = parseFloat(document.getElementById("loan-total").value);
    const monthly = parseFloat(document.getElementById("loan-monthly").value);
    const day = parseInt(document.getElementById("loan-day").value, 10);

    try {
      const res = await fetch(`${API_BASE}/api/loans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          title,
          total_amount: total,
          monthly_payment: monthly,
          remaining_amount: total,
          due_day: day
        })
      });

      if (res.ok) {
        TelegramHelper.triggerHaptic("success");
        showToast("Yangi kredit muvaffaqiyatli qo'shildi!");
        modalAddLoan.classList.remove("active");
        document.getElementById("form-add-loan").reset();
        loadLoans();
        refreshBalance();
      }
    } catch (err) {
      TelegramHelper.triggerHaptic("error");
      showToast("Qo'shishda xatolik!");
    }
  });

  // Pay Loan Modal
  const modalPayLoan = document.getElementById("modal-pay-loan");
  window.openPayModal = function(loanId, loanTitle) {
    TelegramHelper.triggerHaptic("medium");
    document.getElementById("pay-loan-id").value = loanId;
    document.getElementById("pay-loan-title").textContent = `${loanTitle} To'lovi`;
    modalPayLoan.classList.add("active");
  };
  document.getElementById("close-pay-loan").addEventListener("click", () => {
    modalPayLoan.classList.remove("active");
  });

  document.getElementById("form-pay-loan").addEventListener("submit", async (e) => {
    e.preventDefault();
    const loanId = document.getElementById("pay-loan-id").value;
    const amount = parseFloat(document.getElementById("pay-loan-amount").value);

    try {
      const res = await fetch(`${API_BASE}/api/loans/${loanId}/pay?user_id=${user.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount })
      });

      if (res.ok) {
        TelegramHelper.triggerHaptic("success");
        showToast("Kredit to'lovi qabul qilindi!");
        modalPayLoan.classList.remove("active");
        document.getElementById("form-pay-loan").reset();
        loadLoans();
        refreshBalance();
      }
    } catch (err) {
      TelegramHelper.triggerHaptic("error");
      showToast("To'lovda xatolik!");
    }
  });

  // --- Smart Analytics & Black Hole (Qora Tuynuk) ---
  async function loadAnalytics() {
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/analytics`);
      if (res.ok) {
        const data = await res.json();
        document.getElementById("analytics-month-title").textContent = `${data.month_name} Tahlili`;
        document.getElementById("stat-income").textContent = `+${formatMoney(data.total_income)}`;
        document.getElementById("stat-expense").textContent = `-${formatMoney(data.total_expense)}`;
        
        document.getElementById("stat-small-text").innerHTML = 
          `Bu oyda mayda-chuyda xarajatlar: <b>${formatMoney(data.small_expenses_total)} so'm</b>.<br>` +
          `Agar shunday davom etsa, 1 yilda <b>${formatMoney(data.small_expenses_total * 12)} so'm</b> sarflanadi!`;

        document.getElementById("stat-hours-text").innerHTML = 
          `Ushbu oydagi barcha xarajatlar sizning taxminan <b>${data.work_hours_spent} soatlik</b> mashaqqatli mehnatingiz bahosidir.`;

        // Category bars
        const catContainer = document.getElementById("category-bars-container");
        const cats = data.category_breakdown;
        const totalExp = data.total_expense || 1;
        
        const catNames = {
          food: "🍔 Tushlik / Yegulik",
          transport: "🚕 Yo'l / Benzin",
          small: "☕️ Mayda-chuyda",
          home: "🏠 Uy / Ro'zg'or",
          habits: "⚡️ Odatlar",
          loan: "💳 Kredit to'lovlari",
          savings: "🎯 Jamg'arma",
          other: "💡 Boshqa"
        };

        if (Object.keys(cats).length === 0) {
          catContainer.innerHTML = `<div style="font-size:12px; color:var(--text-muted);">Bu oyda hali xarajatlar yo'q.</div>`;
        } else {
          catContainer.innerHTML = Object.entries(cats).map(([catKey, sum]) => {
            const pct = Math.round((sum / totalExp) * 100);
            return `
              <div style="margin-bottom: 8px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
                  <span>${catNames[catKey] || catKey}</span>
                  <span style="font-weight:700;">${formatMoney(sum)} so'm (${pct}%)</span>
                </div>
                <div class="progress-track" style="height:4px; margin:0;">
                  <div class="progress-bar" style="width: ${pct}%; background:#38BDF8;"></div>
                </div>
              </div>`;
          }).join("");
        }
      }
    } catch (err) {
      console.error("Analytics load error:", err);
    }
  }

  // Black Hole (Mystery Loss) Check
  document.getElementById("btn-check-mystery").addEventListener("click", async () => {
    const input = document.getElementById("pocket-cash-input");
    const resultDiv = document.getElementById("mystery-loss-result");
    const actual = parseFloat(input.value);

    if (isNaN(actual) || actual < 0) {
      showToast("Naqd pul miqdorini kiriting!");
      return;
    }

    try {
      // First get current expected balance
      const bRes = await fetch(`${API_BASE}/api/user/${user.id}/balance`);
      const bData = await bRes.json();
      const expected = bData.safe_free_balance;

      const res = await fetch(`${API_BASE}/api/mystery-loss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          expected_amount: expected,
          actual_amount: actual
        })
      });

      if (res.ok) {
        const data = await res.json();
        resultDiv.style.display = "block";
        if (data.status === "loss_detected") {
          TelegramHelper.triggerHaptic("warning");
          resultDiv.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 10px; border-radius: 10px; color: #FCA5A5;">
              ⚠️ <b>Qora tuynuk aniqlandi!</b><br>
              Hisob bo'yicha ${formatMoney(expected)} so'm bo'lishi kerak edi. Cho'ntagingizda ${formatMoney(actual)} so'm qolibdi.<br>
              <b>${formatMoney(data.difference)} so'm</b> noma'lum xarajat sifatida qayd etildi!
            </div>`;
          refreshBalance();
          loadAnalytics();
        } else {
          TelegramHelper.triggerHaptic("success");
          resultDiv.innerHTML = `
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 10px; border-radius: 10px; color: #86EFAC;">
              ✓ <b>Baraka topsin!</b> Cho'ntakdagi pul hisob bilan to'g'ri chiqdi. Yo'qolish aniqlanmadi.
            </div>`;
        }
      }
    } catch (err) {
      console.error(err);
    }
  });

  // --- Transactions & History ---
  const subtabTxBtn = document.getElementById("subtab-tx-btn");
  const subtabGoalsBtn = document.getElementById("subtab-goals-btn");
  const viewTxList = document.getElementById("view-transactions-list");
  const viewGoalsList = document.getElementById("view-goals-list");

  subtabTxBtn.addEventListener("click", () => {
    TelegramHelper.triggerHaptic("light");
    subtabTxBtn.classList.add("active", "expense");
    subtabGoalsBtn.classList.remove("active", "expense");
    viewTxList.style.display = "block";
    viewGoalsList.style.display = "none";
    loadTransactions();
  });

  subtabGoalsBtn.addEventListener("click", () => {
    TelegramHelper.triggerHaptic("light");
    subtabGoalsBtn.classList.add("active", "expense");
    subtabTxBtn.classList.remove("active", "expense");
    viewGoalsList.style.display = "block";
    viewTxList.style.display = "none";
    loadGoals();
  });

  async function loadTransactions() {
    const container = document.getElementById("tx-items-container");
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/transactions?limit=60`);
      if (res.ok) {
        const txs = await res.json();
        if (txs.length === 0) {
          container.innerHTML = `<div style="text-align:center; padding:24px; color:var(--text-muted); font-size:13px;">Tranzaksiyalar tarixi bo'sh.</div>`;
          return;
        }

        const catIcons = {
          food: "🍔",
          transport: "🚕",
          small: "☕️",
          home: "🏠",
          habits: "⚡️",
          loan: "💳",
          savings: "🎯",
          salary: "💵",
          unknown: "🕳",
          other: "💡"
        };

        container.innerHTML = txs.map(t => {
          const isIncome = t.type === "income";
          const icon = catIcons[t.category] || "💸";
          const d = new Date(t.created_at);
          const timeStr = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
          const dateStr = `${d.getDate()}.${d.getMonth() + 1}`;

          return `
            <div class="loan-item-card" style="display:flex; justify-content:space-between; align-items:center; padding:10px 14px;">
              <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:20px;">${icon}</span>
                <div>
                  <div style="font-size:13px; font-weight:700;">${t.note || t.raw_expression || t.category}</div>
                  <div style="font-size:11px; color:var(--text-muted);">${dateStr} ${timeStr}</div>
                </div>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:14px; font-weight:800; color:${isIncome ? 'var(--accent-income)' : 'var(--accent-expense)'};">
                  ${isIncome ? '+' : '-'}${formatMoney(t.amount)}
                </span>
                <button onclick="window.deleteTx(${t.id})" style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:14px; padding:4px;">✕</button>
              </div>
            </div>`;
        }).join("");
      }
    } catch (err) {
      console.error(err);
    }
  }

  window.deleteTx = async function(id) {
    if (!confirm("Ushbu yozuvni o'chirmoqchimisiz?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/transactions/${id}?user_id=${user.id}`, { method: "DELETE" });
      if (res.ok) {
        TelegramHelper.triggerHaptic("success");
        showToast("O'chirildi!");
        loadTransactions();
        refreshBalance();
      }
    } catch (err) {
      showToast("Xatolik!");
    }
  };

  // --- Goals (Kopilka) Logic ---
  async function loadGoals() {
    const container = document.getElementById("goals-items-container");
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/goals`);
      if (res.ok) {
        userGoals = await res.json();
        if (userGoals.length === 0) {
          container.innerHTML = `<div style="text-align:center; padding:24px; color:var(--text-muted); font-size:13px;">Hozircha jamg'arma maqsadlari yo'q.</div>`;
          return;
        }

        container.innerHTML = userGoals.map(g => {
          const pct = Math.min(100, Math.round((g.current_amount / g.target_amount) * 100));
          return `
            <div class="loan-item-card">
              <div class="loan-header">
                <span class="loan-name">🎯 ${g.title}</span>
                <span style="font-weight:800; color:var(--accent-purple);">${formatMoney(g.current_amount)} / ${formatMoney(g.target_amount)} so'm</span>
              </div>
              <div class="progress-track">
                <div class="progress-bar" style="width: ${pct}%; background: linear-gradient(90deg, #8B5CF6, #06B6D4);"></div>
              </div>
              <div class="loan-footer">
                <span>Yig'ildi: <b>${pct}%</b></span>
                <button class="pay-btn-sm" style="background:var(--accent-purple); color:#fff; border:none;" onclick="window.openDepositGoal(${g.id}, '${g.title}')">+ Pul Qo'shish</button>
              </div>
            </div>`;
        }).join("");
      }
    } catch (err) {
      console.error(err);
    }
  }

  // Add Goal Modal
  const modalAddGoal = document.getElementById("modal-add-goal");
  document.getElementById("btn-open-add-goal").addEventListener("click", () => {
    modalAddGoal.classList.add("active");
  });
  document.getElementById("close-add-goal").addEventListener("click", () => {
    modalAddGoal.classList.remove("active");
  });

  document.getElementById("form-add-goal").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("goal-title").value.trim();
    const target = parseFloat(document.getElementById("goal-target").value);

    try {
      const res = await fetch(`${API_BASE}/api/goals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, title, target_amount: target })
      });
      if (res.ok) {
        TelegramHelper.triggerHaptic("success");
        showToast("Maqsad yaratildi!");
        modalAddGoal.classList.remove("active");
        document.getElementById("form-add-goal").reset();
        loadGoals();
      }
    } catch (err) {
      showToast("Xatolik!");
    }
  });

  // Deposit Goal Modal
  const modalDepositGoal = document.getElementById("modal-deposit-goal");
  window.openDepositGoal = function(goalId, goalTitle) {
    document.getElementById("deposit-goal-id").value = goalId;
    document.getElementById("deposit-goal-title").textContent = `${goalTitle}ga Pul Qo'shish`;
    modalDepositGoal.classList.add("active");
  };
  document.getElementById("close-deposit-goal").addEventListener("click", () => {
    modalDepositGoal.classList.remove("active");
  });

  document.getElementById("form-deposit-goal").addEventListener("submit", async (e) => {
    e.preventDefault();
    const goalId = document.getElementById("deposit-goal-id").value;
    const amount = parseFloat(document.getElementById("deposit-goal-amount").value);

    try {
      const res = await fetch(`${API_BASE}/api/goals/${goalId}/deposit?user_id=${user.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount })
      });
      if (res.ok) {
        TelegramHelper.triggerHaptic("success");
        showToast("Jamg'armaga qo'shildi!");
        modalDepositGoal.classList.remove("active");
        document.getElementById("form-deposit-goal").reset();
        loadGoals();
        refreshBalance();
      }
    } catch (err) {
      showToast("Xatolik!");
    }
  });

  // --- Export Modal (PDF & Excel) ---
  const modalExport = document.getElementById("modal-export");
  document.getElementById("btn-open-export").addEventListener("click", () => {
    TelegramHelper.triggerHaptic("medium");
    modalExport.classList.add("active");
  });
  document.getElementById("close-export-modal").addEventListener("click", () => {
    modalExport.classList.remove("active");
  });

  document.getElementById("btn-dl-pdf").addEventListener("click", () => {
    TelegramHelper.triggerHaptic("success");
    modalExport.classList.remove("active");
    showToast("PDF tayyorlanmoqda...");
    window.location.href = `${API_BASE}/api/export/pdf?user_id=${user.id}`;
  });

  document.getElementById("btn-dl-excel").addEventListener("click", () => {
    TelegramHelper.triggerHaptic("success");
    modalExport.classList.remove("active");
    showToast("Excel tayyorlanmoqda...");
    window.location.href = `${API_BASE}/api/export/excel?user_id=${user.id}`;
  });

  // --- Initial Launch ---
  initHeader();
  refreshBalance();
  updateCalcDisplay();
});
