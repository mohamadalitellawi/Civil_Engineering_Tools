import pathlib
from typing import Any, Optional
import pandas as pd
import xlwings as xw

def excel_runner(
    xlsx_path: pathlib.Path,
    cells_to_set: dict[str, Any] = {},
    cells_to_get: list[str] | dict[str, str] = [],
    sheet_idx: int = 0,
    save_path: Optional[str | pathlib.Path] = None,
    visible: bool = False,
    return_series: bool = False
) -> dict:
    """
    Opens the Excel file at 'xlsx_path' silently, sets the cell values according to
    'inputs' and gathers the calculated results from 'results_cells'. Returns a dict
    representing the values of the calculated results cells.

    'xlsx_path': A path to an Excel spreadsheet file
    'cells_to_set': A dictionary of Excel cell names (e.g. "A1") and new values
        that the cells should be assigned to. These cells are set BEFORE values
        are retrieved from 'cells_to_get'. If an empty dict is passed, no cells
        are set before cell values are retrieved from 'cells_to_get'
    'cells_to_get': Either a list of Excel cell names (e.g. "A1") or a dictionary
        of Excel cell name keys and a string which indicates the "label" or the
        "meaning" of the cell. When results are returned, if provided, the results
        will be keyed by these "label" values.
    'sheet_idx': The integer index of the sheet to access
    'save_path': If provided, will save the altered workbook to this location. If None,
        values will be set and/or retrieved without any workbook being saved.
    'visible': If True, the Excel instance will be visible for a second before closing
    'return_series': If True, the returned dictionary will instead be a pandas.Series
        object.
    """
    with xw.App(visible=visible) as app:
        wb = xw.Book(xlsx_path)
        ws = wb.sheets[sheet_idx]
        for cell_loc, input_value in cells_to_set.items():
            try:
                ws[cell_loc].value = input_value
            except Exception as e:  # Error handling for when cellname does not exist
                raise ValueError(f"The cell '{cell_loc}' does not exist.")
            
        calculated_results = {}
        if isinstance(cells_to_get, dict):
            for result_cell, cell_meaning in cells_to_get.items():
                try:
                    calculated_results[cell_meaning] = ws[result_cell].value
                except Exception as e:  # Error handling for when cellname does not exist
                    raise ValueError(f"The cell '{result_cell}' does not exist.")
        elif isinstance(cells_to_get, list):
            for result_cell in cells_to_get:
                try:
                    calculated_results[result_cell] = ws[result_cell].value
                except Exception as e:  # Error handling for when cellname does not exist
                    raise ValueError(f"The cell {result_cell} does not exist.")
                
        if save_path is not None:
            try:
                wb.save(save_path)
            except Exception as e: # Error handling for when trying to write to file that is already open
                msg = e.excepinfo[2]
                if "Cannot access" in msg:
                    raise PermissionError(f"The file at {save_path} is locked for editing.")
                else:
                    raise e
        wb.close()
    if return_series:
        return pd.Series(calculated_results)       
    return calculated_results