document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const themeBtn = document.getElementById('theme-toggle');

  // Загружаем предыдущую тему
  if (localStorage.getItem('theme') === 'dark') {
    body.classList.add('dark');
    themeBtn.textContent = '☀️';
  }

  themeBtn.addEventListener('click', () => {
    body.classList.toggle('dark');
    if (body.classList.contains('dark')) {
      localStorage.setItem('theme', 'dark');
      themeBtn.textContent = '☀️';
    } else {
      localStorage.setItem('theme', 'light');
      themeBtn.textContent = '🌙';
    }
  });
});
