#!/usr/bin/env python3
"""
Decide whether a given date (default: today in US/Eastern) is a NYSE trading day.

Stdlib only. Computes US market holidays by RULE, so it is valid for any year
(2026, 2027, 2028, ... indefinitely) without a hardcoded calendar.

Exit code 0  -> trading day (prints "TRADING_DAY <date>")
Exit code 10 -> not a trading day (prints "MARKET_CLOSED <date> <reason>")

NYSE full-closure holidays implemented:
  New Year's Day, MLK Day, Washington's Birthday (Presidents' Day), Good Friday,
  Memorial Day, Juneteenth (since 2021 obs.), Independence Day, Labor Day,
  Thanksgiving, Christmas.

Observance rules:
  * Fixed-date holiday on Saturday -> observed previous Friday.
  * Fixed-date holiday on Sunday   -> observed following Monday.
  * SPECIAL CASE: when New Year's Day (Jan 1) falls on a Saturday, NYSE does NOT
    observe it on the preceding Friday (no closure). (Sunday -> Mon Jan 2 observed.)
Early-close half-days are NOT full closures -> treated as trading days.
"""
from __future__ import annotations
import argparse, datetime as dt, sys

def nth_weekday(year, month, weekday, n):
    """n-th `weekday` (Mon=0) of month. n>=1."""
    d = dt.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 7 * (n - 1))

def last_weekday(year, month, weekday):
    if month == 12:
        d = dt.date(year, 12, 31)
    else:
        d = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    offset = (d.weekday() - weekday) % 7
    return d - dt.timedelta(days=offset)

def easter_sunday(year):
    """Anonymous Gregorian computus."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day)

def observed_fixed(d):
    """Apply Sat->Fri, Sun->Mon observance to a fixed-date holiday."""
    if d.weekday() == 5:      # Saturday
        return d - dt.timedelta(days=1)
    if d.weekday() == 6:      # Sunday
        return d + dt.timedelta(days=1)
    return d

def nyse_holidays(year):
    """Return {date: name} of NYSE full closures observed in `year`."""
    hols = {}

    # New Year's Day — special: Saturday is NOT observed on the prior Friday.
    nyd = dt.date(year, 1, 1)
    if nyd.weekday() == 6:        # Sunday -> Monday Jan 2
        hols[dt.date(year, 1, 2)] = "New Year's Day (observed)"
    elif nyd.weekday() == 5:      # Saturday -> no closure
        pass
    else:
        hols[nyd] = "New Year's Day"

    hols[nth_weekday(year, 1, 0, 3)] = "Martin Luther King Jr. Day"
    hols[nth_weekday(year, 2, 0, 3)] = "Washington's Birthday (Presidents' Day)"
    hols[easter_sunday(year) - dt.timedelta(days=2)] = "Good Friday"
    hols[last_weekday(year, 5, 0)] = "Memorial Day"

    # Juneteenth — NYSE holiday since 2022 (federal 2021).
    if year >= 2022:
        jt = observed_fixed(dt.date(year, 6, 19))
        hols[jt] = "Juneteenth National Independence Day"

    hols[observed_fixed(dt.date(year, 7, 4))] = "Independence Day"
    hols[nth_weekday(year, 9, 0, 1)] = "Labor Day"
    hols[nth_weekday(year, 11, 3, 4)] = "Thanksgiving Day"
    hols[observed_fixed(dt.date(year, 12, 25))] = "Christmas Day"
    return hols

def reason_closed(d):
    if d.weekday() == 5:
        return "Saturday (weekend)"
    if d.weekday() == 6:
        return "Sunday (weekend)"
    h = nyse_holidays(d.year)
    if d in h:
        return h[d]
    return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", help="YYYY-MM-DD; default = today in US/Eastern")
    args = p.parse_args()
    if args.date:
        d = dt.date.fromisoformat(args.date)
    else:
        # US/Eastern without external tz libs: compute via fixed offset is unsafe across DST.
        # The scheduled task already passes TZ=America/New_York date; here we accept --date.
        d = dt.date.today()
    r = reason_closed(d)
    if r:
        print(f"MARKET_CLOSED {d.isoformat()} {r}")
        sys.exit(10)
    print(f"TRADING_DAY {d.isoformat()}")
    sys.exit(0)

if __name__ == "__main__":
    main()
