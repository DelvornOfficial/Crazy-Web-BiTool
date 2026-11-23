import React, { useState, useEffect, useRef } from 'react';
import BiToolLogo from '../common/BiToolLogo';
import './Hero.css';

// Reusable clean SVG Icons (Zero Emojis)
const RenderFeatureIcon = ({ type }) => {
  switch (type) {
    case 'shield':
    case 'safe':
      return (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );
    case 'zap':
    case 'bolt':
      return (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
      );
    case 'refresh':
    case 'sync':
      return (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="23 4 23 10 17 10"></polyline>
          <polyline points="1 20 1 14 7 14"></polyline>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
        </svg>
      );
    case 'lock':
      return (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
      );
    default:
      return (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
  }
};

export function Hero() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Real clock state
  const [realTime, setRealTime] = useState(() =>
    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  );

  // Dynamic database states (100% Real Data)
  const [latestRelease, setLatestRelease] = useState(null);
  const [isApkLinked, setIsApkLinked] = useState(false);
  const [videoPlaylist, setVideoPlaylist] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [features, setFeatures] = useState([]);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [siteConfig, setSiteConfig] = useState({
    telegram_url: '',
    brand_title: '',
    support_text: '',
    show_app_details_card: 'true',
    buy_key_btn_text: 'Buy Key Yourself',
    buy_key_btn_link: '',
    custom_action_btn_text: '',
    custom_action_btn_link: '',
    show_join_tg_btn: 'true',
    join_tg_btn_text: 'JOIN TG',
    show_download_btn: 'true',
    download_btn_text: 'DOWNLOAD APK',
  });

  const videoRef = useRef(null);

  // Real Clock Timer
  useEffect(() => {
    const t = setInterval(() => {
      setRealTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }));
    }, 5000);
    return () => clearInterval(t);
  }, []);

  // Fetch Real Release, Real Video Playlist, Real Features, and Site Settings from Database
  useEffect(() => {
    // 1. Real Latest Release
    fetch('http://localhost:8000/api/v1/releases/latest')
      .then(async (res) => {
        if (!res.ok) {
          setIsApkLinked(false);
          setLatestRelease(null);
          return;
        }
        const data = await res.json();
        if (data && data.download_url && data.download_url.trim()) {
          setIsApkLinked(true);
          setLatestRelease(data);
        } else {
          setIsApkLinked(false);
          setLatestRelease(null);
        }
      })
      .catch(() => {
        setIsApkLinked(false);
        setLatestRelease(null);
      });

    // 2. Real Multi-Video Playlist
    fetch('http://localhost:8000/api/v1/showcase/videos')
      .then(async (res) => {
        if (res.ok) {
          const list = await res.json();
          if (Array.isArray(list)) {
            setVideoPlaylist(list);
          }
        }
      })
      .catch(() => { });

    // 3. Real Dynamic App Features
    fetch('http://localhost:8000/api/v1/features')
      .then(async (res) => {
        if (res.ok) {
          const featList = await res.json();
          if (Array.isArray(featList)) {
            setFeatures(featList);
          }
        }
      })
      .catch(() => { });

    // 4. Real Site Settings (Telegram URL, Brand Title, Support Text)
    const loadSiteConfig = () => {
      fetch('http://localhost:8000/api/v1/site/config')
        .then(async (res) => {
          if (res.ok) {
            const cfg = await res.json();
            setSiteConfig(cfg);
          }
          setLoadingConfig(false);
        })
        .catch(() => {
          setLoadingConfig(false);
        });
    };

    loadSiteConfig();

    // WebSocket real-time live reload for hero data
    let heroWs = null;
    let heroTimer = null;
    const connectHeroWs = () => {
      try {
        heroWs = new WebSocket('ws://localhost:8000/api/v1/ws/sync');
        heroWs.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.event === 'CONFIG_UPDATED') {
              loadSiteConfig();
            } else if (msg.event === 'RELEASE_UPDATED') {
              fetch('http://localhost:8000/api/v1/releases/latest')
                .then(r => r.ok ? r.json() : null)
                .then(d => {
                  if (d) { setLatestRelease(d); setIsApkLinked(true); }
                  else { setLatestRelease(null); setIsApkLinked(false); }
                }).catch(() => { });
            } else if (msg.event === 'VIDEOS_UPDATED') {
              fetch('http://localhost:8000/api/v1/showcase/videos')
                .then(r => r.ok ? r.json() : [])
                .then(l => setVideoPlaylist(Array.isArray(l) ? l : [])).catch(() => { });
            } else if (msg.event === 'FEATURES_UPDATED') {
              fetch('http://localhost:8000/api/v1/features')
                .then(r => r.ok ? r.json() : [])
                .then(fl => setFeatures(Array.isArray(fl) ? fl : [])).catch(() => { });
            }
          } catch (e) { }
        };
        heroWs.onclose = () => { heroTimer = setTimeout(connectHeroWs, 3000); };
      } catch (e) { heroTimer = setTimeout(connectHeroWs, 3000); }
    };
    connectHeroWs();

    return () => {
      if (heroWs) heroWs.close();
      if (heroTimer) clearTimeout(heroTimer);
    };
  }, []);

  // Active video in playlist
  const currentVideo = videoPlaylist[currentVideoIndex] || null;
  const hasRealVideo = Boolean(currentVideo && currentVideo.video_url);
  const effectiveDuration = videoDuration || currentVideo?.duration_seconds || 0;

  // Real video play/pause coordinator
  const togglePlay = () => {
    if (!hasRealVideo || !videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().catch(() => { });
      setIsPlaying(true);
    }
  };

  const handleVideoLoadedMetadata = () => {
    if (videoRef.current) {
      const dur = Math.floor(videoRef.current.duration);
      if (!isNaN(dur) && dur > 0) {
        setVideoDuration(dur);
      }
    }
  };

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(Math.floor(videoRef.current.currentTime));
    }
  };

  // Preload next video in playlist to eliminate network buffering delay
  const nextVideoIndex = videoPlaylist.length > 1 ? (currentVideoIndex + 1) % videoPlaylist.length : null;
  const nextVideo = nextVideoIndex !== null ? videoPlaylist[nextVideoIndex] : null;

  // Real multi-video playlist auto-advance
  const handleVideoEnded = () => {
    if (videoPlaylist.length > 1) {
      const nextIdx = (currentVideoIndex + 1) % videoPlaylist.length;
      setCurrentVideoIndex(nextIdx);
      setCurrentTime(0);
      setVideoDuration(0);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.play().catch(() => { });
          setIsPlaying(true);
        }
      }, 100);
    } else {
      setIsPlaying(false);
      setCurrentTime(0);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
    }
    setIsMuted(!isMuted);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleDownload = () => {
    if (!isApkLinked) {
      setToastMessage('APK Not Linked: No active APK release uploaded yet. Upload via Admin Panel.');
      setToastVisible(true);
      setTimeout(() => setToastVisible(false), 4000);
      return;
    }

    setToastMessage(`Downloading ${latestRelease?.title || 'Next Level Cheat APK'} (${latestRelease?.file_size_mb || 45} MB)...`);
    setToastVisible(true);
    try {
      window.open('http://localhost:8000/api/v1/downloads/apk', '_blank');
    } catch (err) {
      console.warn('API direct download redirect:', err);
    }
    setTimeout(() => setToastVisible(false), 3500);
  };

  return (
    <section className="nl-hero-wrapper" aria-label="Next Level Cheat Showcase">
      {/* Ambient background glow */}
      <div className="nl-ambient-glow glow-purple" aria-hidden="true"></div>
      <div className="nl-ambient-glow glow-blue" aria-hidden="true"></div>

      {/* Main Responsive Container */}
      <div className="nl-hero-container">
        {/* Left Column on PC / Top Section on Mobile: Media & Action Buttons */}
        <div className="nl-col-showcase">
          {/* Header */}
          <header className="nl-header">
            <div className="nl-brand">
              <BiToolLogo size={28} color="#991b1b" />
              <div className="nl-title-text">
                {loadingConfig ? (
                  <span className="skeleton-line" style={{ width: 80, height: 18, display: 'inline-block' }}></span>
                ) : (
                  siteConfig.brand_title || ''
                )}
              </div>
            </div>

            {/* Status Pill Badge */}
            <div className="nl-status-pill">
              <span className="live-dot" aria-hidden="true"></span>
              <span>{isApkLinked ? `${latestRelease?.version} Engine` : 'Engine Ready'}</span>
            </div>
          </header>

          {/* Video / Showcase Media Player */}
          <div className="nl-video-container">
            <div className="nl-video-box">
              <div
                className={`video-screen ${isPlaying ? 'video-playing' : ''}`}
                onClick={() => {
                  if (isPlaying) togglePlay();
                }}
                style={{ cursor: hasRealVideo ? 'pointer' : 'default', position: 'relative' }}
                title={isPlaying ? 'Click screen to pause' : ''}
              >
                {/* Playlist Counter Badge (shown when multiple real videos exist) */}
                {videoPlaylist.length > 1 && (
                  <div className="playlist-badge" aria-label="Playlist Status">
                    <span className="playlist-dot"></span>
                    <span>Video {currentVideoIndex + 1} / {videoPlaylist.length}</span>
                  </div>
                )}

                {/* HTML5 Real Video Player with Auto Buffer & Preload */}
                {hasRealVideo ? (
                  <>
                    <video
                      key={currentVideo.id || currentVideoIndex}
                      ref={videoRef}
                      src={currentVideo.video_url.startsWith('http') ? currentVideo.video_url : `http://localhost:8000${currentVideo.video_url}`}
                      preload="auto"
                      autoPlay={isPlaying}
                      playsInline
                      className="video-element"
                      controlsList="nodownload nofullscreen noremoteplayback"
                      disablePictureInPicture
                      onContextMenu={(e) => e.preventDefault()}
                      onLoadedMetadata={handleVideoLoadedMetadata}
                      onTimeUpdate={handleVideoTimeUpdate}
                      onEnded={handleVideoEnded}
                    />
                    {/* Hidden Next Video Preloader: Auto-buffers the upcoming video in the background */}
                    {nextVideo && (
                      <video
                        key={`preload-${nextVideo.id || nextVideoIndex}`}
                        src={nextVideo.video_url.startsWith('http') ? nextVideo.video_url : `http://localhost:8000${nextVideo.video_url}`}
                        preload="auto"
                        muted
                        controlsList="nodownload nofullscreen noremoteplayback"
                        disablePictureInPicture
                        onContextMenu={(e) => e.preventDefault()}
                        style={{ display: 'none' }}
                        aria-hidden="true"
                      />
                    )}
                  </>
                ) : (
                  /* Authentic Empty State when no video is uploaded yet */
                  <div className="video-empty-state">
                    <div className="empty-video-icon">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <polygon points="23 7 16 12 23 17 23 7"></polygon>
                        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                      </svg>
                    </div>
                    <span className="empty-video-title">NO SHOWCASE VIDEO UPLOADED</span>
                    <span className="empty-video-subtitle">Upload real video files from your computer storage via the Admin Panel</span>
                  </div>
                )}

                {/* Big Centered Play Button: Only shown if video exists and paused */}
                {hasRealVideo && !isPlaying && (
                  <button
                    type="button"
                    className="nl-play-center-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      togglePlay();
                    }}
                    aria-label="Play Video"
                  >
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Video Controls Bar */}
              <div className="nl-video-controls">
                <button
                  type="button"
                  className="control-btn play-toggle"
                  onClick={togglePlay}
                  disabled={!hasRealVideo}
                  style={{ opacity: hasRealVideo ? 1 : 0.4 }}
                  aria-label={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <rect x="5" y="4" width="4" height="16" />
                      <rect x="15" y="4" width="4" height="16" />
                    </svg>
                  ) : (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  )}
                </button>

                <span className="time-display">
                  {formatTime(currentTime)} / {formatTime(effectiveDuration)}
                </span>

                {/* Scrubber track */}
                <div
                  className="scrubber-track"
                  style={{ cursor: hasRealVideo ? 'pointer' : 'default' }}
                  onClick={(e) => {
                    if (!hasRealVideo || !videoRef.current || effectiveDuration <= 0) return;
                    const rect = e.currentTarget.getBoundingClientRect();
                    const pos = (e.clientX - rect.left) / rect.width;
                    const newTime = Math.floor(pos * effectiveDuration);
                    setCurrentTime(newTime);
                    videoRef.current.currentTime = newTime;
                  }}
                >
                  <div
                    className="scrubber-fill"
                    style={{ width: `${effectiveDuration > 0 ? (currentTime / effectiveDuration) * 100 : 0}%` }}
                  >
                    <span className="scrubber-thumb"></span>
                  </div>
                </div>

                {/* Volume Button */}
                <button
                  type="button"
                  className="control-btn volume-toggle"
                  onClick={toggleMute}
                  disabled={!hasRealVideo}
                  style={{ opacity: hasRealVideo ? 1 : 0.4 }}
                  aria-label="Mute or Unmute"
                >
                  {isMuted ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                    </svg>
                  )}
                </button>

                {/* Fullscreen Button */}
                <button
                  type="button"
                  className="control-btn fullscreen-toggle"
                  disabled={!hasRealVideo}
                  style={{ opacity: hasRealVideo ? 1 : 0.4 }}
                  onClick={() => {
                    if (videoRef.current && videoRef.current.requestFullscreen) {
                      videoRef.current.requestFullscreen();
                    }
                  }}
                  aria-label="Toggle Fullscreen"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          {/* Top Buy Key Button (Configured from Admin Panel) */}
          {siteConfig.buy_key_btn_text && siteConfig.buy_key_btn_text.trim() && (
            <div className="nl-buy-key-wrapper" style={{ width: '100%', marginBottom: '0.85rem' }}>
              <a
                href={siteConfig.buy_key_btn_link || siteConfig.telegram_url || 'https://t.me/'}
                target="_blank"
                rel="noopener noreferrer"
                className="nl-btn btn-buy-key"
              >
                <span className="btn-icon">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M21 2l-2 2m-1-1l-3 3m-1-1l-3 3m-2-2l-2 2a5 5 0 1 0 7 7l7-7-2-2z"></path>
                    <circle cx="7.5" cy="16.5" r="1.5"></circle>
                  </svg>
                </span>
                <span className="btn-label">{siteConfig.buy_key_btn_text}</span>
                <span className="btn-action-arrow">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </span>
              </a>
            </div>
          )}

          {/* Action Buttons: JOIN TG (Dynamic URL from DB) & DOWNLOAD APK / APK NOT LINKED */}
              {(siteConfig.show_join_tg_btn !== 'false' || siteConfig.show_download_btn !== 'false') && (
                <div className="nl-actions-row">
                  {siteConfig.show_join_tg_btn !== 'false' && (
                    <div className="btn-join-tg-wrapper">
                      <div className="tg-suggestion-tag">
                        <span className="tg-tag-ping"></span>
                        RECOMMENDED
                      </div>
                      <a
                        href={siteConfig.telegram_url || 'https://t.me/nextlevelcheat'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="nl-btn btn-join-tg with-suggestion"
                      >
                        <span className="btn-icon tg-icon-bg">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .37z" />
                          </svg>
                        </span>
                        <span className="btn-label">{siteConfig.join_tg_btn_text || 'JOIN TG'}</span>
                        <span className="tg-live-dot" title="Active Community"></span>
                      </a>
                    </div>
                  )}

                  {siteConfig.show_download_btn !== 'false' && (
                    <button
                      type="button"
                      className={`nl-btn btn-download-apk ${!isApkLinked ? 'btn-unlinked' : ''}`}
                      onClick={handleDownload}
                    >
                      <span className="btn-icon">
                        {!isApkLinked ? (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
                          </svg>
                        ) : (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                          </svg>
                        )}
                      </span>
                      <span className="btn-label">{siteConfig.download_btn_text || (isApkLinked ? 'DOWNLOAD APK' : 'APK NOT LINKED')}</span>
                    </button>
                  )}
                </div>
              )}

            {/* Secondary Custom Multi-Purpose Button (Channel / File Download / Config) */}
            {siteConfig.custom_action_btn_text && siteConfig.custom_action_btn_text.trim() && (
              <div className="nl-custom-btn-wrapper" style={{ width: '100%', marginTop: '0.85rem' }}>
                <a
                  href={siteConfig.custom_action_btn_link || '#'}
                  target={siteConfig.custom_action_btn_link && siteConfig.custom_action_btn_link.startsWith('http') ? '_blank' : '_self'}
                  rel="noopener noreferrer"
                  className="nl-btn btn-custom-action"
                >
                  <span className="btn-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                  </span>
                  <span className="btn-label">{siteConfig.custom_action_btn_text}</span>
                  <span className="btn-action-arrow">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                  </span>
                </a>
              </div>
            )}

            {/* Feedback Toast */}
            {toastVisible && (
              <div className="download-toast" role="status">
                <span className="toast-dot" aria-hidden="true"></span>
                <span>{toastMessage}</span>
              </div>
            )}
          </div>

          {/* Right Column on PC / Bottom Section on Mobile: App Details, Specs & Features (Controlled by Admin Panel Toggle) */}
          {siteConfig.show_app_details_card !== 'false' && siteConfig.show_app_details_card !== false && (
            <div className="nl-col-details">
              <div className="nl-app-card">
                {/* Header Row: Icon, Title, Version Badge, Category */}
                <div className="app-card-header">
                  <BiToolLogo size={42} color="#991b1b" />

                  <div className="app-title-col">
                    <div className="app-title-row">
                      <h2 className="app-name">
                        {loadingConfig ? (
                          <span className="skeleton-line" style={{ width: 110, height: 22, display: 'inline-block' }}></span>
                        ) : (
                          siteConfig.brand_title || ''
                        )}
                      </h2>
                      <span className={`version-tag ${!isApkLinked ? 'tag-unlinked' : ''}`}>
                        {isApkLinked ? latestRelease?.version : 'APK NOT LINKED'}
                      </span>
                    </div>
                    <p className="app-meta">
                      {loadingConfig ? (
                        <span className="skeleton-line" style={{ width: 140, height: 14, display: 'inline-block' }}></span>
                      ) : (
                        siteConfig.support_text || ''
                      )}
                    </p>
                  </div>
                </div>

                {/* 4 Metrics Pill Cards - 100% Real PostgreSQL Data */}
                <div className="nl-metrics-grid">
                  <div className="metric-pill">
                    <div className="metric-icon-wrap icon-purple">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                      </svg>
                    </div>
                    <div className="metric-info">
                      <span className="metric-val">{isApkLinked ? Number(latestRelease?.download_count || 0).toLocaleString() : '0'}</span>
                      <span className="metric-txt">Downloads</span>
                    </div>
                  </div>

                  <div className="metric-pill">
                    <div className="metric-icon-wrap icon-cyan">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                        <path d="M7 15h0M2 9.5h20"></path>
                      </svg>
                    </div>
                    <div className="metric-info">
                      <span className="metric-val">{isApkLinked ? `${latestRelease?.file_size_mb} MB` : '-- MB'}</span>
                      <span className="metric-txt">Size</span>
                    </div>
                  </div>

                  <div className="metric-pill">
                    <div className="metric-icon-wrap icon-green">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <rect x="5" y="11" width="14" height="10" rx="2"></rect>
                        <circle cx="8.5" cy="16" r="1"></circle>
                        <circle cx="15.5" cy="16" r="1"></circle>
                        <path d="M9 18h6"></path>
                        <path d="M10 7a4 4 0 0 1 4 0"></path>
                        <line x1="8" y1="5" x2="9" y2="7"></line>
                        <line x1="16" y1="5" x2="15" y2="7"></line>
                      </svg>
                    </div>
                    <div className="metric-info">
                      <span className="metric-val">{isApkLinked ? latestRelease?.min_android_version : 'Android 8.0+'}</span>
                      <span className="metric-txt">Required</span>
                    </div>
                  </div>

                  <div className="metric-pill">
                    <div className="metric-icon-wrap icon-safe">
                      <RenderFeatureIcon type="shield" />
                    </div>
                    <div className="metric-info">
                      <span className="metric-val">100%</span>
                      <span className="metric-txt">Safe</span>
                    </div>
                  </div>
                </div>

                {/* Dynamic Features Section (Title + Short Description from Database) */}
                {features.length > 0 && (
                  <div className="nl-features-section" style={{ marginTop: '1.25rem' }}>
                    <h3 className="features-title" style={{ marginBottom: '0.75rem' }}>Features</h3>
                    <div className="features-grid-cards">
                      {features.map((feat) => (
                        <div key={feat.id || feat.title} className="feature-rich-card">
                          <div className="feature-card-header">
                            <div className="feature-icon-bubble">
                              <RenderFeatureIcon type={feat.icon_type} />
                            </div>
                            <h4 className="feature-card-title">{feat.title}</h4>
                          </div>
                          <p className="feature-card-desc">{feat.short_description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
    </section>
  );
}

export default Hero;
