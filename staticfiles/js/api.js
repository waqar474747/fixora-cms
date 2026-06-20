const API_BASE = '/api/';

function getToken() {
    return localStorage.getItem('auth_token');
}

function setToken(token) {
    localStorage.setItem('auth_token', token);
}

function removeToken() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
}

function isAuthenticated() {
    return !!getToken();
}

function getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }
    return headers;
}

function getFileUploadHeaders() {
    const headers = {};
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }
    return headers;
}

function getUserData() {
    try {
        return JSON.parse(localStorage.getItem('user_data'));
    } catch {
        return null;
    }
}

function setUserData(data) {
    localStorage.setItem('user_data', JSON.stringify(data));
}

async function apiRequest(method, endpoint, data = null, isFileUpload = false) {
    const url = `${API_BASE}${endpoint}`;
    const options = {
        method: method,
        headers: isFileUpload ? getFileUploadHeaders() : getAuthHeaders(),
    };
    if (data) {
        options.body = isFileUpload ? data : JSON.stringify(data);
    }
    try {
        const response = await fetch(url, options);
        const responseData = await response.json();
        if (!response.ok) {
            let errorMsg = 'An error occurred';
            if (typeof responseData === 'object' && responseData !== null) {
                const messages = [];
                for (const key in responseData) {
                    const val = responseData[key];
                    if (Array.isArray(val)) {
                        messages.push(`${key}: ${val.join(', ')}`);
                    } else if (typeof val === 'string') {
                        messages.push(val);
                    } else if (typeof val === 'object') {
                        messages.push(JSON.stringify(val));
                    }
                }
                if (messages.length > 0) {
                    errorMsg = messages.join(' | ');
                }
            } else if (typeof responseData === 'string') {
                errorMsg = responseData;
            }
            throw new Error(errorMsg);
        }
        return responseData;
    } catch (error) {
        throw error;
    }
}

function apiGet(endpoint) {
    return apiRequest('GET', endpoint);
}

function apiPost(endpoint, data, isFileUpload = false) {
    return apiRequest('POST', endpoint, data, isFileUpload);
}

function apiPut(endpoint, data) {
    return apiRequest('PUT', endpoint, data);
}

function apiPatch(endpoint, data) {
    return apiRequest('PATCH', endpoint, data);
}

function apiDelete(endpoint) {
    return apiRequest('DELETE', endpoint);
}

async function loginUser(username, password) {
    const data = await apiPost('login/', { username, password });
    setToken(data.token);
    setUserData(data);
    return data;
}

async function registerUser(userData) {
    const data = await apiPost('register/', userData);
    setToken(data.token);
    setUserData(data);
    return data;
}

async function logoutUser() {
    try {
        await apiPost('logout/');
    } catch (e) {
    }
    removeToken();
}

function redirectToLogin() {
    if (!isAuthenticated() && !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/register') &&
        window.location.pathname !== '/') {
        window.location.href = '/accounts/login/';
    }
}

function showAlert(message, type = 'danger', containerId = 'alert-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    const icons = {
        success: 'fa-check-circle',
        danger: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
    };
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="fas ${icons[type] || icons.info} me-2"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    container.appendChild(alert);
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function getStatusBadge(status) {
    const colors = {
        'PENDING': 'warning',
        'IN_PROGRESS': 'info',
        'RESOLVED': 'success',
        'REJECTED': 'danger',
    };
    const labels = {
        'PENDING': 'Pending',
        'IN_PROGRESS': 'In Progress',
        'RESOLVED': 'Resolved',
        'REJECTED': 'Rejected',
    };
    const color = colors[status] || 'secondary';
    const label = labels[status] || status;
    return `<span class="badge bg-${color}">${label}</span>`;
}

function getPriorityBadge(priority) {
    const colors = {
        'LOW': 'info',
        'MEDIUM': 'warning',
        'HIGH': 'danger',
    };
    const color = colors[priority] || 'secondary';
    return `<span class="badge bg-${color}">${priority}</span>`;
}
