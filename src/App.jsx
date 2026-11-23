import React, { useState, useEffect } from 'react';
import Hero from './component/hero/Hero.jsx';
import BiToolLogo from './component/common/BiToolLogo';
import './App.css';

export function App() {
  const [activeFaq, setActiveFaq] = useState(null);
  const [faqs, setFaqs] = useState([]);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [loadingFaqs, setLoadingFaqs] = useState(true);
  const [siteConfig, setSiteConfig] = useState({
    brand_title: '',
    support_text: '',
    telegram_url: '',
    nav_btn1_text: 'Showcase',
    nav_btn1_link: '#showcase',
    nav_btn2_text: 'Installation',
    nav_btn2_link: '#install',
    nav_btn3_text: 'FAQ',
    nav_btn3_link: '#faq',
    nav_tg_btn_text: 'Join Telegram',
    footer_copy_text: '',
    show_top_nav: 'true',
    show_install_guide: 'true',
    show_faq_section: 'true',
    show_footer: 'true',
  });

  const loadData = () => {
    fetch('http://localhost:8000/api/v1/site/config')
      .then(res => res.json())
      .then(data => {
        if (data) setSiteConfig(data);
        setLoadingConfig(false);
      })
      .catch(() => {
        setLoadingConfig(false);
      });

    fetch('http://localhost:8000/api/v1/faqs/active')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setFaqs(data);
        }
        setLoadingFaqs(false);
      })
      .catch(() => {
        setLoadingFaqs(false);
      });

    // Real dynamic SEO Title & Meta tags injection
    fetch('http://localhost:8000/api/v1/security-center/seo')
      .then(res => res.json())
      .then(seo => {
        if (seo) {
          if (seo.meta_title) document.title = seo.meta_title;
          if (seo.meta_description) {
            let metaDesc = document.querySelector('meta[name="description"]');
            if (!metaDesc) {
              metaDesc = document.createElement('meta');
              metaDesc.name = 'description';
              document.head.appendChild(metaDesc);
            }
            metaDesc.content = seo.meta_description;
          }
          if (seo.meta_keywords) {
            let metaKw = document.querySelector('meta[name="keywords"]');
            if (!metaKw) {
              metaKw = document.createElement('meta');
              metaKw.name = 'keywords';
              document.head.appendChild(metaKw);
            }
            metaKw.content = seo.meta_keywords;
          }
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadData();

    // Realtime WebSocket Live Sync with Backend / Admin Panel
    let ws = null;
    let timer = null;

    const connectWs = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/api/v1/ws/sync');
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.event === 'CONFIG_UPDATED' || msg.event === 'FAQS_UPDATED' || msg.event === 'RELEASE_UPDATED') {
              loadData();
            }
          } catch (e) {}
        };
        ws.onclose = () => {
          timer = setTimeout(connectWs, 3000);
        };
      } catch (err) {
        timer = setTimeout(connectWs, 3000);
      }
    };

    connectWs();

    return () => {
      if (ws) ws.close();
      if (timer) clearTimeout(timer);
    };
  }, []);

  const toggleFaq = (idx) => {
    setActiveFaq(activeFaq === idx ? null : idx);
  };

  const defaultFaqs = [
    {
      question: `Is root required for ${siteConfig?.brand_title || 'बी - TOOL'}?`,
      answer: `No, ${siteConfig?.brand_title || 'बी - TOOL'} operates completely in a non-root environment using virtualized space and memory injection without needing root privileges.`,
    },
    {
      question: 'How does Anti-Ban protection work?',
      answer: 'Our bypass engine dynamically scrambles signatures and hooks into network packets before game telemetry logs are generated, keeping your account 100% secure.',
    },
    {
      question: 'Which Android versions are supported?',
      answer: 'Supports Android 8.0, 9, 10, 11, 12, 13, 14, and 15+ (both 32-bit and 64-bit devices).',
    },
  ];

  const displayFaqs = faqs.length > 0 ? faqs : defaultFaqs;

  return (
    <div className="nl-site-wrapper">
      {/* Top Global Navigation (Controlled by Admin Panel) */}
      {siteConfig.show_top_nav !== 'false' && siteConfig.show_top_nav !== false && (
        <nav className="nl-top-nav">
          <div className="nl-nav-inner">
            <div className="nl-nav-brand">
              <BiToolLogo size={28} color="#991b1b" />
              <span className="nl-nav-title">
                {loadingConfig ? (
                  <span className="skeleton-line" style={{ width: 85, height: 18, display: 'inline-block' }}></span>
                ) : (
                  siteConfig?.brand_title || ''
                )}
              </span>
            </div>

            <div className="nl-nav-links">
              <a href={siteConfig?.nav_btn1_link || "#showcase"}>
                {siteConfig?.nav_btn1_text || "Showcase"}
              </a>
              <a href={siteConfig?.nav_btn2_link || "#install"}>
                {siteConfig?.nav_btn2_text || "Installation"}
              </a>
              <a href={siteConfig?.nav_btn3_link || "#faq"}>
                {siteConfig?.nav_btn3_text || "FAQ"}
              </a>
              <a
                href={siteConfig?.telegram_url || "https://t.me/"}
                target="_blank"
                rel="noopener noreferrer"
                className="nl-nav-tg-btn"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style={{ marginRight: '6px' }}>
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .37z" />
                </svg>
                {siteConfig?.nav_tg_btn_text || "Join Telegram"}
              </a>
            </div>
          </div>
        </nav>
      )}

      {/* Main Hero Section (Matches user reference mockup with dot texture background) */}
      <main id="showcase">
        <Hero />

        {/* Extended Desktop & Tablet Details Section (Controlled by Admin Panel) */}
        {(siteConfig.show_install_guide !== 'false' || siteConfig.show_faq_section !== 'false') && (
          <section className="nl-desktop-details" id="install">
            <div className="details-container">
              {siteConfig.show_install_guide !== 'false' && (
                <>
                  <div className="details-header">
                    <span className="badge-sub">STEP BY STEP</span>
                    <h2>Quick Installation Guide</h2>
                    <p>
                      {loadingConfig ? (
                        <span className="skeleton-line" style={{ width: 220, height: 14, display: 'inline-block' }}></span>
                      ) : (
                        siteConfig?.brand_title ? `Get up and running with ${siteConfig.brand_title} in less than 2 minutes` : 'Quick setup & installation'
                      )}
                    </p>
                  </div>

                  <div className="steps-grid">
                    <div className="step-card">
                      <div className="step-header">
                        <span className="step-num">01</span>
                        <div className="step-icon-wrap">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                          </svg>
                        </div>
                      </div>
                      <h3>Download APK</h3>
                      <p>Click the <strong>DOWNLOAD APK</strong> button above to download the latest signed build.</p>
                    </div>

                    <div className="step-card">
                      <div className="step-header">
                        <span className="step-num">02</span>
                        <div className="step-icon-wrap">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                          </svg>
                        </div>
                      </div>
                      <h3>Allow Unknown Sources</h3>
                      <p>Enable installation from unknown sources in Android Settings if prompted by your browser.</p>
                    </div>

                    <div className="step-card">
                      <div className="step-header">
                        <span className="step-num">03</span>
                        <div className="step-icon-wrap">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                          </svg>
                        </div>
                      </div>
                      <h3>Launch & Inject</h3>
                      <p>Open {siteConfig?.brand_title || 'app'}, select your game title, configure your modules, and launch safely!</p>
                    </div>
                  </div>
                </>
              )}

              {/* FAQ Accordion (Controlled by Admin Panel) */}
              {siteConfig.show_faq_section !== 'false' && (
                <div className="nl-faq-section" id="faq">
                  <div className="details-header">
                    <span className="badge-sub">HELP & SUPPORT</span>
                    <h2>Frequently Asked Questions</h2>
                  </div>

                  <div className="faq-list">
                    {loadingFaqs ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                        <div className="skeleton-line" style={{ height: 48, borderRadius: 12 }}></div>
                        <div className="skeleton-line" style={{ height: 48, borderRadius: 12 }}></div>
                        <div className="skeleton-line" style={{ height: 48, borderRadius: 12 }}></div>
                      </div>
                    ) : faqs.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                        No FAQs added yet.
                      </div>
                    ) : (
                      faqs.map((item, idx) => (
                        <div
                          key={idx}
                          className={`faq-item ${activeFaq === idx ? 'expanded' : ''}`}
                          onClick={() => toggleFaq(idx)}
                        >
                          <div className="faq-question">
                            <span>{item.question}</span>
                            <span className="faq-arrow-icon">
                              <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2.4"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className={activeFaq === idx ? 'rotated' : ''}
                                aria-hidden="true"
                              >
                                <polyline points="6 9 12 15 18 9"></polyline>
                              </svg>
                            </span>
                          </div>
                          {activeFaq === idx && (
                            <div className="faq-answer">
                              <p>{item.answer}</p>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      {/* Footer (Controlled by Admin Panel) */}
      {siteConfig.show_footer !== 'false' && siteConfig.show_footer !== false && (
        <footer className="nl-footer">
          <div className="footer-inner">
            <div className="footer-brand">
              <BiToolLogo size={24} color="#991b1b" />
              <span className="footer-title">
                {loadingConfig ? (
                  <span className="skeleton-line" style={{ width: 80, height: 16, display: 'inline-block' }}></span>
                ) : (
                  siteConfig?.brand_title || ''
                )}
              </span>
            </div>
            <p className="footer-copy">
              {loadingConfig ? (
                <span className="skeleton-line" style={{ width: 180, height: 14, display: 'inline-block' }}></span>
              ) : (
                siteConfig?.footer_copy_text || ''
              )}
            </p>
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;
