import time
from operator import itemgetter
from lcd_manager import display_on_lcd
import lcd_manager
from stop import Stop

import threading


# (stop number, time to walk -- add 3 to google maps)
STOPS = [
    Stop('actransit', 53653, 5),  # Market & 46th
    Stop('emery', 5357, 11),  # 40th and San Pab -- toward BART (Powell)
    Stop('emery', 5317, 11),  # 40th and San Pab -- toward BART (Hollis)
    Stop('emery', 5367, 12),  # 40th and San Pab -- toward Eville
    Stop('emery', 5341, 13)   # IHOP toward Eville
]


def cycle_screens(dwell_time=5):
    if not sum([len(stop.predictions) for stop in STOPS]) > 0:
        lcd_manager.off()
        time.sleep(60)
        return

    for stop in STOPS:
        for route_name, times in stop.predictions.iteritems():
            predictions = sorted(times, key=itemgetter("epoch_time"))
            joined_time = " & ".join([prediction['friendly_time'] for prediction in predictions if prediction['friendly_time']][:2]) or "No prediction"

            top_line = "%s-%s" % (route_name, predictions[0]['destination'])
            bottom_line = "%s" % joined_time

            display_on_lcd([top_line, bottom_line])
            time.sleep(dwell_time)
            1/0


def update_all_latest_predictions():
    for stop in STOPS:
        stop.update_predictions()


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
            try:
                update_all_latest_predictions()
            except Exception as e:
                display_on_lcd([str(e)[0:lcd_manager.LCD_WIDTH], str(e)[lcd_manager.LCD_WIDTH:lcd_manager.LCD_WIDTH*2]])
                raise e
            time.sleep(30)


class ScreenThread(StoppableThread):
    def run(self):
        while not self._stop.is_set():
            try:
                cycle_screens()
            except Exception as e:
                display_on_lcd([str(e)[0:lcd_manager.LCD_WIDTH], str(e)[lcd_manager.LCD_WIDTH:lcd_manager.LCD_WIDTH*2]])
                raise e

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
