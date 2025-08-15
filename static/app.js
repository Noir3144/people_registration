// ===================
// Existing Logic (your original app.js code)
// ===================
// (अगर तुम्हारे पुराने कोड में कुछ खास functions थे तो वो यहाँ रहेंगे)

// ===================
// New Logic for Thumbnail Preview & Dynamic Photo Upload
// ===================

// Function to create a photo upload field with preview
function createPhotoField(containerId, namePrefix) {
    const container = document.getElementById(containerId);

    // Wrapper
    const fieldWrapper = document.createElement('div');
    fieldWrapper.className = 'photo-field';

    // File input
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.name = `${namePrefix}[]`;
    fileInput.accept = '.jpg,.jpeg,.png';
    fileInput.style.display = 'none';

    // Thumbnail preview
    const preview = document.createElement('img');
    preview.className = 'photo-preview';
    preview.style.display = 'none';

    // Add photo button
    const addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.className = 'add-photo-btn';
    addButton.innerHTML = '+';

    // Button click opens file dialog
    addButton.addEventListener('click', () => {
        fileInput.click();
    });

    // When file selected
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (event) {
                preview.src = event.target.result;
                preview.style.display = 'inline-block';
            };
            reader.readAsDataURL(file);

            // Automatically add new photo field when current gets a file
            if (!container.querySelector('.photo-field:last-child input').files.length) {
                // Do nothing if last one is empty
            } else {
                createPhotoField(containerId, namePrefix);
            }
        }
    });

    // Append elements
    fieldWrapper.appendChild(preview);
    fieldWrapper.appendChild(addButton);
    fieldWrapper.appendChild(fileInput);
    container.appendChild(fieldWrapper);
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    // For registration form
    if (document.getElementById('registration-photos')) {
        createPhotoField('registration-photos', 'registration_photos');
    }

    // For missing report form
    if (document.getElementById('missing-photos')) {
        createPhotoField('missing-photos', 'missing_photos');
    }
});
