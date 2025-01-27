# from rest_framework.views import APIView
# from django.http import HttpResponse
# from rest_framework.response import Response
# from rest_framework import status
import pandas as pd
import numpy as np
import pymssql
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import calendar
import io

# Set Matplotlib backend to Agg
matplotlib.use('Agg')

start_date_param = "2023-05-01"
end_date_param = "2023-08-01"
table = "Hunting"



# print("start_date_param", start_date_param)
# print("end_date_param", end_date_param)
# print("table", table)

# Connection parameters
server = '3.108.198.195'
database = 'indiataxes_com_indiataxes'
username = 'indiataxes_com_indiataxes'
password = 'SW_02ITNETCOM'

# Create connections for two date ranges
connection = pymssql.connect(server, username, password, database)
print("SQL Server connected successfully!")


end_date_param = datetime.strptime(end_date_param, '%Y-%m-%d')

start_date_current = datetime.strptime(start_date_param, '%Y-%m-%d')

# Check if start_date_current is greater than today's date
today = datetime.now()
if start_date_current > today:
    # Use the same quarter in the previous year, only changing the year
    start_date_current = start_date_current.replace(year=start_date_current.year - 1)

# Calculate end_date_current as 3 months after start_date_current
end_date_current = end_date_param
# print("start_date_current", start_date_current)
# print("end_date_current", end_date_current)

# Calculate the same date range for the previous year
start_date_previous = start_date_current - timedelta(days=365)
end_date_previous = end_date_current - timedelta(days=365)
# print("start_date_previous", start_date_previous)
# print("end_date_previous", end_date_previous)

# Strip time components if necessary
start_date_previous = start_date_previous.replace(
    hour=0, minute=0, second=0, microsecond=0)
end_date_previous = end_date_previous.replace(
    hour=0, minute=0, second=0, microsecond=0)
start_date_current = start_date_current.replace(
    hour=0, minute=0, second=0, microsecond=0)
end_date_current = end_date_current.replace(
    hour=0, minute=0, second=0, microsecond=0)

if table == "Hunting":
    query_previous = "SELECT REQ_ID, REQ_DATE FROM CS_CS_REQUEST WHERE REQ_Date BETWEEN %s AND %s"
    query_current = "SELECT REQ_ID, REQ_DATE FROM CS_CS_REQUEST WHERE REQ_Date BETWEEN %s AND %s"
    date_column = 'REQ_DATE'
else:
    # Adjust column names based on the actual column names in your SQL queries
    query_previous = "SELECT ID, DATE FROM indiataxes_com_indiataxes.S_CLIENT_QUERIES_TICKET WHERE DATE BETWEEN %s AND %s"
    query_current = "SELECT ID, DATE FROM indiataxes_com_indiataxes.S_CLIENT_QUERIES_TICKET WHERE DATE BETWEEN %s AND %s"
    date_column = 'DATE'

params_previous = (start_date_previous, end_date_previous)
params_current = (start_date_current, end_date_current)

# Create two dataframes for the two date ranges
df_previous = pd.read_sql(query_previous, connection, params=params_previous, parse_dates=[
    date_column, 'CLOSED_DATE', 'REOPEN_DATE', 'REOPEN_COMP_DATE'])
df_current = pd.read_sql(query_current, connection, params=params_current, parse_dates=[
    date_column, 'CLOSED_DATE', 'REOPEN_DATE', 'REOPEN_COMP_DATE'])

# Convert the specified date column to a datetime object in both dataframes
df_previous[date_column] = pd.to_datetime(df_previous[date_column])
# print("df_previous:",df_previous)
df_current[date_column] = pd.to_datetime(df_current[date_column])

# Close the connection
connection.close()

# Function to get the calendar week number for a given date
def get_calendar_week(date):
    return date.isocalendar()[1]

# Apply the function to create a new column for calendar week
df_previous['Calendar_Week'] = df_previous[date_column].apply(get_calendar_week)
df_current['Calendar_Week'] = df_current[date_column].apply(get_calendar_week)

# Aggregate data based on calendar week for both current and previous years
if table == "Hunting":
    df_previous_weekly = df_previous.groupby('Calendar_Week').agg({'REQ_ID': 'nunique'}).reset_index()
    df_current_weekly = df_current.groupby('Calendar_Week').agg({'REQ_ID': 'nunique'}).reset_index()
else:
    df_previous_weekly = df_previous.groupby('Calendar_Week').agg({'ID': 'nunique'}).reset_index()
    df_current_weekly = df_current.groupby('Calendar_Week').agg({'ID': 'nunique'}).reset_index()

# print("df_previous_weekly", df_previous_weekly)
# print("df_current_weekly", df_current_weekly)

if not df_previous_weekly.empty:
    # Rename the columns
    df_previous_weekly = df_previous_weekly.rename(
        columns={'DATE': 'Start_Date', 'ID': 'Previous_ID_Count'})

    df_current_weekly = df_current_weekly.rename(
        columns={'DATE': 'Start_Date', 'ID': 'Current_ID_Count'})

    # Check the number of calendar weeks in each DataFrame
    len_previous = len(df_previous_weekly)
    len_current = len(df_current_weekly)

    # If the lengths are different, adjust df_current_weekly to match the length of df_previous_weekly
    if len_current > len_previous:
        df_current_weekly = df_current_weekly.iloc[:len_previous]

    # Now both DataFrames have the same number of calendar weeks

    print("df_previous_weekly:", df_previous_weekly)
    print("df_current_weekly:", df_current_weekly)



    # Plotting
    bar_width = 0.35
    # Use np.arange to ensure integer indexing
    index = np.arange(len(df_previous_weekly))

    fig, ax = plt.subplots()  # Use subplots to capture the plot

    if table == "Hunting":
        # Start the loop from index 1 to skip the first column
        for i in range(1, len(df_previous_weekly) - 1):  # Adjusted range to exclude the last element

            # print("df_previous_weekly['Previous_ID_Count'].....................", df_previous_weekly['Previous_ID_Count'])
            ax.bar(index[i], df_previous_weekly['REQ_ID'][i], width=bar_width, color='blue')
            ax.bar(index[i] + bar_width, df_current_weekly['REQ_ID'][i], width=bar_width, color='orange')

            # Annotate each bar with its value
            ax.annotate(str(df_previous_weekly['REQ_ID'][i]),
                        xy=(index[i], df_previous_weekly['REQ_ID'][i]), ha='center', va='bottom',
                        fontsize=8)
            ax.annotate(str(df_current_weekly['REQ_ID'][i]),
                        xy=(index[i] + bar_width, df_current_weekly['REQ_ID'][i]), ha='center',
                        va='bottom', fontsize=8)
    else:
        # Start the loop from index 1 to skip the first column
        for i in range(1, len(df_previous_weekly) - 1):  # Adjusted range to exclude the last element

            # print("df_previous_weekly['Previous_ID_Count'].....................", df_previous_weekly['Previous_ID_Count'])
            ax.bar(index[i], df_previous_weekly['Previous_ID_Count'][i], width=bar_width, color='blue')
            ax.bar(index[i] + bar_width, df_current_weekly['Current_ID_Count'][i], width=bar_width, color='orange')

            # Annotate each bar with its value
            ax.annotate(str(df_previous_weekly['Previous_ID_Count'][i]),
                        xy=(index[i], df_previous_weekly['Previous_ID_Count'][i]), ha='center', va='bottom',
                        fontsize=8)
            ax.annotate(str(df_current_weekly['Current_ID_Count'][i]),
                        xy=(index[i] + bar_width, df_current_weekly['Current_ID_Count'][i]), ha='center',
                        va='bottom', fontsize=8)


    # Set labels and title
    ax.set_xlabel('Weeks')
    ax.set_ylabel('Count')
    ax.set_title(f'Comparison of Counts Between  {start_date_param} to {end_date_param}')

    # Set xticks only if the DataFrame is not empty
    ax.set_xticks(index[1:] + bar_width / 2)
    ax.set_xticklabels([f'w{i}' for i in range(1, len(df_previous_weekly))])

    # Set legend outside the loop
    ax.legend(['Previous Year', 'Current Year'])

    # Show the plot
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    # Close the plot to free up resources
    plt.close()

