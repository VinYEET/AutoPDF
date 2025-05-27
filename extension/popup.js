// Your two API endpoints:
const PRESIGN_URL  = 'https://u17smv77x1.execute-api.us-east-1.amazonaws.com/prod/presign';
const METADATA_URL = 'https://u17smv77x1.execute-api.us-east-1.amazonaws.com/prod/metadata';

const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const statusDiv = document.getElementById('status');

// Enable the Upload button as soon as a file is selected
fileInput.addEventListener('change', () => {
  uploadBtn.disabled = !fileInput.files.length;
});

uploadBtn.addEventListener('click', async () => {
  const file     = fileInput.files[0];
  const filename = encodeURIComponent(file.name);

  try {
    // === Presign step ===
    statusDiv.textContent = 'Requesting upload URL…';
    const presignResp = await fetch(`${PRESIGN_URL}?filename=${filename}`);
    if (!presignResp.ok) throw new Error(`Presign failed (${presignResp.status})`);
    const { url, key } = await presignResp.json();

    // === Upload step ===
    statusDiv.textContent = 'Uploading file…';
    const uploadResp = await fetch(url, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/pdf' },
      body:     file
    });
    if (!uploadResp.ok) throw new Error(`Upload failed (${uploadResp.status})`);

    // === Poll for metadata ===
    statusDiv.textContent = 'Upload complete! Fetching metadata…';

    let metadata = null;
    for (let i = 0; i < 10; i++) {
      // wait 1s between attempts
      await new Promise(r => setTimeout(r, 1000));
      const metaResp = await fetch(`${METADATA_URL}?key=${encodeURIComponent(key)}`);
      if (metaResp.ok) {
        metadata = await metaResp.json();
        break;
      }
    }

    // === Render result ===
    if (!metadata) {
      statusDiv.innerHTML = `
        Uploaded as <strong>${key}</strong>.<br>
        Metadata still processing—check back later.
      `;
    } else {
      // Save & open tab
      chrome.storage.local.set({ lastMetadata: metadata, lastKey: key }, () => {
        chrome.tabs.create({ url: chrome.runtime.getURL('metadata.html') });
      });
    }

  } catch (err) {
    statusDiv.textContent = `Error: ${err.message}`;
  }
});
