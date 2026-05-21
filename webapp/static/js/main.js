let isMeasuring = false;

// Загрузка истории с сервера
async function loadHistory() {
    try {
        // 1. Запрашиваем историю с бекенда
        const response = await fetch('/history');
        
        // 2. Преобразуем ответ в JSON-массив объектов {timestamp, country}
        const history = await response.json();
        
        // 3. Находим таблицу в браузере и очищаем её текущее содержимое
        const tbody = document.getElementById('historyBody');
        tbody.innerHTML = '';
        
        // 4. Если история пуста — показываем сообщение
        if (history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="loading">Нет записей</td></tr>';
            return;
        }
        
        // 5. Перебираем записи в обратном порядке (сначала новые)
        history.slice().reverse().forEach(item => {
            const row = tbody.insertRow();           // Создаём строку таблицы
            row.insertCell(0).textContent = item.timestamp;      // Время измерения
            row.insertCell(1).textContent = item.request_type;   // Количество точек
        });
        
    } catch (e) {
        // 6. Логируем ошибку в консоль (например, если сервер недоступен)
        console.error('Ошибка загрузки истории:', e);
    }
}

// Показать ошибку
function showError(message) {
    const errorDiv = document.getElementById('errorMsg');  // Находим блок для ошибок
    errorDiv.textContent = message;                       // Устанавливаем текст ошибки
    errorDiv.classList.add('show');                       // Делаем блок видимым (CSS: display: block)
    setTimeout(() => errorDiv.classList.remove('show'), 3000); // Скрываем через 3 секунды
}

// Запуск измерения ВАХ
async function startMeasurement() {
    // Защита от повторного нажатия во время измерения
    if (isMeasuring) {
        showError('Измерение уже выполняется. Дождитесь завершения.');
        return;
    }

    // Блокируем кнопку и меняем её текст
    const btn = document.getElementById('measureBtn');
    isMeasuring = true;
    btn.disabled = true;
    btn.textContent = 'Снятие ВАХ...';
    
    // Массивы для накопления точек
    let xData = [];  // Напряжения
    let yData = [];  // Токи
    
    // Настройка графика (линии + маркеры)
    const trace = {
        x: [], y: [],
        mode: 'lines+markers',
        type: 'scatter',
        name: 'ВАХ',
        line: { color: '#007bff', width: 2 },   // Синяя линия
        marker: { size: 8, color: '#007bff' }   // Синие маркеры
    };
    
    // Настройка осей с автоматическим масштабированием
    const layout = {
        title: 'Снятие ВАХ... точки появляются по мере измерения',
        xaxis: { title: 'Напряжение (В)', autorange: true, gridcolor: '#eee' },
        yaxis: { title: 'Ток (А)', autorange: true, gridcolor: '#eee' },
        showlegend: false,
        margin: { l: 50, r: 50, t: 60, b: 50 },
        modebar: { orientation: 'v', bgcolor: 'rgba(255,255,255,0.9)', color: '#444' }
    };
    
    // Создаём новый график (очищаем старый)
    Plotly.newPlot('plot', [trace], layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']  // Убираем лишние кнопки
    });
    
    try {
        // Отправляем POST-запрос на сервер для начала измерения
        const response = await fetch('/measure-stream', { method: 'POST' });

        // 👇 НОВАЯ ПРОВЕРКА: если сервер занят другим пользователем
        if (response.status === 409) {
            const error = await response.json();
            showError('⚠️ ' + error.error);
            btn.disabled = false;
            isMeasuring = false;
            btn.textContent = 'Снять ВАХ';
            return;  // Выходим, не пытаемся читать поток
        }


        // Получаем потоковое чтение ответа (SSE - Server-Sent Events)
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Бесконечный цикл чтения поступающих точек
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;  // Поток закрыт
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);  // Убираем префикс "data: "
                    
                    if (data === 'DONE') {
                        // Измерение завершено
                        await loadHistory();                 // Обновляем историю
                        btn.disabled = false;
                        isMeasuring = false;
                        btn.textContent = 'Снять ВАХ';
                        
                        // Финальное масштабирование осей с отступами 10%
                        if (xData.length > 0) {
                            const xMin = Math.min(...xData);
                            const xMax = Math.max(...xData);
                            const yMin = Math.min(...yData);
                            const yMax = Math.max(...yData);
                            const xPadding = (xMax - xMin) * 0.1 || 1;
                            const yPadding = (yMax - yMin) * 0.1 || 1;
                            
                            Plotly.relayout('plot', {
                                'xaxis.range': [xMin - xPadding, xMax + xPadding],
                                'yaxis.range': [yMin - yPadding, yMax + yPadding]
                            });
                        }
                        return;
                    } else {
                        // Получили новую точку: парсим напряжение и ток
                        const [voltage, current] = data.split(',').map(Number);
                        xData.push(voltage);
                        yData.push(current);
                        
                        // Обновляем график новой точкой
                        Plotly.update('plot', { x: [xData], y: [yData] }, {}, [0]);
                        
                        // Автоматическое масштабирование после каждой точки
                        if (xData.length > 0) {
                            const xMin = Math.min(...xData);
                            const xMax = Math.max(...xData);
                            const yMin = Math.min(...yData);
                            const yMax = Math.max(...yData);
                            const xPadding = (xMax - xMin) * 0.1 || 0.5;
                            const yPadding = (yMax - yMin) * 0.1 || 0.5;
                            
                            Plotly.relayout('plot', {
                                'xaxis.range': [xMin - xPadding, xMax + xPadding],
                                'yaxis.range': [yMin - yPadding, yMax + yPadding]
                            });
                        }
                    }
                }
            }
        }
    } catch (error) {
        // Обработка ошибок (сеть, сервер и т.д.)
        showError('Ошибка: ' + error.message);
        btn.disabled = false;
        isMeasuring = false;
        btn.textContent = 'Снять ВАХ';
    }
}

// Инициализация пустого графика
async function initEmptyPlot() {
    // Описание данных графика (trace)
    const trace = {
        x: [],                      // Массив координат X (напряжение) — пока пуст
        y: [],                      // Массив координат Y (ток) — пока пуст
        mode: 'lines+markers',      // Режим отображения: линии + маркеры точек
        type: 'scatter',            // Тип графика: точечный с линиями
        name: 'ВАХ'                 // Название для легенды (не отображается т.к. showlegend: false)
    };
    
    // Настройка внешнего вида и осей
    const layout = {
        title: { text: 'Нажмите "Снять ВАХ" для построения графика'},  // Заголовок графика
        xaxis: {
            title: {text: 'Напряжение (В)'},    // Подпись оси X
            range: [-2, 2],             // Фиксированный диапазон от -6 до 6 В
            gridcolor: '#eee'           // Светло-серые линии сетки
        },
        yaxis: {
            title: {text: 'Ток (А)'},            // Подпись оси Y
            range: [-0.001, 0.001],              // Фиксированный диапазон от -2 до 2 А
            gridcolor: '#eee'            // Светло-серые линии сетки
        },
        showlegend: false,               // Скрыть легенду
        //margin: { l: 70, r: 50, t: 60, b: 70 }   // Отступы: лево, право, верх, низ
    };
    
    // Создаём график в контейнере с id="plot"
    Plotly.newPlot('plot', [trace], layout, {
        responsive: true,       // Адаптация под размер экрана
        displayModeBar: false    // Показывать панель инструментов
    });
}

// Назначение обработчиков событий
document.addEventListener('DOMContentLoaded', async () => {
    // DOM полностью загрузился, можно безопасно работать с элементами страницы
    
    await initEmptyPlot();      // 1. Рисуем пустой график (ожидаем завершения)
    await loadHistory();        // 2. Загружаем историю запросов с сервера
    
    const measureBtn = document.getElementById('measureBtn');  // 3. Находим кнопку
    measureBtn.addEventListener('click', startMeasurement);    // 4. Вешаем обработчик клика
});

// Автообновление истории каждые 5 секунд
setInterval(() => {           // Запускаем таймер, который срабатывает каждые 5000 мс
    if (!isMeasuring) {       // Проверяем: не идёт ли сейчас измерение ВАХ
        loadHistory();        // Если нет — обновляем таблицу истории (чтобы видеть запросы других пользователей)
    }
}, 5000);