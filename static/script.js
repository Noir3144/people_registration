// script.js
// Responsible for camera capture slots (registration), missing upload slots, and notifications

const RegForm = (function(){
  const containerSelector = '#camera-slots';
  let container;
  let streams = {};
  let captureBlobs = []; // blobs to append to form on submit

  function createEmptySlot(){
    const slot = document.createElement('div');
    slot.className = 'slot slot-empty';
    slot.innerHTML = `<div class="plus">+</div>`;
    slot.addEventListener('click', () => openCameraForSlot(slot));
    return slot;
  }

  async function openCameraForSlot(slot){
    // open camera, show live preview UI inside slot
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
      alert('Camera not available on this device.');
      return;
    }
    const vid = document.createElement('video');
    vid.autoplay = true;
    vid.playsInline = true;
    vid.style.width = '100%';
    vid.style.height = '100%';
    slot.innerHTML = '';
    slot.appendChild(vid);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}});
      streams[slot] = stream;
      vid.srcObject = stream;

      const controls = document.createElement('div');
      controls.className = 'slot-actions';
      const take = document.createElement('button');
      take.className = 'small-btn';
      take.innerText = 'Capture';
      const cancel = document.createElement('button');
      cancel.className = 'small-btn';
      cancel.innerText = 'Cancel';
      controls.appendChild(cancel);
      controls.appendChild(take);
      slot.appendChild(controls);

      take.addEventListener('click', async () => {
        // capture frame
        const canvas = document.createElement('canvas');
        canvas.width = vid.videoWidth || 640;
        canvas.height = vid.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(vid, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          setSlotImage(slot, blob);
        }, 'image/jpeg', 0.85);
        stopStream(stream);
      });

      cancel.addEventListener('click', () => {
        stopStream(stream);
        slot.replaceWith(createEmptySlot());
      });

    } catch (e) {
      console.error('camera error', e);
      alert('Unable to access camera: ' + e.message);
      slot.replaceWith(createEmptySlot());
    }
  }

  function stopStream(s){
    try {
      s.getTracks().forEach(t => t.stop());
    } catch(e){}
  }

  function setSlotImage(slot, blob){
    const url = URL.createObjectURL(blob);
    slot.classList.remove('slot-empty');
    slot.innerHTML = `<img src="${url}">`;
    const actions = document.createElement('div');
    actions.className = 'slot-actions';
    const retake = document.createElement('button'); retake.className = 'small-btn'; retake.innerText='Retake';
    const remove = document.createElement('button'); remove.className = 'small-btn'; remove.innerText='Remove';
    actions.appendChild(remove); actions.appendChild(retake);
    slot.appendChild(actions);

    // store blob
    captureBlobs.push(blob);

    retake.addEventListener('click', () => {
      // create a new empty slot and open camera
      const newSlot = createEmptySlot();
      slot.replaceWith(newSlot);
      openCameraForSlot(newSlot);
      // remove corresponding blob (best-effort: remove last)
      captureBlobs.pop();
    });
    remove.addEventListener('click', () => {
      slot.remove();
      // best-effort remove last blob
      captureBlobs.pop();
    });

    // append a new empty slot if none exists
    const containerEl = document.querySelector(containerSelector);
    if (!containerEl.querySelector('.slot-empty')) {
      containerEl.appendChild(createEmptySlot());
    }
  }

  function populateHiddenInput(){
    // create DataTransfer-like behavior by building FormData in submit handler,
    // but HTML <input type=file> cannot be programmatically assigned with blobs cross-browser.
    // We will intercept form submit and send via fetch XHR with FormData.
  }

  function hijackSubmit(){
    const form = document.getElementById('reg-form');
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      // append captured blobs
      captureBlobs.forEach((b, i) => {
        fd.append('family_photos', new File([b], `p${i+1}.jpeg`, {type: 'image/jpeg'}));
      });
      // send via fetch to avoid relying on hidden file inputs
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
      // start with one empty slot
      container.innerHTML = '';
      container.appendChild(createEmptySlot());
      hijackSubmit();
    }
  };
})();

const MissingForm = (function(){
  const containerSelector = '#missing-slots';
  let container;
  let uploadedFiles = []; // store File objects for submission

  function createUploadSlot(){
    const slot = document.createElement('div');
    slot.className = 'slot slot-empty';
    slot.innerHTML = `<div class="plus">+</div>`;
    slot.addEventListener('click', () => openFilePickerForSlot(slot));
    return slot;
  }

  function openFilePickerForSlot(slot){
    // use hidden input to allow multiple clicks
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.display = 'none';
    input.addEventListener('change', () => {
      const f = input.files[0];
      if (!f) {
        return;
      }
      setSlotImage(slot, f);
    });
    document.body.appendChild(input);
    input.click();
    // removed later by file select handler
  }

  function setSlotImage(slot, file){
    const url = URL.createObjectURL(file);
    slot.classList.remove('slot-empty');
    slot.innerHTML = `<img src="${url}">`;
    const actions = document.createElement('div');
    actions.className = 'slot-actions';
    const retake = document.createElement('button'); retake.className = 'small-btn'; retake.innerText='Replace';
    const remove = document.createElement('button'); remove.className = 'small-btn'; remove.innerText='Remove';
    actions.appendChild(remove); actions.appendChild(retake);
    slot.appendChild(actions);

    uploadedFiles.push(file);

    retake.addEventListener('click', () => {
      openFilePickerForSlot(slot);
      // remove last file as best-effort; accurate mapping requires index association
      uploadedFiles.pop();
    });
    remove.addEventListener('click', () => {
      slot.remove();
      uploadedFiles.pop();
    });

    const containerEl = document.querySelector(containerSelector);
    if (!containerEl.querySelector('.slot-empty')) {
      containerEl.appendChild(createUploadSlot());
    }
  }

  function hijackSubmit(){
    const form = document.getElementById('missing-form');
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      uploadedFiles.forEach((f, i) => {
        fd.append('missing_photos', f, `m${i+1}${(f.name.match(/\.\w+$/)||['.jpeg'])[0]}`);
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

const Notif = (function(){
  let btnSelector = '#notif-btn';
  let modalSelector = '#notif-modal';
  let listSelector = '#notif-list';
  let closeSelector = '#close-notif';

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
          el.innerHTML = `<strong>${item.phone}</strong> <div class="small muted">${item.timestamp}</div>
                          <div>${item.description || ''}</div>
                          <div class="small">File: ${item.file}</div>`;
          listEl.appendChild(el);
        });
      });
  }

  function bind(btnSel = '#notif-btn', modalSel = '#notif-modal', listSel = '#notif-list', closeSel = '#close-notif'){
    btnSelector = btnSel;
    modalSelector = modalSel;
    listSelector = listSel;
    closeSelector = closeSel;
    const btn = document.querySelector(btnSelector);
    const modal = document.querySelector(modalSelector);
    const listEl = document.querySelector(listSelector);
    const closeBtn = document.querySelector(closeSelector);
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
    init: function(btn = '#notif-btn', modal = '#notif-modal', list = '#notif-list', close = '#close-notif'){
      bind(btn, modal, list, close);
    }
  };
})();
