"""
Глобальные настройки
"""

import os

LOG_PATH = os.path.join(os.getcwd(), "app.log")
DB_LOG_PATH = os.path.join(os.getcwd(), "db.log")
SETTINGS_PATH = os.path.join(os.getcwd(), "settings.ini")
TICKET_PATH = os.path.join(os.getcwd(), "tickets")
ALGORITHM_PATH = os.path.join(os.getcwd(), "algorithms")
TICKET_TEMPLATE_PATH = os.path.join(os.getcwd(), "manager", "modes", "ticket_templates.json")
