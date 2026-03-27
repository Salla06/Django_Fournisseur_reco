/* ════════════════════════════════════════════════
   RECOSHOP PRO — Supplier JS
════════════════════════════════════════════════ */

'use strict';

// ── Sidebar mobile toggle ──────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('spSidebar');
  if (sidebar) sidebar.classList.toggle('open');
}

// Fermer la sidebar en cliquant hors
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('spSidebar');
  const hamburger = document.querySelector('.sp-hamburger');
  if (
    sidebar &&
    sidebar.classList.contains('open') &&
    !sidebar.contains(e.target) &&
    hamburger &&
    !hamburger.contains(e.target)
  ) {
    sidebar.classList.remove('open');
  }
});

// ── Auto-hide alerts ───────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.sp-alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity .5s ease';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, 500);
    }, 4000);
  });
});

// ── Active nav link highlight ──────────────────
document.addEventListener('DOMContentLoaded', function () {
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sp-nav-link').forEach(function (link) {
    if (link.href && link.getAttribute('href') !== '#') {
      const linkPath = new URL(link.href, window.location.origin).pathname;
      if (currentPath === linkPath) {
        link.classList.add('active');
      }
    }
  });
});

// ── Form validation helpers ────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const productForm = document.getElementById('productForm');
  if (!productForm) return;

  const priceInput = document.getElementById('id_price');
  const origPriceInput = document.getElementById('id_original_price');

  productForm.addEventListener('submit', function (e) {
    let valid = true;
    const errors = [];

    // Vérifier que le prix original est supérieur au prix si renseigné
    if (priceInput && origPriceInput && origPriceInput.value) {
      const price = parseFloat(priceInput.value);
      const origPrice = parseFloat(origPriceInput.value);
      if (!isNaN(price) && !isNaN(origPrice) && origPrice <= price) {
        errors.push('Le prix original doit être supérieur au prix actuel.');
        valid = false;
      }
    }

    if (!valid) {
      e.preventDefault();
      // Afficher les erreurs
      let container = document.getElementById('js-errors');
      if (!container) {
        container = document.createElement('div');
        container.id = 'js-errors';
        productForm.insertBefore(container, productForm.firstChild);
      }
      container.innerHTML = errors.map(function (err) {
        return '<div class="sp-alert sp-alert-error">' + err + '</div>';
      }).join('');
      container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
});

// ── Table row clickable ────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.sp-table tbody tr').forEach(function (row) {
    const viewLink = row.querySelector('.sp-action-view');
    if (viewLink) {
      row.style.cursor = 'pointer';
      row.addEventListener('click', function (e) {
        if (!e.target.closest('.sp-table-actions')) {
          window.location.href = viewLink.href;
        }
      });
    }
  });
});
