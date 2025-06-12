import pytest
from mat_ceng import say_hi
from mat_ceng import Material,Section_Dimensions,Load_Case,calculate_column_actual_moment_of_inertia
import pathlib


module_folder = pathlib.Path(__file__).parents[1] / 'src' / 'mat_ceng'

def test_say_hi():
    print(f'{module_folder=}')
    assert say_hi() == 'Hello World'


