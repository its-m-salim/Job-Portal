// Небольшой скрипт для интерфейса. Работает без библиотек.
document.addEventListener('DOMContentLoaded', function () {

  // 1) Меню-бургер на телефоне
  var nav = document.getElementById('nav');
  var toggle = document.querySelector('.nav-toggle');
  if (nav && toggle) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // 2) Кнопка "Показать пароль"
  document.querySelectorAll('.pass-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = btn.parentElement.querySelector('input');
      var hidden = input.type === 'password';
      input.type = hidden ? 'text' : 'password';
      btn.textContent = hidden ? 'Скрыть' : 'Показать';
    });
  });

  // 3) Фильтры на главной применяются сразу при выборе
  document.querySelectorAll('[data-autosubmit]').forEach(function (el) {
    el.addEventListener('change', function () { el.form.submit(); });
  });

  // 4) Подтверждение опасных действий: <form data-confirm="Вы уверены?">
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // 5) На телефоне блок фильтров по умолчанию свёрнут
  var filters = document.querySelector('details.filters');
  if (filters && window.matchMedia('(max-width: 900px)').matches) {
    filters.removeAttribute('open');
  }
});
