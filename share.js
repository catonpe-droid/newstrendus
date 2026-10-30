/* NewsTrendus article sharing. No trackers, SDKs, or external JavaScript. */
(function () {
  'use strict';
  function init() {
    const article = document.querySelector('main.article-main article');
    if (!article || document.getElementById('nt-share-panel')) return;
    const content = article.querySelector('.nt-story-content') || article.querySelector('.article-inside:last-of-type') || article;
    const getMeta = (key) => document.querySelector('meta[property="' + key + '"],meta[name="' + key + '"]')?.content?.trim() || '';
    const canonical = document.querySelector('link[rel="canonical"]')?.href || window.location.href.split('#')[0];
    let pageURL;
    try {
      pageURL = new URL(canonical, window.location.origin);
      if (!['http:', 'https:'].includes(pageURL.protocol)) throw new Error('Invalid URL');
    } catch (_) { pageURL = new URL(window.location.href); }
    const url = pageURL.href;
    const title = getMeta('og:title') || article.querySelector('h1')?.textContent?.trim() || document.title;
    const desc = getMeta('og:description') || getMeta('description') || '';
    const image = getMeta('og:image') || article.querySelector('.nt-hero')?.src || '';
    const section = document.createElement('section');
    section.className = 'nt-share-panel';
    section.id = 'nt-share-panel';
    section.setAttribute('aria-label', 'Share this news article');

    const heading = document.createElement('h2');
    heading.textContent = 'Share this article';
    const intro = document.createElement('p');
    intro.className = 'nt-share-intro';
    intro.textContent = 'Found this story useful? Share it with someone who may want to read it.';
    section.append(heading, intro);

    const preview = document.createElement('div');
    preview.className = 'nt-share-preview';
    if (image && /^https:\/\//i.test(image)) {
      const photo = document.createElement('img');
      photo.src = image;
      photo.alt = getMeta('og:image:alt') || 'Representative image for this article';
      photo.loading = 'lazy';
      photo.decoding = 'async';
      preview.append(photo);
    }
    const previewText = document.createElement('div');
    previewText.className = 'nt-share-preview-copy';
    const previewLabel = document.createElement('span');
    previewLabel.className = 'nt-share-preview-site';
    previewLabel.textContent = 'NEWSTRENDUS.COM';
    const previewTitle = document.createElement('strong');
    previewTitle.textContent = title;
    previewText.append(previewLabel, previewTitle);
    if (desc) {
      const previewDesc = document.createElement('span');
      previewDesc.className = 'nt-share-preview-desc';
      previewDesc.textContent = desc;
      previewText.append(previewDesc);
    }
    preview.append(previewText);
    section.append(preview);

    const actions = document.createElement('div');
    actions.className = 'nt-share-actions';
    const shareOptions = [
      ['WhatsApp', 'wa', 'https://api.whatsapp.com/send?text=' + encodeURIComponent(title + ' — NewsTrendus\n' + url)],
      ['Facebook', 'fb', 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url)],
      ['X (Twitter)', 'x', 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(title) + '&url=' + encodeURIComponent(url)],
      ['LinkedIn', 'in', 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(url)]
    ];
    shareOptions.forEach(([label, key, href]) => {
      const link = document.createElement('a');
      link.className = 'nt-share-action nt-share-' + key;
      link.href = href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = label;
      link.setAttribute('aria-label', 'Share on ' + label);
      actions.append(link);
    });
    const copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'nt-share-action nt-share-copy';
    copy.textContent = 'Copy link';
    const status = document.createElement('span');
    status.className = 'nt-share-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    copy.addEventListener('click', async () => {
      let success = false;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(url);
          success = true;
        }
      } catch (_) {}
      if (!success) {
        const field = document.createElement('textarea');
        field.value = url;
        field.setAttribute('readonly', '');
        field.style.position = 'fixed';
        field.style.opacity = '0';
        document.body.append(field);
        field.select();
        try { success = document.execCommand('copy'); } catch (_) {}
        field.remove();
      }
      copy.textContent = success ? 'Copied!' : 'Copy unavailable';
      status.textContent = success ? 'Article link copied.' : 'Select and copy the link from your browser address bar.';
      window.setTimeout(() => { copy.textContent = 'Copy link'; status.textContent = ''; }, 2500);
    });
    actions.append(copy);

    if (typeof navigator.share === 'function') {
      const native = document.createElement('button');
      native.type = 'button';
      native.className = 'nt-share-action nt-share-native';
      native.textContent = 'More options';
      native.addEventListener('click', async () => {
        try { await navigator.share({ title, text: desc.slice(0, 180), url }); }
        catch (_) { /* User cancelled native share dialog. */ }
      });
      actions.append(native);
    }
    section.append(actions, status);
    content.append(section);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
