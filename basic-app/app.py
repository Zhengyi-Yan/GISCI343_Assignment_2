from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
from ipyleaflet import Map, basemaps, GeoJSON
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt

# -----------------------------
# Load and prepare data
# -----------------------------

Path("data/processed").mkdir(parents=True, exist_ok=True)

# -----------------------------
# Load spatial data
# -----------------------------

bus_routes = gpd.read_file("data/bus_routes.geojson")
train_routes = gpd.read_file("data/train_routes.geojson")

# Make sure bus routes are in WGS84 for ipyleaflet
if bus_routes.crs is None:
    bus_routes = bus_routes.set_crs(4326)
else:
    bus_routes = bus_routes.to_crs(4326)

# Make sure train routes are in WGS84 for ipyleaflet
if train_routes.crs is None:
    train_routes = train_routes.set_crs(4326)
else:
    train_routes = train_routes.to_crs(4326)

# Clean route number fields for reliable filtering
bus_routes["ROUTENUMBER_CLEAN"] = (
    bus_routes["ROUTENUMBER"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# -----------------------------
# Load patronage table
# -----------------------------

# Change this to "patronage_data.csv" if the file is beside app.py
df = pd.read_csv("data/patronage_data.csv")

# Clean service names
df["service"] = df["service"].astype(str).str.strip()

# Year columns
year_cols = ["2019", "2020", "2021", "2022", "2023", "2024"]

# Convert year columns to numeric values
for col in year_cols:
    df[col] = pd.to_numeric(df[col])

# Convert from wide format to long format
patronage = df.melt(
    id_vars=["service"],
    value_vars=year_cols,
    var_name="year",
    value_name="patronage"
)

patronage["year"] = patronage["year"].astype(int)
patronage["patronage"] = patronage["patronage"].astype(int)

# Add 2019 baseline for each service
baseline = patronage[patronage["year"] == 2019][
    ["service", "patronage"]
].rename(columns={"patronage": "baseline_2019"})

patronage = patronage.merge(baseline, on="service", how="left")

# Calculate recovery metrics
patronage["recovery_index"] = (
    patronage["patronage"] / patronage["baseline_2019"] * 100
)

patronage["change_from_2019_pct"] = (
    (patronage["patronage"] - patronage["baseline_2019"])
    / patronage["baseline_2019"] * 100
)

# Add service type
def service_to_type(service):
    if service.lower() == "train":
        return "Rail network"
    return "Bus route"

patronage["service_type"] = patronage["service"].apply(service_to_type)

# Add period labels
def year_to_period(year):
    if year == 2019:
        return "Pre-COVID baseline"
    elif year in [2020, 2021]:
        return "COVID disruption"
    elif year == 2022:
        return "Early recovery"
    else:
        return "Recovery period"

patronage["period"] = patronage["year"].apply(year_to_period)

# -----------------------------
# User interface
# -----------------------------

app_ui = ui.page_fluid(
    ui.h2("Auckland Public Transport Recovery Explorer"),
    ui.p(
        "Compare selected high-patronage Auckland bus routes and rail patronage "
        "against 2019 pre-COVID levels."
    ),

    ui.input_checkbox_group(
        "services",
        "Services",
        choices=sorted(patronage["service"].unique().tolist()),
        selected=sorted(patronage["service"].unique().tolist())
    ),

    ui.input_slider(
        "year_range",
        "Year range",
        min=int(patronage["year"].min()),
        max=int(patronage["year"].max()),
        value=[
            int(patronage["year"].min()),
            int(patronage["year"].max())
        ],
        step=1,
        sep=""
    ),

    ui.input_checkbox_group(
        "periods",
        "Periods",
        choices=[
            "Pre-COVID baseline",
            "COVID disruption",
            "Early recovery",
            "Recovery period"
        ],
        selected=[
            "Pre-COVID baseline",
            "COVID disruption",
            "Early recovery",
            "Recovery period"
        ]
    ),

    ui.input_select(
        "metric",
        "Chart metric",
        choices={
            "patronage": "Raw patronage",
            "recovery_index": "Recovery index, 2019 = 100",
            "change_from_2019_pct": "Change from 2019 (%)"
        },
        selected="recovery_index"
    ),

    ui.input_action_button(
        "reset",
        "Reset filters"
    ),

    ui.hr(),

    ui.output_text("summary"),
    ui.output_table("tbl"),
    ui.output_plot("chart"),

    ui.h3("Network map"),
    output_widget("network_map", height="500px")
)

# -----------------------------
# Server logic
# -----------------------------

def server(input, output, session):

    @reactive.calc
    def filtered():
        df = patronage.copy()

        # Service checkbox filter
        df = df[df["service"].isin(input.services())]

        # Year range slider filter
        start_year, end_year = input.year_range()
        df = df[
            (df["year"] >= start_year) &
            (df["year"] <= end_year)
        ]

        # Period checkbox filter
        df = df[df["period"].isin(input.periods())]

        return df

    @reactive.effect
    @reactive.event(input.reset)
    def _():
        ui.update_checkbox_group(
            "services",
            selected=sorted(patronage["service"].unique().tolist())
        )

        ui.update_slider(
            "year_range",
            value=[
                int(patronage["year"].min()),
                int(patronage["year"].max())
            ]
        )

        ui.update_checkbox_group(
            "periods",
            selected=[
                "Pre-COVID baseline",
                "COVID disruption",
                "Early recovery",
                "Recovery period"
            ]
        )

        ui.update_select(
            "metric",
            selected="recovery_index"
        )

    @render.text
    def summary():
        df = filtered()

        if len(df) == 0:
            return "No records match the current filters."

        latest_year = df["year"].max()
        latest = df[df["year"] == latest_year]

        best_recovery = latest.loc[latest["recovery_index"].idxmax()]
        lowest_recovery = latest.loc[latest["recovery_index"].idxmin()]

        return (
            f"Showing {len(df)} records. In {latest_year}, "
            f"{best_recovery['service']} had the highest recovery index "
            f"at {best_recovery['recovery_index']:.1f}, while "
            f"{lowest_recovery['service']} had the lowest at "
            f"{lowest_recovery['recovery_index']:.1f}. "
            f"A value of 100 means the service matched its 2019 patronage level."
        )

    @render.table
    def tbl():
        df = filtered().copy()

        table = df[
            [
                "service",
                "service_type",
                "year",
                "period",
                "patronage",
                "recovery_index",
                "change_from_2019_pct"
            ]
        ].copy()

        table["recovery_index"] = table["recovery_index"].round(1)
        table["change_from_2019_pct"] = table["change_from_2019_pct"].round(1)

        return table.sort_values(["service", "year"]).head(30)

    @render.plot
    def chart():
        df = filtered()

        fig, ax = plt.subplots(figsize=(8, 4))

        if len(df) == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax.set_axis_off()
            return fig

        metric = input.metric()

        for service, group in df.groupby("service"):
            group = group.sort_values("year")
            ax.plot(
                group["year"],
                group[metric],
                marker="o",
                label=service
            )

        if metric == "recovery_index":
            ax.axhline(100, linestyle="--", linewidth=1)
            ax.set_ylabel("Recovery index, 2019 = 100")
            ax.set_title("Patronage recovery compared with 2019 baseline")

        elif metric == "change_from_2019_pct":
            ax.axhline(0, linestyle="--", linewidth=1)
            ax.set_ylabel("Change from 2019 (%)")
            ax.set_title("Percentage change from 2019 patronage")

        else:
            ax.set_ylabel("Annual patronage")
            ax.set_title("Annual patronage by selected service")

        ax.set_xlabel("Year")
        ax.set_xticks(sorted(df["year"].unique()))
        ax.legend(title="Service")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig

    @render_widget
    def network_map():
        selected_services = list(input.services() or [])

        selected_services_clean = [
            str(service).strip().upper()
            for service in selected_services
        ]

        show_train = "TRAIN" in selected_services_clean

        selected_bus_services = [
            service for service in selected_services_clean
            if service != "TRAIN"
        ]

        # Same line weight, solid bus lines
        bus_styles = {
            "70": {
                "color": "#2ca25f",
                "weight": 4,
                "opacity": 0.85,
            },
            "NX1": {
                "color": "#d73027",
                "weight": 4,
                "opacity": 0.85,
            },
            "NX2": {
                "color": "#2563eb",
                "weight": 4,
                "opacity": 0.85,
            },
        }

        train_style = {
            "color": "#f97316",
            "weight": 5,
            "opacity": 1.0,
        }

        m = Map(
            center=(-36.85, 174.77),
            zoom=11,
            basemap=basemaps.CartoDB.Positron,
            scroll_wheel_zoom=True
        )

        # Add selected bus routes
        for service in selected_bus_services:
            selected_bus_route = bus_routes[
                bus_routes["ROUTENUMBER_CLEAN"] == service
            ].copy()

            if len(selected_bus_route) > 0:
                bus_layer = GeoJSON(
                    data=json.loads(selected_bus_route.to_json()),
                    style=bus_styles.get(
                        service,
                        {
                            "color": "#333333",
                            "weight": 4,
                            "opacity": 0.8,
                        }
                    ),
                    name=f"Bus route {service}"
                )

                m.add_layer(bus_layer)

        # Add full train network if train is selected
        if show_train and len(train_routes) > 0:
            train_layer = GeoJSON(
                data=json.loads(train_routes.to_json()),
                style=train_style,
                name="Train network"
            )

            m.add_layer(train_layer)

        return m

app = App(app_ui, server)