import time
from abbreviations import bart_abbreviations, city_abbreviations
import nextbus
import arrow
from operator import itemgetter
from lcd import lcd

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


def strike(text):
    return '\u0336'.join(text) + '\u0336'


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
    for agency, stops in STOPS.iteritems():
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
        if not prediction.direction.route.title in routes:
            routes[prediction.direction.route.title] = []
        routes[prediction.direction.route.title].append(
            {
                'epoch_time': prediction.epoch_time,
                'destination': prediction.direction.title,
                'friendly_time': friendly_prediction_time(prediction.epoch_time, walk_time)
            }
        )
    return routes

if __name__ == "__main__":
    while True:
        cycle_screens(5)
