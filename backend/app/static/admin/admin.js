// ==============================================================================
// Next Level Cheat - Admin Panel JS Controller
// ==============================================================================

const API_BASE = '/api/v1';
let authToken = localStorage.getItem('nlc_admin_token') || null;

// -----------------------------------------------------------------------------
// Realtime WebSocket Connection & Button Loading Helpers
// -----------------------------------------------------------------------------
let wsClient = null;

function connectRealtimeSync() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/sync`;

  try {
    wsClient = new WebSocket(wsUrl);

    wsClient.onopen = () => {
      console.log('Realtime WebSocket Sync connected.');
    };

    wsClient.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        console.log('Realtime Sync event received:', payload.event);

        if (payload.event === 'CONFIG_UPDATED') {
          fetchSiteSettings();
          fetchDashboardData();
        } else if (payload.event === 'RELEASE_UPDATED') {
          fetchReleases();
          fetchDashboardData();
        } else if (payload.event === 'VIDEOS_UPDATED') {
          fetchVideos();
        } else if (payload.event === 'FEATURES_UPDATED') {
          fetchFeatures();
        } else if (payload.event === 'FAQS_UPDATED') {
          fetchFaqs();
        }
      } catch (e) { }
    };

    wsClient.onclose = () => {
      // Auto-reconnect after 3 seconds
      setTimeout(connectRealtimeSync, 3000);
    };

    wsClient.onerror = () => {
      if (wsClient) wsClient.close();
    };
  } catch (err) {
    setTimeout(connectRealtimeSync, 3000);
  }
}

// Start WebSocket when admin page loads
document.addEventListener('DOMContentLoaded', () => {
  connectRealtimeSync();
  if (authToken) {
    showDashboard();
  } else {
    showLogin();
  }
});

function setButtonLoading(btn, isLoading, loadingText = 'Saving...') {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="spin" style="margin-right:6px;">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
      </svg>
      ${loadingText}
    `;
  } else {
    btn.disabled = false;
    if (btn.dataset.originalHtml) {
      btn.innerHTML = btn.dataset.originalHtml;
    }
  }
}

function showLogin() {
  document.getElementById('loginSection').style.display = 'flex';
  document.getElementById('dashboardSection').style.display = 'none';
}

function togglePasswordVisibility() {
  const pwd = document.getElementById('passwordInput');
  const eye = document.getElementById('eyeIcon');
  if (!pwd || !eye) return;
  if (pwd.type === 'password') {
    pwd.type = 'text';
    eye.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
  } else {
    pwd.type = 'password';
    eye.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
  }
}

function showDashboard() {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('dashboardSection').style.display = 'flex';
  fetchDashboardData();
  fetchReleases();
  fetchVideos();
  fetchFeatures();
  fetchFaqs();
  fetchSiteSettings();

  // Restore the exact active tab user was on before reload/refresh
  const savedTab = localStorage.getItem('nlc_admin_active_tab') || 'releasesTab';
  switchTab(savedTab);
}

// -----------------------------------------------------------------------------
// Authentication
// -----------------------------------------------------------------------------
async function handleLogin(e) {
  e.preventDefault();
  const alertBox = document.getElementById('loginAlert');
  alertBox.style.display = 'none';

  const username = document.getElementById('usernameInput').value.trim();
  const password = document.getElementById('passwordInput').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();

    if (!res.ok) {
      if (typeof data.detail === 'string') {
        alertBox.textContent = data.detail;
      } else if (Array.isArray(data.detail)) {
        alertBox.textContent = data.detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ');
      } else if (data.detail && typeof data.detail === 'object') {
        alertBox.textContent = JSON.stringify(data.detail);
      } else {
        alertBox.textContent = 'Authentication failed. Please verify credentials.';
      }
      alertBox.style.display = 'block';
      return;
    }

    authToken = data.access_token;
    localStorage.setItem('nlc_admin_token', authToken);
    localStorage.setItem('nlc_admin_name', data.admin.username);
    localStorage.setItem('nlc_admin_role', data.admin.role);

    document.getElementById('currentAdminName').textContent = data.admin.username;
    document.getElementById('currentAdminRole').textContent = data.admin.role.toUpperCase();
    const avatarLetter = document.getElementById('avatarLetter');
    if (avatarLetter && data.admin.username) {
      avatarLetter.textContent = data.admin.username.charAt(0).toUpperCase();
    }

    showDashboard();
  } catch (err) {
    alertBox.textContent = 'Server connection error. Ensure FastAPI backend is running.';
    alertBox.style.display = 'block';
  }
}

function handleLogout() {
  localStorage.removeItem('nlc_admin_token');
  localStorage.removeItem('nlc_admin_name');
  localStorage.removeItem('nlc_admin_role');
  authToken = null;
  showLogin();
}

function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

// -----------------------------------------------------------------------------
// Dashboard Stats & Audits
// -----------------------------------------------------------------------------
async function fetchDashboardData() {
  try {
    const res = await fetch(`${API_BASE}/admin/dashboard-stats`, {
      headers: getAuthHeaders()
    });

    if (res.status === 401) {
      handleLogout();
      return;
    }

    const data = await res.json();

    document.getElementById('statDownloads').textContent = Number(data.total_downloads).toLocaleString();
    document.getElementById('statVersion').textContent = data.latest_version || 'N/A';
    document.getElementById('statReleases').textContent = data.active_releases_count;
    document.getElementById('statAudits').textContent = data.total_audit_events;

    renderAudits(data.recent_audits || []);
  } catch (err) {
    console.error('Failed to load dashboard statistics', err);
  }
}

function renderAudits(audits) {
  const tbody = document.getElementById('auditsTableBody');
  if (!audits || audits.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem; color:var(--text-muted);">No audit events recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = audits.map(a => {
    let badgeClass = 'badge-success';
    if (a.status === 'FAILED') badgeClass = 'badge-failed';
    if (a.status === 'BLOCKED') badgeClass = 'badge-blocked';

    const dateStr = a.created_at ? new Date(a.created_at).toLocaleString() : 'N/A';

    return `
      <tr>
        <td style="font-family:var(--mono); font-size:0.8rem; color:var(--text-muted);">${dateStr}</td>
        <td><strong style="color:var(--text-main);">${escapeHtml(a.admin_username)}</strong></td>
        <td><code style="background:#f1f5f9; color:var(--text-main); font-weight:600; padding:0.2rem 0.5rem; border-radius:5px; border:1px solid #e2e8f0;">${escapeHtml(a.action)}</code></td>
        <td style="font-family:var(--mono); font-size:0.82rem; color:var(--text-secondary);">${escapeHtml(a.ip_address)}</td>
        <td><span class="status-badge ${badgeClass}">${escapeHtml(a.status)}</span></td>
        <td style="color:var(--text-secondary); font-size:0.84rem;">${escapeHtml(a.details || '')}</td>
      </tr>
    `;
  }).join('');
}

// -----------------------------------------------------------------------------
// TAB 1: Releases Manager (APK)
// -----------------------------------------------------------------------------
async function fetchReleases() {
  try {
    const res = await fetch(`${API_BASE}/releases`, {
      headers: getAuthHeaders()
    });

    if (!res.ok) return;

    const releases = await res.json();
    renderReleases(releases);
  } catch (err) {
    console.error('Failed to load releases', err);
  }
}

function renderReleases(releases) {
  const tbody = document.getElementById('releasesTableBody');
  if (!releases || releases.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2.5rem; color:var(--text-muted);">No APK releases uploaded yet.<br><small style="color:var(--danger-text);">Website currently indicates: "APK Not Linked"</small></td></tr>';
    return;
  }

  tbody.innerHTML = releases.map(r => `
    <tr>
      <td><strong style="color:var(--primary); font-family:var(--mono); font-weight:700;">${escapeHtml(r.version)}</strong></td>
      <td><strong style="color:var(--text-main); font-weight:600;">${escapeHtml(r.title)}</strong></td>
      <td style="color:var(--text-secondary); font-family:var(--mono); font-weight:600;">${r.file_size_mb} MB</td>
      <td style="color:var(--text-secondary);">${escapeHtml(r.min_android_version)}</td>
      <td style="color:var(--text-main); font-weight:700;">${Number(r.download_count).toLocaleString()}</td>
      <td>
        <span class="status-badge ${r.is_active ? 'badge-success' : 'badge-failed'}">
          ${r.is_active ? 'Active' : 'Archived'}
        </span>
      </td>
      <td>
        <a href="${escapeHtml(r.download_url)}" target="_blank" style="color:var(--primary); font-weight:600; text-decoration:none; font-family:var(--mono); font-size:0.8rem; display:inline-flex; align-items:center; gap:3px;">
          Download / File &rarr;
        </a>
      </td>
      <td>
        <button type="button" class="btn-xs-delete" onclick="handleDeleteRelease(${r.id}, '${escapeHtml(r.version)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Delete
        </button>
      </td>
    </tr>
  `).join('');
}

function openNewReleaseModal() {
  document.getElementById('releaseModal').classList.add('active');
  document.getElementById('modalAlert').style.display = 'none';
}

function closeNewReleaseModal() {
  document.getElementById('releaseModal').classList.remove('active');
}

async function handleCreateRelease(e) {
  e.preventDefault();
  const alertBox = document.getElementById('modalAlert');
  alertBox.style.display = 'none';

  const fileInput = document.getElementById('relFileInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    alertBox.textContent = 'Please choose an APK file from your computer/storage.';
    alertBox.style.display = 'block';
    return;
  }

  const file = fileInput.files[0];
  if (!file.name.toLowerCase().endsWith('.apk')) {
    alertBox.textContent = 'Invalid file. Please select a valid .apk file.';
    alertBox.style.display = 'block';
    return;
  }

  const submitBtn = document.getElementById('relSubmitBtn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="spin">
      <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
    </svg>
    Uploading &amp; Saving to Database...
  `;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('version', document.getElementById('relVersion').value.trim());
  formData.append('title', document.getElementById('relTitle').value.trim());
  formData.append('min_android_version', document.getElementById('relOs').value.trim());
  formData.append('changelog', document.getElementById('relChangelog').value.trim());

  try {
    const res = await fetch(`${API_BASE}/releases/upload-apk`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
        // NOTE: Don't set Content-Type header so browser adds boundary automatically
      },
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to upload and publish release.';
      alertBox.style.display = 'block';
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
      return;
    }

    closeNewReleaseModal();
    document.getElementById('newReleaseForm').reset();
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
    fetchReleases();
    fetchDashboardData();
  } catch (err) {
    alertBox.textContent = 'Server connection error during APK upload.';
    alertBox.style.display = 'block';
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

async function handleDeleteRelease(releaseId, version) {
  if (!confirm(`Are you sure you want to permanently delete release "${version}"?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/releases/${releaseId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Failed to delete release.');
      return;
    }

    fetchReleases();
    fetchDashboardData();
  } catch (err) {
    alert('Failed to connect to backend.');
  }
}

// -----------------------------------------------------------------------------
// TAB 2: Multiple Video Playlist Management
// -----------------------------------------------------------------------------
async function fetchVideos() {
  try {
    const res = await fetch(`${API_BASE}/showcase/all-videos`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;

    const videos = await res.json();
    renderVideos(videos);
  } catch (err) {
    console.error('Failed to load videos', err);
  }
}

function renderVideos(videos) {
  const tbody = document.getElementById('videosTableBody');
  if (!videos || videos.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2.5rem; color:var(--text-muted);">No showcase videos in playlist.<br><small style="color:var(--primary);">Click "Add Video to Playlist" to upload your first showcase video.</small></td></tr>';
    return;
  }

  tbody.innerHTML = videos.map(v => {
    const isLocal = v.video_url.startsWith('/static/');
    const fileDisplay = isLocal ? `[Local] ${v.video_url.split('/').pop()}` : v.video_url;

    return `
    <tr>
      <td><strong style="color:var(--text-main); font-family:var(--mono); font-weight:700;">#${v.display_order}</strong></td>
      <td><strong style="color:var(--text-main); font-weight:700; font-size:0.92rem;">${escapeHtml(v.title)}</strong></td>
      <td style="color:var(--text-secondary); font-family:var(--mono); font-weight:600;">${v.duration_seconds}s</td>
      <td>
        <a href="${escapeHtml(v.video_url)}" target="_blank" style="color:var(--primary); font-weight:600; text-decoration:none; font-family:var(--mono); font-size:0.8rem;">
          ${escapeHtml(fileDisplay.substring(0, 36))}... &rarr;
        </a>
      </td>
      <td>
        <span class="status-badge ${v.is_active ? 'badge-success' : 'badge-failed'}">
          ${v.is_active ? 'Active' : 'Disabled'}
        </span>
      </td>
      <td>
        <button type="button" class="btn-xs-delete" onclick="handleDeleteVideo(${v.id}, '${escapeHtml(v.title)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Delete
        </button>
      </td>
    </tr>
  `;
  }).join('');
}

function handleVideoFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  const titleInput = document.getElementById('vidTitle');
  if (!titleInput.value.trim()) {
    const nameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
    titleInput.value = nameWithoutExt.replace(/[_\-]/g, ' ').toUpperCase();
  }

  const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
  document.getElementById('fileInfoText').textContent = `✓ Selected: ${file.name} (${sizeMb} MB). Ready to upload!`;
  document.getElementById('fileInfoText').style.color = '#38bdf8';

  // Auto-detect duration from video metadata
  try {
    const tempVideo = document.createElement('video');
    tempVideo.preload = 'metadata';
    tempVideo.onloadedmetadata = function () {
      window.URL.revokeObjectURL(tempVideo.src);
      if (tempVideo.duration && !isNaN(tempVideo.duration)) {
        document.getElementById('vidDuration').value = Math.max(1, Math.round(tempVideo.duration));
      }
    };
    tempVideo.src = URL.createObjectURL(file);
  } catch (e) {
    // Fallback
  }
}

function openNewVideoModal() {
  document.getElementById('videoModal').classList.add('active');
  document.getElementById('videoModalAlert').style.display = 'none';
  document.getElementById('vidFileInput').value = '';
  document.getElementById('fileInfoText').textContent = 'Supports MP4, WebM, MOV, MKV files directly from your computer storage.';
  document.getElementById('fileInfoText').style.color = 'var(--text-muted)';
  document.getElementById('vidSubmitBtn').disabled = false;
  document.getElementById('vidSubmitBtn').textContent = 'Upload & Add Video';
}

function closeNewVideoModal() {
  document.getElementById('videoModal').classList.remove('active');
}

async function handleCreateVideo(e) {
  e.preventDefault();
  const alertBox = document.getElementById('videoModalAlert');
  alertBox.style.display = 'none';

  const fileInput = document.getElementById('vidFileInput');
  const urlInput = document.getElementById('vidUrl');
  const title = document.getElementById('vidTitle').value.trim();
  const duration = parseInt(document.getElementById('vidDuration').value) || 30;
  const order = parseInt(document.getElementById('vidOrder').value) || 1;
  const submitBtn = document.getElementById('vidSubmitBtn');

  if (!fileInput.files.length && !urlInput.value.trim()) {
    alertBox.textContent = 'Please choose a video file from your computer or provide a URL.';
    alertBox.style.display = 'block';
    return;
  }

  submitBtn.disabled = true;

  try {
    let res;
    if (fileInput.files.length > 0) {
      // Direct file upload from local storage
      submitBtn.textContent = 'Uploading Video File (Please Wait)...';
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('title', title);
      formData.append('duration_seconds', duration);
      formData.append('display_order', order);

      res = await fetch(`${API_BASE}/showcase/upload-video`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData
      });
    } else {
      // External URL upload
      submitBtn.textContent = 'Saving Video...';
      const payload = {
        title: title,
        video_url: urlInput.value.trim(),
        duration_seconds: duration,
        display_order: order,
        is_active: true
      };

      res = await fetch(`${API_BASE}/showcase/videos`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });
    }

    const data = await res.json();
    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to add video.';
      alertBox.style.display = 'block';
      submitBtn.disabled = false;
      submitBtn.textContent = 'Upload & Add Video';
      return;
    }

    closeNewVideoModal();
    fetchVideos();
    fetchDashboardData();
  } catch (err) {
    alertBox.textContent = 'Server connection error during video upload.';
    alertBox.style.display = 'block';
    submitBtn.disabled = false;
    submitBtn.textContent = 'Upload & Add Video';
  }
}

async function handleDeleteVideo(videoId, title) {
  if (!confirm(`Are you sure you want to delete video "${title}" from the playlist?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/showcase/videos/${videoId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Failed to delete video.');
      return;
    }

    fetchVideos();
    fetchDashboardData();
  } catch (err) {
    alert('Failed to connect to backend.');
  }
}

// -----------------------------------------------------------------------------
// TAB 3: Dynamic App Features
// -----------------------------------------------------------------------------
async function fetchFeatures() {
  try {
    const res = await fetch(`${API_BASE}/features/all`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;

    const features = await res.json();
    renderFeatures(features);
  } catch (err) {
    console.error('Failed to load features', err);
  }
}

function renderFeatures(features) {
  const tbody = document.getElementById('featuresTableBody');
  if (!features || features.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2.5rem; color:var(--text-muted);">No app features configured.<br><small style="color:var(--primary);">Click "Add New Feature" to add your first feature card.</small></td></tr>';
    return;
  }

  tbody.innerHTML = features.map(f => `
    <tr>
      <td><strong style="color:var(--text-main); font-family:var(--mono); font-weight:700;">#${f.display_order}</strong></td>
      <td><strong style="color:var(--text-main); font-weight:700; font-size:0.92rem;">${escapeHtml(f.title)}</strong></td>
      <td style="color:var(--text-secondary); font-size:0.88rem; line-height:1.45;">${escapeHtml(f.short_description)}</td>
      <td><code style="background:#f1f5f9; color:var(--primary); font-weight:600; font-size:0.8rem; padding:0.25rem 0.55rem; border-radius:6px; border:1px solid #e2e8f0;">${escapeHtml(f.icon_type)}</code></td>
      <td>
        <span class="status-badge ${f.is_active ? 'badge-success' : 'badge-failed'}">
          ${f.is_active ? 'Active' : 'Disabled'}
        </span>
      </td>
      <td>
        <button type="button" class="btn-xs-delete" onclick="handleDeleteFeature(${f.id}, '${escapeHtml(f.title)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Delete
        </button>
      </td>
    </tr>
  `).join('');
}

function openNewFeatureModal() {
  document.getElementById('featureModal').classList.add('active');
  document.getElementById('featureModalAlert').style.display = 'none';
}

function closeNewFeatureModal() {
  document.getElementById('featureModal').classList.remove('active');
}

async function handleCreateFeature(e) {
  e.preventDefault();
  const alertBox = document.getElementById('featureModalAlert');
  alertBox.style.display = 'none';

  const submitBtn = e.target.querySelector('button[type="submit"]');
  setButtonLoading(submitBtn, true, 'Saving Feature...');

  const payload = {
    title: document.getElementById('featTitle').value.trim(),
    short_description: document.getElementById('featDesc').value.trim(),
    icon_type: document.getElementById('featIcon').value,
    display_order: parseInt(document.getElementById('featOrder').value) || 1,
    is_active: true
  };

  try {
    const res = await fetch(`${API_BASE}/features`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    setButtonLoading(submitBtn, false);

    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to add feature.';
      alertBox.style.display = 'block';
      return;
    }

    closeNewFeatureModal();
    document.getElementById('newFeatureForm').reset();
    fetchFeatures();
    fetchDashboardData();
  } catch (err) {
    setButtonLoading(submitBtn, false);
    alertBox.textContent = 'Server connection error.';
    alertBox.style.display = 'block';
  }
}

async function handleDeleteFeature(featureId, title) {
  if (!confirm(`Are you sure you want to delete feature "${title}"?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/features/${featureId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Failed to delete feature.');
      return;
    }

    fetchFeatures();
    fetchDashboardData();
  } catch (err) {
    alert('Failed to connect to backend.');
  }
}

// -----------------------------------------------------------------------------
// TAB 3.5: Dynamic FAQs Management
// -----------------------------------------------------------------------------
async function fetchFaqs() {
  try {
    const res = await fetch(`${API_BASE}/faqs/all`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;

    const faqs = await res.json();
    renderFaqs(faqs);
  } catch (err) {
    console.error('Failed to load faqs', err);
  }
}

function renderFaqs(faqs) {
  const tbody = document.getElementById('faqsTableBody');
  if (!tbody) return;
  if (!faqs || faqs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 2.5rem; color:var(--text-muted);">No FAQs added yet.<br><small style="color:var(--primary);">Click "Add New FAQ" to add your first question.</small></td></tr>';
    return;
  }

  tbody.innerHTML = faqs.map(f => `
    <tr>
      <td><strong style="color:var(--text-main); font-family:var(--mono); font-weight:700;">#${f.display_order}</strong></td>
      <td><strong style="color:var(--text-main); font-weight:700; font-size:0.92rem;">${escapeHtml(f.question)}</strong></td>
      <td style="color:var(--text-secondary); font-size:0.88rem; line-height:1.45; max-width:380px;">${escapeHtml(f.answer)}</td>
      <td>
        <span class="status-badge ${f.is_active ? 'badge-success' : 'badge-failed'}">
          ${f.is_active ? 'Active' : 'Disabled'}
        </span>
      </td>
      <td>
        <button type="button" class="btn-xs-delete" onclick="handleDeleteFaq(${f.id}, '${escapeHtml(f.question)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Delete
        </button>
      </td>
    </tr>
  `).join('');
}

function openNewFaqModal() {
  document.getElementById('faqModal').classList.add('active');
  document.getElementById('faqModalAlert').style.display = 'none';
}

function closeNewFaqModal() {
  document.getElementById('faqModal').classList.remove('active');
}

async function handleCreateFaq(e) {
  e.preventDefault();
  const alertBox = document.getElementById('faqModalAlert');
  alertBox.style.display = 'none';

  const submitBtn = e.target.querySelector('button[type="submit"]');
  setButtonLoading(submitBtn, true, 'Saving FAQ...');

  const payload = {
    question: document.getElementById('faqQuestion').value.trim(),
    answer: document.getElementById('faqAnswer').value.trim(),
    display_order: parseInt(document.getElementById('faqOrder').value) || 1,
    is_active: true
  };

  try {
    const res = await fetch(`${API_BASE}/faqs`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    setButtonLoading(submitBtn, false);

    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to add FAQ.';
      alertBox.style.display = 'block';
      return;
    }

    closeNewFaqModal();
    document.getElementById('newFaqForm').reset();
    fetchFaqs();
    fetchDashboardData();
  } catch (err) {
    setButtonLoading(submitBtn, false);
    alertBox.textContent = 'Server connection error.';
    alertBox.style.display = 'block';
  }
}

async function handleDeleteFaq(faqId, question) {
  if (!confirm(`Are you sure you want to delete FAQ "${question}"?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/faqs/${faqId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Failed to delete FAQ.');
      return;
    }

    fetchFaqs();
    fetchDashboardData();
  } catch (err) {
    alert('Failed to connect to backend.');
  }
}

// -----------------------------------------------------------------------------
// TAB 4: Site Settings (Telegram Link)
// -----------------------------------------------------------------------------
async function fetchSiteSettings() {
  try {
    const res = await fetch(`${API_BASE}/site/config`);
    if (!res.ok) return;

    const data = await res.json();
    document.getElementById('telegramUrlInput').value = data.telegram_url || 'https://t.me/nextlevelcheat';
    document.getElementById('brandTitleInput').value = data.brand_title || 'बी - TOOL';
    document.getElementById('supportTextInput').value = data.support_text || 'Tools • Android / PC';
    document.getElementById('navBtn1TextInput').value = data.nav_btn1_text || 'Showcase';
    document.getElementById('navBtn1LinkInput').value = data.nav_btn1_link || '#showcase';
    document.getElementById('navBtn2TextInput').value = data.nav_btn2_text || 'Installation';
    document.getElementById('navBtn2LinkInput').value = data.nav_btn2_link || '#install';
    document.getElementById('navBtn3TextInput').value = data.nav_btn3_text || 'FAQ';
    document.getElementById('navBtn3LinkInput').value = data.nav_btn3_link || '#faq';
    document.getElementById('navTgBtnTextInput').value = data.nav_tg_btn_text || 'Join Telegram';
    document.getElementById('footerCopyTextInput').value = data.footer_copy_text || '© 2026 बी - TOOL. White + Chromium Charcoal Black Edition.';
    document.getElementById('showAppDetailsCardSelect').value = data.show_app_details_card !== undefined ? String(data.show_app_details_card) : 'true';
    document.getElementById('showTopNavSelect').value = data.show_top_nav !== undefined ? String(data.show_top_nav) : 'true';
    document.getElementById('showFooterSelect').value = data.show_footer !== undefined ? String(data.show_footer) : 'true';
    document.getElementById('showInstallGuideSelect').value = data.show_install_guide !== undefined ? String(data.show_install_guide) : 'true';
    document.getElementById('showFaqSectionSelect').value = data.show_faq_section !== undefined ? String(data.show_faq_section) : 'true';
    document.getElementById('showJoinTgBtnSelect').value = data.show_join_tg_btn !== undefined ? String(data.show_join_tg_btn) : 'true';
    document.getElementById('joinTgBtnTextInput').value = data.join_tg_btn_text || 'JOIN TG';
    document.getElementById('showDownloadBtnSelect').value = data.show_download_btn !== undefined ? String(data.show_download_btn) : 'true';
    document.getElementById('downloadBtnTextInput').value = data.download_btn_text || 'DOWNLOAD APK';
    document.getElementById('buyKeyBtnTextInput').value = data.buy_key_btn_text !== undefined ? data.buy_key_btn_text : 'Buy Key Yourself';
    document.getElementById('buyKeyBtnLinkInput').value = data.buy_key_btn_link || '';
    document.getElementById('customActionBtnTextInput').value = data.custom_action_btn_text || '';
    document.getElementById('customActionBtnLinkInput').value = data.custom_action_btn_link || '';
  } catch (err) {
    console.error('Failed to load site settings', err);
  }
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const alertBox = document.getElementById('settingsAlert');
  alertBox.style.display = 'none';

  const submitBtn = e.target.querySelector('button[type="submit"]');
  setButtonLoading(submitBtn, true, 'Updating Settings...');

  const payload = {
    telegram_url: document.getElementById('telegramUrlInput').value.trim(),
    brand_title: document.getElementById('brandTitleInput').value.trim(),
    support_text: document.getElementById('supportTextInput').value.trim(),
    nav_btn1_text: document.getElementById('navBtn1TextInput').value.trim(),
    nav_btn1_link: document.getElementById('navBtn1LinkInput').value.trim(),
    nav_btn2_text: document.getElementById('navBtn2TextInput').value.trim(),
    nav_btn2_link: document.getElementById('navBtn2LinkInput').value.trim(),
    nav_btn3_text: document.getElementById('navBtn3TextInput').value.trim(),
    nav_btn3_link: document.getElementById('navBtn3LinkInput').value.trim(),
    nav_tg_btn_text: document.getElementById('navTgBtnTextInput').value.trim(),
    footer_copy_text: document.getElementById('footerCopyTextInput').value.trim(),
    show_app_details_card: document.getElementById('showAppDetailsCardSelect').value,
    show_top_nav: document.getElementById('showTopNavSelect').value,
    show_footer: document.getElementById('showFooterSelect').value,
    show_install_guide: document.getElementById('showInstallGuideSelect').value,
    show_faq_section: document.getElementById('showFaqSectionSelect').value,
    show_join_tg_btn: document.getElementById('showJoinTgBtnSelect').value,
    join_tg_btn_text: document.getElementById('joinTgBtnTextInput').value.trim(),
    show_download_btn: document.getElementById('showDownloadBtnSelect').value,
    download_btn_text: document.getElementById('downloadBtnTextInput').value.trim(),
    buy_key_btn_text: document.getElementById('buyKeyBtnTextInput').value.trim(),
    buy_key_btn_link: document.getElementById('buyKeyBtnLinkInput').value.trim(),
    custom_action_btn_text: document.getElementById('customActionBtnTextInput').value.trim(),
    custom_action_btn_link: document.getElementById('customActionBtnLinkInput').value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/site/config`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    setButtonLoading(submitBtn, false);

    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to update settings.';
      alertBox.className = 'alert-box alert-danger';
      alertBox.style.display = 'block';
      return;
    }

    alertBox.textContent = 'Settings and navigation buttons updated successfully!';
    alertBox.className = 'alert-box alert-success';
    alertBox.style.display = 'block';
    fetchDashboardData();
  } catch (err) {
    setButtonLoading(submitBtn, false);
    alertBox.textContent = 'Server connection error.';
    alertBox.className = 'alert-box alert-danger';
    alertBox.style.display = 'block';
  }
}

// -----------------------------------------------------------------------------
// TAB 6: Unlock Account Tool
// -----------------------------------------------------------------------------
async function handleUnlock(e) {
  e.preventDefault();
  const alertBox = document.getElementById('unlockAlert');
  alertBox.style.display = 'none';

  const username = document.getElementById('unlockUsernameInput').value.trim();
  try {
    const res = await fetch(`${API_BASE}/admin/unlock-account/${encodeURIComponent(username)}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    const data = await res.json();
    alertBox.textContent = data.message || data.detail;
    alertBox.className = res.ok ? 'alert-box alert-success' : 'alert-box alert-danger';
    alertBox.style.display = 'block';
  } catch (err) {
    alertBox.textContent = 'Failed to execute unlock command.';
    alertBox.className = 'alert-box alert-danger';
    alertBox.style.display = 'block';
  }
}

// -----------------------------------------------------------------------------
// TAB 7: Real-Time Traffic & Intrusion Graph (Canvas 2D)
// -----------------------------------------------------------------------------
async function fetchAnalyticsData() {
  try {
    const res = await fetch(`${API_BASE}/security-center/traffic-metrics`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;
    const data = await res.json();

    const totalReqEl = document.getElementById('graphTotalReq');
    const totalDlEl = document.getElementById('graphTotalDl');
    const blockedEl = document.getElementById('graphBlocked');
    if (totalReqEl) totalReqEl.textContent = Number(data.total_requests || 0).toLocaleString();
    if (totalDlEl) totalDlEl.textContent = Number(data.total_downloads || 0).toLocaleString();
    if (blockedEl) blockedEl.textContent = Number(data.total_blocked_attacks || 0).toLocaleString();

    renderTrafficCanvas(data.timeline || []);
  } catch (err) {
    console.error('Failed to load traffic metrics:', err);
  }
}

function renderTrafficCanvas(timeline) {
  const canvas = document.getElementById('trafficCanvas');
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * (window.devicePixelRatio || 1);
  canvas.height = rect.height * (window.devicePixelRatio || 1);

  const ctx = canvas.getContext('2d');
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

  const width = rect.width;
  const height = rect.height;

  ctx.clearRect(0, 0, width, height);

  if (!timeline || timeline.length === 0) {
    ctx.fillStyle = '#94a3b8';
    ctx.font = '13px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Collecting real-time traffic statistics...', width / 2, height / 2);
    return;
  }

  const paddingLeft = 35;
  const paddingBottom = 25;
  const graphW = width - paddingLeft - 15;
  const graphH = height - paddingBottom - 15;

  let maxReq = 10;
  timeline.forEach(p => {
    if (p.requests > maxReq) maxReq = p.requests;
    if (p.downloads > maxReq) maxReq = p.downloads;
  });
  maxReq = Math.ceil(maxReq * 1.25);

  // Draw grid lines
  ctx.strokeStyle = '#f1f5f9';
  ctx.lineWidth = 1;
  const gridLines = 4;
  for (let i = 0; i <= gridLines; i++) {
    const y = 15 + (graphH / gridLines) * i;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - 15, y);
    ctx.stroke();

    const val = Math.round(maxReq - (maxReq / gridLines) * i);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(val, paddingLeft - 6, y + 3);
  }

  const stepX = graphW / (timeline.length - 1 || 1);

  // Draw Requests Line & Gradient
  ctx.beginPath();
  timeline.forEach((pt, idx) => {
    const x = paddingLeft + idx * stepX;
    const y = 15 + graphH - (pt.requests / maxReq) * graphH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = '#4f46e5';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Requests Area Gradient Fill
  ctx.lineTo(paddingLeft + (timeline.length - 1) * stepX, 15 + graphH);
  ctx.lineTo(paddingLeft, 15 + graphH);
  ctx.closePath();
  const gradReq = ctx.createLinearGradient(0, 15, 0, 15 + graphH);
  gradReq.addColorStop(0, 'rgba(79, 70, 229, 0.25)');
  gradReq.addColorStop(1, 'rgba(79, 70, 229, 0.0)');
  ctx.fillStyle = gradReq;
  ctx.fill();

  // Draw Downloads Line
  ctx.beginPath();
  timeline.forEach((pt, idx) => {
    const x = paddingLeft + idx * stepX;
    const y = 15 + graphH - (pt.downloads / maxReq) * graphH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = '#10b981';
  ctx.lineWidth = 2;
  ctx.stroke();

  // X Axis labels (timestamps)
  ctx.fillStyle = '#64748b';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  const labelInterval = Math.max(1, Math.floor(timeline.length / 6));
  timeline.forEach((pt, idx) => {
    if (idx % labelInterval === 0 || idx === timeline.length - 1) {
      const x = paddingLeft + idx * stepX;
      ctx.fillText(pt.hour || '', x, height - 6);
    }
  });
}

// -----------------------------------------------------------------------------
// TAB 8: SEO Settings Handler
// -----------------------------------------------------------------------------
async function fetchSeoSettings() {
  try {
    const res = await fetch(`${API_BASE}/security-center/seo`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;
    const data = await res.json();
    if (!data) return;

    if (document.getElementById('seoMetaTitle')) document.getElementById('seoMetaTitle').value = data.meta_title || '';
    if (document.getElementById('seoMetaDesc')) document.getElementById('seoMetaDesc').value = data.meta_description || '';
    if (document.getElementById('seoMetaKeywords')) document.getElementById('seoMetaKeywords').value = data.meta_keywords || '';
    if (document.getElementById('seoCanonical')) document.getElementById('seoCanonical').value = data.canonical_url || '';
    if (document.getElementById('seoAuthor')) document.getElementById('seoAuthor').value = data.author || '';
    if (document.getElementById('seoGoogleVerify')) document.getElementById('seoGoogleVerify').value = data.google_verification || '';
  } catch (err) {
    console.error('Failed to load SEO settings:', err);
  }
}

async function handleSaveSeo(e) {
  e.preventDefault();
  const alertBox = document.getElementById('seoAlert');
  alertBox.style.display = 'none';

  const submitBtn = e.target.querySelector('button[type="submit"]');
  setButtonLoading(submitBtn, true, 'Saving SEO...');

  const payload = {
    meta_title: document.getElementById('seoMetaTitle').value.trim(),
    meta_description: document.getElementById('seoMetaDesc').value.trim(),
    meta_keywords: document.getElementById('seoMetaKeywords').value.trim(),
    canonical_url: document.getElementById('seoCanonical').value.trim(),
    author: document.getElementById('seoAuthor').value.trim(),
    google_verification: document.getElementById('seoGoogleVerify').value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/security-center/seo`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    setButtonLoading(submitBtn, false);

    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to save SEO settings.';
      alertBox.className = 'alert-box alert-danger';
      alertBox.style.display = 'block';
      return;
    }

    alertBox.textContent = 'SEO settings saved and deployed to live website!';
    alertBox.className = 'alert-box alert-success';
    alertBox.style.display = 'block';
  } catch (err) {
    setButtonLoading(submitBtn, false);
    alertBox.textContent = 'Server connection error.';
    alertBox.className = 'alert-box alert-danger';
    alertBox.style.display = 'block';
  }
}

// -----------------------------------------------------------------------------
// TAB 9: High Risk Telegram Bot & Backup Handlers
// -----------------------------------------------------------------------------
async function fetchTelegramConfig() {
  try {
    const res = await fetch(`${API_BASE}/security-center/telegram-config`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return;
    const data = await res.json();
    if (!data) return;

    if (document.getElementById('tgBotToken')) document.getElementById('tgBotToken').value = data.bot_token || '';
    if (document.getElementById('tgOwnerChatId')) document.getElementById('tgOwnerChatId').value = data.owner_chat_id || '';
  } catch (err) {
    console.error('Failed to load Telegram bot configuration:', err);
  }
}

async function handleSaveTelegramBot(e) {
  e.preventDefault();
  const alertBox = document.getElementById('highRiskAlert');
  alertBox.style.display = 'none';

  const submitBtn = e.target.querySelector('button[type="submit"]');
  setButtonLoading(submitBtn, true, 'Connecting Watchdog...');

  const payload = {
    bot_token: document.getElementById('tgBotToken').value.trim(),
    owner_chat_id: document.getElementById('tgOwnerChatId').value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/security-center/telegram-config`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    setButtonLoading(submitBtn, false);

    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to save Telegram watchdog settings.';
      alertBox.className = 'alert-box alert-danger';
      alertBox.style.display = 'block';
      return;
    }

    alertBox.textContent = 'Telegram Watchdog activated! Attack alerts & weekly backups enabled.';
    alertBox.className = 'alert-box alert-success';
    alertBox.style.display = 'block';
  } catch (err) {
    setButtonLoading(submitBtn, false);
    alertBox.textContent = 'Server connection error.';
    alertBox.className = 'alert-box alert-danger';
    alertBox.style.display = 'block';
  }
}

async function handleTriggerBackupNow() {
  const alertBox = document.getElementById('highRiskAlert');
  alertBox.style.display = 'none';

  if (!confirm('Export complete PostgreSQL database and send directly to your Telegram bot?')) {
    return;
  }

  try {
    alertBox.textContent = 'Generating database dump and uploading to Telegram...';
    alertBox.className = 'alert-box alert-info';
    alertBox.style.display = 'block';

    const res = await fetch(`${API_BASE}/security-center/trigger-backup-now`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const data = await res.json();

    if (!res.ok) {
      alertBox.textContent = data.detail || 'Failed to dispatch backup.';
      alertBox.className = 'alert-box alert-danger';
      alertBox.style.display = 'block';
      return;
    }

    alertBox.textContent = data.message || 'Database export sent to Telegram successfully!';
    alertBox.className = 'alert-box alert-success';
    alertBox.style.display = 'block';
  } catch (err) {
    alertBox.textContent = 'Failed to execute instant backup.';
    alertBox.className = 'alert-box alert-danger';
    alertBox.style.display = 'block';
  }
}

// -----------------------------------------------------------------------------
// Tab Switching (CRM Left Sidebar)
// -----------------------------------------------------------------------------
const tabTitles = {
  releasesTab: 'Release Management (APK)',
  videoTab: 'Showcase Video Playlist',
  featuresTab: 'Dynamic App Features',
  faqsTab: 'Website FAQs Management',
  analyticsTab: 'Real-Time Traffic & Intrusion Graph',
  seoTab: 'Advanced SEO Engine',
  highRiskTab: 'HIGH RISK: Telegram Security Watchdog & Weekly Backup',
  settingsTab: 'Global Settings & Navigation Bar Buttons',
  auditsTab: 'Security & Access Audits',
  unlockTab: 'Admin Account Unlock Tool'
};

function switchTab(tabId) {
  // Save current active tab so reload stays on the exact same page
  localStorage.setItem('nlc_admin_active_tab', tabId);

  // Hide all sections
  document.querySelectorAll('.panel-section').forEach(el => el.style.display = 'none');

  // Remove active from all sidebar buttons
  document.querySelectorAll('.sidebar-btn').forEach(btn => btn.classList.remove('active'));

  // Show target section
  const targetSection = document.getElementById(tabId);
  if (targetSection) {
    targetSection.style.display = 'flex';
  }

  // Set active on matching sidebar button
  const activeBtn = document.querySelector(`.sidebar-btn[data-tab="${tabId}"]`);
  if (activeBtn) {
    activeBtn.classList.add('active');
  }

  // Update topbar title
  const pageTitleEl = document.getElementById('pageTitle');
  if (pageTitleEl && tabTitles[tabId]) {
    pageTitleEl.textContent = tabTitles[tabId];
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById('crmSidebar');
  if (sidebar && sidebar.classList.contains('open')) {
    sidebar.classList.remove('open');
  }

  // Fetch relevant tab data
  if (tabId === 'auditsTab') {
    fetchDashboardData();
  } else if (tabId === 'videoTab') {
    fetchVideos();
  } else if (tabId === 'featuresTab') {
    fetchFeatures();
  } else if (tabId === 'settingsTab') {
    fetchSiteSettings();
  } else if (tabId === 'releasesTab') {
    fetchReleases();
  } else if (tabId === 'analyticsTab') {
    fetchAnalyticsData();
  } else if (tabId === 'seoTab') {
    fetchSeoSettings();
  } else if (tabId === 'highRiskTab') {
    fetchTelegramConfig();
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById('crmSidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function (m) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
  });
}
