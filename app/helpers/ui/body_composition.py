import dash_core_components as dcc
from helpers.constants import *
import dash_html_components as html


def get_body_composition_table(body_composition):
    return html.Table(
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Th('Weight (kg)'),
                        html.Td(round(body_composition['weight'], 2) if body_composition['weight'] is not None else EMPTY_PLACEHOLDER)
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Fat (%)'),
                        html.Td(round(body_composition['fat'], 2) if body_composition['fat'] is not None else EMPTY_PLACEHOLDER)
                    ]
                )
            ]
        ),
        className='table table-hover'
    )