from dataclasses import dataclass


from environs import Env
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

#
# def get_logger():
#     logger = logging.getLogger(__file__)
#     logger.setLevel(logging.DEBUG)
#     format_log = logging.Formatter(u'%(filename)s:%(lineno)d #%(levelname)-8s '
#                u'[%(asctime)s]: %(message)s')
#     logger_path = BASE_DIR / 'logs' / f'{__name__}.log'
#     file_handler = logging.FileHandler(logger_path, mode='w', encoding='UTF-8')
#     file_handler.setFormatter(format_log)
#     file_handler.setLevel(logging.DEBUG)
#
#     std_handler = logging.StreamHandler()
#     std_handler.setFormatter(format_log)
#     std_handler.setLevel(logging.DEBUG)
#
#     logger.addHandler(file_handler)
#     logger.addHandler(std_handler)
#     return logger


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default_formatter': {
            'format': "%(asctime)s - [%(levelname)8s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
        },
        'rotating_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "my"}.log',
            'backupCount': 1,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
        'errors_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "errors"}.log',
            'backupCount': 1,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
    },
    'loggers': {
        'my_logger': {
            'handlers': ['rotating_file_handler'],
            'level': 'INFO',
            'propagate': True
        },
        'errors_logger': {
            'handlers': ['errors_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


@dataclass
class DatabaseConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_port: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота
    base_dir = BASE_DIR


@dataclass
class Proxy:
    adress: str
    user: str
    password: str
    port: str


@dataclass
class Logic:
    STOP_TOKEN: list


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    proxy: Proxy
    logic: Logic


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'),
                               admin_ids=list(map(int, env.list('ADMIN_IDS'))),
                               ),
                  db=DatabaseConfig(database=env('DB_NAME'),
                                    db_host=env('DB_HOST'),
                                    db_port=env('DB_PORT'),
                                    db_user=env('DB_USER'),
                                    db_password=env('DB_PASSWORD'),
                                    ),
                  proxy=Proxy(adress=env('PROXY_ADRESS'),
                              user=env('PROXY_USER'),
                              password=env('PROXY_PASSWORD'),
                              port=env('PROXY_PORT'),
                              ),
                  logic=Logic(STOP_TOKEN=list(map(str, env.list('STOP_TOKEN')))),
                  )


config = load_config('myenv.env')

# print('BOT_TOKEN:', config.tg_bot.token)
# print('ADMIN_IDS:', config.tg_bot.admin_ids)
# print()
# print('DATABASE:', config.db.database)
# print('DB_HOST:', config.db.db_host)
# print('DB_port:', config.db.db_port)
# print('DB_USER:', config.db.db_user)
# print('DB_PASSWORD:', config.db.db_password)
# print(config.tg_bot.admin_ids)
print(config.logic)
