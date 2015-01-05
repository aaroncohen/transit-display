import arrow
import nextbus

ROUTE_BLACKLIST = ['88']


class Stop(object):
    def __init__(self, agency, stop_number, walk_time):
        self.agency = agency
        self.stop_number = int(stop_number)
        self.walk_time = int(walk_time)
        self.predictions = {}

    def update_predictions(self):
        self.predictions = get_bus_times(self.agency, self.stop_number, self.walk_time)

    def routes(self):
        return self.predictions.keys()


def get_bus_times(agency_tag, stop_id, walk_time):
    routes = {}

    try:
        predictions = nextbus.get_predictions_for_stop(agency_tag, stop_id).predictions
    except Exception:
        print "Failed to get times from NextBus"
        return routes

    for prediction in predictions:
        route_title = prediction.direction.route.title

        if route_title not in ROUTE_BLACKLIST:
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
