# NEXT LEVEL CHEAT / बी - TOOL - COMPLETE API DOCUMENTATION (POSTMAN / CURL READY)
Base URL: `http://localhost:8000` (or `https://your-domain.com`)

---

## 1. Authentication (Admin Access & Security)

### 1.1 Login & Get JWT Access Token
- **Method**: `POST`
- **URL**: `/api/v1/auth/login`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "username": "admin",
  "password": "your_secure_password"
}
```
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "admin": {
    "username": "admin",
    "role": "superadmin"
  }
}
```

### 1.2 Get Current Admin Profile
- **Method**: `GET`
- **URL**: `/api/v1/auth/me`
- **Headers**: `Authorization: Bearer <TOKEN>`

### 1.3 Change Admin Password
- **Method**: `POST`
- **URL**: `/api/v1/auth/change-password`
- **Headers**: `Authorization: Bearer <TOKEN>`, `Content-Type: application/json`
- **Body**:
```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

---

## 2. Global Site Configuration (Navbar, Brand, Telegram, Footer)

### 2.1 Get Active Site Config (Public - Used by Frontend)
- **Method**: `GET`
- **URL**: `/api/v1/site/config`
- **Response**:
```json
{
  "brand_title": "बी - TOOL",
  "support_text": "Tools • Android / PC",
  "telegram_url": "https://t.me/nextlevelcheat",
  "nav_btn1_text": "Showcase",
  "nav_btn1_link": "#showcase",
  "nav_btn2_text": "Installation",
  "nav_btn2_link": "#install",
  "nav_btn3_text": "FAQ",
  "nav_btn3_link": "#faq",
  "nav_tg_btn_text": "Join Telegram",
  "footer_copy_text": "© 2026 बी - TOOL. White + Chromium Charcoal Black Edition."
}
```

### 2.2 Update Site Config (Admin)
- **Method**: `PUT`
- **URL**: `/api/v1/site/config`
- **Headers**: `Authorization: Bearer <TOKEN>`, `Content-Type: application/json`
- **Body**: (Send fields to update from above)

---

## 3. Releases & APK Downloads

### 3.1 Get Latest Active APK Release (Public)
- **Method**: `GET`
- **URL**: `/api/v1/releases/latest`
- **Response**:
```json
{
  "id": 1,
  "version": "v2.4.0",
  "title": "बी - TOOL Final Stable Build",
  "file_size_mb": 45.2,
  "download_count": 1420,
  "min_android_version": "Android 8.0+",
  "is_active": true
}
```

### 3.2 Direct Download APK (Public - Auto Increments Counter)
- **Method**: `GET`
- **URL**: `/api/v1/downloads/apk`
- **Note**: Redirects or streams the active APK binary to the user and logs download telemetry.

### 3.3 Upload APK Release (Admin)
- **Method**: `POST`
- **URL**: `/api/v1/releases/upload-apk`
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: (.apk binary file)
  - `title`: `बी - TOOL Final Stable`
  - `version`: `v2.4.0`
  - `min_android_version`: `Android 8.0+`
  - `changelog`: `Added Anti-Ban bypass and speed booster`

### 3.4 List All Releases (Admin)
- **Method**: `GET`
- **URL**: `/api/v1/releases`
- **Headers**: `Authorization: Bearer <TOKEN>`

### 3.5 Delete Release
- **Method**: `DELETE`
- **URL**: `/api/v1/releases/{release_id}`
- **Headers**: `Authorization: Bearer <TOKEN>`

---

## 4. Protected Showcase Video & Playlist

### 4.1 List Showcase Videos (Public - Direct Paths Masked)
- **Method**: `GET`
- **URL**: `/api/v1/showcase/videos`
- **Response**:
```json
[
  {
    "id": 6,
    "title": "Gameplay Showcase",
    "video_url": "/api/v1/showcase/stream/6",
    "duration_seconds": 30,
    "display_order": 1,
    "is_active": true
  }
]
```

### 4.2 Stream Video (Protected HTTP 206 Partial Content)
- **Method**: `GET`
- **URL**: `/api/v1/showcase/stream/{video_id}`
- **Headers**: `Range: bytes=0-` (optional, supported for scrubbing)
- **Security**: Direct server disk paths are completely hidden.

### 4.3 Upload Local Video (Admin)
- **Method**: `POST`
- **URL**: `/api/v1/showcase/upload-video`
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: (.mp4 / .webm video file)
  - `title`: `Zero Recoil Showcase`
  - `duration_seconds`: `30`
  - `display_order`: `1`

### 4.4 Delete Showcase Video
- **Method**: `DELETE`
- **URL**: `/api/v1/showcase/videos/{video_id}`
- **Headers**: `Authorization: Bearer <TOKEN>`

---

## 5. Dynamic App Features

### 5.1 List Features (Public)
- **Method**: `GET`
- **URL**: `/api/v1/features`

### 5.2 Create New Feature (Admin)
- **Method**: `POST`
- **URL**: `/api/v1/features`
- **Headers**: `Authorization: Bearer <TOKEN>`, `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Anti-Ban Shield",
  "short_description": "Scrambles device fingerprints and bypasses server telemetry.",
  "icon_type": "shield",
  "display_order": 1,
  "is_active": true
}
```

### 5.3 Delete Feature
- **Method**: `DELETE`
- **URL**: `/api/v1/features/{feature_id}`
- **Headers**: `Authorization: Bearer <TOKEN>`

---

## 6. Dynamic FAQs Management

### 6.1 List Active FAQs (Public)
- **Method**: `GET`
- **URL**: `/api/v1/faqs/active`

### 6.2 Create New FAQ (Admin)
- **Method**: `POST`
- **URL**: `/api/v1/faqs`
- **Headers**: `Authorization: Bearer <TOKEN>`, `Content-Type: application/json`
- **Body**:
```json
{
  "question": "Is root required for बी - TOOL?",
  "answer": "No root is required. It works seamlessly in virtualized space.",
  "display_order": 1
}
```

### 6.3 Delete FAQ
- **Method**: `DELETE`
- **URL**: `/api/v1/faqs/{faq_id}`
- **Headers**: `Authorization: Bearer <TOKEN>`

---

## 7. High Risk & Telegram Watchdog (Security, Backup, SEO, Traffic)

### 7.1 Get Telegram Config
- **Method**: `GET`
- **URL**: `/api/v1/security-center/telegram-config`
- **Headers**: `Authorization: Bearer <TOKEN>`

### 7.2 Save Telegram Bot & Start Watchdog (Auto-Verified)
- **Method**: `POST`
- **URL**: `/api/v1/security-center/telegram-config`
- **Headers**: `Authorization: Bearer <TOKEN>`, `Content-Type: application/json`
- **Body**:
```json
{
  "bot_token": "8886743296:AAHVRwYx6AUkrJ3trt5m8lHNqu-EwRYc4WU",
  "owner_chat_id": "8816802036"
}
```

### 7.3 Trigger 100% Full VPS Disaster Recovery Backup Now
- **Method**: `POST`
- **URL**: `/api/v1/security-center/trigger-backup-now`
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Response**:
```json
{
  "status": "success",
  "delivered": true,
  "backup_file": "NEXTLEVEL_FULL_VPS_BACKUP_20261030_171930.zip",
  "file_size_mb": 3.64,
  "message": "Complete system & media archive dispatched to your Telegram chat!"
}
```

### 7.4 Real-time Traffic Graph & Telemetry Metrics
- **Method**: `GET`
- **URL**: `/api/v1/security-center/traffic-metrics`
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Response**: Total requests, downloads, blocked attacks, and 24-hr hourly traffic timeline.

### 7.5 SEO Engine Settings (Meta tags, Title, Google Verification)
- **Method**: `GET` / `POST`
- **URL**: `/api/v1/security-center/seo`
- **Headers (for POST)**: `Authorization: Bearer <TOKEN>`, `Content-Type: application/json`
- **Body**:
```json
{
  "meta_title": "बी - TOOL | High-Precision Mobile & PC Utilities",
  "meta_description": "Official safe utilities, zero recoil and anti-ban shield for Android and PC.",
  "meta_keywords": "बी tool, gaming tools, zero recoil, anti-ban, apk",
  "canonical_url": "https://yourdomain.com/",
  "author": "बी - TOOL Team",
  "google_verification": "google-site-verification=xxxx"
}
```

---

## 8. Admin Security & Dashboard Audits

### 8.1 Dashboard Counters & Security Logs
- **Method**: `GET`
- **URL**: `/api/v1/admin/dashboard-stats`
- **Headers**: `Authorization: Bearer <TOKEN>`

### 8.2 Security Audit Trail
- **Method**: `GET`
- **URL**: `/api/v1/admin/audit-logs`
- **Headers**: `Authorization: Bearer <TOKEN>`

### 8.3 Unlock Admin Account (Clear brute force lockout)
- **Method**: `POST`
- **URL**: `/api/v1/admin/unlock-account/{username}`
- **Headers**: `Authorization: Bearer <TOKEN>`

---

## 9. Realtime WebSocket Sync
- **Protocol**: `ws://` or `wss://`
- **URL**: `/api/v1/ws/sync`
- **Events Broadcasted**:
  - `CONFIG_UPDATED`
  - `RELEASE_UPDATED`
  - `VIDEOS_UPDATED`
  - `FEATURES_UPDATED`
  - `FAQS_UPDATED`

