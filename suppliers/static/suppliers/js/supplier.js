/* ════════════════════════════════════════════════
   RECOSHOP PRO — Supplier JS (minimal)
   Le reste est géré par main.js du client
════════════════════════════════════════════════ */

'use strict';

// Validation du formulaire produit (prix barré > prix)
document.addEventListener('DOMContentLoaded', function () {
  const productForm = document.getElementById('productForm');
  if (!productForm) return;

  productForm.addEventListener('submit', function (e) {
    const price     = parseFloat(document.querySelector('[name=price]')?.value) || 0;
    const origPrice = parseFloat(document.querySelector('[name=original_price]')?.value) || 0;

    if (origPrice > 0 && origPrice <= price) {
      e.preventDefault();
      alert('Le prix barré doit être supérieur au prix actuel.');
      document.querySelector('[name=original_price]').focus();
    }
  });
});
