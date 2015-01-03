import time
import signal
from abbreviations import bart_abbreviations, city_abbreviations
import nextbus
import arrow
from operator import itemgetter

try:
    from lcd import lcd
except ImportError:
    import mocklcd as lcd

import threading

LCD_WIDTH = 16
LCD_HEIGHT = 2

ROUTE_BLACKLIST = []

# (stop number, time to walk -- add 3 to google maps)
STOPS = {
    'actransit': [
        (53653, 5)  # Market & 46th
    ],
    'emery': [
        (5357, 11),  # 40th and San Pab -- toward BART (Powell)
        (5317, 11),  # 40th and San Pab -- toward BART (Hollis)
        (5367, 12),  # 40th and San Pab -- toward Eville
        (5341, 13)   # IHOP toward Eville
    ]
}

latest_predictions = {}


def friendly_prediction_time(epoch_time, walk_time=None):
    time_till_secs = (arrow.get(epoch_time/1000.0) - arrow.now()).seconds

    if time_till_secs < 10:
        time_str = "now"
    elif time_till_secs < 60:
        time_str = "%s sec" % time_till_secs
    elif time_till_secs < 180 * 60:
        time_str = "%s min" % (int(time_till_secs / 60))
    else:
        time_str = "%s hr" % (time_till_secs / 60 / 60)

    if time_till_secs / 60. > walk_time + 10:
        urgency = ""
    elif time_till_secs / 60. > walk_time + 3:
        urgency = "!"
    elif time_till_secs / 60. > walk_time:
        urgency = " !!"
    else:
        urgency = ""
        time_str = ""

    return "%s%s" % (time_str, urgency)


def squish_text(text):
    squishes = 0
    while len(text) > LCD_WIDTH:
        if squishes == 0:
            for abbrev_dict in [bart_abbreviations, city_abbreviations]:
                for k, v in abbrev_dict.iteritems():
                    text = text.replace(k, v)
        elif squishes == 1:
            text = text.replace('To ', '')
            text = text.replace('to ', '')
        elif squishes == 2:
            text = text.replace(' ', '')
        else:
            text = text[:LCD_WIDTH]
        squishes += 1

    return text


def display_on_lcd(text_rows):
    squished_rows = []
    for row in text_rows[:LCD_HEIGHT]:
        if len(row) > LCD_WIDTH:
            squished_rows.append(squish_text(row)[:LCD_WIDTH])
        else:
            squished_rows.append(row.center(LCD_WIDTH))
    lcd.message("\n".join(squished_rows[:LCD_HEIGHT]))


def cycle_screens(dwell_time=5):
    for agency, stops in latest_predictions.iteritems():
        for stop, walk_time in stops:
            route_predictions = get_bus_times(agency, stop, walk_time)
            for route_name in sorted(route_predictions):
                if route_name in ROUTE_BLACKLIST:
                    continue

                predictions = sorted(route_predictions[route_name], key=itemgetter("epoch_time"))
                joined_time = " & ".join([prediction['friendly_time'] for prediction in predictions if prediction['friendly_time']][:2]) or "No prediction"

                top_line = ("%s-%s" % (route_name, predictions[0]['destination']))
                bottom_line = ("%s" % joined_time)

                display_on_lcd([top_line, bottom_line])
                time.sleep(dwell_time)


def get_bus_times(agency_tag, stop_id, walk_time):
    predictions = nextbus.get_predictions_for_stop(agency_tag, stop_id).predictions
    routes = {}
    for prediction in predictions:
        route_title = prediction.direction.route.title
        if not route_title in routes:
            routes[route_title] = []

        routes[route_title].append(
            {
                'epoch_time': prediction.epoch_time,
                'destination': prediction.direction.title,
                'friendly_time': friendly_prediction_time(prediction.epoch_time, walk_time)
            }
        )
    return routes


def get_latest_predictions(agency, stops):
    return {(stop, walk_time): get_bus_times(agency, stop, walk_time) for stop, walk_time in stops}


def update_all_latest_predictions():
    for agency, stops in STOPS.iteritems():
            latest_predictions[agency] = get_latest_predictions(agency, stops)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class APIThread(StoppableThread):
    def run(self):
        while not self._stop.is_set():
            update_all_latest_predictions()
            time.sleep(30)


class ScreenThread(StoppableThread):
    def run(self):
        while not self._stop.is_set():
            cycle_screens()

if __name__ == "__main__":
    update_all_latest_predictions()

    api_thread = APIThread()
    api_thread.daemon = True

    screen_thread = ScreenThread()
    screen_thread.daemon = True

    api_thread.start()
    screen_thread.start()

    api_thread.join()
    screen_thread.join()
