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
        let responseData;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
        } else {
            const text = await response.text();
            try {
                responseData = JSON.parse(text);
            } catch {
                responseData = { detail: text || 'Request failed' };
            }
        }
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
                        const nested = Object.values(val).flat().join(', ');
                        if (nested) messages.push(nested);
                    }
                }
                if (messages.length > 0) {
                    errorMsg = messages.join(' | ');
                } else if (responseData.detail) {
                    errorMsg = responseData.detail;
                }
            } else if (typeof responseData === 'string') {
                errorMsg = responseData;
            }
            throw new Error(errorMsg);
        }
        return responseData;
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('Network error. Please check your connection.');
        }
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
        !window.location.pathname.includes('/admin-login') &&
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
        'SUBMITTED': 'secondary',
        'PENDING': 'warning',
        'UNDER_REVIEW': 'info',
        'IN_PROGRESS': 'primary',
        'RESOLVED': 'success',
        'REJECTED': 'danger',
    };
    const labels = {
        'SUBMITTED': 'Submitted',
        'PENDING': 'Pending',
        'UNDER_REVIEW': 'Under Review',
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
        'EMERGENCY': 'dark',
    };
    const labels = {
        'EMERGENCY': 'EMERGENCY',
    };
    const color = colors[priority] || 'secondary';
    const label = labels[priority] || priority;
    const extra = priority === 'EMERGENCY' ? ' class="pulse-badge"' : '';
    return `<span class="badge bg-${color}"${extra}>${label}</span>`;
}

// QR Code helpers
function parseQRData(decodedText) {
    try { return JSON.parse(decodedText); } catch { return null; }
}

// GPS helpers
function getCurrentLocation(timeout = 10000) {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation not supported'));
            return;
        }
        navigator.geolocation.getCurrentPosition(
            pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy }),
            err => reject(err),
            { enableHighAccuracy: true, timeout: timeout }
        );
    });
}

function formatCoords(lat, lng, accuracy) {
    let s = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    if (accuracy) s += ` (±${Math.round(accuracy)}m)`;
    return s;
}

function openMapLink(lat, lng) {
    window.open(`https://www.google.com/maps?q=${lat},${lng}`, '_blank');
}