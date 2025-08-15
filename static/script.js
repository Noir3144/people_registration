/* ===== Theme, i18n, Slots, Notifications ===== */

const UI = (() => {
  const initTheme = () => {
    const root = document.documentElement;
    const saved = localStorage.getItem('theme');
    if (saved) root.setAttribute('data-theme', saved);
    else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
      root.setAttribute('data-theme', 'light');
    }
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        root.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
      });
    }
  };
  return { initTheme };
})();

const I18N = (() => {
  const load = async (forceLang) => {
    const lang = forceLang || (document.cookie.match(/(?:^|;\s*)lang=([^;]+)/)?.[1]) || 'en';
    try {
      const res = await fetch(`/static/i18n/${lang}.json`, { cache: 'no-cache' });
      const dict = await res.json();
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (dict[key]) el.textContent = dict[key];
      });
    } catch (e) {
      // silent fail; English stays
    }
  };
  return { load };
})();

/* ---- Dynamic photo slots ----
   - data-mode="camera" => opens device camera
   - data-mode="upload" => gallery/file picker
   - data-name="reg_photos[]" or "missing_photos[]"
*/
const Slots = (() => {
  const template = (name, mode) => {
    // capture attr only for camera mode
    const capture = mode === 'camera' ? ' capture="environment" ' : '';
    return `
    <div class="slot">
      <label class="slot-box">
        <input class="slot-input" type="file" accept="image/*" ${capture} name="${name}" />
        <div class="slot-empty">
          <span class="plus">＋</span>
          <span class="hint">${mode === 'camera' ? 'Tap to open camera' : 'Tap to upload'}</span>
        </div>
        <img class="slot-preview" alt="" />
      </label>
      <div class="slot-actions">
        <button type="button" class="ghost sm slot-retake">Retake</button>
        <button type="button" class="ghost sm slot-remove">Remove</button>
      </div>
    </div>`;
  };

  const onChange = (slot, list) => {
    const input = slot.querySelector('.slot-input');
    const preview = slot.querySelector('.slot-preview');
    const empty = slot.querySelector('.slot-empty');

    if (input.files && input.files[0]) {
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        preview.src = reader.result;
        preview.style.display = 'block';
        empty.style.display = 'none';

        // ensure there is always one empty slot at the end
        const unused = list.querySelectorAll('.slot-input:not([data-used])');
        input.dataset.used = '1';
        if (unused.length === 0) {
          // create one more slot
          const mode = list.dataset.mode;
          const name = list.dataset.name;
          list.insertAdjacentHTML('beforeend', template(name, mode));
          bindSlot(list.lastElementChild, list);
        }
      };
      reader.readAsDataURL(file);
    } else {
      // cleared
      preview.src = '';
      preview.style.display = 'none';
      empty.style.display = 'flex';
      delete input.dataset.used;
    }
  };

  const onRetake = (slot) => {
    const input = slot.querySelector('.slot-input');
    input.value = '';
    input.click(); // reopen chooser/camera
  };

  const onRemove = (slot, list) => {
    slot.remove();
    // ensure at least one empty slot exists
    if (!list.querySelector('.slot-input')) {
      const mode = list.dataset.mode;
      const name = list.dataset.name;
      list.insertAdjacentHTML('beforeend', template(name, mode));
      bindSlot(list.lastElementChild, list);
    }
  };

  const bindSlot = (slot, list) => {
    slot.querySelector('.slot-input').addEventListener('change', () => onChange(slot, list));
    slot.querySelector('.slot-retake').addEventListener('click', () => onRetake(slot));
    slot.querySelector('.slot-remove').addEventListener('click', () => onRemove(slot, list));
  };

  const init = (selector) => {
    const list = document.querySelector(selector);
    if (!list) return;
    // first empty slot
    list.insertAdjacentHTML('beforeend', template(list.dataset.name, list.dataset.mode));
    bindSlot(list.lastElementChild, list);
  };

  return { init };
})();

/* ---- Notifications ---- */
const Notif = (() => {
  const renderItem = (n) => {
    const badge = n.kind === 'missing' ? 'badge-warn' : 'badge-ok';
    const title = n.kind === 'missing' ? 'Missing Report' : 'Registration';
    const extras = [];
    if (n.extra && typeof n.extra === 'object') {
      Object.entries(n.extra).forEach(([k, v]) => extras.push(`${k}: ${v}`));
    }
    return `
      <div class="row-item">
        <div class="row-left">
          <span class="badge ${badge}"></span>
        </div>
        <div class="row-main">
          <div class="row-title">${title} • ${n.phone}</div>
          <div class="row-sub">${new Date(n.ts).toLocaleString()}</div>
          ${extras.length ? `<div class="row-extra">${extras.join(' · ')}</div>` : ''}
        </div>
      </div>
    `;
  };

  const load = async (api) => {
    const list = document.getElementById('notif-list');
    list.innerHTML = '<div class="muted">Loading…</div>';
    try {
      const res = await fetch(api || '/api/notifications', { cache: 'no-cache' });
      const data = await res.json();
      if (!data.length) {
        list.innerHTML = '<div class="muted">No notifications yet.</div>';
        return;
      }
      list.innerHTML = data.map(renderItem).join('');
    } catch (e) {
      list.innerHTML = '<div class="muted">Failed to load.</div>';
    }
  };
  return { load };
})();
