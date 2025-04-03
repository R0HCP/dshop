// theme-switcher.js

const themeToggleBtn = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('theme');
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

// Функция для применения темы
const applyTheme = (theme) => {
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        if (themeToggleBtn) {
           themeToggleBtn.querySelector('.toggle-text').textContent = 'Темная тема';
           // Доп. логика для ARIA, если нужно
           // themeToggleBtn.setAttribute('aria-pressed', 'true');
        }
    } else {
        // Если тема 'light' или не установлена, применяем светлую
        document.documentElement.removeAttribute('data-theme'); // Убираем атрибут, чтобы сработали стили :root или @media
        localStorage.setItem('theme', 'light'); // Сохраняем как светлую для ясности
         if (themeToggleBtn) {
           themeToggleBtn.querySelector('.toggle-text').textContent = 'Светлая тема';
           // Доп. логика для ARIA, если нужно
           // themeToggleBtn.setAttribute('aria-pressed', 'false');
        }
    }
};

// 1. Проверяем сохраненную тему в localStorage
if (currentTheme) {
    applyTheme(currentTheme);
} else {
    // 2. Если в localStorage нет, проверяем настройки ОС
    if (prefersDarkScheme.matches) {
        applyTheme('dark'); // Применяем темную, но НЕ сохраняем в localStorage, чтобы системная настройка оставалась главной
        // Важно: НЕ используем localStorage.setItem здесь, чтобы при смене системной темы без перезагрузки страницы (если браузер поддерживает), тема сайта тоже менялась (см. listener ниже)
    } else {
        applyTheme('light'); // Применяем светлую по умолчанию
    }
}

// 3. Слушатель для кнопки
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const newTheme = document.documentElement.hasAttribute('data-theme') ? 'light' : 'dark';
        applyTheme(newTheme); // Применяем и сохраняем в localStorage
    });
}

// 4. (Опционально) Слушатель изменения системной темы
// Сработает, если пользователь меняет тему ОС, пока сайт открыт,
// и если пользователь ДО ЭТОГО не выбрал тему вручную на сайте.
prefersDarkScheme.addEventListener('change', (e) => {
    // Переключаем тему сайта, ТОЛЬКО если в localStorage нет явного выбора пользователя
    if (!localStorage.getItem('theme') || localStorage.getItem('theme') === null) { // проверяем еще раз на всякий случай
       applyTheme(e.matches ? 'dark' : 'light');
       // Важно: все еще НЕ сохраняем в localStorage здесь
    } else if(localStorage.getItem('theme') === 'dark' && !e.matches) {
        // Если пользователь выбрал темную, а ОС стала светлой, И МЫ ХОТИМ, чтобы сайт остался темным - ничего не делаем.
        // Если ХОТИМ, чтобы сайт СЛЕДОВАЛ за ОС даже после ручного выбора - раскомментировать строку ниже
        // applyTheme('light');
    } else if(localStorage.getItem('theme') === 'light' && e.matches) {
        // Если пользователь выбрал светлую, а ОС стала темной, И МЫ ХОТИМ, чтобы сайт остался светлым - ничего не делаем.
        // Если ХОТИМ, чтобы сайт СЛЕДОВАЛ за ОС даже после ручного выбора - раскомментировать строку ниже
        // applyTheme('dark');
    }
});

// Убедимся, что текст кнопки соответствует ИЗНАЧАЛЬНОЙ теме при загрузке
document.addEventListener('DOMContentLoaded', () => {
    if(document.documentElement.hasAttribute('data-theme')){
        if (themeToggleBtn) themeToggleBtn.querySelector('.toggle-text').textContent = 'Темная тема';
    } else {
        if (themeToggleBtn) themeToggleBtn.querySelector('.toggle-text').textContent = 'Светлая тема';
    }
});