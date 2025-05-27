document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.local.get(['lastMetadata','lastKey'], ({ lastMetadata, lastKey }) => {
      const c = document.getElementById('metadata');
      if (!lastMetadata) {
        c.textContent = 'No metadata available yet.';
        return;
      }
  
      c.innerHTML = `
        <p><strong>Uploaded Key:</strong> <code>${lastKey}</code></p>
        <p><strong>Uploaded At:</strong> ${lastMetadata.uploaded || '—'}</p>
        <p><strong>Title:</strong> ${lastMetadata.title || '—'}</p>
        <p><strong>Author:</strong> ${lastMetadata.author || '—'}</p>
        <p><strong>Pages:</strong> ${lastMetadata.pages}</p>
        <p><strong>Preview:</strong><br>${lastMetadata.preview}</p>
      `;
    });
  });