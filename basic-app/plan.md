## 1. Motivation and Audience

### 1.1 What problem does your dashboard address?
#### How did Auckland’s most popular bus routes and rail patronage recover compared with 2019 pre-COVID levels?
This dashboard explores how Auckland’s most popular bus routes and rail patronage recovered compared with 2019 pre-COVID levels. It focuses on routes 70, NX1, NX2, and the rail network, using a recovery index where 2019 = 100.

### 1.2 Who is it for?
The dashboard is intended for transport planners, students, local government staff, or anyone interested in Auckland public transport recovery. It helps users compare which services recovered more strongly, which remain below 2019 levels, and how bus routes differ from the wider rail network.

### 1.3 What insight does it enable?
This dashboard helps show how Auckland’s key public transport services recovered after the disruption caused by COVID. By comparing routes 70, NX1, NX2, and the rail network against their 2019 pre-COVID patronage levels, users can see which services returned closest to normal and which remained below their previous levels. This provides insight into how travel behaviour changed over time and whether major bus routes and rail services recovered at the same pace.

## 2. Data and Preparation

### 2.1 Datasets used
This dashboard uses annual patronage data from 2019 to 2024 for routes 70, NX1, NX2, and the rail network. The bus routes' data are derived from Auckland Transport's bus performance reports, while the rail data is derived from Auckland Transport monthly patronage data summed into yearly totals.

### 2.2 Cleaning and preparation steps
The patronage table was prepared using Excel as a clean CSV with one row per service and the columns being years 2019 to 2024. Using Python, the data was reshaped from wide to long format, converted to numeric values, and used to calculate recovery_index and change_from_2019_pct. Years were also grouped into periods: pre-COVID baseline, COVID disruption, early recovery, and recovery period.

Spatial data is loaded from bus_routes.geojson and train_routes.geojson. Both are reprojected to EPSG:4326 for ipyleaflet, and route numbers are cleaned so selected services can be matched to their map features.
### 2.3 Limitations
A key limitation is that bus values are individual routes, while rail represents the whole train network, so raw patronage cannot be directly compared. The analysis also does not account for population growth, service frequency, or other travel behaviour changes.

## Section 3: Technical Planning

### App Structure
This dashboard is built using Shiny for Python. The dashboard loads a cleaned patronage CSV file and two bus and train route spatial datasets. The patronage data is reshaped from wide to long format before performing analysis and additional columns are calculated, including baseline_2019, recovery_index, change_from_2019_pct, service_type, and period.

The main inputs for the dashboard are the selected services, year range, and recovery periods. These inputs supply user input for a shared @reactive.calc function called filtered(), which filters the patronage table once and then supplies the filtered data to visualization outputs. This avoids repeating the same filtering code separately for each chart and the map.

The main outputs for the dashboard are rendered using Shiny's decorators. The route cards are produced with @render.ui, while the charts are produced with @render.plot. The interactive map is made using ipyleaflet and uses register_widget to connect with Shiny. A @reactive.effect updates the map layers when the selected services change, so the map shows only the relevant bus routes and train network. Another @reactive.effect with @reactive.event(input.reset) resets all filters when the user clicks the reset button.

### Performance
The bus and train route geometries are loaded once at the start of the app rather than repeatedly inside each output. The rail geometry is simplified before display, and the route specific GeoDataFrames are precomputed for the bus routes. This improves the dashboard's performance as it reduces repeated spatial filtering and helps the map update more smoothly.

## Section 4: User Interface Walkthrough
When the user opens the dashboard, they first see the Home page. A sidebar on the left with selections and filters allows them to change the visualisation data based on services, years, and periods of years. There is also a 'reset filter' button that clears the user's selection and removes all filters. Towards the top of the sidebar, the user sees a 'Charts' tab that allows them to view more detailed breakdown charts regarding the recovery information, responsive to their filter selections.

On the home page of the dashboard, they see a large title on the top of the page, describing the main theme of the dashboard (Auckland Public Transport Recovery Dashboard), with a subtitle just below to specify the recovery comparison. Below that, the user sees cards showing each route's 2024 recovery index based on their filter selections. Further below, they see a recovery index chart of their filtered selections showing the recovery index of individual routes across 2019 to 2024. Adjacent to the chart is an interactive map showing the services' routes. The user is able to click on each individual route to see the route's information such as their direction, 2024 patronage data, and the patronage recovery percentage compared with 2019 data. Again, the routes are also reflected by the user's filter selections.

The user can then switch to the Charts tab for a more detailed breakdown. This page includes a recovery index chart, a raw annual patronage chart, and a latest-year recovery ranking chart. The recovery index chart is used for the fairest comparison because each service is compared against its own 2019 baseline. The raw patronage chart is included as context, but users are advised that rail represents the whole train network while the bus values are individual routes.