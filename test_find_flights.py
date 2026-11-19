"""Checks for find_flights (cache, failures, cancel, self-transfer stitching) and the app's settings check,
with Google stubbed out. Run: python test_find_flights.py"""
import json, os, tempfile
from datetime import datetime, timedelta
import find_flights as ff
import flights_app as app  # before CACHE_FILE below: importing it points the cache at the app's data folder

ff.CACHE_FILE = os.path.join(tempfile.mkdtemp(), "qc.json")
ff.pause = lambda s: None
calls = []

def fake(o, d, day):
    calls.append((o, d, day))
    if o == "X":
        raise RuntimeError("429")
    if d == "NONE":
        return []
    return [{"orig": o, "dest": d, "date": day, "price": 10, "airline": "Ryanair", "flight_no": "FR1",
            "dep_time": "06:00", "arr_time": "07:00", "dep_dt": datetime(2026, 12, 20, 6), "arr_dt": datetime(2026, 12, 20, 7),
             "segments": [{"from": o, "to": d, "dep_dt": datetime(2026, 12, 20, 6), "arr_dt": datetime(2026, 12, 20, 7)}]},
            {"orig": o, "dest": d, "date": day, "price": 20, "dep_dt": datetime(2026, 12, 20, 9), "arr_dt": datetime(2026, 12, 20, 10),
             "segments": []}]

real_fetch = ff.fetch_one_way
ff.fetch_one_way = fake
tasks = [("CPH", "STN", "2026-12-20"), ("CPH", "NONE", "2026-12-20"), ("X", "STN", "2026-12-20")]
r1 = ff.fetch_many(tasks); n1 = len(calls)
r2 = ff.fetch_many(tasks); n2 = len(calls) - n1
assert len(r1) == 1 and n1 == 6, (len(r1), n1)      # X: first try + 3 retries
assert len(r2) == 1 and n2 == 4, n2                 # second run only re-asks the failure
assert r2[0]["dep_dt"] == datetime(2026, 12, 20, 6)  # datetimes survive the JSON round-trip...
assert r2[0]["segments"][0]["arr_dt"] == datetime(2026, 12, 20, 7)  # ...also nested ones
assert len(ff.fetch_many(tasks[:1], cheapest_only=False)) == 2  # every option when asked
assert ff.from_cache({"res": None}) == [] and len(ff.from_cache({"res": {"dep_dt": "2026-12-20T06:00:00"}})) == 1  # old cache format
c = json.load(open(ff.CACHE_FILE))
assert set(c) == {"CPH|STN|2026-12-20", "CPH|NONE|2026-12-20"}  # failures are never cached
for v in c.values():
    v["at"] = (datetime.now() - timedelta(hours=ff.CACHE_HOURS + 1)).isoformat()
json.dump(c, open(ff.CACHE_FILE, "w")); calls.clear()
ff.fetch_many(tasks[:2]); assert len(calls) == 2    # expired answers are fetched again
open(ff.CACHE_FILE, "w").write("{broken"); assert ff.load_cache() == {}

# Lookups that fail after every retry are reported, not silently dropped
ff.FAILED.clear(); ff.fetch_many(tasks)
assert ff.FAILED == [("X", "STN", "2026-12-20")], ff.FAILED

# Progress reports end at the full count
seen = []; ff.PROGRESS = lambda stage, done, total: seen.append((done, total))
ff.fetch_many(tasks[:2]); ff.PROGRESS = None
assert seen[-1] == (2, 2), seen

# Cancel stops a search and raises, after saving what was found
ff.CANCEL.set()
try:
    ff.fetch_many([("CPH", "NEW", "2026-12-21")]); raise AssertionError("no Cancelled")
except ff.Cancelled:
    pass
ff.CANCEL.clear()

# Self-transfers: the cheapest second flight leaves before the first lands; the later, pricier one must still be found
ff.CACHE_FILE = os.path.join(tempfile.mkdtemp(), "qc.json")
def flight(o, d, day, h1, h2, price):
    dep, arr = datetime(2026, 12, 20, h1), datetime(2026, 12, 20, h2)
    return {"orig": o, "dest": d, "date": day, "price": price, "airline": "Ryanair", "flight_no": "FR1",
            "dep_time": f"{h1:02}:00", "arr_time": f"{h2:02}:00", "dep_dt": dep, "arr_dt": arr,
            "segments": [{"from": o, "to": d, "dep_dt": dep, "arr_dt": arr}]}
ff.fetch_one_way = lambda o, d, day, *_: (
    [flight(o, d, day, 8, 10, 10)] if (o, d, day) == ("CPH", "STN", "2026-12-20") else
    [flight(o, d, day, 6, 9, 20), flight(o, d, day, 18, 21, 25)] if (o, d, day) == ("STN", "FAO", "2026-12-20") else [])
combos = ff.scan_fast_self_transfers(["CPH"], ["FAO"], ["STN"], ["2026-12-20"])
assert list(combos["Total_EUR"]) == [35], combos

# App settings check
good = {"home": ["CPH"], "away": ["FAO"], "hubs": ["STN"], "direct": False, "outbound": True, "return": True,
        "conn": 3, "max1": 100, "max2": 100, "out_from": "2099-12-18", "out_to": "2099-12-20", "ret_from": "2099-12-28", "ret_to": "2099-12-30",
        "adults": 2, "cabin": True, "checked": 1, "bagfee": 40}
assert len(app.validate(good)) == 2
for bad, words in [({"out_from": "2000-01-01"}, "in the past"), ({"conn": 0}, "Min. connection"),
                   ({"ret_from": "2099-12-01", "ret_to": "2099-12-02"}, "before the outbound"),
                   ({"out_to": "2099-12-17"}, "before the first day"), ({"out_to": "2100-02-01"}, "at most 31 days"),
                   ({"adults": 0}, "Adults"), ({"checked": 3}, "Checked bags"), ({"bagfee": -1}, "negative")]:
    try:
        app.validate({**good, **bad}); raise AssertionError(f"accepted {bad}")
    except ValueError as e:
        assert words in str(e), (bad, e)

# CSV round trip: saved trips load back with both legs
path = os.path.join(tempfile.mkdtemp(), "out.csv")
ff.save_merged(combos.astype({"Leg1_EUR": "Int64"}).assign(Checked="2026-11-19", Ticket=""), path, ["Route", "Leg1_Date", "Leg1", "Leg2_Date", "Leg2", "Ticket"])
trip, = app.load_trips(path)
assert trip["route"] == ["CPH", "STN", "FAO"] and trip["legs"][1]["dep"] == "18:00" and trip["total"] == 35
assert trip["fare"] == "a1c0"  # rows from before fares count as 1 adult, no bags

# A search for 2 adults with cabin bags adds its own rows instead of overwriting the 1-adult prices
keys = ["Route", "Leg1_Date", "Leg1", "Leg2_Date", "Leg2", "Ticket", "Fare"]
ff.save_merged(combos.assign(Checked="2026-11-19", Ticket="", Fare="a2c1", Total_EUR=150).astype({"Leg1_EUR": "Int64"}), path, keys)
assert sorted(t["fare"] for t in app.load_trips(path)) == ["a1c0", "a2c1"]
ff.save_merged(combos.assign(Checked="2026-11-20", Ticket="", Fare="a2c1", Total_EUR=140).astype({"Leg1_EUR": "Int64"}), path, keys)
assert sorted((t["fare"], t["total"]) for t in app.load_trips(path)) == [("a1c0", 35), ("a2c1", 140)]  # same fare: newest price wins

# The fare reaches Google and the cache key
seen_q = []
ff.get_flights = lambda q: seen_q.append(q) or []
ff.fetch_one_way = real_fetch
ff.FARE = {"adults": 2, "cabin": 1}
ff.fetch_many([("CPH", "LIS", "2099-12-20")])
pb = seen_q[-1].pb()
assert len(pb.passengers) == 2 and pb.baggage.carry_on_bags == 2, pb
assert "CPH|LIS|2099-12-20|a2c1" in json.load(open(ff.CACHE_FILE))
ff.FARE = {"adults": 1, "cabin": 0}
print("ok")
