## 1. Motivation and Audience

### 1.1 What problem does your dashboard address?
#### How did Auckland’s most popular bus routes and rail patronage recover compared with 2019 pre-COVID levels?

### 1.2 Who is it for?
This dashboard is designed for Auckland Transport planners, local government staff, and members of the public who want to understand how public transport demand changes across the year. It could help planners identify whether bus, train, or ferry services show stronger seasonal changes, which may inform service planning, communication, or further investigation into travel behaviour.

### 1.3 What insight does it enable?

The dashboard enables users to identify which Auckland public transport mode is most sensitive to seasonal change by comparing bus, train, and ferry boardings across different seasons.


## 2. Data and Preparation

### 2.1 Datasets used

| Bus, train and ferry passengers by day | https://at.govt.nz/about-us/reports-publications/how-many-people-are-taking-buses-trains-and-ferries#index-7f339090b26756a74c9402bc98b7a846ea5f5d87d7cd1068f939f6382553628e | CSV | ~373 rows | date, mode, boardings |

### 2.2 Cleaning and preparation steps

1. Skipped the extra title and note rows at the top of the CSV.
2. Kept only the useful columns: `Date`, `Day`, `Bus`, `Train`, `Ferry`, and `Grand Total`.
3. Renamed the columns to simpler names.
4. Converted the `date` column into a proper date format.
5. Converted the bus, train, ferry, and total boarding values into numbers.
6. Removed rows with missing or invalid dates or boarding values.
7. Added new time columns such as year, month, weekday, and weekend status.
8. Added a `season` column based on the month.
9. Sorted the data by date.
10. Changed the data from wide format into long format so it can be filtered by transport mode.
11. Saved the cleaned data as a new CSV for the Shiny app.

### 2.3 Limitations

### 2.3 Limitations

- The patronage dataset only covers July 2024 to June 2025, so the dashboard shows seasonal patterns for one year rather than long-term seasonal trends.
- The data is aggregated by transport mode, so it can compare bus, train, and ferry use, but it cannot show which specific bus routes, train lines, or ferry services carried the most passengers.
- Daily boardings show how many passengers used each mode, but they do not explain why changes happened, such as weather, holidays, service disruptions, fares, or special events.
- The spatial bus route and bus stop layers show the public transport network, but they do not show service frequency, reliability, or actual passenger numbers at each stop or route.

## Section 3: Technical Planning

When the user opens the dashboard, they see a sidebar on the left and a main dashboard area on the right. The page title reads “Auckland Public Transport Dashboard”, with a short subtitle explaining that the dashboard explores how daily bus, train, and ferry boardings change across seasons. Below the title, there is a large question card asking: “Which Auckland public transport mode is most sensitive to seasonal change?” This introduces the main purpose of the dashboard before the user interacts with the controls.

The sidebar contains the main user inputs. A date range input lets the user choose the period of patronage data to analyse. A transport mode checkbox group lets the user select Bus, Train, Ferry, or multiple modes at once. A season checkbox group lets the user choose Summer, Autumn, Winter, and Spring. A day type radio button input lets the user switch between all days, weekdays only, and weekends only. At the bottom of the sidebar, a reset action button returns the filters to their default values.

The main area contains several outputs arranged as dashboard cards. At the top, summary value cards show total or average daily boardings for Bus, Train, Ferry, and all modes combined. Below this, a quantitative chart shows average daily boardings over time, with separate lines for each selected transport mode. Beside the chart, a map shows Auckland’s public transport network, including bus routes and bus stops.

When the user changes any filter, the dashboard updates automatically. For example, selecting only Ferry and Summer will update the summary cards, chart, and filtered data so they only reflect ferry boardings during summer dates. Selecting “Weekends only” changes the results to show weekend travel patterns instead of all days. The map can also respond to layer choices, allowing the user to show or hide bus routes and bus stops.

The app will use a shared `@reactive.calc` function to create one filtered dataset based on the selected date range, transport modes, seasons, and day type. The summary cards, chart, and table will all use this same filtered dataset so the data is not filtered separately for each output. A `@reactive.effect` will be used for the reset button, which will update the inputs back to their default values when clicked. The filtering logic will subset rows based on the current values of the sidebar inputs.