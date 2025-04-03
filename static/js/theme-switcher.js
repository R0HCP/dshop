// static/js/theme-switcher.js
document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-switcher-btn');
    const body = document.body;

    // Проверка, найдена ли кнопка
    if (!themeToggleBtn) {
        console.error("ОШИБКА: Кнопка с ID 'theme-switcher-btn' не найдена!");
        return; // Если кнопки нет, дальше скрипт не выполнится
    }
     // Проверка, найден ли body
     if (!body) {
        console.error("ОШИБКА: Тег <body> не найден!");
        return;
    }

    // Функция для установки начальной темы
    const initializeTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            body.classList.add('dark-theme'); // Применяем темную тему, если сохранена
            console.log("Загружена темная тема (из localStorage)");
        } else {
            body.classList.remove('dark-theme'); // В остальных случаях - светлая (убираем класс темной)
             console.log("Загружена светлая тема (по умолчанию или из localStorage)");
        }
    };

    // Функция для переключения темы при клике
    const toggleTheme = () => {
        body.classList.toggle('dark-theme'); // Добавляет класс, если его нет, убирает - если есть

        // Сохраняем выбор в localStorage
        if (body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
            console.log("Переключено на темную тему. Выбор сохранен.");
        } else {
            localStorage.setItem('theme', 'light');
             console.log("Переключено на светлую тему. Выбор сохранен.");
        }
    };

    // Устанавливаем тему при загрузке страницы
    initializeTheme();

    // Вешаем обработчик клика на кнопку
    console.log("Добавляем обработчик клика на кнопку...");
    themeToggleBtn.addEventListener('click', toggleTheme);
     console.log("Обработчик клика добавлен.");

});