from shiny import App, ui, render, reactive
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, basemaps, GeoData
from ipywidgets import HTML
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"


def format_boardings(value, _):
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.0f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:.0f}"

# -----------------------------
# Load and prepare data
# -----------------------------

(DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)

# -----------------------------
# Load spatial data
# -----------------------------

bus_routes = gpd.read_file(DATA_DIR / "bus_routes.geojson").to_crs(4326)
train_routes = gpd.read_file(DATA_DIR / "train_routes.geojson").to_crs(4326)

# Clean route number fields for reliable filtering
bus_routes["ROUTENUMBER_CLEAN"] = (
    bus_routes["ROUTENUMBER"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Precompute lightweight route GeoDataFrames for the map so reactive map
# updates do not repeatedly filter or simplify route layers.
train_routes_display = train_routes.copy()
train_routes_display["geometry"] = train_routes_display.geometry.simplify(
    tolerance=0.0002,
    preserve_topology=True
)

bus_route_gdfs = {
    route: bus_routes[bus_routes["ROUTENUMBER_CLEAN"] == route].copy()
    for route in ["70", "NX1", "NX2"]
}

# -----------------------------
# Load patronage table
# -----------------------------

df = pd.read_csv(DATA_DIR / "patronage_data.csv")

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

service_choices = {
    "70": "70",
    "NX1": "NX1",
    "NX2": "NX2",
    "train": "Train (Rail Network)",
}


def transport_icon(mode):
    if mode == "train":
        return ui.HTML(
            """
            <svg viewBox="0 0 64 64" aria-hidden="true">
              <rect x="17" y="8" width="30" height="42" rx="7"></rect>
              <rect x="22" y="14" width="20" height="12" rx="2"></rect>
              <circle cx="25" cy="38" r="3"></circle>
              <circle cx="39" cy="38" r="3"></circle>
              <path d="M23 56h18M26 50l-6 8M38 50l6 8"></path>
            </svg>
            """
        )

    return ui.HTML(
        """
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <rect x="13" y="10" width="38" height="40" rx="7"></rect>
          <rect x="19" y="16" width="26" height="13" rx="2"></rect>
          <circle cx="23" cy="40" r="4"></circle>
          <circle cx="41" cy="40" r="4"></circle>
          <path d="M18 54h8M38 54h8"></path>
        </svg>
        """
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.div(
            ui.div(
                ui.div(transport_icon("bus"), class_="brand-icon"),
                ui.div(
                    ui.div("Auckland", class_="brand-title"),
                    ui.div("Transport", class_="brand-title"),
                    class_="brand-text"
                ),
                class_="brand"
            ),
            ui.input_radio_buttons(
                "view_tab",
                None,
                choices={
                    "home": "Home",
                    "charts": "Charts",
                },
                selected="home"
            ),
            ui.div("Filters", class_="filter-heading"),
            ui.input_checkbox_group(
                "services",
                "Services",
                choices=service_choices,
                selected=list(service_choices.keys())
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
            ui.input_action_button(
                "reset",
                "Reset filters"
            ),
            class_="sidebar-inner"
        ),
        width=285,
        class_="app-sidebar"
    ),
    ui.include_css(APP_DIR / "www" / "dashboard.css"),
    ui.div(
        ui.h1("Auckland Public Transport Recovery Dashboard", class_="dashboard-title"),
        ui.p(
            "Explore how Auckland's most popular bus routes and rail patronage "
            "have recovered compared with 2019 pre-COVID levels.",
            class_="dashboard-subtitle"
        ),
        ui.panel_conditional(
            "input.view_tab === 'home'",
            ui.div(
                ui.div(
                    ui.div("Q:", class_="hero-icon"),
                    ui.div(
                        ui.div(
                            "How did Auckland's most popular bus routes and rail patronage recover?",
                            class_="hero-title"
                        ),
                        ui.p(
                            "Use the filters to compare selected services across years and recovery periods.",
                            class_="hero-copy"
                        )
                    ),
                    class_="hero-panel"
                ),
                ui.output_ui("route_recovery_cards"),
                ui.div(
                    ui.div(
                        ui.h3("Recovery index over time (2019 = 100)"),
                        ui.output_plot("home_recovery_chart"),
                        class_="dashboard-card"
                    ),
                    ui.div(
                        ui.h3("Service network map"),
                        output_widget("network_map", height="500px"),
                        class_="dashboard-card"
                    ),
                    class_="home-grid"
                ),
                class_="home-tab"
            )
        ),
        ui.panel_conditional(
            "input.view_tab === 'charts'",
            ui.div(
                ui.div(
                    ui.h3("Recovery index over time (2019 = 100)"),
                    ui.output_plot("recovery_trend_chart"),
                    class_="dashboard-card"
                ),
                ui.div(
                    ui.h3("Annual patronage by selected service"),
                    ui.output_plot("raw_patronage_chart"),
                    ui.p(
                        "Tip: Rail patronage represents the whole train network, while the bus values are individual routes. "
                        "Untick rail to compare bus routes more clearly, or use the recovery index to compare each service "
                        "against its own 2019 baseline.",
                        class_="chart-note"
                    ),
                    class_="dashboard-card"
                ),
                ui.div(
                    ui.h3("Latest-year recovery ranking"),
                    ui.output_plot("recovery_ranking_chart"),
                    class_="dashboard-card"
                ),
                class_="chart-grid"
            )
        ),
        class_="dashboard-shell"
    ),
    window_title="Auckland Public Transport Recovery Dashboard",
    fillable=True
)

# -----------------------------
# Server logic
# -----------------------------

def server(input, output, session):
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

    route_popup_labels = {
        "70": {
            "title": "Route 70",
            "description": "Botany to Britomart via Panmure and Ellerslie.",
        },
        "NX1": {
            "title": "Northern Express NX1",
            "description": "Hibiscus Coast to Britomart via the Northern Busway.",
        },
        "NX2": {
            "title": "Northern Express NX2",
            "description": (
                "Hibiscus Coast to Auckland universities "
                "via Wellesley Street."
            ),
        },
    }

    patronage_2024 = patronage[patronage["year"] == 2024].set_index("service")
    service_colours = {
        "70": "#0d6efd",
        "NX1": "#169b62",
        "NX2": "#7b3fe4",
        "train": "#f59f00",
    }
    service_titles = {
        "70": "Route 70",
        "NX1": "Route NX1",
        "NX2": "Route NX2",
        "train": "Rail Network",
    }

    map_state = {
        "map": None,
        "bus_layers": {},
        "train_layer": None,
    }

    def build_network_map():
        network_map_widget = Map(
            center=(-36.85, 174.77),
            zoom=11,
            basemap=basemaps.CartoDB.Positron,
            scroll_wheel_zoom=True
        )

        bus_layers = {}

        for service, route_gdf in bus_route_gdfs.items():
            route_names = ", ".join(
                sorted(route_gdf["ROUTENAME"].dropna().unique())
            )
            route_patterns = route_gdf["ROUTEPATTERN"].nunique()
            popup_label = route_popup_labels.get(
                service,
                {
                    "title": f"Bus route {service}",
                    "description": "Selected Auckland bus route.",
                }
            )
            route_patronage = patronage_2024.loc[service]

            layer = GeoData(
                geo_dataframe=route_gdf,
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

            layer.popup = HTML(
                value=(
                    f"<b>{popup_label['title']}</b><br>"
                    f"{popup_label['description']}<br>"
                    f"2024 patronage: {route_patronage['patronage'] / 1_000_000:.2f}M<br>"
                    f"Recovery: {route_patronage['recovery_index']:.0f}% of 2019<br>"
                )
            )

            bus_layers[service] = layer

        train_layer = GeoData(
            geo_dataframe=train_routes_display,
            style=train_style,
            name="Train network"
        )

        train_lines = ", ".join(
            sorted(train_routes_display["ROUTENUMBER"].dropna().unique())
        )

        train_layer.popup = HTML(
            value=(
                "<b>Train network</b><br>"
                f"2024 patronage: {patronage_2024.loc['train', 'patronage'] / 1_000_000:.2f}M<br>"
                f"Recovery: {patronage_2024.loc['train', 'recovery_index']:.0f}% of 2019<br>"
                f"Lines: {train_lines}<br>"
            )
        )

        map_state["map"] = network_map_widget
        map_state["bus_layers"] = bus_layers
        map_state["train_layer"] = train_layer

        return network_map_widget

    network_map_widget = build_network_map()
    register_widget("network_map", network_map_widget)

    @reactive.effect
    def update_map_layers():
        selected_services = {
            str(service).strip().upper()
            for service in (input.services() or [])
        }

        network_map_widget.layers = [network_map_widget.layers[0]]

        for service, layer in map_state["bus_layers"].items():
            if service in selected_services:
                network_map_widget.add_layer(layer)

        if "TRAIN" in selected_services:
            network_map_widget.add_layer(map_state["train_layer"])

    @reactive.calc
    def filtered():
        df = patronage.copy()

        # Service checkbox filter
        selected_services = input.services() or []
        df = df[df["service"].isin(selected_services)]

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

    @render.ui
    def route_recovery_cards():
        df = filtered()

        if len(df) == 0:
            return ui.div(
                "No services match the current filters.",
                class_="dashboard-card"
            )

        latest_year = df["year"].max()
        latest = df[df["year"] == latest_year].copy()
        service_order = ["70", "NX1", "NX2", "train"]
        cards = []

        for service in service_order:
            service_row = latest[latest["service"] == service]

            if len(service_row) == 0:
                continue

            row = service_row.iloc[0]
            colour = service_colours.get(service, "#0d6efd")
            mode = "train" if service == "train" else "bus"

            cards.append(
                ui.div(
                    ui.div(
                        transport_icon(mode),
                        class_="route-icon",
                        style=(
                            f"color: {colour}; "
                            f"background-color: {colour}1f;"
                        )
                    ),
                    ui.div(
                        ui.div(
                            service_titles.get(service, service),
                            class_="route-title",
                            style=f"color: {colour};"
                        ),
                        ui.div(
                            f"{row['recovery_index']:.1f}",
                            class_="route-value"
                        ),
                        ui.div(
                            f"{latest_year} recovery index",
                            class_="route-caption"
                        )
                    ),
                    class_="route-card"
                )
            )

        return ui.div(*cards, class_="route-card-grid")

    @render.plot
    def home_recovery_chart():
        df = filtered()

        fig, ax = plt.subplots(figsize=(8, 4))

        if len(df) == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax.set_axis_off()
            return fig

        for service, group in df.groupby("service"):
            group = group.sort_values("year")
            ax.plot(
                group["year"],
                group["recovery_index"],
                marker="o",
                color=service_colours.get(service),
                label=service_titles.get(service, service)
            )

        ax.axhline(100, linestyle="--", linewidth=1, color="#667085")
        ax.set_xlabel("Year")
        ax.set_ylabel("Recovery index (2019 = 100)")
        ax.set_xticks(sorted(df["year"].unique()))
        ax.legend(title="Service")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig

    @render.plot
    def recovery_trend_chart():
        df = filtered()

        fig, ax = plt.subplots(figsize=(9, 4))

        if len(df) == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax.set_axis_off()
            return fig

        for service, group in df.groupby("service"):
            group = group.sort_values("year")
            ax.plot(
                group["year"],
                group["recovery_index"],
                marker="o",
                label=service
            )

        ax.axhline(100, linestyle="--", linewidth=1, color="#666666")
        ax.set_title("Patronage recovery compared with 2019 baseline")
        ax.set_xlabel("Year")
        ax.set_ylabel("Recovery index, 2019 = 100")
        ax.set_xticks(sorted(df["year"].unique()))
        ax.legend(title="Service")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig

    @render.plot
    def raw_patronage_chart():
        df = filtered()

        fig, ax = plt.subplots(figsize=(9, 4))

        if len(df) == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax.set_axis_off()
            return fig

        for service, group in df.groupby("service"):
            group = group.sort_values("year")
            ax.plot(
                group["year"],
                group["patronage"],
                marker="o",
                label=service
            )

        ax.set_title("Annual patronage by selected service")
        ax.set_xlabel("Year")
        ax.set_ylabel("Annual boardings")
        ax.yaxis.set_major_formatter(FuncFormatter(format_boardings))
        ax.set_xticks(sorted(df["year"].unique()))
        ax.legend(title="Service")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig

    @render.plot
    def recovery_ranking_chart():
        df = filtered()

        fig, ax = plt.subplots(figsize=(9, 4))

        if len(df) == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax.set_axis_off()
            return fig

        latest_year = df["year"].max()
        latest = df[df["year"] == latest_year].sort_values("recovery_index")

        ax.barh(
            latest["service"],
            latest["recovery_index"],
            color="#2ca25f"
        )
        ax.axvline(100, linestyle="--", linewidth=1, color="#666666")
        ax.set_title(f"{latest_year} recovery ranking")
        ax.set_xlabel("Recovery index, 2019 = 100")
        ax.set_ylabel("Service")
        ax.grid(True, axis="x", alpha=0.3)
        plt.tight_layout()

        return fig

app = App(app_ui, server)
