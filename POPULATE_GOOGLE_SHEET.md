# Instructions to Populate Google Sheet Manually

Since Google Sheets API requires service account credentials, here's how to populate your sheet manually for now:

## Sheet URL
https://docs.google.com/spreadsheets/d/1dIvu9tkyDGjyXIJshHv0P3W5LEN9K_kjkKrUiEIUl3Y/edit?usp=sharing

## Step 1: Set up Headers

Add these headers in Row 1:
```
A1: Row ID
B1: Question Number
C1: Exam Type
D1: Year
E1: Subject
F1: Chapter
G1: Topic
H1: Question Preview
I1: YouTube URL
J1: Timestamp (seconds)
K1: Last Updated
```

## Step 2: Copy-Paste This Data

I'll generate a CSV you can copy directly into the sheet.

Run this command to generate the CSV:

```bash
cd /app/backend
python3 << 'EOF'
from seed.chemical_equilibrium_questions import CHEMICAL_EQUILIBRIUM_QUESTIONS
import csv

rows = []
for i, q in enumerate(CHEMICAL_EQUILIBRIUM_QUESTIONS, 1):
    row_id = f"Q{str(i).zfill(3)}"
    preview = q['questionText'][:50].replace('\n', ' ') + "..."
    
    row = [
        row_id,
        q['questionNumber'],
        q['examType'],
        q['year'],
        q['subject'],
        q['chapter'],
        q['topic'],
        preview,
        "",  # YouTube URL
        0,   # Timestamp
        ""   # Last Updated
    ]
    rows.append(row)

# Print as tab-separated (easy to paste into Google Sheets)
for row in rows:
    print('\t'.join(str(x) for x in row))

EOF
```

Then:
1. Copy the output
2. Go to your Google Sheet
3. Click on cell A2
4. Paste (Ctrl+V)
5. All 25 questions will populate!

## Alternative: Use the provided CSV file

I'll create a CSV file you can import directly into Google Sheets.
