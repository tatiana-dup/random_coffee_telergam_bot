from ..config import load_config


config = load_config()
tz_name = config.time.name

DATE_FORMAT = '%d.%m.%Y'
DATE_TIME_FORMAT_LOCALTIME = f'%d.%m.%Y %H:%M {tz_name}'
DATE_TIME_FORMAT_UTC = '%d.%m.%Y %H:%M'
DATE_FORMAT_1 = '%Y.%m.%d'

DEFAULT_GLOBAL_INTERVAL_WEEKS = 2
