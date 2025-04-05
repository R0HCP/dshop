// dshop/static/js/theme-switcher.js

(function() {
    const htmlElement = document.documentElement;
    const switchButton = document.getElementById('theme-switcher-btn');
    const iconSun = document.getElementById('theme-icon-sun');
    const iconMoon = document.getElementById('theme-icon-moon');

    // Функция для применения темы
    const applyTheme = (theme) => {
        htmlElement.setAttribute('data-bs-theme', theme);
        if (iconSun && iconMoon) {
            if (theme === 'dark') {
                iconSun.classList.add('d-none');
                iconMoon.classList.remove('d-none');
            } else {
                iconSun.classList.remove('d-none');
                iconMoon.classList.add('d-none');
            }
        }
    };

    // Функция для определения предпочитаемой ОС темы
    const getPreferredTheme = () => {
        // Сначала проверяем сохраненную тему в localStorage
        try {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                return savedTheme;
            }
        } catch (e) {
            console.error("LocalStorage error:", e);
            // Если localStorage недоступен, продолжаем без сохраненной темы
        }

        // Если сохраненной темы нет, проверяем системные настройки
        // window.matchMedia('(prefers-color-scheme: dark)').matches вернет true, если ОС в темном режиме
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    // Функция для переключения темы (остается такой же)
    const toggleTheme = () => {
        const currentTheme = htmlElement.getAttribute('data-bs-theme') || getPreferredTheme(); // Получаем текущую или предпочитаемую
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        applyTheme(newTheme);
        // Сохраняем ЯВНЫЙ выбор пользователя в localStorage
        try {
            localStorage.setItem('theme', newTheme);
        } catch (e) {
            console.error("LocalStorage error:", e);
        }
    };

    // --- Применение темы при загрузке ---
    const initialTheme = getPreferredTheme(); // Определяем тему (сохраненную или системную)
    applyTheme(initialTheme); // Применяем ее
    // --- Конец блока применения темы ---

    // Навешиваем обработчик на кнопку
    if (switchButton) {
        switchButton.addEventListener('click', toggleTheme);
    } else {
        console.warn("Theme switcher button not found.");
    }

    // (Опционально) Слушаем изменения системной темы,
    // но ПЕРЕКЛЮЧАЕМ только если пользователь НЕ делал явный выбор
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        try {
            const savedTheme = localStorage.getItem('theme');
            // Если пользователь НЕ сохранял тему вручную, следуем за системой
            if (!savedTheme) {
                applyTheme(event.matches ? 'dark' : 'light');
            }
        } catch (e) {
            console.error("LocalStorage error:", e);
            // В случае ошибки, возможно, стоит просто применить системную тему
            applyTheme(event.matches ? 'dark' : 'light');
        }
    });

})();