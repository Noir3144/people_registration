// Add another family photo field
const addBtn = document.getElementById('addPhotoBtn');
const zone = document.getElementById('photoZone');
if (addBtn && zone) {
  addBtn.addEventListener('click', () => {
    const label = document.createElement('label');
    label.className = 'drop';
    label.innerHTML = '<span class="plus">+</span><input type="file" name="family_photos" accept=".jpg,.jpeg,.png" />';
    zone.appendChild(label);
  });
}

// Notifications auto-refresh
async function loadNotifications(){
  try{
    const res = await fetch('/notifications');
    const data = await res.json();
    const board = document.getElementById('notifBoard');
    if(!Array.isArray(data) || data.length===0){
      board.innerHTML = '<div class="notif">No notifications yet.</div>';
      return;
    }
    board.innerHTML = '';
    data.forEach(n=>{
      const item = document.createElement('div');
      item.className = 'notif';
      item.innerHTML = `
        <div><strong>Status:</strong> ${n.status || 'reported'}</div>
        <div class="meta">${n.timestamp || ''} — ${n.phone ? ('Phone: '+n.phone) : ''}</div>
        ${n.description ? `<div>${n.description}</div>`:''}
      `;
      board.appendChild(item);
    });
  }catch(e){
    console.error('Notif error', e);
  }
}
loadNotifications();
setInterval(loadNotifications, 5000);
