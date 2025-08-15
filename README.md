# people_registration# Crowd Portal — Registration & Missing Person Reporting

## What this package provides
- Language selection (cookie-based).
- Camera-first registration with dynamic photo slots (registration).
- Missing-person report using file upload (gallery/computer) with dynamic slots.
- Contact fields: Mobile (required), WhatsApp (required), Secondary (optional).
- Notifications endpoint (`/notifications`) to view recent reports.
- Files are saved to `Registration/<phone>/` and `Missing/<phone>/` on the host machine.
- iOS-like dark glass theme.

## Local run (development)
1. Create a virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
