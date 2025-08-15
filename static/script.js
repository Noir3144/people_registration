// ================= IMAGE COMPRESSION HELPER =================
function compressImage(file, maxSize = 1280, quality = 0.8) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      let { width, height } = img;
      if (width > height && width > maxSize) {
        height = Math.round((height *= maxSize / width));
        width = maxSize;
      } else if (height > maxSize) {
        width = Math.round((width *= maxSize / height));
        height = maxSize;
      }

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob(
        (blob) => {
          resolve(new File([blob], file.name.replace(/\.\w+$/, ".jpeg"), { type: "image/jpeg" }));
        },
        "image/jpeg",
        quality
      );
    };
    img.src = URL.createObjectURL(file);
  });
}

// ================= REGISTRATION FORM (Camera App) =================
const RegForm = (function(){
  const containerSelector = '#camera-slots';
  let container;
  let capturedFiles = [];
  let cameraInput; // persistent input

  function createEmptySlot(){
    const slot = document.createElement('div');
    slot.className = 'slot slot-empty';
    slot.innerHTML = `<div class="plus">+</div>`;
    slot.addEventListener('click', () => openCamera(slot));
    return slot;
  }

  function openCamera(slot){
    if (!cameraInput) {
      cameraInput = document.createElement('input');
      cameraInput.type = 'file';
      cameraInput.accept = 'image/*';
      cameraInput.capture = 'environment';
      cameraInput.style.display = 'none';
      document.body.appendChild(cameraInput);
    }

    cameraInput.onchange = async () => {
      const file = cameraInput.files[0];
      if (!file) return;
      const compressed = await compressImage(file);
      showPreview(slot, compressed);
      cameraInput.value = ''; // reset so next click works
    };

    cameraInput.click();
  }

  function showPreview(slot, file){
    const url = URL.createObjectURL(file);
    slot.classList.remove('slot-empty');
    slot.innerHTML = `<img src="${url}">`;

    capturedFiles.push(file);

    const actions = document.createElement('div');
    actions.className = 'slot-actions';

    const retake = document.createElement('button');
    retake.className = 'small-btn';
    retake.innerText = 'Retake';
    retake.addEventListener('click', () => {
      capturedFiles = capturedFiles.filter(f => f !== file);
      openCamera(slot);
    });

    const remove = document.createElement('button');
    remove.className = 'small-btn';
    remove.innerText = 'Remove';
    remove.addEventListener('click', () => {
      capturedFiles = capturedFiles.filter(f => f !== file);
      slot.remove();
    });

    actions.appendChild(remove);
    actions.appendChild(retake);
    slot.appendChild(actions);

    if (!container.querySelector('.slot-empty')) {
      container.appendChild(createEmptySlot());
    }
  }

  function hijackSubmit(){
    const form = document.getElementById('reg-form');
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      capturedFiles.forEach((f, i) => {
        fd.append('family_photos', f, `p${i+1}.jpeg`);
      });
      fetch(form.action, {method:'POST', body: fd})
        .then(r => {
          if (r.redirected) window.location = r.url;
          else return r.text().then(t => { alert('Submitted'); });
        })
        .catch(err => { alert('Upload failed: ' + err); });
    });
  }

  return {
    initCameraSlots: function(){
      container = document.querySelector(containerSelector);
      if(!container) return;
      container.innerHTML = '';
      container.appendChild(createEmptySlot());
      hijackSubmit();
    }
  };
})();

// ================= MISSING FORM (File Upload) =================
const MissingForm = (function(){
  const containerSelector = '#missing-slots';
  let container;
  let uploadedFiles = [];
  let uploadInput; // persistent input

  function createUploadSlot(){
    const slot = document.createElement('div');
    slot.className = 'slot slot-empty';
    slot.innerHTML = `<div class="plus">+</div>`;
    slot.addEventListener('click', () => openFilePickerForSlot(slot));
    return slot;
  }

  function openFilePickerForSlot(slot){
    if (!uploadInput) {
      uploadInput = document.createElement('input');
      uploadInput.type = 'file';
      uploadInput.accept = 'image/*';
      uploadInput.style.display = 'none';
      document.body.appendChild(uploadInput);
    }

    uploadInput.onchange = async () => {
      const file = uploadInput.files[0];
      if (!file) return;
      const compressed = await compressImage(file);
      showPreview(slot, compressed);
      uploadInput.value = ''; // reset
    };

    uploadInput.click();
  }

  function showPreview(slot, file){
    const url = URL.createObjectURL(file);
    slot.classList.remove('slot-empty');
    slot.innerHTML = `<img src="${url}">`;

    uploadedFiles.push(file);

    const actions = document.createElement('div');
    actions.className = 'slot-actions';

    const replace = document.createElement('button');
    replace.className = 'small-btn';
    replace.innerText = 'Replace';
    replace.addEventListener('click', () => {
      uploadedFiles = uploadedFiles.filter(f => f !== file);
      openFilePickerForSlot(slot);
    });

    const remove = document.createElement('button');
    remove.className = 'small-btn';
    remove.innerText = 'Remove';
    remove.addEventListener('click', () => {
      uploadedFiles = uploadedFiles.filter(f => f !== file);
      slot.remove();
    });

    actions.appendChild(remove);
    actions.appendChild(replace);
    slot.appendChild(actions);

    if (!container.querySelector('.slot-empty')) {
      container.appendChild(createUploadSlot());
    }
  }

  function hijackSubmit(){
    const form = document.getElementById('missing-form');
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      uploadedFiles.forEach((f, i) => {
        fd.append('missing_photos', f, `m${i+1}.jpeg`);
      });
      fetch(form.action, {method:'POST', body: fd})
        .then(r => {
          if (r.redirected) window.location = r.url;
          else return r.text().then(t => { alert('Submitted'); });
        })
        .catch(err => { alert('Upload failed: ' + err); });
    });
  }

  return {
    initUploadSlots: function(){
      container = document.querySelector(containerSelector);
      if(!container) return;
      container.innerHTML = '';
      container.appendChild(createUploadSlot());
      hijackSubmit();
    }
  };
})();

// ================= NOTIFICATIONS =================
const Notif = (function(){
  function fetchAndShow(listEl){
    fetch('/notifications')
      .then(r => r.json())
      .then(data => {
        if (!data || !data.length) {
          listEl.innerHTML = '<div class="muted small">No notifications yet.</div>';
          return;
        }
        listEl.innerHTML = '';
        data.forEach(item => {
          const el = document.createElement('div');
          el.className = 'notif-item';
          el.style.padding = '10px 0';
          el.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
          el.innerHTML = `<strong>${item.phone}</strong>
                          <div class="small muted">${item.timestamp}</div>
                          <div>${item.description || ''}</div>
                          <div class="small">File: ${item.file}</div>`;
          listEl.appendChild(el);
        });
      });
  }

  function bind(btnSel, modalSel, listSel, closeSel){
    const btn = document.querySelector(btnSel);
    const modal = document.querySelector(modalSel);
    const listEl = document.querySelector(listSel);
    const closeBtn = document.querySelector(closeSel);
    if(!btn || !modal || !listEl || !closeBtn) return;
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      modal.classList.remove('hidden');
      fetchAndShow(listEl);
    });
    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    modal.addEventListener('click', (ev) => {
      if(ev.target === modal) modal.classList.add('hidden');
    });
  }

  return {
    init: function(btnSel = '#notif-btn', modalSel = '#notif-modal', listSel = '#notif-list', closeSel = '#close-notif'){
      bind(btnSel, modalSel, listSel, closeSel);
    }
  };
})();
