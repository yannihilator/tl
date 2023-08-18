from datetime import date, datetime
import os
import argparse

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np
from fuzzysearch import fuzzysearch

def save_data():
    # Save entries df.
    df_entries['id'] = df_entries.index + 1
    df_entries.to_csv('entries.csv', index=False)

    # Save charge codes df.
    df_charge_code['id'] = df_charge_code.index + 1
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
        index = len(df_entries) if len(df_entries) > 0 else 0
        df_entries.loc[index] = ['',start_time,'','']
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
            # Search for the charge code based on the keyword.
            for index, row in df_charge_code.iterrows():
                # Use fuzzysearch to match.
                if fuzzysearch(charge_keyword, row['charge_code'].lower()):
                    # Ask the user if this is the correct charge number.
                    charge_keyword = input(f'Found {row["charge_code"]}. Input new search, or press enter if correct: ')
                    if charge_keyword == '':
                        charge_code = row

        # Add record and save data.
        df_entries.loc[df_entries.id == current.id, 'stop'] = stop_time
        df_entries.loc[df_entries.id == current.id, 'charge'] = charge_code['id']
        save_data()
        print(f'Record added for {charge_code["charge_code"]}')

def add(charge_code, entry):
    '''
    Method that adds a charge code or entry to their respective datafile.
    '''
    if charge_code:
        index = len(df_charge_code) if len(df_charge_code) > 0 else 0
        df_charge_code.loc[index] = ['',charge_code]

    save_data()
    print(f'Added {charge_code}')


def status():
    cls()
    # Create the CLI Status UI.
    today = date.today().strftime('%m/%d/%Y')
    print(f'Timelog for {today}')
    print('======================')

    # Add status on current entry, if timer is running.
    current = current_record()
    if not current.empty:
        duration = datetime.now() - current['start']
        print(f'Current Entry: {duration}')
        print(f'Today\'s Total: ')

    # Add status on record for today.
    print('')
    print('-------------------------------------------------------')
    print('ID  |  Duration  |  Start  |  Stop  |  Charge Code')
    print('')

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
df_charge_code = pd.read_csv('charge_codes.csv')

# Main entrypoint.
run()
