/* ===== Language + i18n ===== */
const LANG_KEY = "site_lang";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "bn", label: "বাংলা" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ml", label: "മലയാളം" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "or", label: "ଓଡ଼ିଆ" },
  { code: "as", label: "অসমীয়া" },
  { code: "ur", label: "اردو" }
];

// Minimal demo translations. Extend as needed.
const T = {
  en: {
    "app.title": "Finder Portal",
    "nav.register": "Register",
    "nav.report": "Report Missing",
    "nav.board": "Notification Board",
    "lang.change": "Change",
    "lang.select_language": "Select Language",
    "lang.skip": "Continue in English",

    "reg.title": "Family Registration",
    "reg.subtitle": "Upload photos and contact details to help identify and contact you.",

    "miss.title": "Report Missing Person",
    "miss.subtitle": "Share photos and details to notify others.",

    "board.title": "Notification Board",
    "board.subtitle": "Recently reported missing/found items.",
    "board.reported": "Reported",
    "board.empty": "No notifications yet.",

    "field.phone": "Mobile Number",
    "field.whatsapp": "WhatsApp Number",
    "field.secondary": "Secondary Contact (Optional)",
    "field.photos": "Photos",
    "field.description": "Description",

    "ui.add_photo": "Add Photo",
    "ui.retake": "Retake",
    "ui.remove": "Remove",

    "action.submit": "Submit",
    "action.reset": "Reset",

    // Flash / messages (keys emitted by backend)
    "msg.phone_whatsapp_required": "Mobile and WhatsApp numbers are required.",
    "msg.registration_success": "Registration submitted successfully.",
    "msg.upload_error": "Upload failed. Please try again.",
    "msg.missing_photo_required": "At least one missing photo is required.",
    "msg.missing_report_success": "Missing report submitted.",
    "msg.missing_report_error": "Error submitting missing report.",
  },

  hi: {
    "app.title": "फाइंडर पोर्टल",
    "nav.register": "रजिस्टर",
    "nav.report": "मिसिंग रिपोर्ट",
    "nav.board": "सूचना बोर्ड",
    "lang.change": "बदलें",
    "lang.select_language": "भाषा चुनें",
    "lang.skip": "अंग्रेज़ी में जारी रखें",

    "reg.title": "परिवार पंजीकरण",
    "reg.subtitle": "पहचान और संपर्क में सहायता के लिए फ़ोटो व संपर्क विवरण अपलोड करें।",

    "miss.title": "लापता व्यक्ति रिपोर्ट",
    "miss.subtitle": "दूसरों को सूचित करने के लिए फ़ोटो व विवरण साझा करें।",

    "board.title": "सूचना बोर्ड",
    "board.subtitle": "हाल ही में रिपोर्ट किए गए मिसिंग/मिले हुए लोग।",
    "board.reported": "रिपोर्टेड",
    "board.empty": "अभी कोई सूचना नहीं।",

    "field.phone": "मोबाइल नंबर",
    "field.whatsapp": "व्हाट्सऐप नंबर",
    "field.secondary": "द्वितीय संपर्क (वैकल्पिक)",
    "field.photos": "फ़ोटो",
    "field.description": "विवरण",

    "ui.add_photo": "फ़ोटो जोड़ें",
    "ui.retake": "फिर से लें",
    "ui.remove": "हटाएं",

    "action.submit": "सबमिट",
    "action.reset": "रीसेट",

    "msg.phone_whatsapp_required": "मोबाइल और व्हाट्सऐप नंबर आवश्यक हैं।",
    "msg.registration_success": "पंजीकरण सफलतापूर्वक सबमिट हुआ।",
    "msg.upload_error": "अपलोड विफल। पुनः प्रयास करें।",
    "msg.missing_photo_required": "कम से कम एक मिसिंग फ़ोटो आवश्यक है।",
    "msg.missing_report_success": "मिसिंग रिपोर्ट सबमिट हुई।",
    "msg.missing_report_error": "मिसिंग रिपोर्ट सबमिट करने में त्रुटि।",
  },

  // Add other languages similarly…
};

function getLang() {
  return localStorage.getItem(LANG_KEY) || "en";
}

function setLang(lang) {
  localStorage.setItem(LANG_KEY, lang);
}

function translateElement(el, lang) {
  const key = el.getAttribute("data-i18n");
  if (!key) return;
  const text = (T[lang] && T[lang][key]) || (T["en"][key]) || el.textContent;
  el.textContent = text;
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    // If placeholders need translation, use data-i18n for sibling label instead
  }
}

window.applyI18n = function() {
  const lang = getLang();
  document.querySelectorAll("[data-i18n]").forEach(el => translateElement(el, lang));
  document.title = (T[lang]["app.title"] || "Finder Portal");
}

/* Build Language Modal */
function buildLanguageModal() {
  const list = document.getElementById("langList");
  if (!list) return;
  list.innerHTML = "";
  LANGUAGES.forEach(l => {
    const div = document.createElement("div");
    div.className = "lang";
    div.innerHTML = `<span>${l.label}</span><span>${l.code.toUpperCase()}</span>`;
    div.addEventListener("click", () => {
      setLang(l.code);
      hideLangModal();
      applyI18n();
    });
    list.appendChild(div);
  });

  const skip = document.getElementById("langSkip");
  if (skip) skip.addEventListener("click", () => {
    setLang("en");
    hideLangModal();
    applyI18n();
  });

  const change = document.getElementById("changeLang");
  if (change) change.addEventListener("click", () => showLangModal());
}

function showLangModal(){ document.getElementById("langModal")?.classList.add("visible"); }
function hideLangModal(){ document.getElementById("langModal")?.classList.remove("visible"); }

/* ===== Dynamic Photo Slots ===== */
function setupSlots(containerId, templateId) {
  const container = document.getElementById(containerId);
  const tmpl = document.getElementById(templateId);
  if (!container || !tmpl) return;

  function addEmptySlot() {
    const node = tmpl.content.firstElementChild.cloneNode(true);
    const input = node.querySelector(".file-input");
    const preview = node.querySelector(".preview");

    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      preview.src = url;
      node.classList.add("filled");
      // After one is filled, add another empty slot automatically
      ensureEmptySlot();
    });

    node.querySelector('[data-action="retake"]').addEventListener("click", () => {
      input.value = "";
      preview.removeAttribute("src");
      node.classList.remove("filled");
      input.click();
    });

    node.querySelector('[data-action="remove"]').addEventListener("click", () => {
      const url = preview.getAttribute("src");
      if (url) URL.revokeObjectURL(url);
      node.remove();
      ensureEmptySlot();
    });

    container.appendChild(node);
    return node;
  }

  function ensureEmptySlot() {
    const hasEmpty = [...container.querySelectorAll(".slot")].some(s => !s.classList.contains("filled"));
    if (!hasEmpty) addEmptySlot();
  }

  // Start with a single empty slot
  addEmptySlot();
}

/* ===== Form basic client-side checks (optional) ===== */
function attachPhoneNormalization(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", (e) => {
    const reqIds = ["phone", "whatsapp"];
    for (const id of reqIds) {
      const el = form.querySelector(`#${id}`);
      if (!el || !el.value.trim()) {
        e.preventDefault();
        showInlineFlash("msg.phone_whatsapp_required");
        return false;
      }
    }
  });
}

function showInlineFlash(key){
  const container = document.querySelector(".flash-container") || (() => {
    const c = document.createElement("div");
    c.className = "flash-container";
    document.body.appendChild(c);
    return c;
  })();

  const div = document.createElement("div");
  div.className = "flash glass";
  div.setAttribute("data-i18n", key);
  div.textContent = key;
  container.appendChild(div);
  applyI18n();

  setTimeout(() => { div.remove(); }, 4000);
}

/* ===== Boot ===== */
document.addEventListener("DOMContentLoaded", () => {
  buildLanguageModal();

  // Show modal only if no language selected yet
  if (!localStorage.getItem(LANG_KEY)) {
    showLangModal();
  } else {
    hideLangModal();
  }

  // Apply current language
  applyI18n();

  // Allow user to reopen language modal
  const changeBtn = document.getElementById("changeLang");
  changeBtn && changeBtn.addEventListener("click", () => showLangModal());

  // Setup dynamic slots on pages that have them
  setupSlots("photoSlots", "slotTemplate");
  setupSlots("missSlots", "missSlotTemplate");

  // Basic form validations
  attachPhoneNormalization("regForm");
  attachPhoneNormalization("missForm");
});
