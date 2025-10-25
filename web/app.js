// API Base URL
const API_BASE = window.location.origin;
let authToken = localStorage.getItem('auth_token');
let ws = null;

// Charts
let keyTypeChart = null;
let efficiencyChart = null;

// All keys cache for filtering
let allKeysCache = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
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
    if (ws) ws.close();
    showLoginPage();
    showToast('已退出登录', 'success');
}

function showLoginPage() {
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('dashboardPage').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('dashboardPage').classList.remove('hidden');
    loadConfig();
    loadKeys();
    loadMemoryStats();
    loadQueryStats();
    initCharts();
    startStatusPolling();
    connectWebSocket();
}

// Config Functions
async function handleSaveConfig(event) {
    event.preventDefault();
    
    const tokensText = document.getElementById('githubTokens').value;
    const tokens = tokensText.split('\n').map(t => t.trim()).filter(t => t);
    const proxy = document.getElementById('proxy').value.trim();
    const scanMode = document.querySelector('input[name="scanMode"]:checked').value;
    const dateRange = parseInt(document.getElementById('dateRange').value);

    // 渠道验证配置
    const validators = {
        gemini: {
            enabled: document.getElementById('geminiEnabled').checked,
            model: document.getElementById('geminiModel').value.trim()
        },
        openrouter: {
            enabled: document.getElementById('openrouterEnabled').checked,
            model: document.getElementById('openrouterModel').value.trim()
        },
        modelscope: {
            enabled: document.getElementById('modelscopeEnabled').checked,
            model: document.getElementById('modelscopeModel').value.trim()
        },
        siliconflow: {
            enabled: document.getElementById('siliconflowEnabled').checked,
            model: document.getElementById('siliconflowModel').value.trim()
        }
    };

    // 性能配置
    const performance = {
        max_concurrent_files: parseInt(document.getElementById('maxConcurrent').value),
        request_delay: parseFloat(document.getElementById('requestDelay').value),
        github_timeout: parseInt(document.getElementById('githubTimeout').value),
        validation_timeout: parseInt(document.getElementById('validationTimeout').value),
        max_retries: parseInt(document.getElementById('maxRetries').value)
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
                // Don't load tokens for security
                document.getElementById('proxy').value = data.config.proxy || '';
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

function startStatusPolling() {
    loadStatus();
    // 降低轮询频率到5秒
    statusInterval = setInterval(loadStatus, 5000);
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
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

// Throttled stats update
const updateStats = window.perfUtils.throttle(function(stats) {
    document.getElementById('statFiles').textContent = stats.total_files || 0;
    document.getElementById('statKeys').textContent = stats.total_keys || 0;
    document.getElementById('statValidKeys').textContent = stats.valid_keys || 0;
    
    // Update efficiency chart if scanning
    if (stats.total_files > 0) {
        updateEfficiencyChart(stats);
    }
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

// WebSocket for real-time logs
function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/logs`);

    // Batch process WebSocket messages
    let messageQueue = [];
    let processingQueue = false;

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        messageQueue.push(message);
        
        if (!processingQueue) {
            processingQueue = true;
            requestAnimationFrame(() => {
                processMessageQueue();
                processingQueue = false;
            });
        }
    };

    function processMessageQueue() {
        while (messageQueue.length > 0) {
            const message = messageQueue.shift();
            
            if (message.event === 'log') {
                addLogEntry(message.data);
            } else if (message.event === 'history') {
                // Only show last 50 logs from history
                const recentLogs = message.data.slice(-50);
                recentLogs.forEach(log => addLogEntry(log));
            } else if (message.event === 'stats') {
                updateStats(message.data);
            }
        }
    }

    ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 3s...');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Optimized log entry with throttling
const addLogEntry = window.perfUtils.throttle(function(log) {
    const container = document.getElementById('logsContainer');
    
    // Clear placeholder
    if (container.textContent.includes('等待日志')) {
        container.innerHTML = '';
    }

    const logDiv = document.createElement('div');
    logDiv.className = 'log-item flex gap-2';

    const time = new Date(log.timestamp).toLocaleTimeString('zh-CN');
    
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

    logDiv.innerHTML = `
        <span class="text-slate-400">[${time}]</span>
        <span class="${color} font-bold">${icon}</span>
        <span class="text-slate-700">${escapeHtml(log.message)}</span>
    `;

    container.appendChild(logDiv);
    
    // Use requestAnimationFrame for smooth scrolling
    requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
    });

    // Keep only last 200 logs (减少DOM数量)
    while (container.children.length > 200) {
        container.removeChild(container.firstChild);
    }
}, 100);

function clearLogs() {
    const container = document.getElementById('logsContainer');
    container.innerHTML = '<div class="text-slate-500">日志已清空</div>';
}

// Keys Management
async function loadKeys(keyType = null, search = null) {
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
            displayKeys(data.keys);
            updateCharts();
        }
    } catch (error) {
        console.error('Failed to load keys:', error);
    }
}

// Optimized search with debounce
const handleKeySearch = window.perfUtils.debounce(function() {
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
    await loadKeys();
    updateCharts();
    showToast('已刷新', 'success');
}

// Charts
function initCharts() {
    // Key Type Distribution Chart
    const keyTypeCtx = document.getElementById('keyTypeChart');
    if (keyTypeCtx) {
        keyTypeChart = new Chart(keyTypeCtx, {
            type: 'doughnut',
            data: {
                labels: ['Gemini', 'OpenRouter', 'ModelScope', 'SiliconFlow'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgb(147, 51, 234)',  // purple
                        'rgb(59, 130, 246)',   // blue
                        'rgb(34, 197, 94)',    // green
                        'rgb(251, 146, 60)'    // orange
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    }

    // Efficiency Trend Chart
    const efficiencyCtx = document.getElementById('efficiencyChart');
    if (efficiencyCtx) {
        efficiencyChart = new Chart(efficiencyCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '扫描文件数',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '有效密钥数',
                    data: [],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { font: { size: 10 } }
                    },
                    x: {
                        ticks: { font: { size: 10 } }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { font: { size: 11 } }
                    }
                }
            }
        });
    }
}

async function updateCharts() {
    try {
        const response = await fetch(`${API_BASE}/api/keys`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            const keys = data.keys;

            // Update key type distribution
            const typeCounts = {
                'gemini': 0,
                'openrouter': 0,
                'modelscope': 0,
                'siliconflow': 0
            };

            keys.forEach(key => {
                const type = key.type.toLowerCase();
                if (typeCounts.hasOwnProperty(type)) {
                    typeCounts[type]++;
                }
            });

            if (keyTypeChart) {
                keyTypeChart.data.datasets[0].data = [
                    typeCounts.gemini,
                    typeCounts.openrouter,
                    typeCounts.modelscope,
                    typeCounts.siliconflow
                ];
                keyTypeChart.update();
            }
        }
    } catch (error) {
        console.error('Failed to update charts:', error);
    }
}

// Throttled chart update
const updateEfficiencyChart = window.perfUtils.throttle(function(stats) {
    if (!efficiencyChart) return;

    const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    // Keep only last 20 data points
    if (efficiencyChart.data.labels.length >= 20) {
        efficiencyChart.data.labels.shift();
        efficiencyChart.data.datasets[0].data.shift();
        efficiencyChart.data.datasets[1].data.shift();
    }

    efficiencyChart.data.labels.push(now);
    efficiencyChart.data.datasets[0].data.push(stats.total_files || 0);
    efficiencyChart.data.datasets[1].data.push(stats.valid_keys || 0);
    efficiencyChart.update('none'); // No animation for real-time updates
}, 2000); // 限制每2秒更新一次

function displayKeys(keys) {
    const tbody = document.getElementById('keysTableBody');
    
    if (keys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-3 py-8 text-center text-slate-500">暂无数据</td></tr>';
        return;
    }

    tbody.innerHTML = keys.map((key, index) => `
        <tr class="${index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'} hover:bg-slate-100">
            <td class="px-3 py-2">
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded ${getKeyTypeBadge(key.type)}">
                    ${key.type.toUpperCase()}
                </span>
            </td>
            <td class="px-3 py-2 font-mono text-xs">${escapeHtml(key.key.substring(0, 20))}...</td>
            <td class="px-3 py-2 text-xs">
                <a href="${escapeHtml(key.url)}" target="_blank" class="text-blue-600 hover:underline">
                    ${escapeHtml(key.source)}
                </a>
            </td>
            <td class="px-3 py-2 text-xs text-slate-600">${key.found_at}</td>
            <td class="px-3 py-2 text-center">
                <button onclick="copyKey('${escapeAttribute(key.key)}')" class="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary/90">
                    复制
                </button>
            </td>
        </tr>
    `).join('');
}

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
        await navigator.clipboard.writeText(key);
        showToast('已复制到剪贴板', 'success');
    } catch (error) {
        showToast('复制失败', 'error');
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
    updateChartsTheme(isDark);
    showToast(isDark ? '已切换到暗黑模式' : '已切换到亮色模式', 'success');
}

function updateDarkModeIcon(isDark) {
    const icon = document.getElementById('darkModeIcon');
    const text = document.getElementById('darkModeText');
    
    if (isDark) {
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>';
        if (text) text.textContent = '亮色';
    } else {
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>';
        if (text) text.textContent = '暗黑';
    }
}

function updateChartsTheme(isDark) {
    const textColor = isDark ? '#e2e8f0' : '#334155';
    const gridColor = isDark ? '#334155' : '#e2e8f0';
    
    if (keyTypeChart) {
        keyTypeChart.options.plugins.legend.labels.color = textColor;
        keyTypeChart.update();
    }
    
    if (efficiencyChart) {
        efficiencyChart.options.scales.x.ticks.color = textColor;
        efficiencyChart.options.scales.y.ticks.color = textColor;
        efficiencyChart.options.scales.x.grid = { color: gridColor };
        efficiencyChart.options.scales.y.grid = { color: gridColor };
        efficiencyChart.update();
    }
}

