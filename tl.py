from datetime import date, datetime
import os
import argparse

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np
from fuzzysearch import fuzzysearch

def convert_timedelta(duration):
    '''
    Converts a given Timedelta object into readable string for easier display.
    '''
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

def save_data():
    # Save entries df.
    df_entries.to_csv('entries.csv', index=False)

    # Save charge codes df.
    df_charge_code.to_csv('charge_codes.csv', index=False)

def cls():
    '''
    Function that clears console
    '''
    os.system('cls' if os.name=='nt' else 'clear')

def latest_record():
    '''
    This function gets the latest record based on start time from the entry CSV.
    '''
    if df_entries.empty:
        return None

    # Gets the latest record.
    latest_time = df_entries['start'].max()
    latest_record = df_entries.loc[df_entries['start'] == latest_time]
    if len(latest_record) == 1:
        start_time_record = latest_record.iloc[0]
        return start_time_record
    else:
        return None

def current_record():
    '''
    Gets the record based on if there is a start time. If there is no record with ONLY a start time, it returns null.
    '''
    latest = latest_record()
    return latest if (not latest is None) and (pd.isnull(latest['stop']) and pd.isnull(latest['start']) == False) else pd.Series(dtype=object)

def start():
    '''
    Method that starts the timer for the current task.
    '''
    if df_charge_code.empty:
        print('Add at least one charge code before starting the timelog')
        return

    current = current_record()
    if not current.empty:
        print('Timer is already running!')
    else:
        # Set the start time.
        start_time = datetime.now()

        # Add record and save to datafile.
        id = df_entries['id'].max() + 1 if len(df_entries) > 0 else 1
        index = len(df_entries) if len(df_entries) > 0 else 0
        df_entries.loc[index] = [id,start_time,'','']
        save_data()

        # Notify timer has started.
        print(f'Running at {start_time}')

def stop():
    '''
    Stops the timer if it's already running and saves off the record.
    '''
    current = current_record()
    if current.empty:
        print('The timer is not running!')
    else:
        # Set the stop time.
        stop_time = datetime.now()

        # Get the charge code based on user input.
        charge_keyword = input('Charge code search (Press enter for none): ')
        charge_code = None

        while charge_keyword != '':
            # Boolean if it finds a match.
            found = False
            # Search for the charge code based on the keyword.
            for index, row in df_charge_code.iterrows():
                # Use fuzzysearch to match.
                if not found and fuzzysearch(charge_keyword, row['charge_code'].lower()):
                    # Ask the user if this is the correct charge number.
                    charge_keyword = input(f'Found {row["charge_code"]}. Input new search, or press enter if correct: ')
                    if charge_keyword == '':
                        found = True
                        charge_code = row

            # Prompt user if there was none found.
            if not found:
                charge_keyword = input('Could not find a charge code based on your search. Input new search, or press enter for none: ')

        # Add record and save data.
        df_entries.loc[df_entries.id == current.id, 'stop'] = stop_time
        df_entries.loc[df_entries.id == current.id, 'charge'] = charge_code['id'] if charge_code is not None else None
        save_data()

        # Construct and show message that it was added.
        duration = convert_timedelta(stop_time - current['start'])
        charge = charge_code['charge_code'] if charge_code is not None else '--'
        print(f'Added {duration} for {charge}')

def add(charge_code, entry):
    '''
    Method that adds a charge code or entry to their respective datafile.
    '''
    if charge_code:
        id = df_charge_code['id'].max() + 1
        index = len(df_charge_code) if len(df_charge_code) > 0 else 0
        df_charge_code.loc[index] = [id,charge_code]

    save_data()
    print(f'Added {charge_code}')


def status():
    # Get the entries for today and sum their duration.
    df_today = df_entries.sort_values('start',ascending=False)
    df_today = pd.merge(df_today, df_charge_code, left_on='charge', right_on='id', how='left')
    today_duration = (df_today['stop'] - df_today['start']).sum()
    # Create the CLI Status UI.
    cls()
    today = date.today().strftime('%m/%d/%Y')
    print(f'                         Timelog for {today}')
    print('====================================================================')

    # Add status on running entry, if timer is running.
    current = current_record()
    if not current.empty:
        # Get duration of running entry.
        running_duration = datetime.now() - current['start']
        running_duration_str = convert_timedelta(running_duration)
        # Get duration of total for the day, including running entry.
        total_running_duration = today_duration + running_duration
        total_running_duration_str = convert_timedelta(total_running_duration)
        print(f'Running: {running_duration_str}')
        print(f'Today:   {total_running_duration_str}')
    else:
        # Show total duration for the today.
        total_duration_str = convert_timedelta(today_duration)
        print(f'Today:   {total_duration_str}')


    # Add status on record for today.
    print('____________________________________________________________________')
    print('  ID   |    Duration    |    Start    |    Stop    |    Charge Code')
    print('____________________________________________________________________')
    for index,row in df_today.iterrows():
        start = row['start'].strftime('%H:%M:%S') if not pd.isnull(row['start']) else '   --   '
        stop = row['stop'].strftime('%H:%M:%S') if not pd.isnull(row['stop']) else '   --   '
        duration = convert_timedelta(row['stop'] - row['start']) if (not pd.isnull(row['start']) and not pd.isnull(row['stop'])) else '   --   '
        charge = row['charge_code'] if not pd.isnull(row['charge_code']) else '   --   '
        print(f'  {row["id_x"]}         {duration}        {start}     {stop}       {charge}')

def run():
    # Get arguments.
    args = parser.parse_args()

    # Call function based on command argument.
    if args.command == 'status':
        status()

    if args.command == 'add':
        add(args.charge_code, args.entry)

    if args.command == 'stop':
        stop()

    if args.command == 'start':
        start()

# Intantiate the parser.
parser = argparse.ArgumentParser(description='CLI timelog so you can track your time efficiently.')
# Command argument.
parser.add_argument('command', type=str, help='Main argument for timelog. Can be: start, stop, status, add')
# Optional charge code argument.
parser.add_argument('--charge-code', type=str, help='Charge code argument')
# Optional entry argument.
parser.add_argument('--entry', type=str, help='Entry argument')

# Create the CSV datafiles if they do not exist.
if not os.path.exists('entries.csv'):
    file = open('entries.csv','a+')
    file.write('id,start,stop,charge')
    file.close()

if not os.path.exists('charge_codes.csv'):
    file = open('charge_codes.csv','a+')
    file.write('id,charge_code')
    file.close()

# Get dataframes.
df_entries = pd.read_csv('entries.csv')
df_entries['start'] = pd.to_datetime(df_entries['start'])
df_entries['stop'] = pd.to_datetime(df_entries['stop'])
#df_entries['duration'] = df_entries['stop'] - df_entries['start']
df_charge_code = pd.read_csv('charge_codes.csv')

# Main entrypoint.
run()
