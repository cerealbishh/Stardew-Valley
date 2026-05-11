class UpdateChecker {
  constructor() {
    this.banner = null;
    this.timer = null;
    this.visible = false;
    this._initBanner();
    this._registerSW();
  }

  _initBanner() {
    this.banner = document.createElement('div');
    this.banner.id = 'update-banner';
    Object.assign(this.banner.style, {
      display: 'none',
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      background: '#d4b895',
      color: '#243429',
      padding: '10px 14px',
      borderRadius: '10px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.35)',
      fontFamily: "'Courier New', monospace",
      fontSize: '13px',
      fontWeight: 'bold',
      zIndex: '9999',
      maxWidth: '260px',
      lineHeight: '1.4',
      border: '2px solid #e8a5b5'
    });
    this.banner.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px">
        <span>✨ Update available</span>
        <button id="update-refresh-btn" style="background:#243429;color:#d4b895;border:none;padding:5px 10px;border-radius:6px;cursor:pointer;font-family:inherit;font-weight:bold;font-size:12px">Refresh</button>
      </div>
      <div style="font-size:11px;margin-top:5px;opacity:0.75">Auto-refreshes in 30 seconds…</div>
    `;
    document.body.appendChild(this.banner);
    document.getElementById('update-refresh-btn').addEventListener('click', () => this._refresh());
  }

  async _registerSW() {
    if (!('serviceWorker' in navigator)) return;
    try {
      const reg = await navigator.serviceWorker.register('./service-worker.js');
      navigator.serviceWorker.addEventListener('message', (e) => {
        if (e.data && e.data.type === 'UPDATE_AVAILABLE') this._showBanner();
      });
      const ping = () => { if (reg.controller) reg.controller.postMessage({ type: 'CHECK_UPDATE' }); };
      window.addEventListener('focus', ping);
      document.addEventListener('visibilitychange', () => { if (!document.hidden) ping(); });
    } catch (err) {}
  }

  _showBanner() {
    if (this.visible) return;
    this.visible = true;
    this.banner.style.display = 'block';
    this.timer = setTimeout(() => this._refresh(), 30000);
  }

  _refresh() {
    clearTimeout(this.timer);
    if ('caches' in window) {
      caches.keys().then((names) => names.forEach((n) => caches.delete(n)));
    }
    window.location.href = window.location.href.split('?')[0] + '?v=' + Date.now();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new UpdateChecker());
} else {
  new UpdateChecker();
}
