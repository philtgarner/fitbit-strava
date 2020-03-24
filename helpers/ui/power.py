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

    max_split_count = max(map(lambda s: len(s['splits']), power_splits))

    rows = list()
    for splits in power_splits:
        cells = list()
        split_count = len(splits['splits'])
        previous_power = None
        for split in splits['splits']:
            current_power = round(split)
            class_name = 'text-center'
            if previous_power is not None:
                if current_power > previous_power:
                    class_name = 'text-center table-success'
                elif current_power < previous_power:
                    class_name = 'text-center table-danger'
            cells.append(html.Td(current_power, colSpan=max_split_count/split_count, className=class_name))
            previous_power = current_power
        rows.append(html.Tr(cells))

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
