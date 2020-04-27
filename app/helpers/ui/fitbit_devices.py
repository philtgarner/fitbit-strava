from helpers.constants import *
import dash_html_components as html
from datetime import datetime


def get_device_table(devices):
    rows = list()

    # Loop over all the devices.
    # I think most people will only ever have one but it's worth looping just in case
    for device in devices:

        # Get the battery level formatted with a percentage sign
        battery_level = device.get('batteryLevel', None)
        battery_level_formatted = EMPTY_PLACEHOLDER if battery_level is None else f'{battery_level}%'

        # Get the last sync time formatted as we display dates
        sync_date = device.get('lastSyncTime', None)
        sync_date_formatted = EMPTY_PLACEHOLDER
        if sync_date is not None:
            sync_date_formatted = datetime.strptime(sync_date, FITBIT_LOCAL_TIME).strftime(DISPLAY_DATE_FORMAT)

        # Append the device information, battery level and last sync time
        rows.append(
            html.Tr(
                [
                    html.Th('Device'),
                    html.Td(device.get('deviceVersion', EMPTY_PLACEHOLDER)),
                ]
            )
        )
        rows.append(
            html.Tr(
                [
                    html.Th('Battery'),
                    html.Td(battery_level_formatted),
                ]
            )
        )
        rows.append(
            html.Tr(
                [
                    html.Th('Last sync'),
                    html.Td(sync_date_formatted),
                ]
            )
        )

    # Return the table with all the rows for all the devices
    return html.Table(
        [
            html.Tbody(
                [
                    *rows
                ]
            )
        ],
        className='table table-hover'
    )