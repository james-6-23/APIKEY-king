// API Base URL
const API_BASE = window.location.origin;
let authToken = localStorage.getItem('auth_token');
let ws = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
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
        updateScanStatus(true);
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

function updateScanStatus(running) {
    const statusDiv = document.getElementById('scanStatus');
    const btnStart = document.getElementById('btnStart');
    const btnStop = document.getElementById('btnStop');

    if (running) {
        statusDiv.innerHTML = `
            <div class="spinner"></div>
            <span class="text-sm text-success font-medium">运行中</span>
        `;
        btnStart.disabled = true;
        btnStart.classList.add('opacity-50', 'cursor-not-allowed');
        btnStop.disabled = false;
        btnStop.classList.remove('opacity-50', 'cursor-not-allowed');
    } else {
        statusDiv.innerHTML = `
            <div class="w-3 h-3 bg-slate-400 rounded-full"></div>
            <span class="text-sm text-slate-600">未运行</span>
        `;
        btnStart.disabled = false;
        btnStart.classList.remove('opacity-50', 'cursor-not-allowed');
        btnStop.disabled = true;
        btnStop.classList.add('opacity-50', 'cursor-not-allowed');
    }
}

// Status Polling
let statusInterval;
function startStatusPolling() {
    loadStatus();
    statusInterval = setInterval(loadStatus, 2000);
}

async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/scan/status`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            updateScanStatus(data.running);
            updateStats(data.stats);
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

function updateStats(stats) {
    document.getElementById('statFiles').textContent = stats.total_files || 0;
    document.getElementById('statKeys').textContent = stats.total_keys || 0;
    document.getElementById('statValidKeys').textContent = stats.valid_keys || 0;
}

// WebSocket for real-time logs
function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/logs`);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.event === 'log') {
            addLogEntry(message.data);
        } else if (message.event === 'history') {
            message.data.forEach(log => addLogEntry(log));
        } else if (message.event === 'stats') {
            updateStats(message.data);
        }
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 3s...');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function addLogEntry(log) {
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
    container.scrollTop = container.scrollHeight;

    // Keep only last 500 logs
    while (container.children.length > 500) {
        container.removeChild(container.firstChild);
    }
}

function clearLogs() {
    const container = document.getElementById('logsContainer');
    container.innerHTML = '<div class="text-slate-500">日志已清空</div>';
}

// Keys Management
async function loadKeys() {
    try {
        const response = await fetch(`${API_BASE}/api/keys`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            displayKeys(data.keys);
        }
    } catch (error) {
        console.error('Failed to load keys:', error);
    }
}

async function refreshKeys() {
    await loadKeys();
    showToast('已刷新', 'success');
}

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

