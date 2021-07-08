import time
import datetime


def interpret_time(gtime):

    return int(time.mktime(datetime.datetime.strptime(f'{datetime.datetime.strftime(datetime.datetime.now(), "%d/%m%Y")} {gtime}', "%d/%m%Y %H:%M:%S").timetuple()))
