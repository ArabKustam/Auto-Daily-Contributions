/**
 * AutoCommit Pro - Interactive Dashboard Client
 */

document.addEventListener('DOMContentLoaded', () => {
  // Navigation Tabs
  const navItems = document.querySelectorAll('.nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const pageTitle = document.getElementById('page-title');

  const titles = {
    dashboard: 'Обзор активности',
    analytics: 'Детальная аналитика файлов',
    logs: 'Журнал изменений и пушей',
    settings: 'Настройки, марафоны & расписание'
  };

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = item.getAttribute('data-tab');

      navItems.forEach(n => n.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      item.classList.add('active');
      const targetPane = document.getElementById(`tab-${tabId}`);
      if (targetPane) targetPane.classList.add('active');
      if (pageTitle && titles[tabId]) pageTitle.textContent = titles[tabId];
    });
  });

  // Global State
  let allAnalyticsData = [];
  let allLogsData = [];

  // Toast Helper
  const toast = document.getElementById('toast');
  function showToast(message, duration = 3000) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }

  // Load Status and Overview Data
  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();

      // Metrics
      const totalEl = document.getElementById('stat-total-commits');
      if (totalEl) totalEl.textContent = data.total_commits || 0;

      const todayDoneEl = document.getElementById('stat-today-done');
      if (todayDoneEl) todayDoneEl.textContent = `+${data.today_completed_commits || 0} сегодня`;

      const progressEl = document.getElementById('stat-today-progress');
      if (progressEl) progressEl.textContent = `${data.today_completed_commits || 0} / ${data.today_target_commits || 0}`;

      const barEl = document.getElementById('stat-progress-bar');
      if (barEl) {
        const pct = data.today_target_commits > 0 
          ? Math.min(100, Math.round((data.today_completed_commits / data.today_target_commits) * 100))
          : 0;
        barEl.style.width = `${pct}%`;
      }

      const statusTextEl = document.getElementById('stat-today-status-text');
      if (statusTextEl) {
        if (data.today_status === 'completed') {
          statusTextEl.innerHTML = '<span class="trend-up">✓ Дневная норма выполнена</span>';
        } else {
          statusTextEl.textContent = `В процессе (${data.today_status})`;
        }
      }

      // Mode Badge
      const badgeEl = document.getElementById('stat-mode-badge');
      const marathonDescEl = document.getElementById('stat-marathon-desc');
      if (badgeEl) {
        badgeEl.className = 'badge';
        if (data.marathon && data.marathon.active && data.marathon.days_left > 0) {
          badgeEl.classList.add('badge-marathon');
          badgeEl.textContent = `🔥 ${data.marathon.type} (дней: ${data.marathon.days_left})`;
          if (marathonDescEl) {
            const rNames = (data.marathon.assigned_repos || []).map(r => r.split(/[\\/]/).pop()).join(', ');
            marathonDescEl.textContent = `Фокус: ${rNames}`;
          }
        } else if (data.today_day_type && data.today_day_type.includes('Special')) {
          badgeEl.classList.add('badge-spike');
          badgeEl.textContent = '⚡ Всплеск активности';
          if (marathonDescEl) marathonDescEl.textContent = 'Особый день (Spike)';
        } else {
          badgeEl.textContent = 'Обычный день';
          if (marathonDescEl) marathonDescEl.textContent = 'Марафон не активен';
        }
      }

      const reposCountEl = document.getElementById('stat-repos-count');
      if (reposCountEl) reposCountEl.textContent = (data.repositories || []).length;

      // Update Marathon Banner on Settings page
      const mBannerHeading = document.getElementById('marathon-status-heading');
      const mBannerSub = document.getElementById('marathon-status-sub');
      const resetMarathonBtn = document.getElementById('card-reset-marathon');
      if (mBannerHeading && mBannerSub) {
        if (data.marathon && data.marathon.active && data.marathon.days_left > 0) {
          mBannerHeading.textContent = `🔥 Активен марафон: ${data.marathon.type}`;
          const rList = (data.marathon.assigned_repos || []).map(r => r.split(/[\\/]/).pop()).join(', ');
          mBannerSub.textContent = `Осталось дней: ${data.marathon.days_left}. Закрепленные репозитории: ${rList}. Диапазон: 10–59 пушей/день.`;
          if (resetMarathonBtn) resetMarathonBtn.style.display = 'flex';
        } else {
          mBannerHeading.textContent = 'Марафон не запущен';
          mBannerSub.textContent = 'Бот работает в обычном ежедневном режиме с рандомными шансами особых дней.';
          if (resetMarathonBtn) resetMarathonBtn.style.display = 'none';
        }
      }

      // Sync time
      const syncEl = document.getElementById('last-sync-time');
      if (syncEl) syncEl.textContent = `Обновлено: ${new Date().toLocaleTimeString()}`;

      // Checkboxes on settings page
      const chkSched = document.getElementById('chk-scheduler');
      if (chkSched) chkSched.checked = !!data.scheduler_enabled;
      const chkAuto = document.getElementById('chk-autostart');
      if (chkAuto) chkAuto.checked = !!data.autostart_enabled;

      // Render Repos Overview
      renderReposOverview(data.repositories_stats || []);

    } catch (err) {
      console.error('Error fetching status:', err);
    }
  }

  function renderReposOverview(repos) {
    const grid = document.getElementById('repos-overview-grid');
    if (!grid) return;
    grid.innerHTML = '';

    repos.forEach(repo => {
      const card = document.createElement('div');
      card.className = 'repo-card';
      card.innerHTML = `
        <div class="repo-card-top">
          <a href="https://github.com/ArabKustam/${repo.name}" target="_blank" class="repo-name-link">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
            ${repo.name}
          </a>
          <span class="repo-badge">${repo.branch || 'main'}</span>
        </div>
        <div class="repo-stat-row">
          <span>Всего коммитов бота:</span>
          <strong>${repo.commits_count || 0}</strong>
        </div>
        <div class="repo-stat-row">
          <span>Изменено файлов:</span>
          <strong>${repo.files_count || 0}</strong>
        </div>
        <div class="repo-stat-row">
          <span>Последний пуш:</span>
          <span>${repo.last_commit_time || 'Никогда'}</span>
        </div>
      `;
      grid.appendChild(card);
    });
  }

  // Load Detailed Analytics Data
  async function fetchAnalytics() {
    try {
      const res = await fetch('/api/analytics');
      if (!res.ok) return;
      const data = await res.json();
      allAnalyticsData = data.files_analytics || [];

      renderFilesTable(allAnalyticsData);
      renderHeatmap(data.heatmap_data || []);
      renderCategoryBars(data.categories || {});
    } catch (err) {
      console.error('Error fetching analytics:', err);
    }
  }

  function renderHeatmap(heatmapData) {
    const container = document.getElementById('heatmap-grid');
    if (!container) return;
    container.innerHTML = '';

    heatmapData.forEach(item => {
      const cell = document.createElement('div');
      let lvl = 0;
      if (item.count > 0 && item.count < 3) lvl = 1;
      else if (item.count >= 3 && item.count < 6) lvl = 2;
      else if (item.count >= 6 && item.count < 15) lvl = 3;
      else if (item.count >= 15) lvl = 4;

      cell.className = `heatmap-cell lvl-${lvl}`;
      cell.title = `${item.date}: ${item.count} коммитов`;
      container.appendChild(cell);
    });
  }

  function renderCategoryBars(categories) {
    const container = document.getElementById('category-bars-list');
    if (!container) return;
    container.innerHTML = '';

    const colors = {
      fix: '#f85149',
      refactor: '#a371f7',
      update: '#58a6ff',
      docs: '#39d353',
      style: '#e3b341',
      other: '#8b949e'
    };

    let total = 0;
    Object.values(categories).forEach(v => total += v);
    if (total === 0) total = 1;

    for (const [cat, count] of Object.entries(categories)) {
      const pct = Math.round((count / total) * 100);
      const color = colors[cat.toLowerCase()] || colors.other;

      const item = document.createElement('div');
      item.className = 'cat-item';
      item.innerHTML = `
        <div class="cat-meta">
          <span class="cat-name">${cat.toUpperCase()}</span>
          <span class="cat-count">${count} (${pct}%)</span>
        </div>
        <div class="cat-bar-bg">
          <div class="cat-bar-fill" style="width: ${pct}%; background-color: ${color};"></div>
        </div>
      `;
      container.appendChild(item);
    }
  }

  function renderFilesTable(files) {
    const tbody = document.getElementById('files-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (files.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Изменения файлов пока не зафиксированы</td></tr>';
      return;
    }

    files.forEach(item => {
      const tr = document.createElement('tr');
      const ext = item.file.split('.').pop().toLowerCase();
      tr.innerHTML = `
        <td><strong>${item.repo}</strong></td>
        <td><span class="file-pill">${item.file}</span></td>
        <td>.${ext}</td>
        <td><span class="count-badge">${item.count}</span></td>
        <td style="color: #7ee787;">${item.edit_type || 'Комментарий / Whitespace'}</td>
        <td style="color: var(--text-muted); font-size: 12px;">${item.last_modified}</td>
        <td><span class="badge" style="background: rgba(46, 160, 67, 0.15); color: #2ea043; border-color: rgba(46, 160, 67, 0.3);">Синхронизировано</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Analytics Search filter
  const searchInput = document.getElementById('analytics-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const filtered = allAnalyticsData.filter(item => 
        item.file.toLowerCase().includes(query) || item.repo.toLowerCase().includes(query)
      );
      renderFilesTable(filtered);
    });
  }

  // Load Logs
  async function fetchLogs() {
    try {
      const res = await fetch('/api/logs');
      if (!res.ok) return;
      const data = await res.json();
      allLogsData = data.history || [];

      // Update repo dropdown
      const repoSelect = document.getElementById('log-filter-repo');
      if (repoSelect && repoSelect.options.length <= 1) {
        const repos = [...new Set(allLogsData.map(l => l.repo))];
        repos.forEach(r => {
          const opt = document.createElement('option');
          opt.value = r;
          opt.textContent = r;
          repoSelect.appendChild(opt);
        });
      }

      renderLogs(allLogsData);

      // Raw terminal output
      const rawBody = document.getElementById('raw-log-body');
      if (rawBody) {
        rawBody.textContent = data.raw_log || 'Логи пусты.';
        rawBody.scrollTop = rawBody.scrollHeight;
      }
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  }

  function renderLogs(logs) {
    const container = document.getElementById('log-entries-container');
    if (!container) return;
    container.innerHTML = '';

    const filterVal = document.getElementById('log-filter-repo')?.value || 'all';
    const filtered = filterVal === 'all' ? logs : logs.filter(l => l.repo === filterVal);

    if (filtered.length === 0) {
      container.innerHTML = '<div style="padding: 16px; color: var(--text-muted); text-align: center;">Нет записей лога.</div>';
      return;
    }

    filtered.slice().reverse().forEach(log => {
      const item = document.createElement('div');
      item.className = 'log-item';
      item.innerHTML = `
        <span class="log-time">${log.timestamp || ''}</span>
        <span class="log-repo-tag">${log.repo || ''}</span>
        <span class="log-file">${log.file || 'allow-empty'}</span>
        <span class="log-msg">${log.message || ''}</span>
        <div class="log-status">
          <span class="log-dot"></span>
          <span>Pushed</span>
        </div>
      `;
      container.appendChild(item);
    });
  }

  // Log filter change
  document.getElementById('log-filter-repo')?.addEventListener('change', () => {
    renderLogs(allLogsData);
  });

  document.getElementById('btn-refresh-logs')?.addEventListener('click', () => {
    fetchLogs();
    showToast('Логи обновлены');
  });

  // Settings Configuration Form
  async function fetchConfig() {
    try {
      const res = await fetch('/api/config');
      if (!res.ok) return;
      const cfg = await res.json();

      document.getElementById('cfg-norm-min').value = cfg.normal_day?.min_commits || 1;
      document.getElementById('cfg-norm-max').value = cfg.normal_day?.max_commits || 6;
      document.getElementById('cfg-spec-min').value = cfg.special_day?.min_commits || 12;
      document.getElementById('cfg-spec-max').value = cfg.special_day?.max_commits || 48;
      document.getElementById('cfg-mar-min').value = cfg.marathons?.trio_3_days?.min_commits || 10;
      document.getElementById('cfg-mar-max').value = cfg.marathons?.trio_3_days?.max_commits || 59;
    } catch (err) {
      console.error('Error fetching config:', err);
    }
  }

  const settingsForm = document.getElementById('settings-form');
  if (settingsForm) {
    settingsForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        normal_day: {
          min_commits: parseInt(document.getElementById('cfg-norm-min').value, 10),
          max_commits: parseInt(document.getElementById('cfg-norm-max').value, 10)
        },
        special_day: {
          min_commits: parseInt(document.getElementById('cfg-spec-min').value, 10),
          max_commits: parseInt(document.getElementById('cfg-spec-max').value, 10)
        },
        marathons: {
          trio_3_days: {
            min_commits: parseInt(document.getElementById('cfg-mar-min').value, 10),
            max_commits: parseInt(document.getElementById('cfg-mar-max').value, 10)
          },
          week_7_days: {
            min_commits: parseInt(document.getElementById('cfg-mar-min').value, 10),
            max_commits: parseInt(document.getElementById('cfg-mar-max').value, 10)
          }
        }
      };

      try {
        const res = await fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          showToast('✓ Настройки успешно сохранены!');
          fetchStatus();
        } else {
          showToast('Ошибка при сохранении настроек');
        }
      } catch (err) {
        showToast('Сетевая ошибка: ' + err.message);
      }
    });
  }

  // Toggle Scheduler
  const chkScheduler = document.getElementById('chk-scheduler');
  if (chkScheduler) {
    chkScheduler.addEventListener('change', async (e) => {
      const enabled = e.target.checked;
      try {
        const res = await fetch('/api/toggle-scheduler', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled })
        });
        const d = await res.json();
        showToast(d.message || (enabled ? 'Планировщик Windows активирован' : 'Планировщик отключен'));
        fetchStatus();
      } catch (err) {
        showToast('Ошибка: ' + err.message);
        e.target.checked = !enabled;
      }
    });
  }

  // Toggle Startup
  const chkAutostart = document.getElementById('chk-autostart');
  if (chkAutostart) {
    chkAutostart.addEventListener('change', async (e) => {
      const enabled = e.target.checked;
      try {
        const res = await fetch('/api/toggle-autostart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled })
        });
        const d = await res.json();
        showToast(d.message || (enabled ? 'Автозагрузка включена' : 'Автозагрузка выключена'));
        fetchStatus();
      } catch (err) {
        showToast('Ошибка: ' + err.message);
        e.target.checked = !enabled;
      }
    });
  }

  // Run Now Logic & Modal
  const modal = document.getElementById('run-modal');
  const modalSpinner = document.getElementById('modal-spinner');
  const modalLog = document.getElementById('modal-log-output');
  const modalClose = document.getElementById('modal-close');

  async function triggerRunNow() {
    if (modal) modal.classList.add('active');
    if (modalSpinner) modalSpinner.style.display = 'flex';
    if (modalLog) {
      modalLog.style.display = 'none';
      modalLog.textContent = '';
    }

    try {
      const res = await fetch('/api/run-now', { method: 'POST' });
      const data = await res.json();
      if (modalSpinner) modalSpinner.style.display = 'none';
      if (modalLog) {
        modalLog.style.display = 'block';
        modalLog.textContent = data.output || 'Завершено без вывода.';
      }
      showToast('✓ Бот успешно завершил выполнение коммитов!');
      fetchStatus();
      fetchAnalytics();
      fetchLogs();
    } catch (err) {
      if (modalSpinner) modalSpinner.style.display = 'none';
      if (modalLog) {
        modalLog.style.display = 'block';
        modalLog.textContent = 'Ошибка запуска: ' + err.message;
      }
    }
  }

  document.getElementById('btn-run-top')?.addEventListener('click', triggerRunNow);
  modalClose?.addEventListener('click', () => {
    if (modal) modal.classList.remove('active');
  });

  // Sprint / Marathon Starters
  async function triggerMarathon(days) {
    try {
      const res = await fetch('/api/start-marathon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days })
      });
      const data = await res.json();
      showToast(data.message || `Марафон на ${days} дней активирован!`);
      fetchStatus();
    } catch (err) {
      showToast('Ошибка запуска марафона: ' + err.message);
    }
  }

  document.getElementById('btn-start-trio')?.addEventListener('click', () => triggerMarathon(3));
  document.getElementById('btn-start-week')?.addEventListener('click', () => triggerMarathon(7));
  document.getElementById('btn-stop-marathon')?.addEventListener('click', () => triggerMarathon(0));

  // Open Repos Folder
  document.getElementById('btn-open-repos')?.addEventListener('click', async () => {
    try {
      await fetch('/api/open-repos', { method: 'POST' });
      showToast('Папка с репозиториями открыта');
    } catch (err) {
      showToast('Не удалось открыть папку');
    }
  });

  // Initial Data Load
  fetchStatus();
  fetchAnalytics();
  fetchLogs();
  fetchConfig();

  // Auto-refresh every 4 seconds
  setInterval(() => {
    fetchStatus();
    fetchLogs();
  }, 4000);
}); 
