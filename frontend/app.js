// API Base URL
const API_BASE = window.location.origin;
let authToken = localStorage.getItem('auth_token');
let ws = null;
let wsShouldReconnect = false;

// All keys cache for filtering
let allKeysCache = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initLogVirtualList();
    if (authToken) {
        verifyAuth();
    } else {
        showLoginPage();
    }
});

// Auth Functions
async function handleLogin(event) {
    event.preventDefault();
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (!response.ok) {
            throw new Error('密码错误');
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('auth_token', authToken);

        showToast('登录成功', 'success');
        showDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function verifyAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/verify`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            showDashboard();
        } else {
            throw new Error('Token expired');
        }
    } catch (error) {
        localStorage.removeItem('auth_token');
        authToken = null;
        showLoginPage();
    }
}

function handleLogout() {
    localStorage.removeItem('auth_token');
    authToken = null;
    wsShouldReconnect = false;
    disconnectWebSocket();
    stopStatusPolling();
    showLoginPage();
    showToast('已退出登录', 'success');
}

function showLoginPage() {
    wsShouldReconnect = false;
    stopStatusPolling();
    disconnectWebSocket();

    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('dashboardPage').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('dashboardPage').classList.remove('hidden');
    wsShouldReconnect = true;
    loadConfig();
    loadKeys();
    loadMemoryStats();
    loadQueryStats();
    startStatusPolling();
    connectWebSocket();
}

// Config Functions
async function handleSaveConfig(event) {
    event.preventDefault();

    // 检查是否在模态框中（通过检查ID后缀）
    const isModal = event.target.id === 'configFormModal';
    const suffix = isModal ? 'Modal' : '';

    const tokensText = document.getElementById('githubTokens' + suffix).value;
    const tokens = tokensText.split('\n').map(t => t.trim()).filter(t => t);
    const proxy = document.getElementById('proxy' + suffix).value.trim();
    const scanMode = document.querySelector(`input[name="scanMode${suffix}"]:checked`).value;
    const dateRange = parseInt(document.getElementById('dateRange' + suffix).value);

    // 渠道验证配置
    const validators = {
        gemini: {
            enabled: document.getElementById('geminiEnabled' + suffix).checked,
            model: document.getElementById('geminiModel' + suffix).value.trim()
        },
        openrouter: {
            enabled: document.getElementById('openrouterEnabled' + suffix).checked,
            model: document.getElementById('openrouterModel' + suffix).value.trim()
        },
        modelscope: {
            enabled: document.getElementById('modelscopeEnabled' + suffix).checked,
            model: document.getElementById('modelscopeModel' + suffix).value.trim()
        },
        siliconflow: {
            enabled: document.getElementById('siliconflowEnabled' + suffix).checked,
            model: document.getElementById('siliconflowModel' + suffix).value.trim()
        }
    };

    // 性能配置
    const performance = {
        max_concurrent_files: parseInt(document.getElementById('maxConcurrent' + suffix).value),
        request_delay: parseFloat(document.getElementById('requestDelay' + suffix).value),
        github_timeout: parseInt(document.getElementById('githubTimeout' + suffix).value),
        validation_timeout: parseInt(document.getElementById('validationTimeout' + suffix).value),
        max_retries: parseInt(document.getElementById('maxRetries' + suffix).value)
    };

    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                github_tokens: tokens,
                proxy: proxy || null,
                scan_mode: scanMode,
                date_range_days: dateRange,
                validators: validators,
                performance: performance
            })
        });

        if (!response.ok) throw new Error('配置保存失败');

        showToast('配置保存成功', 'success');

        // 如果在模态框中，关闭模态框
        if (isModal) {
            hideConfigDialog();
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.config) {
                // 加载 GitHub Tokens (明文显示)
                if (data.config.github_tokens && data.config.github_tokens.length > 0) {
                    document.getElementById('githubTokens').value = data.config.github_tokens.join('\n');
                }

                // 加载其他配置
                document.getElementById('proxy').value = data.config.proxy || '';
                document.getElementById('dateRange').value = data.config.date_range_days || 730;

                const scanMode = data.config.scan_mode || 'compatible';
                document.querySelector(`input[name="scanMode"][value="${scanMode}"]`).checked = true;

                // 加载验证器配置
                if (data.config.validators) {
                    const validators = data.config.validators;

                    if (validators.gemini) {
                        document.getElementById('geminiEnabled').checked = validators.gemini.enabled;
                        document.getElementById('geminiModel').value = validators.gemini.model || 'gemini-2.0-flash-exp';
                    }
                    if (validators.openrouter) {
                        document.getElementById('openrouterEnabled').checked = validators.openrouter.enabled;
                        document.getElementById('openrouterModel').value = validators.openrouter.model || 'deepseek/deepseek-chat-v3:free';
                    }
                    if (validators.modelscope) {
                        document.getElementById('modelscopeEnabled').checked = validators.modelscope.enabled;
                        document.getElementById('modelscopeModel').value = validators.modelscope.model || 'Qwen/Qwen2-1.5B-Instruct';
                    }
                    if (validators.siliconflow) {
                        document.getElementById('siliconflowEnabled').checked = validators.siliconflow.enabled;
                        document.getElementById('siliconflowModel').value = validators.siliconflow.model || 'Qwen/Qwen2.5-7B-Instruct';
                    }
                }

                // 加载性能配置
                if (data.config.performance) {
                    const perf = data.config.performance;
                    document.getElementById('maxConcurrent').value = perf.max_concurrent_files || 5;
                    document.getElementById('requestDelay').value = perf.request_delay || 1.0;
                    document.getElementById('githubTimeout').value = perf.github_timeout || 30;
                    document.getElementById('validationTimeout').value = perf.validation_timeout || 30;
                    document.getElementById('maxRetries').value = perf.max_retries || 3;
                }
            }
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// Scan Control Functions
async function handleStartScan() {
    try {
        const response = await fetch(`${API_BASE}/api/scan/control`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'start' })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '启动失败');
        }

        showToast('扫描已启动', 'success');
        updateScanStatus(true, false);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handlePauseScan() {
    try {
        const response = await fetch(`${API_BASE}/api/scan/control`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'pause' })
        });

        if (!response.ok) throw new Error('暂停失败');

        showToast('扫描已暂停', 'success');
        updateScanStatus(true, true);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleResumeScan() {
    try {
        const response = await fetch(`${API_BASE}/api/scan/control`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'resume' })
        });

        if (!response.ok) throw new Error('恢复失败');

        showToast('扫描已恢复', 'success');
        updateScanStatus(true, false);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleStopScan() {
    try {
        const response = await fetch(`${API_BASE}/api/scan/control`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'stop' })
        });

        if (!response.ok) throw new Error('停止失败');

        showToast('停止信号已发送', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function updateScanStatus(running, paused = false) {
    const statusDiv = document.getElementById('scanStatus');
    const btnStart = document.getElementById('btnStart');
    const btnPause = document.getElementById('btnPause');
    const btnResume = document.getElementById('btnResume');
    const btnStop = document.getElementById('btnStop');
    const progressContainer = document.getElementById('progressContainer');

    if (running) {
        if (paused) {
            // 暂停状态
            statusDiv.innerHTML = `
                <div class="w-3 h-3 bg-amber-500 rounded-full animate-pulse"></div>
                <span class="text-sm text-amber-600 font-medium">已暂停</span>
            `;
            btnStart.disabled = true;
            btnPause.classList.add('hidden');
            btnResume.classList.remove('hidden');
            btnResume.disabled = false;
            btnStop.disabled = false;
        } else {
            // 运行中
            statusDiv.innerHTML = `
                <div class="spinner"></div>
                <span class="text-sm text-success font-medium">运行中</span>
            `;
            btnStart.disabled = true;
            btnPause.classList.remove('hidden');
            btnPause.disabled = false;
            btnResume.classList.add('hidden');
            btnStop.disabled = false;
        }
        btnStart.classList.add('opacity-50', 'cursor-not-allowed');
        btnStop.classList.remove('opacity-50', 'cursor-not-allowed');
        progressContainer.classList.remove('hidden');
    } else {
        // 未运行
        statusDiv.innerHTML = `
            <div class="w-3 h-3 bg-slate-400 rounded-full"></div>
            <span class="text-sm text-slate-600">未运行</span>
        `;
        btnStart.disabled = false;
        btnStart.classList.remove('opacity-50', 'cursor-not-allowed');
        btnPause.disabled = true;
        btnPause.classList.add('opacity-50', 'cursor-not-allowed');
        btnResume.classList.add('hidden');
        btnStop.disabled = true;
        btnStop.classList.add('opacity-50', 'cursor-not-allowed');
        progressContainer.classList.add('hidden');
    }
}

// Status Polling with optimization
let statusInterval;
let lastStatusUpdate = 0;
let isPageVisible = true;

// Page visibility detection
document.addEventListener('visibilitychange', () => {
    isPageVisible = !document.hidden;
    if (isPageVisible) {
        loadStatus(); // 立即更新
    }
});

function startStatusPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
    loadStatus();
    // 降低轮询频率到5秒，页面不可见时暂停
    statusInterval = setInterval(() => {
        if (isPageVisible) {
            loadStatus();
        }
    }, 5000);
}

function stopStatusPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
}

async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/scan/status`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            updateScanStatus(data.running, data.paused);
            updateStats(data.stats);
            updateProgress(data.stats);
            updateScanMode(data.scan_mode);  // 更新扫描模式显示
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

// Throttled stats update
const updateStats = window.perfUtils.throttle(function (stats) {
    document.getElementById('statFiles').textContent = stats.total_files || 0;
    document.getElementById('statKeys').textContent = stats.total_keys || 0;
    document.getElementById('statValidKeys').textContent = stats.valid_keys || 0;
}, 1000); // 限制每秒更新一次

function updateProgress(stats) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const currentQuery = document.getElementById('currentQuery');

    const percent = stats.progress_percent || 0;
    const query = stats.current_query || '-';

    if (progressBar) progressBar.style.width = `${percent}%`;
    if (progressText) progressText.textContent = `${percent}% (${stats.current_query_index || 0}/${stats.total_queries || 0})`;
    if (currentQuery) currentQuery.textContent = query;
}

function updateScanMode(scanMode) {
    const modeContainer = document.getElementById('currentScanMode');
    const modeText = document.getElementById('scanModeText');

    if (scanMode && modeContainer && modeText) {
        // 显示模式信息
        modeContainer.classList.remove('hidden');

        // 转换模式名称为友好显示
        const modeNames = {
            'compatible': '全部平台',
            'gemini-only': 'Gemini',
            'openrouter-only': 'OpenRouter',
            'modelscope-only': 'ModelScope',
            'siliconflow-only': 'SiliconFlow'
        };

        modeText.textContent = modeNames[scanMode] || scanMode;
    } else if (modeContainer) {
        // 隐藏模式信息
        modeContainer.classList.add('hidden');
    }
}

// WebSocket for real-time logs
function connectWebSocket() {
    if (!wsShouldReconnect) return;
    if (ws) disconnectWebSocket();

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/logs`);

    // Batch process WebSocket messages
    let messageQueue = [];
    let processingQueue = false;
    let lastProcessTime = 0;

    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            messageQueue.push(message);

            // 立即处理消息（实时显示）
            if (!processingQueue) {
                processingQueue = true;
                requestAnimationFrame(() => {
                    processMessageQueue();
                    processingQueue = false;
                });
            }
        } catch (e) {
            console.error('WebSocket message parse error:', e);
        }
    };

    function processMessageQueue() {
        // 处理队列中的所有消息（实时显示）
        while (messageQueue.length > 0) {
            const message = messageQueue.shift();

            if (message.event === 'log') {
                // 显示所有类型的日志
                addLogEntry(message.data);
            } else if (message.event === 'history') {
                // 显示最近50条历史日志
                const recentLogs = message.data.slice(-50);
                recentLogs.forEach(log => {
                    addLogEntry(log);
                });
            } else if (message.event === 'stats') {
                updateStats(message.data);
            }
        }
    }

    ws.onclose = () => {
        ws = null;
        if (!wsShouldReconnect) return;
        console.log('WebSocket disconnected, reconnecting in 5s...');
        setTimeout(() => {
            if (isPageVisible && wsShouldReconnect) {
                connectWebSocket();
            }
        }, 5000); // 增加重连间隔
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
    };
}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
}

// 日志虚拟列表与批量渲染
const LOG_ROW_HEIGHT = 20;          // 估算行高（px），影响虚拟滚动
const LOG_VISIBLE_BUFFER = 10;      // 预渲染缓冲行数
const LOG_MAX_STORE = 800;          // 最大保留日志条数（内存）

let logStore = [];
let logBuffer = [];
let logUpdateScheduled = false;
let logRenderScheduled = false;
let logsContainer, logsTopSpacer, logsListEl, logsBottomSpacer;
let shouldStickToBottom = true;

function initLogVirtualList() {
    logsContainer = document.getElementById('logsContainer');
    if (!logsContainer) return;

    // 创建虚拟列表结构
    logsContainer.innerHTML = '';
    logsTopSpacer = document.createElement('div');
    logsBottomSpacer = document.createElement('div');
    logsListEl = document.createElement('div');
    logsListEl.id = 'logsVirtualList';
    logsListEl.className = 'space-y-1';

    logsContainer.appendChild(logsTopSpacer);
    logsContainer.appendChild(logsListEl);
    logsContainer.appendChild(logsBottomSpacer);

    logsContainer.addEventListener('scroll', handleLogScroll);
    renderLogsVirtual(); // 初次渲染占位
}

function handleLogScroll() {
    if (!logsContainer) return;
    const threshold = 40;
    const distanceToBottom = logsContainer.scrollHeight - logsContainer.scrollTop - logsContainer.clientHeight;
    shouldStickToBottom = distanceToBottom <= threshold;
    scheduleLogRender();
}

function addLogEntry(log) {
    logBuffer.push(log);

    if (!logUpdateScheduled) {
        logUpdateScheduled = true;
        setTimeout(() => {
            flushLogBuffer();
            logUpdateScheduled = false;
        }, 16); // ~60fps
    }
}

function flushLogBuffer() {
    if (logBuffer.length === 0) return;

    // 追加到总存储，预裁剪
    logStore.push(...logBuffer);
    if (logStore.length > LOG_MAX_STORE) {
        logStore = logStore.slice(logStore.length - LOG_MAX_STORE);
    }
    logBuffer = [];

    scheduleLogRender();
}

function scheduleLogRender() {
    if (logRenderScheduled) return;
    logRenderScheduled = true;
    requestAnimationFrame(() => {
        renderLogsVirtual();
        logRenderScheduled = false;
    });
}

function renderLogsVirtual() {
    if (!logsContainer || !logsListEl || !logsTopSpacer || !logsBottomSpacer) return;

    const total = logStore.length;
    if (total === 0) {
        logsListEl.innerHTML = '<div class="text-slate-500">等待日志...</div>';
        logsTopSpacer.style.height = '0px';
        logsBottomSpacer.style.height = '0px';
        return;
    }

    const containerHeight = logsContainer.clientHeight || 1;
    const visibleCount = Math.ceil(containerHeight / LOG_ROW_HEIGHT) + LOG_VISIBLE_BUFFER * 2;

    // 根据滚动位置计算窗口
    const startIndex = Math.max(0, Math.floor((logsContainer.scrollTop || 0) / LOG_ROW_HEIGHT) - LOG_VISIBLE_BUFFER);
    const endIndex = Math.min(total, startIndex + visibleCount);

    logsTopSpacer.style.height = `${startIndex * LOG_ROW_HEIGHT}px`;
    logsBottomSpacer.style.height = `${(total - endIndex) * LOG_ROW_HEIGHT}px`;

    const fragment = document.createDocumentFragment();
    for (let i = startIndex; i < endIndex; i++) {
        const log = logStore[i];
        const time = new Date(log.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

        let icon = '•';
        let color = 'text-slate-600';

        if (log.type === 'success') {
            icon = '✓';
            color = 'text-success';
        } else if (log.type === 'error') {
            icon = '✗';
            color = 'text-destructive';
        } else if (log.type === 'warning') {
            icon = '⚠';
            color = 'text-amber-600';
        } else if (log.type === 'info') {
            icon = 'ℹ';
            color = 'text-blue-600';
        }

        const logDiv = document.createElement('div');
        logDiv.className = 'flex gap-2 text-xs';
        logDiv.innerHTML = `<span class="text-slate-400">[${time}]</span><span class="${color}">${icon}</span><span>${escapeHtml(log.message)}</span>`;
        fragment.appendChild(logDiv);
    }

    logsListEl.innerHTML = '';
    logsListEl.appendChild(fragment);

    if (shouldStickToBottom) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }
}

function clearLogs() {
    logStore = [];
    logBuffer = [];
    shouldStickToBottom = true;
    scheduleLogRender();
}

// Keys Management
let currentPage = 1;
let currentKeyType = '';
let currentSearch = '';
const keysPerPage = 50;

async function loadKeys(keyType = null, search = null, page = 1) {
    try {
        let url = `${API_BASE}/api/keys`;
        const params = new URLSearchParams();
        if (keyType) params.append('key_type', keyType);
        if (search) params.append('search', search);
        if (params.toString()) url += `?${params.toString()}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            allKeysCache = data.keys;
            currentPage = page;
            currentKeyType = keyType || '';
            currentSearch = search || '';
            displayKeys(data.keys);
        }
    } catch (error) {
        console.error('Failed to load keys:', error);
    }
}

// Optimized search with debounce
const handleKeySearch = window.perfUtils.debounce(function () {
    const search = document.getElementById('keySearch').value.trim();
    const keyType = document.getElementById('keyTypeFilter').value;

    let filteredKeys = allKeysCache;

    // Filter by type
    if (keyType) {
        filteredKeys = filteredKeys.filter(key => key.type.toLowerCase() === keyType);
    }

    // Filter by search
    if (search) {
        const searchLower = search.toLowerCase();
        filteredKeys = filteredKeys.filter(key =>
            key.key.toLowerCase().includes(searchLower) ||
            key.source.toLowerCase().includes(searchLower)
        );
    }

    displayKeys(filteredKeys);
}, 300);

async function refreshKeys() {
    // 保持当前的过滤条件刷新
    await loadKeys(currentKeyType || null, currentSearch || null, currentPage);
    showToast('已刷新', 'success');
}

function displayKeys(keys) {
    const tbody = document.getElementById('keysTableBody');

    // 重置全选复选框
    const selectAllCheckbox = document.getElementById('selectAllKeys');
    if (selectAllCheckbox) selectAllCheckbox.checked = false;
    updateSelectedCount();

    if (keys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-3 py-8 text-center text-slate-500">暂无数据</td></tr>';
        updatePagination(0, 0);
        return;
    }

    // 计算分页
    const totalPages = Math.ceil(keys.length / keysPerPage);
    const startIdx = (currentPage - 1) * keysPerPage;
    const endIdx = startIdx + keysPerPage;
    const pageKeys = keys.slice(startIdx, endIdx);

    // 使用 DocumentFragment 提升性能
    const fragment = document.createDocumentFragment();

    pageKeys.forEach((key, index) => {
        const tr = document.createElement('tr');
        tr.className = index % 2 === 0 ? 'bg-white hover:bg-slate-100' : 'bg-slate-50/50 hover:bg-slate-100';

        // 余额显示逻辑：只有当有余额时才显示，否则显示 "-"
        const balanceDisplay = key.balance
            ? `<span class="text-green-600 font-medium">¥${escapeHtml(key.balance)}</span>`
            : '<span class="text-slate-400">-</span>';

        tr.innerHTML = `
            <td class="px-3 py-3 text-center">
                <input type="checkbox" class="key-checkbox w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary cursor-pointer"
                    data-key="${escapeAttribute(key.key)}" data-type="${escapeAttribute(key.type)}" onchange="updateSelectedCount()" />
            </td>
            <td class="px-3 py-3">
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded ${getKeyTypeBadge(key.type)}">
                    ${key.type.toUpperCase()}
                </span>
            </td>
            <td class="px-3 py-3 font-mono text-xs truncate max-w-[180px]" title="${escapeAttribute(key.key)}">${escapeHtml(key.key.substring(0, 20))}...</td>
            <td class="px-3 py-3 text-xs">${balanceDisplay}</td>
            <td class="px-3 py-3 text-xs truncate max-w-[200px]">
                <a href="${escapeHtml(key.url)}" target="_blank" class="text-blue-600 hover:underline" title="${escapeAttribute(key.source)}">
                    ${escapeHtml(key.source)}
                </a>
            </td>
            <td class="px-3 py-3 text-xs text-slate-600 whitespace-nowrap">${key.found_at}</td>
            <td class="px-3 py-3 text-center">
                <button onclick="copyKey('${escapeAttribute(key.key)}')" class="px-3 py-1.5 text-xs bg-primary text-white rounded hover:bg-primary/90 whitespace-nowrap">
                    复制
                </button>
            </td>
        `;

        fragment.appendChild(tr);
    });

    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    // 更新分页控件
    updatePagination(keys.length, totalPages);
}

function updatePagination(totalKeys, totalPages) {
    const paginationContainer = document.getElementById('paginationContainer');
    if (!paginationContainer) return;

    if (totalKeys === 0 || totalPages <= 1) {
        paginationContainer.classList.add('hidden');
        return;
    }

    paginationContainer.classList.remove('hidden');

    const startIdx = (currentPage - 1) * keysPerPage + 1;
    const endIdx = Math.min(currentPage * keysPerPage, totalKeys);

    paginationContainer.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="text-sm text-slate-600">
                显示 ${startIdx}-${endIdx} / 共 ${totalKeys} 条
            </div>
            <div class="flex gap-2">
                <button onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}
                    class="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed">
                    首页
                </button>
                <button onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}
                    class="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed">
                    上一页
                </button>
                <span class="px-3 py-1 text-sm text-slate-700">
                    ${currentPage} / ${totalPages}
                </span>
                <button onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}
                    class="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed">
                    下一页
                </button>
                <button onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}
                    class="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed">
                    末页
                </button>
            </div>
        </div>
    `;
}

function goToPage(page) {
    currentPage = page;
    handleKeySearch();
}

// ===== 批量操作功能 =====

function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.key-checkbox');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
    updateSelectedCount();
}

function updateSelectedCount() {
    const selectedCount = document.querySelectorAll('.key-checkbox:checked').length;
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = selectedCount;
    }
}

function getSelectedKeys() {
    const checkboxes = document.querySelectorAll('.key-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.dataset.key);
}

async function copySelectedKeys() {
    const keys = getSelectedKeys();
    if (keys.length === 0) {
        showToast('请先选择要复制的密钥', 'warning');
        return;
    }

    await copyKeysToClipboard(keys, `已复制 ${keys.length} 个选中的密钥`);
}

async function copyKeysByType(type) {
    if (!allKeysCache || allKeysCache.length === 0) {
        showToast('暂无密钥数据', 'warning');
        return;
    }

    let keys;
    let message;

    if (type === 'all') {
        keys = allKeysCache.map(k => k.key);
        message = `已复制全部 ${keys.length} 个密钥`;
    } else {
        keys = allKeysCache.filter(k => k.type === type).map(k => k.key);
        if (keys.length === 0) {
            const typeNames = {
                'gemini': 'Gemini',
                'openrouter': 'OpenRouter',
                'modelscope': 'ModelScope',
                'siliconflow': 'SiliconFlow'
            };
            showToast(`暂无 ${typeNames[type] || type} 类型的密钥`, 'warning');
            return;
        }
        message = `已复制 ${keys.length} 个 ${type.toUpperCase()} 密钥`;
    }

    await copyKeysToClipboard(keys, message);
}

async function copyKeysToClipboard(keys, successMessage) {
    const keysText = keys.join('\n');

    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(keysText);
            showToast(successMessage, 'success');
        } else {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = keysText;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                showToast(successMessage, 'success');
            } catch (err) {
                showToast('复制失败，请手动复制', 'error');
            }
            document.body.removeChild(textarea);
        }
    } catch (error) {
        console.error('Copy failed:', error);
        showToast('复制失败', 'error');
    }
}

// ===== 密钥类型徽章 =====

function getKeyTypeBadge(type) {
    const badges = {
        'gemini': 'bg-purple-100 text-purple-800',
        'openrouter': 'bg-blue-100 text-blue-800',
        'modelscope': 'bg-green-100 text-green-800',
        'siliconflow': 'bg-amber-100 text-amber-800'
    };
    return badges[type] || 'bg-slate-100 text-slate-800';
}

async function copyKey(key) {
    try {
        // 优先使用现代 Clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(key);
            showToast('已复制到剪贴板', 'success');
        } else {
            // 降级方案：使用传统的 execCommand 方法
            const textArea = document.createElement('textarea');
            textArea.value = key;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);

                if (successful) {
                    showToast('已复制到剪贴板', 'success');
                } else {
                    throw new Error('execCommand failed');
                }
            } catch (err) {
                document.body.removeChild(textArea);
                throw err;
            }
        }
    } catch (error) {
        console.error('Copy failed:', error);
        showToast('复制失败，请手动复制', 'error');
    }
}

async function exportKeys() {
    try {
        const response = await fetch(`${API_BASE}/api/keys`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('导出失败');

        const data = await response.json();
        const keys = data.keys;

        if (keys.length === 0) {
            showToast('没有可导出的数据', 'error');
            return;
        }

        // Create CSV
        const csv = [
            ['类型', '密钥', '来源', 'URL', '发现时间'].join(','),
            ...keys.map(k => [
                k.type,
                k.key,
                k.source,
                k.url,
                k.found_at
            ].map(v => `"${v}"`).join(','))
        ].join('\n');

        // Download
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `apikeys_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();

        showToast('CSV 已导出', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function exportKeysTxt() {
    // 导出当前过滤后的密钥
    const keysToExport = getFilteredKeys();

    if (keysToExport.length === 0) {
        showToast('没有可导出的数据', 'error');
        return;
    }

    // Create TXT - one key per line
    const txt = keysToExport.map(k => k.key).join('\n');

    // Download
    const blob = new Blob([txt], { type: 'text/plain;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);

    // 文件名包含类型信息
    const typeText = currentKeyType ? `_${currentKeyType}` : '';
    link.download = `apikeys${typeText}_${new Date().toISOString().split('T')[0]}.txt`;
    link.click();

    const typeDesc = currentKeyType ? `(${currentKeyType.toUpperCase()})` : '';
    showToast(`TXT 已导出 ${typeDesc}`, 'success');
}

function getFilteredKeys() {
    const search = document.getElementById('keySearch').value.trim();
    const keyType = document.getElementById('keyTypeFilter').value;

    let filteredKeys = allKeysCache;

    // Filter by type
    if (keyType) {
        filteredKeys = filteredKeys.filter(key => key.type.toLowerCase() === keyType);
    }

    // Filter by search
    if (search) {
        const searchLower = search.toLowerCase();
        filteredKeys = filteredKeys.filter(key =>
            key.key.toLowerCase().includes(searchLower) ||
            key.source.toLowerCase().includes(searchLower)
        );
    }

    return filteredKeys;
}

// Utility Functions
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');

    const bgColor = type === 'success' ? 'bg-success' : 'bg-destructive';
    const icon = type === 'success'
        ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
        : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';

    toast.className = `toast ${bgColor} text-white px-4 py-3 rounded-md shadow-lg flex items-center gap-3`;
    toast.innerHTML = `${icon}<span class="text-sm font-medium">${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function escapeAttribute(text) {
    return String(text).replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// Memory Management
async function loadMemoryStats() {
    try {
        const response = await fetch(`${API_BASE}/api/memory/stats`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            const stats = data.stats;
            const memoryText = `${stats.processed_queries || 0} 个查询，${stats.scanned_files || 0} 个文件`;
            document.getElementById('memoryStats').textContent = memoryText;
        }
    } catch (error) {
        console.error('Failed to load memory stats:', error);
        document.getElementById('memoryStats').textContent = '加载失败';
    }
}

async function clearMemory() {
    if (!confirm('确定要清除所有扫描记忆吗？\n\n这将清除：\n- 已处理的查询记录\n- 已扫描的文件记录\n\n下次扫描将从头开始。')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/memory/clear`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('清除记忆失败');

        showToast('扫描记忆已清除，下次扫描将从头开始', 'success');
        loadMemoryStats();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Query Stats
async function loadQueryStats() {
    try {
        const scanMode = document.querySelector('input[name="scanMode"]:checked').value;
        const mode = scanMode === 'compatible' ? 'default' : scanMode.replace('-only', '');

        const response = await fetch(`${API_BASE}/api/queries?mode=${mode}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('queryInfo').textContent = `${data.total} 条搜寻规则`;
            showToast(`当前使用 ${data.total} 条搜寻规则（${mode}模式）`, 'success');
        }
    } catch (error) {
        console.error('Failed to load query stats:', error);
        document.getElementById('queryInfo').textContent = '查看搜寻规则';
    }
}

// Config Dialog
function showConfigDialog() {
    // 将配置表单移到模态框中
    const configCard = document.getElementById('configCardOld');
    const modalContent = document.getElementById('configModalContent');
    const modal = document.getElementById('configModal');

    if (configCard && modalContent && modal) {
        // 只在第一次时移动内容
        if (modalContent.children.length === 0) {
            // 克隆配置表单内容（不包括标题和关闭按钮）
            const formContent = configCard.querySelector('form');
            if (formContent) {
                const clonedForm = formContent.cloneNode(true);
                // 保持表单的提交处理
                clonedForm.id = 'configFormModal';
                clonedForm.onsubmit = handleSaveConfig;
                modalContent.appendChild(clonedForm);

                // 同步ID以避免冲突，并更新name属性
                modalContent.querySelectorAll('[id]').forEach(el => {
                    if (el.id !== 'configFormModal') {
                        el.id = el.id + 'Modal';
                    }
                });

                // 更新radio按钮的name属性
                modalContent.querySelectorAll('input[type="radio"]').forEach(el => {
                    if (el.name && !el.name.endsWith('Modal')) {
                        el.name = el.name + 'Modal';
                    }
                });
            }
        }

        // 显示模态框
        modal.classList.remove('hidden');
        // 加载最新配置
        loadConfigToModal();
    }
}

function hideConfigDialog() {
    const modal = document.getElementById('configModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// 加载配置到模态框
async function loadConfigToModal() {
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.config) {
                // 加载 GitHub Tokens (明文显示)
                const tokensInput = document.getElementById('githubTokensModal');
                if (tokensInput && data.config.github_tokens && data.config.github_tokens.length > 0) {
                    tokensInput.value = data.config.github_tokens.join('\n');
                }

                // 加载其他配置
                const proxyInput = document.getElementById('proxyModal');
                if (proxyInput) proxyInput.value = data.config.proxy || '';

                const dateRangeInput = document.getElementById('dateRangeModal');
                if (dateRangeInput) dateRangeInput.value = data.config.date_range_days || 730;

                const scanMode = data.config.scan_mode || 'compatible';
                const scanModeInput = document.querySelector(`input[name="scanModeModal"][value="${scanMode}"]`);
                if (scanModeInput) scanModeInput.checked = true;

                // 加载验证器配置
                if (data.config.validators) {
                    const validators = data.config.validators;

                    if (validators.gemini) {
                        const geminiEnabled = document.getElementById('geminiEnabledModal');
                        const geminiModel = document.getElementById('geminiModelModal');
                        if (geminiEnabled) geminiEnabled.checked = validators.gemini.enabled;
                        if (geminiModel) geminiModel.value = validators.gemini.model || 'gemini-2.0-flash-exp';
                    }
                    if (validators.openrouter) {
                        const openrouterEnabled = document.getElementById('openrouterEnabledModal');
                        const openrouterModel = document.getElementById('openrouterModelModal');
                        if (openrouterEnabled) openrouterEnabled.checked = validators.openrouter.enabled;
                        if (openrouterModel) openrouterModel.value = validators.openrouter.model || 'deepseek/deepseek-chat-v3:free';
                    }
                    if (validators.modelscope) {
                        const modelscopeEnabled = document.getElementById('modelscopeEnabledModal');
                        const modelscopeModel = document.getElementById('modelscopeModelModal');
                        if (modelscopeEnabled) modelscopeEnabled.checked = validators.modelscope.enabled;
                        if (modelscopeModel) modelscopeModel.value = validators.modelscope.model || 'Qwen/Qwen2-1.5B-Instruct';
                    }
                    if (validators.siliconflow) {
                        const siliconflowEnabled = document.getElementById('siliconflowEnabledModal');
                        const siliconflowModel = document.getElementById('siliconflowModelModal');
                        if (siliconflowEnabled) siliconflowEnabled.checked = validators.siliconflow.enabled;
                        if (siliconflowModel) siliconflowModel.value = validators.siliconflow.model || 'Qwen/Qwen2.5-7B-Instruct';
                    }
                }

                // 加载性能配置
                if (data.config.performance) {
                    const perf = data.config.performance;
                    const maxConcurrent = document.getElementById('maxConcurrentModal');
                    const requestDelay = document.getElementById('requestDelayModal');
                    const githubTimeout = document.getElementById('githubTimeoutModal');
                    const validationTimeout = document.getElementById('validationTimeoutModal');
                    const maxRetries = document.getElementById('maxRetriesModal');

                    if (maxConcurrent) maxConcurrent.value = perf.max_concurrent_files || 5;
                    if (requestDelay) requestDelay.value = perf.request_delay || 1.0;
                    if (githubTimeout) githubTimeout.value = perf.github_timeout || 30;
                    if (validationTimeout) validationTimeout.value = perf.validation_timeout || 30;
                    if (maxRetries) maxRetries.value = perf.max_retries || 3;
                }
            }
        }
    } catch (error) {
        console.error('Failed to load config to modal:', error);
    }
}

// Reports Management
async function showReportsDialog() {
    const modal = document.getElementById('reportsModal');
    if (modal) {
        modal.classList.remove('hidden');
        await loadReports();
    }
}

function hideReportsDialog() {
    const modal = document.getElementById('reportsModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function loadReports() {
    try {
        const response = await fetch(`${API_BASE}/api/reports`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('加载失败');

        const data = await response.json();
        displayReports(data.reports);
    } catch (error) {
        console.error('Failed to load reports:', error);
        showToast(error.message, 'error');
    }
}

function displayReports(reports) {
    const container = document.getElementById('reportsContent');

    if (reports.length === 0) {
        container.innerHTML = `
            <div class="text-center text-slate-500 py-12">
                <svg class="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <p class="text-lg">暂无扫描报告</p>
                <p class="text-sm mt-2">完成扫描后会自动生成报告</p>
            </div>
        `;
        return;
    }

    // 创建报告卡片网格
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4';

    reports.forEach(report => {
        const card = createReportCard(report);
        grid.appendChild(card);
    });

    container.innerHTML = '';
    container.appendChild(grid);
}

function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'bg-white border border-slate-200 rounded-lg p-5 hover:shadow-lg transition-shadow';

    const modeNames = {
        'compatible': '全部平台',
        'gemini-only': 'Gemini',
        'openrouter-only': 'OpenRouter',
        'modelscope-only': 'ModelScope',
        'siliconflow-only': 'SiliconFlow'
    };

    const modeName = modeNames[report.scan_mode] || report.scan_mode;
    const modeColors = {
        'compatible': 'bg-slate-100 text-slate-800',
        'gemini-only': 'bg-purple-100 text-purple-800',
        'openrouter-only': 'bg-blue-100 text-blue-800',
        'modelscope-only': 'bg-green-100 text-green-800',
        'siliconflow-only': 'bg-amber-100 text-amber-800'
    };
    const modeColor = modeColors[report.scan_mode] || 'bg-slate-100 text-slate-800';

    const startTime = new Date(report.started_at).toLocaleString('zh-CN');
    const endTime = report.ended_at ? new Date(report.ended_at).toLocaleString('zh-CN') : '进行中';

    // 计算成功率
    const successRate = report.total_keys > 0
        ? ((report.valid_keys / report.total_keys) * 100).toFixed(1)
        : 0;

    // 只有当有有效密钥时才显示复制按钮
    const copyButtonHtml = report.valid_keys > 0 ? `
        <div class="pt-3 border-t border-slate-100 mt-3">
            <button onclick="copyReportKeys(${report.id})"
                class="w-full py-2 px-3 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
                </svg>
                一键复制密钥
            </button>
        </div>
    ` : '';

    card.innerHTML = `
        <div class="flex items-start justify-between mb-3">
            <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                    <span class="inline-flex px-2 py-1 text-xs font-medium rounded ${modeColor}">
                        ${modeName}
                    </span>
                    <span class="text-xs px-2 py-1 rounded ${report.status === 'completed' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}">
                        ${report.status === 'completed' ? '已完成' : '运行中'}
                    </span>
                </div>
                <p class="text-xs text-slate-500">${startTime}</p>
            </div>
            <button onclick="deleteReport(${report.id})" class="text-slate-400 hover:text-red-600">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
            </button>
        </div>

        <div class="grid grid-cols-3 gap-3 mb-3">
            <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">${report.total_files || 0}</div>
                <div class="text-xs text-slate-600">扫描文件</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-purple-600">${report.total_keys || 0}</div>
                <div class="text-xs text-slate-600">发现密钥</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${report.valid_keys || 0}</div>
                <div class="text-xs text-slate-600">有效密钥</div>
            </div>
        </div>

        <div class="pt-3 border-t border-slate-100">
            <div class="flex justify-between text-xs text-slate-600">
                <span>成功率</span>
                <span class="font-semibold ${successRate > 50 ? 'text-green-600' : 'text-amber-600'}">${successRate}%</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2 mt-2">
                <div class="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all" style="width: ${successRate}%"></div>
            </div>
        </div>

        ${copyButtonHtml}
    `;

    return card;
}

async function deleteReport(reportId) {
    if (!confirm('确定要删除这个报告吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/reports/${reportId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('删除失败');

        showToast('报告已删除', 'success');
        loadReports();  // 刷新列表
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function copyReportKeys(reportId) {
    try {
        const response = await fetch(`${API_BASE}/api/reports/${reportId}/keys`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('获取密钥失败');

        const data = await response.json();

        if (!data.keys || data.keys.length === 0) {
            showToast('该报告没有有效密钥', 'warning');
            return;
        }

        // 将密钥用换行符连接
        const keysText = data.keys.join('\n');

        // 复制到剪贴板
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(keysText);
            showToast(`已复制 ${data.keys.length} 个密钥`, 'success');
        } else {
            // 降级方案：使用 textarea
            const textarea = document.createElement('textarea');
            textarea.value = keysText;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                showToast(`已复制 ${data.keys.length} 个密钥`, 'success');
            } catch (err) {
                showToast('复制失败，请手动复制', 'error');
            }
            document.body.removeChild(textarea);
        }
    } catch (error) {
        console.error('Failed to copy report keys:', error);
        showToast(error.message, 'error');
    }
}

// Password Management
function showChangePasswordDialog() {
    document.getElementById('changePasswordModal').classList.remove('hidden');
}

function hideChangePasswordDialog() {
    document.getElementById('changePasswordModal').classList.add('hidden');
    document.getElementById('changePasswordForm').reset();
}

async function handleChangePassword(event) {
    event.preventDefault();

    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        showToast('两次输入的新密码不一致', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showToast('新密码长度至少6位', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/settings/change-password`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '修改失败');
        }

        showToast('密码修改成功，请重新登录', 'success');
        hideChangePasswordDialog();

        // 自动登出
        setTimeout(() => {
            handleLogout();
        }, 1500);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Dark Mode
function initDarkMode() {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'true') {
        document.documentElement.classList.add('dark');
        updateDarkModeIcon(true);
    }
}

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', isDark);
    updateDarkModeIcon(isDark);
    showToast(isDark ? '已切换到暗黑模式' : '已切换到亮色模式', 'success');
}

function updateDarkModeIcon(isDark) {
    const icon = document.getElementById('darkModeIcon');

    if (isDark) {
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>';
    } else {
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>';
    }
}
