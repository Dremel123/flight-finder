---
name: Flight Finder
description: Self-transfer flight search where every trip is printed as a baggage routing tag.
colors:
  band: "#0E5E48"
  band-deep: "#0A4A39"
  band-line: "#3F7F6C"
  band-text: "#F6F7F4"
  band-muted: "#CFE3DA"
  stock: "#F6F7F4"
  paper: "#FFFFFF"
  print: "#17191B"
  muted: "#545A57"
  hall: "#D9DDD8"
  seam: "#B4BAB3"
  perf: "#8E958E"
  rush: "#E8541E"
  rush-ink: "#B33A0E"
  land: "#CDD4CC"
  sea: "#EEF1ED"
typography:
  display:
    fontFamily: "Archivo, sans-serif"
    fontSize: "46px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 72"
  headline:
    fontFamily: "Archivo, sans-serif"
    fontSize: "42px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 66"
  title:
    fontFamily: "Archivo, sans-serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.03em"
    fontVariation: "'wdth' 75"
  time:
    fontFamily: "Archivo, sans-serif"
    fontSize: "23px"
    fontWeight: 700
    lineHeight: 1
    fontVariation: "'wdth' 82"
  code-chip:
    fontFamily: "Archivo, sans-serif"
    fontSize: "19px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.04em"
    fontVariation: "'wdth' 75"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "'tnum' 1"
  label:
    fontFamily: "Archivo, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.45
  flag:
    fontFamily: "Archivo, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.1em"
rounded:
  print: "2px"
  chip: "3px"
  tag: "6px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "14px"
  lg: "20px"
  xl: "24px"
  gutter: "32px"
components:
  button-search:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.band}"
    rounded: "{rounded.tag}"
    padding: "18px"
  button-search-hover:
    backgroundColor: "{colors.paper}"
  button-search-busy:
    backgroundColor: "{colors.band-deep}"
    textColor: "{colors.band-text}"
  field-rail:
    backgroundColor: "{colors.band-deep}"
    textColor: "{colors.band-text}"
    rounded: "{rounded.tag}"
    padding: "9px 12px"
  field-bar:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.print}"
    rounded: "{rounded.tag}"
    padding: "9px 12px"
  code-chip:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.print}"
    typography: "{typography.code-chip}"
    rounded: "{rounded.chip}"
    padding: "5px 2px 4px 8px"
  code-chip-invalid:
    backgroundColor: "{colors.rush}"
    textColor: "{colors.paper}"
  toggle:
    textColor: "{colors.band-muted}"
    rounded: "{rounded.pill}"
    padding: "8px 14px"
  toggle-on:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.band}"
  tab:
    textColor: "{colors.muted}"
    typography: "{typography.title}"
    padding: "10px 10px 8px"
  tab-selected:
    textColor: "{colors.print}"
  trip-tag:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.print}"
    rounded: "{rounded.tag}"
  trip-tag-hover:
    backgroundColor: "{colors.paper}"
  flag-risk:
    backgroundColor: "{colors.rush}"
    textColor: "{colors.paper}"
    typography: "{typography.flag}"
    rounded: "{rounded.print}"
    padding: "5px 7px 4px"
  flag-plain:
    backgroundColor: "{colors.print}"
    textColor: "{colors.paper}"
---

# Design System: Flight Finder

## Overview

**Creative North Star: "The Baggage Routing Tag"**

Every trip is a printed airline bag tag lying on the grey floor of a baggage hall. The route reads as condensed three-letter codes, the price sits on a perforated stub, and risk is printed onto the tag itself as a rush-orange stripe rather than explained in a tooltip. Clicking a tag unfolds it along a perforation into an itinerary and a small route map, so the hub becomes a place, not just a code.

The shell is a solid tag-band green settings rail on the left; the work area is flat hall grey carrying a column of off-white tag stock printed in near-black. Everything is flat: depth comes from colour fields, hairline seams and dashed perforations, never from shadows. One typeface, Archivo, does all the work, squeezed to condensed widths for codes, times and prices and left at normal width for reading.

Density is that of an operating tool: large, legible type (16px body minimum for running text, 42px codes, 46px prices) because readability is a stated product requirement, with tight but regular spacing between tags.

**Key Characteristics:**
- Tag-band green rail, hall-grey ground, off-white tag stock, near-black thermal print.
- Rush orange carries attention only: risk, invalid input, keyboard focus.
- Archivo variable width: condensed for codes, times, prices; normal for body.
- Flat. Hairline seams, dashed perforations, no elevation shadows, no smooth gradients.
- Shared hour scale across tags so legs compare by eye.

## Colors

A green-and-paper print palette with one hot signal colour held in reserve.

### Primary
- **Tag-Band Green** (band): the settings rail ground, the tag band for normal trips, the selected tab underline and count badge, flown arcs on the map, the itinerary rail line, slider accent and selection highlight.
- **Deep Band** (band-deep): input wells inside the rail and the busy state of the Search button.
- **Band Seam** (band-line): hairline borders and dividers inside the rail; the rail's scrollbar thumb.
- **Band Mist** (band-muted): field labels, hints, unselected toggle text and placeholders on green.

### Tertiary
- **Rush Orange** (rush): the diagonal risk stripe on a tag band, overnight change lines (doubled line on the hour scale and itinerary), overnight map arcs, risk flags, invalid code chips, and the 3px keyboard focus ring.
- **Rush Ink** (rush-ink): orange as text on light stock: the "+1" next-day marker, overnight wait copy, error messages.

### Neutral
- **Tag Stock** (stock): every trip tag, the top bar, the log drawer, code chips and the Search button. Also the rail's text colour (band-text holds the same value).
- **Plain Paper** (paper): hover lift for tags and the Search button, white inputs in the top bar, hollow hub dots.
- **Thermal Print** (print): primary text, flown-leg bars, the direct-trip band, plain flags, and the log console ground.
- **Faded Print** (muted): secondary text: days, airlines, per-leg prices, captions, unselected tabs.
- **Hall Grey** (hall): the results ground beneath the tags; inactive tab count badge.
- **Seam** (seam): hairline borders, hour-scale ticks, scrollbar thumbs.
- **Perforation** (perf): the 2px dashed tear lines on the price stub and the unfolded detail.
- **Land / Sea** (land, sea): the route map's coastline fill and water.

### Named Rules
**The Rush Means Attention Rule.** Rush orange marks something the user must notice: a risky connection, a bad input, where keyboard focus is. It never decorates, brands or fills a neutral surface.

**The Band Says What Kind Rule.** The 10px colour band on a tag's left edge classifies the trip: green for a normal self-transfer, print black for direct, rush-and-stock diagonal stripes (135deg, 8px/6px hard stops) for any trip with an overnight or next-day risk.

## Typography

**Display Font:** Archivo (variable, self-hosted, weight 400-800, width 62-125%), fallback sans-serif
**Body Font:** Archivo at normal width, fallback system-ui, sans-serif
**Label/Mono Font:** system monospace (ui-monospace, DejaVu Sans Mono) for the search log only

**Character:** A single grotesque stretched between two voices: tightly condensed heavy capitals that read like printed airport codes, and a plain normal-width body for sentences. Tabular figures are on globally so times and prices align.

### Hierarchy
- **Display** (800, 46px, width 72%, 1): the trip price on the stub. The largest thing on a tag.
- **Headline** (800, 42px, width 66%, 1): route codes on a tag; the hub code drops to 30px inside a 2px print box.
- **Title** (800, 26-28px, width 72-78%, uppercase, tracked .02-.05em): product name, result tabs, the Search button (23px), empty-state heading (34px).
- **Time** (700, 20-23px, width 82%): leg times on tags and itinerary times; slider value output at 22px/78%.
- **Code chip** (800, 19px, width 75%, .04em): IATA codes in the airport inputs; itinerary codes at 20px.
- **Body** (400, 16px, 1.45, tabular): running text, inputs, select menus.
- **Label** (500, 15px): field titles on the rail, top-bar tool labels, summaries, day labels. Captions step down to 13-14px only for secondary metadata (checked date, map notes, hints).
- **Flag** (700, 12px, .1em, uppercase): the risk / direct flag on the stub. The only tracked small caps in the system, and it always carries data ("Overnight in STN", "Direct").

### Named Rules
**The Squeeze For Codes Rule.** Width, not weight alone, signals a machine-printed value: codes, times and prices are condensed (66-82%); anything a person reads as a sentence stays at 100%.

## Layout

A two-column window grid: a fixed 340px rail and a fluid results column (290px rail below 1000px). The rail stacks brand, a scrolling form split into hairline-ruled fieldsets (Where / When / Limits), then toggles and a full-width Search button pinned to the bottom. The results column stacks a stock top bar (tabs left, filter / max price / sort right), the scrolling tag list (18px 32px 40px padding; 20px side padding below 1000px), and a collapsible log drawer at the bottom.

A tag is a four-column grid: 10px band | route (250-300px) | legs (fluid) | 150px price stub, min-height 120px. Below 1280px the legs drop to a second row under the route, and the unfolded detail stacks itinerary above map. Rail fields pair in two-column rows with a 10px gap.

Spacing runs on a small set of steps (6, 10, 14, 20, 24, 32px); tags are separated by 10px of hall grey.

## Elevation & Depth

Flat. There is no elevation shadow anywhere. Depth is conveyed by colour fields (green rail, grey hall, stock tags), 1px seams between regions, and 2px dashed perforations where a tag would tear. `box-shadow` appears only as a line-drawing tool: focus rings on fields (`0 0 0 1px`), the selected tab's 4px inset underline, the busy button's inset hairline, and the hollow hub dot's inset ring.

### Named Rules
**The Lying Flat Rule.** Tags rest on the floor. Hover brightens a tag from stock to paper; it never lifts, scales or casts a shadow.

## Shapes

Small, practical corners: 6px on tags, fields, the Search button and error box; 3px on code chips, the hub code box and count badges; 2px on flags. Pills (999px) are reserved for the on/off toggles. Edges inside a tag are hairlines (1px seam) and perforations (2px dashed perf). Circles appear only as map and itinerary stops: filled for an endpoint, hollow with a 3px ring for a hub.

## Components

### Buttons
- **Search (primary):** a slab of tag stock on the green rail, band-green condensed uppercase text (800, 23px, 78%), 18px padding, 6px corners, full rail width minus 24px margins. Hover goes to paper; active scales to .98; busy turns band-deep with a spinner and inset hairline.
- **Text button:** "Show all n" under a folded chip list: 15px semibold, underlined 3px offset, band-text.

### Chips
- **Code chips:** stock tags with condensed print codes and a faded remove cross, inside a band-deep well that behaves as one input. Invalid codes turn rush with white text. Long lists fold to two rows (74px).
- **Toggles:** pills outlined in band-line with band-muted text; checked fills stock with band text and shows a check icon.

### Cards / Containers
- **Trip tag:** stock, 6px corners, no border, no shadow. Band | route | legs | perforated stub. Opening reveals a detail panel below a 2px dashed perforation (opens instantly; the panel fades and slides in 8px over .35s ease-out — never animate its height, which re-lays out every tag), itinerary left, map right.

### Inputs / Fields
- **Rail fields:** band-deep well, 1px band-line border, band-text value, 6px corners. Hover border goes band-muted; focus border and a 1px ring go band-text. Dates use the dark colour scheme.
- **Top-bar fields:** paper, 1px seam border, 6px corners; select carries a band-green chevron.

### Navigation
- **Tabs:** condensed uppercase 26px titles with a count badge. Unselected: faded print text, hall badge. Selected: print text, 4px band-green underline, band badge with band-text.

### Hour Scale (signature)
Every tag's legs sit on one shared hour scale: day lines in seam with a 12px day label, dotted hour ticks, flights as 5px print bars, ordinary waits as a 2px dashed print line, overnight waits as a doubled rush line.

### Route Map (signature)
On unfold, an SVG map in land/sea greys draws the trip's arcs (3.5px band, rush when overnight) with a .9s stroke animation, second leg delayed .35s. Endpoints are filled print dots; the hub is a hollow paper dot. Labels are condensed print codes with muted times, haloed in sea colour.

### Search Log
A details drawer on stock: chevron, bold "Search log", last line in monospace. Open, it shows a 220px print-black console with light text.

## Do's and Don'ts

### Do:
- **Do** set codes, times and prices in Archivo at condensed widths (66-82%) and weight 700-800.
- **Do** keep body copy at 16px and labels at 15px or larger; drop to 12-14px only for secondary metadata and flags.
- **Do** mark every overnight or next-day risk on the tag itself: striped band, doubled rush line, rush flag, rush-ink text.
- **Do** separate regions with 1px seams and tear points with 2px dashed perforations.
- **Do** honour reduced motion: no arc drawing, no unfold transition.

### Don't:
- **Don't** use rush orange for branding, decoration or a neutral highlight.
- **Don't** add elevation shadows or smooth gradients; the hard-stop risk stripe is the only patterned fill.
- **Don't** lift, scale or shadow a tag on hover.
- **Don't** introduce a second typeface for display; Archivo carries everything except the log console.
- **Don't** add uppercase tracked labels above headings; small caps exist only as data-bearing flags.
