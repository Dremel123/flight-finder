# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

(Rendered in a native desktop window: PySide6 QWebEngineView loading `ui.html`, bridged to Python via QWebChannel. Linux desktop, ~1440×900 default window.)

## Users

People who run Flight Finder on their own machine to find the cheapest way between two sets of airports (default: Denmark ↔ Portugal around Christmas) when no direct flight is cheap enough. Several people install and run their own searches; not only the original author.

## Product Purpose

Scan many dates and hub airports on Google Flights, combine two cheap one-way legs into a self-transfer trip, and list the cheapest outbound and return options. Success: a user spots a trip that is cheaper than booking direct, with a safe connection, in seconds.

## Positioning

It finds self-transfer combinations through budget hubs (STN, BGY, CRL…) that flight search sites do not stitch together, with a minimum connection time to allow for re-checking bags.

## Operating Context

A search runs for minutes in the background; the user watches progress in a log, then filters/sorts results. Results persist as CSV files next to the script (`cheapest_outbound.csv`, `cheapest_return.csv`, `direct_*.csv`). Settings persist in `settings.json`.

## Capabilities and Constraints

- Inputs: home, destination, and hub airports (IATA codes); outbound and return date ranges; max price per leg; minimum connection hours; parallel requests; outbound/return/direct-only toggles.
- Results: per trip the route codes, each leg's day, times, airline, price, layover length (overnight flagged), total price, date checked.
- Filtering by text (codes, airline), max price slider, sort by price/date/trip length. Up to 300 rows rendered.
- Data comes from scraping Google Flights; rate limits (HTTP 429) make searches slow.
- Web fonts load from Google Fonts; everything else is local.

## Evidence on Hand

Real scan results in `cheapest_outbound.csv` and `cheapest_return.csv`. No users, testimonials, or metrics exist.

## Product Principles

- The cheapest safe trip should be readable at a glance: price, route, times, layover.
- Never hide risk: overnight layovers and next-day arrivals stay visible.
- Long searches must feel alive and legible, not frozen.
- Usable by people who did not write it: plain labels, clear errors.

## Accessibility & Inclusion

Large, readable type is a stated requirement (the user rejected a UI they "can't read").
