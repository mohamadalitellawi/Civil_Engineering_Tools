import pytest
from mat_ceng import say_hi
from mat_ceng import Material,Section_Dimensions,Load_Case,calculate_column_actual_moment_of_inertia
import pathlib


module_folder = pathlib.Path(__file__).parents[1] / 'src' / 'mat_ceng'

def test_say_hi():
    print(f'{module_folder=}')
    assert say_hi() == 'Hello World'

def test_calculate_column_actual_moment_of_inertia():
    material = Material(50,420)
    dim = Section_Dimensions(650,1200,40,0.02)
    load = (Load_Case(Pu=2633,Mu_22=1132,Mu_33=1854,Pu_sustained=1000)).import_from_etabs(flip_axial_sign=False)
    result = calculate_column_actual_moment_of_inertia(material, dim,load)
    expected = (0.396,0.493)
    assert result['ratio'][0],3 == pytest.approx(expected[0])
    assert result['ratio'][1],3 == pytest.approx(expected[1])

