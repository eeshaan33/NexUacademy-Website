# Google Sheets API Setup Guide for JEE Master

## Complete Step-by-Step Instructions

Follow these steps to enable Google Sheets integration for YouTube link management:

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `JEE Master YouTube Links`
4. Click **"Create"**
5. Wait for project creation (takes ~30 seconds)

---

## Step 2: Enable Google Sheets API

1. In the Google Cloud Console, select your new project
2. Go to **"APIs & Services"** → **"Library"**
3. Search for `Google Sheets API`
4. Click on **"Google Sheets API"**
5. Click **"Enable"** button
6. Wait for activation

---

## Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in details:
   - **Service account name**: `jee-master-sheets-access`
   - **Service account ID**: (auto-filled)
   - **Description**: `Service account for managing YouTube solution links`
4. Click **"Create and Continue"**
5. **Grant access** (Role): Select **"Editor"** or **"Owner"**
6. Click **"Continue"** → **"Done"**

---

## Step 4: Create Service Account Key

1. In **"Credentials"** page, find your service account
2. Click on the service account email
3. Go to **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. A JSON file will download automatically - **SAVE THIS FILE SECURELY!**

---

## Step 5: Add Credentials to Environment

### Option A: Using JSON File Content (Recommended)

1. Open the downloaded JSON file in a text editor
2. Copy the **entire JSON content**
3. Add to `/app/backend/.env`:

```env
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"jee-master-sheets-access@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'
```

**IMPORTANT**: Replace the entire JSON string with your actual credentials

### Option B: Using File Path

1. Upload the JSON file to `/app/backend/credentials.json`
2. Add to `.env`:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=/app/backend/credentials.json
```

---

## Step 6: Test the Integration

### Create a Google Sheet Manually

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it: `JEE PYQ YouTube Links - Test`
4. Copy the **Sheet ID** from URL:
   - URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
   - Copy the `SHEET_ID` part
5. Add to `/app/backend/.env`:

```env
GOOGLE_SHEET_ID=your_sheet_id_here
```

### Share Sheet with Service Account

1. In your Google Sheet, click **"Share"** button
2. Paste the service account email:
   - Find it in your JSON file: `client_email` field
   - Format: `jee-master-sheets-access@your-project.iam.gserviceaccount.com`
3. Give **"Editor"** permission
4. Uncheck **"Notify people"**
5. Click **"Share"**

---

## Step 7: Test API Connection

Run this test script to verify everything works:

```bash
cd /app/backend
python3 -c "
from services.google_sheets_service import GoogleSheetsManager
import os

# Test initialization
sheets = GoogleSheetsManager()
print('✅ Google Sheets service initialized')

# Test reading (requires sheet to be shared)
if sheets.service and os.environ.get('GOOGLE_SHEET_ID'):
    print('✅ Google Sheets API is ready!')
    print(f'📊 Sheet ID: {os.environ.get(\"GOOGLE_SHEET_ID\")}')
else:
    print('❌ Missing GOOGLE_SHEET_ID in environment')
"
```

---

## Step 8: Populate Google Sheet with Questions

### Manual Method (Immediate):

1. Open your Google Sheet
2. Add header row:
   ```
   Row ID | Question Number | Exam Type | Year | Subject | Chapter | Topic | Question Preview | YouTube URL | Timestamp (seconds) | Last Updated
   ```
3. Add question rows (Q001, Q002, etc.)
4. We have 25 Chemical Equilibrium questions ready to populate!

### Automated Method (Via API):

Once credentials are set, run:

```bash
curl -X POST "https://jee-test-engine.preview.emergentagent.com/api/admin/create-google-sheet" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

This will:
- Create a new Google Sheet automatically
- Populate with all 25 questions
- Add instructions sheet
- Return the sheet URL

---

## Step 9: Start Sync Mechanism

The system automatically syncs YouTube links every 30 seconds.

To manually trigger sync:

```bash
curl -X POST "https://jee-test-engine.preview.emergentagent.com/api/admin/sync-youtube-links" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

---

## Complete Environment Variables

Your `/app/backend/.env` should contain:

```env
# Existing variables
MONGO_URL=mongodb://...
DB_NAME=jee_master

# Google Sheets Integration
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_SHEET_ID=your_sheet_id_here
```

---

## Usage Instructions (For You)

### Adding YouTube Solution Links:

1. Open the Google Sheet
2. Find the question by Row ID (Q001, Q002, etc.)
3. In the **"YouTube URL"** column, paste the video URL:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
4. In the **"Timestamp (seconds)"** column, enter when solution starts:
   ```
   125  (for 2 minutes 5 seconds)
   ```
5. Save (auto-saves)
6. Wait 30 seconds - changes sync automatically!

### Finding Timestamp:

1. Pause YouTube video at the solution start point
2. Right-click → **"Copy video URL at current time"**
3. You'll get: `https://www.youtube.com/watch?v=VIDEO_ID&t=125s`
4. The number before `s` is the timestamp (125 seconds)

---

## Troubleshooting

### Error: "Failed to initialize Google Sheets service"
- Check credentials JSON is valid
- Ensure no line breaks in the JSON string in .env
- Verify service account key is correct

### Error: "Failed to sync YouTube links"
- Verify GOOGLE_SHEET_ID is correct
- Check sheet is shared with service account email
- Ensure sheet has correct column structure

### Error: "Permission denied"
- Share the sheet with service account email
- Give "Editor" permission, not just "Viewer"

### Links not syncing:
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Manually trigger sync via API
- Verify YouTube URL format is correct

---

## Quick Start (If You Already Have Credentials)

If you already have a Google Service Account JSON file:

```bash
# 1. Add to environment
echo "GOOGLE_CREDENTIALS_JSON='$(cat your-credentials.json | tr -d '\n')'" >> /app/backend/.env

# 2. Create and share a Google Sheet, then add its ID
echo "GOOGLE_SHEET_ID=your_sheet_id" >> /app/backend/.env

# 3. Restart backend
sudo supervisorctl restart backend

# 4. Test
curl http://localhost:8001/api/admin/questions-stats
```

---

## Next Steps

Once Google Sheets is set up:

1. ✅ Questions are already in database (25 Chemical Equilibrium questions)
2. ✅ API endpoints are ready
3. 🔄 Set up Google Sheets (follow steps above)
4. 🎨 Build PYQ frontend (next phase)
5. 🔗 Add YouTube links via Google Sheet
6. ✨ Students can practice with video solutions!

---

## Support

If you encounter any issues:
1. Check backend logs
2. Verify all environment variables
3. Test with the provided curl commands
4. Share error messages for debugging

