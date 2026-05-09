# GISCI343 Assignment 2

## Auckland Public Transport Recovery Dashboard

## What does this dashboard show?

This dashboard explores the question:

**How did Auckland’s most popular bus routes and rail patronage recover compared with 2019 pre-COVID levels?**

The dashboard focuses on three high-patronage bus routes, **70**, **NX1**, and **NX2**, as well as the wider **rail network**. It compares annual patronage from **2019 to 2024** and uses a recovery index where **2019 = 100**.

A recovery index of 100 means the service matched its 2019 patronage level. Values below 100 mean patronage was still below 2019 levels, while values above 100 mean patronage exceeded 2019 levels.

## Why was this dashboard made?

Public transport patronage changed significantly during and after the COVID period. This dashboard was made to show how strongly selected Auckland services recovered compared with their 2019 pre-COVID baseline.

It helps users compare:

- which services recovered closest to 2019 levels
- how recovery changed from 2020 to 2024
- how major bus routes differ from the wider rail network
- where the selected routes are located spatially

The dashboard is intended for students, transport planners, local government staff, or anyone interested in Auckland public transport recovery.

## How does the dashboard work?

The dashboard allows users to filter the data by:

- selected services: route 70, NX1, NX2, and rail
- year range: 2019 to 2024
- recovery period: pre-COVID baseline, COVID disruption, early recovery, and recovery period

The Home page shows recovery cards, a recovery index line chart, and an interactive route map. The Charts page provides a more detailed view, including:

- recovery index over time
- raw annual patronage
- latest-year recovery ranking

The interactive map shows the selected bus routes and rail network. Clicking on a route displays information such as 2024 patronage and recovery compared with 2019.

## Data sources and preparation

The bus patronage data was derived from Auckland Transport bus performance reports for routes 70, NX1, and NX2. The rail patronage data was derived from Auckland Transport monthly patronage data, summed into annual totals.

The final patronage dataset was prepared as a clean CSV with one row per service and year columns from 2019 to 2024. In Python, the data was reshaped from wide to long format, and new fields were calculated:

- `baseline_2019`
- `recovery_index`
- `change_from_2019_pct`
- `service_type`
- `period`

Spatial data is loaded from `bus_routes.geojson` and `train_routes.geojson`. These route layers are displayed using `ipyleaflet`.

## Limitations

The main limitation is that the bus data represents individual routes, while the rail data represents the whole rail network. This means raw patronage is useful for context, but it is not a direct like-for-like comparison.

The recovery index provides a fairer comparison because each service is compared against its own 2019 baseline.

The dashboard also does not account for population growth, service frequency, fare changes, rail disruptions, remote work patterns, or other factors that may affect patronage. Therefore, it shows observed patronage recovery, not a full explanation of why recovery differed between services.

## How to run the project locally

This project uses **Shiny for Python**. The app is also exported with **Shinylive** so it can run on GitHub Pages.

### 1. Clone or download the project

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 2. Install dependencies with uv

If uv is being used, install the project dependencies with:

```bash
uv sync
```

This creates or updates the project virtual environment.

### 3. Run the Shiny app locally

From the folder that contains app.py, run:

```bash
uv run shiny run --reload app.py
```
Then open the local URL shown in the terminal.
