import dash_core_components as dcc
from helpers.constants import *
import dash_html_components as html


def get_cycling_average_power_table(power_averages, body_composition):
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Duration'),
                        html.Th('Power (Watts)'),
                        html.Th('Power:weight (Watts/kg)')
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td('Twenty minutes'),
                            html.Td(round(power_averages['twenty_minute'], 1)),
                            html.Td(round(power_averages['twenty_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Ten minutes'),
                            html.Td(round(power_averages['ten_minute'], 1)),
                            html.Td(round(power_averages['ten_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Five minutes'),
                            html.Td(round(power_averages['five_minute'], 1)),
                            html.Td(round(power_averages['five_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('One minute'),
                            html.Td(round(power_averages['one_minute'], 1)),
                            html.Td(round(power_averages['one_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Thirty seconds'),
                            html.Td(round(power_averages['thirty_second'], 1)),
                            html.Td(round(power_averages['thirty_second'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Five seconds'),
                            html.Td(round(power_averages['five_second'], 1)),
                            html.Td(round(power_averages['five_second'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('One second'),
                            html.Td(round(power_averages['one_second'], 1)),
                            html.Td(round(power_averages['one_second'] / body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                        ]
                    )

                ]
            )
        ],
        className='table table-hover'
    )


def get_cycling_power_summary_table(power_summary):
    return html.Table(
        [
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Th('Normalised power'),
                            html.Td(round(power_summary['normalised_power'], 1)),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Th('Intensity factor'),
                            html.Td(round(power_summary['intensity_factor'], 2)),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Th('TSS'),
                            html.Td(round(power_summary['tss'], 1)),
                        ]
                    )
                ]
            )
        ],
        className='table table-hover'
    )


def get_cycling_power_splits_table(power_splits):

    # Get the maximum number of splits
    # This is used to work out how many columns each cell has to span
    max_split_count = max(map(lambda s: len(s['splits']), power_splits))

    rows = list()

    # Loop over all the sets of splits
    for splits in power_splits:
        cells = list()

        # Get the number of splits in this set of splits
        split_count = len(splits['splits'])

        # Keep track of the previous power for colour coding. The first one will always have no colour
        previous_power = None
        for split in splits['splits']:

            class_name = 'text-center'

            # If we don't have a split then just show the empty placeholder
            if split is None:
                cells.append(html.Td(EMPTY_PLACEHOLDER, colSpan=max_split_count / split_count, className=class_name))
            else:
                # Round the power to the nearest Watt
                current_power = round(split)
                if previous_power is not None:
                    if current_power > previous_power:
                        class_name = 'text-center table-success'
                    elif current_power < previous_power:
                        class_name = 'text-center table-danger'

                # Append the new cell to the list of cells in this row
                cells.append(html.Td(current_power, colSpan=max_split_count/split_count, className=class_name))
                previous_power = current_power

        # Append this row to the list of rows
        rows.append(html.Tr(cells))

    # Return the table containing all the rows we have just put together
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


def get_cycling_power_gradient_table(gradient_splits):

    rows = list()
    for index, row in gradient_splits.iterrows():
        rows.append(
            html.Tr(
                [
                    html.Td(str(index)),
                    html.Td(str(row['duration'].to_pytimedelta())),
                    html.Td(round(row['power_mean'], 0) if isinstance(row['power_mean'], (int, float)) else EMPTY_PLACEHOLDER),
                    html.Td(round(row['power_max'], 0) if isinstance(row['power_max'], (int, float)) else EMPTY_PLACEHOLDER)
                ]
            )
        )

    return html.Table(
        [
            html.Thead(
                [
                    html.Th('Gradient'),
                    html.Th('Duration'),
                    html.Th(TITLE_AVERAGE_POWER),
                    html.Th(TITLE_MAX_POWER)
                ]
            ),
            html.Tbody(
                [
                    *rows
                ]
            )
        ],
        className='table table-hover'
    )


