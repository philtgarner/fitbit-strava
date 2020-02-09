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

