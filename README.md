# GISCI343_Assignment_2

## Question:
### Which public transport mode is most sensitive to seasonal change?
#### Do bus, train, and ferry boardings rise and fall differently across summer, autumn, winter, and spring?

## Dashboard question

This dashboard asks which Auckland public transport mode is most sensitive to seasonal change. It compares daily bus, train, and ferry boardings across summer, autumn, winter, and spring, allowing users to filter by transport mode, season, and date range to see whether each mode rises and falls differently throughout the year.

## Where does the data come from?

The data comes from Auckland Transport’s public transport patronage reports. This dashboard currently uses the “bus, train and ferry boardings by day” CSV for July 2024 to June 2025, which records daily boardings for each transport mode. The CSV was cleaned in Python by removing the report header rows, keeping the Date, Day, Bus, Train, Ferry, and Grand Total columns, converting dates and boarding counts into usable formats, and reshaping the data into long format so the app can filter by mode, season, and date range.