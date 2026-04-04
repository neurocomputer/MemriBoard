"""
Шаблон ini файла
"""

TEMPLATE_INI = """
; настройки отладки
[debug]
; в board максимально быстро
fastest=0

; настройки журналирования
[logging]

; Application logging
; logging levels: debug | info | warning | error | critical
app_logging_level=warning
; Whether to rewrite log file on start or create new each time
app_log_rewrite_on_start=1

; Database logging
; logging levels: debug | info | warning | error | critical
database_logging_level=warning
; Whether to rewrite log file on start or create new each time
database_log_rewrite_on_start=1

; настройки подключения
[connector]
; 0-подробная запись в лог
silent=0
; com-порт
com_port=
; таймаут запроса доступа (75)
timeout=0.075
; количество попыток доступа
attempts_to_kick=20

; настройки очередей
[queues]
; глубина очереди для результатов
resmax=3000

; настройка параметров платы
[board]
; тип платы
board_type=
; разрядность ЦАП
dac_bit=12
; опорное напряжение ЦАП
vol_ref_dac=5
; нагрузочный резистор
res_load=3000
; напряжение чтения
vol_read=0.3
; разрядность АЦП
adc_bit=14
; опорное напряжение АЦП
vol_ref_adc=5
; сопротивление переключателей
res_switches=10
; усиление
gain=11
; резистор обратной связи сумматора
sum_gain=330
; время импульса чтения (мкс)
read_time=1200
; время простоя между записью и чтением (мкс)
blank_time=5
; время простоя между запросами (мкс)
blank_time_between=55000
; программный ограничитель тока
soft_cc=0.002

; настройки интерфейса
[gui]
; последний подключенныый кроссбар
last_crossbar_serial=
; тикет для чтения
measure_ticket=measure.json
; тикет для записи весов
program_ticket=programming.json
; ячейки для записи
writable_cells=
; блокировка платы
lock_board_type=0
; локализация
language=English

; бэкап датабазы
[backup]
; путь для бэкапа
backup_path=
"""