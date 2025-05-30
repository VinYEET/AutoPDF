const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

const PRESIGN_URL  = 'https://u17smv77x1.execute-api.us-east-1.amazonaws.com/prod/presign';
const METADATA_URL = 'https://u17smv77x1.execute-api.us-east-1.amazonaws.com/prod/metadata';

const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const statusDiv = document.getElementById('status');

// Disable upload if file >5 MiB
fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (file && file.size > MAX_UPLOAD_BYTES) {
    statusDiv.textContent = `❌ File too large (>${MAX_UPLOAD_BYTES/1024/1024} MB).`;
    uploadBtn.disabled = true;
  } else {
    statusDiv.textContent = '';
    uploadBtn.disabled = !file;
  }
});

uploadBtn.addEventListener('click', async () => {
  const file     = fileInput.files[0];
  const filename = encodeURIComponent(file.name);

  try {
    // Get presigned POST info
    statusDiv.textContent = 'Requesting upload URL…';
    const presignResp = await fetch(`${PRESIGN_URL}?filename=${filename}`);
    if (!presignResp.ok) throw new Error(`Presign error (${presignResp.status})`);
    const { url, fields, key } = await presignResp.json();

    // Upload via multipart/form-data POST
    statusDiv.textContent = 'Uploading file…';
    const fd = new FormData();
    Object.entries(fields).forEach(([k, v]) => fd.append(k, v));
    fd.append('file', file);

    const uploadResp = await fetch(url, { method: 'POST', body: fd });
    if (!uploadResp.ok) throw new Error(`Upload failed (${uploadResp.status})`);

    // Poll the metadata API for results
    statusDiv.textContent = 'Upload complete! Fetching metadata…';
    let metadata = null;
    for (let i = 0; i < 10; i++) {
      await new Promise(r => setTimeout(r, 1000));
      const metaResp = await fetch(`${METADATA_URL}?key=${encodeURIComponent(key)}`);
      if (metaResp.ok) {
        metadata = await metaResp.json();
        break;
      }
    }

    // Store & show the metadata in a tab
    if (!metadata) {
      statusDiv.textContent = 'Metadata not available yet—try again shortly.';
    } else {
      chrome.storage.local.set({ lastMetadata: metadata, lastKey: key }, () => {
        chrome.tabs.create({ url: chrome.runtime.getURL('metadata.html') });
      });
    }

  } catch (err) {
    statusDiv.textContent = `Error: ${err.message}`;
  }
});
