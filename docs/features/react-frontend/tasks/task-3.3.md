---
id: task-3.3
title: Build Upload view with CSV form and error handling
complexity: medium
method: write-test
blocked_by: [task-2.1, task-2.2]
blocks: [task-4.1]
files: [frontend/src/pages/UploadPage.tsx]
standards: []
---

## Description
Build the Upload view with a file input form for CSV files. Handles three response scenarios: success (201), validation errors (422), and file-too-large (413). Uses the `useUploadCSV` mutation hook.

## Actions
1. Create a file input with a submit button. Accept only `.csv` files
2. On submit, call `useUploadCSV().mutate(file)`
3. On success (201): display a success message with the count of ingested records (derived from `data.length`)
4. On 422 error: display a table of validation errors with columns: Row, Field, Message (from `ApiError.errors`)
5. On 413 error: display a message "File exceeds the maximum allowed upload size" (from `ApiError.detail`)
6. Show loading state while upload is in progress
7. Add a "Reset" button to clear the form and results for another upload
8. Style with Tailwind: clean form, success/error states with appropriate colors

## Edge Cases
- User submits without selecting a file: disable submit button when no file selected
- Network error: display generic error message

## Acceptance
- [ ] Valid CSV upload shows success message with ingested record count
- [ ] Invalid CSV upload (422) displays error table with row, field, message
- [ ] Oversized file upload (413) displays file-too-large error message
- [ ] Submit button is disabled when no file is selected or upload is in progress
- [ ] Form can be reset for another upload
