# Visual Design Specification
## AI Shovel Stocks Tracker

---

## 1. Visual Direction

The dashboard should feel like a professional market monitoring tool rather than a generic chart page.

Target look:

- Dark institutional dashboard
- Clean research layout
- Modular card-based sections
- Clear comparison layers
- Low visual clutter
- Industry-first structure

The chosen visual direction combines:

- **V3 color palette**: dark blue / slate background with subtle blue and purple glow
- **Industry split layout**: separate panels by industry group
- **Index overview layer**: compare industry baskets against major benchmarks

---

## 2. Color System

### Background

Primary background:

```css
#07111f
#0b1020
#111827
```

Gradient:

```css
radial-gradient(circle at top left, rgba(59,130,246,.18), transparent 30%)
radial-gradient(circle at top right, rgba(168,85,247,.16), transparent 28%)
linear-gradient(135deg, #07111f 0%, #0b1020 50%, #111827 100%)
```

### Panel Background

```css
linear-gradient(
  180deg,
  rgba(255,255,255,.105),
  rgba(255,255,255,.06)
)
```

### Borders

```css
rgba(255,255,255,.12)
```

### Primary Text

```css
#f8fafc
```

### Secondary Text

```css
#94a3b8
```

### Accent Blue

```css
#7dd3fc
```

### Positive Green

```css
#34d399
```

### Negative Red

```css
#fb7185
```

---

## 3. Typography

Recommended font stack:

```css
Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

### Eyebrow

- Size: 12px
- Weight: 800
- Transform: uppercase
- Letter spacing: 0.12em
- Color: accent blue

### Main Title

- Size: 38px
- Weight: 800
- Letter spacing: -0.045em
- Line height: 1.05

### Section Label

- Size: 13px
- Weight: 800
- Transform: uppercase
- Letter spacing: 0.06em
- Color: light blue

### Chart Title

- Size: 15px to 18px
- Weight: 700
- Color: primary text

### Subtext

- Size: 12px to 14px
- Color: secondary text

---

## 4. Layout Structure

### Overall Page

The dashboard should follow this order:

1. Header
2. KPI cards
3. Benchmark overview
4. Industry index overview vs benchmarks
5. Industry index vs benchmarks by industry
6. Industry peer comparison by industry
7. Correlation heatmap and tables
8. Methodology footer

---

## 5. Header Design

### Content

- Eyebrow: AI Infrastructure Equity Monitor
- Title: AI Shovel Stocks Tracker
- Description:
  - Explain purpose
  - Mention benchmark, industry index, peer comparison, correlation

### Sidebar

Sidebar should contain:

- Tracking window
- Industry group selector
- Benchmark selector
- Custom ticker text area
- Toggle for industry index panels
- Toggle for peer panels
- Refresh data button

---

## 6. KPI Cards

### Card Count

Four KPI cards:

1. Tracking Window
2. Best Stock Return
3. Worst Stock Return
4. Best Industry Index

### Card Style

```css
border-radius: 22px;
border: 1px solid rgba(255,255,255,.12);
background: linear-gradient(180deg, rgba(255,255,255,.105), rgba(255,255,255,.06));
box-shadow: 0 22px 55px rgba(0,0,0,.28);
```

### Card Content

Each card should have:

- Small label
- Large value
- Small explanatory note

---

## 7. Chart Design

All charts should use ECharts.

### Chart Theme

- Transparent background
- Dark axis labels
- Muted grid lines
- Scrollable legend
- Hover tooltip
- Inside zoom
- Slider zoom
- Save-as-image option

### Tooltip

Style:

```js
backgroundColor: "rgba(15,23,42,.94)"
borderColor: "rgba(148,163,184,.25)"
textStyle: { color: "#e5e7eb" }
```

### Axis

Axis text:

```js
"#94a3b8"
```

Grid line:

```js
"rgba(148,163,184,.12)"
```

### Data Zoom

Each time-series chart should include:

- Inside zoom
- Bottom slider zoom

This makes the dashboard useful as a long-term tracker.

---

## 8. Chart Modules

### 8.1 Benchmark Overview

Purpose:

- Show market and AI-theme backdrop

Series:

- NVDA
- AMD
- SPY
- QQQ

Height:

- 560px

### 8.2 Industry Index Overview vs Benchmarks

Purpose:

- Compare all industry baskets with benchmark lines

Series:

- All selected industry indexes
- NVDA
- AMD
- SPY
- QQQ

Height:

- 620px

Design note:

- This is the main "total view."
- It should answer whether each industry is beating or lagging the four benchmarks.

### 8.3 Industry Index vs Benchmarks

Purpose:

- Compare one industry basket with four benchmarks

Layout:

- Two-column grid
- One panel per industry

Height per chart:

- 430px

### 8.4 Industry Peer Comparison

Purpose:

- Compare stocks within the same industry group

Layout:

- Two-column grid
- One panel per industry

Height per chart:

- 430px

Design note:

- This prevents overcrowding.
- Do not put all peer stocks into one single chart.

### 8.5 Correlation Heatmap

Purpose:

- Show daily-return correlation versus benchmark targets

Ordering:

- Sort by correlation to Nvidia when available

Color scale:

```js
["#be123c", "#1f2937", "#059669"]
```

Height:

- 820px

### 8.6 Tables

Tables should be placed in tabs:

1. Correlation Table
2. Price Data
3. Industry Index Data

Use CSV export buttons below relevant tables.

---

## 9. Interaction Model

User interactions:

1. Change window
2. Select industry groups
3. Edit ticker list
4. Select benchmarks
5. Hide or show index panels
6. Hide or show peer panels
7. Zoom charts
8. Toggle chart legends
9. Export CSVs
10. Save charts as images

---

## 10. Responsive Design

Desktop:

- KPI cards in four columns
- Industry panels in two columns
- Bottom heatmap/table in tabs

Mobile / narrow screen:

- KPI cards stack vertically
- Industry panels stack vertically
- Chart heights can stay fixed or be reduced later

---

## 11. Visual Hierarchy

The most important information should appear first:

1. Benchmark context
2. Industry index total view
3. Industry index vs benchmarks
4. Individual peer details
5. Correlation diagnostics
6. Raw data

This hierarchy prevents the user from getting lost in too many individual stock lines.

---

## 12. Design Rationale

The dashboard intentionally avoids a single crowded 30-stock chart.

Instead, it uses three levels:

### Level 1: Market Context

Benchmarks only.

### Level 2: Industry Context

Equal-weight industry indexes versus benchmarks.

### Level 3: Stock Context

Peer comparison inside each industry group.

This structure gives both top-down and bottom-up views.

---

## 13. Future Visual Enhancements

Potential additions:

1. Collapsible industry panels
2. Color-coded industry badges
3. Rolling correlation mini charts
4. Drawdown waterfall chart
5. Top movers ranking card
6. Small multiples with synchronized axes
7. Sector performance bar chart
8. Snapshot export to PDF
9. Light/dark theme toggle
10. Watchlist save/load function
