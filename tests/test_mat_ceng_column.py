import pytest
from mat_ceng import (
    Material,
    Section_Dimensions,
    Load_Case,
    Column,
    calculate_column_actual_moment_of_inertia,
    calculate_minor_delta_ns,
    calculate_major_delta_ns,
    calculate_Cm,
    calculate_Ise)


def test_calculate_column_actual_moment_of_inertia():
    material = Material(50,420)
    dim = Section_Dimensions(650,1200,40,0.02)
    load = (Load_Case(Pu=2633,Mu_22=1132,Mu_33=1854,Pu_sustained=1000)).import_from_etabs(flip_axial_sign=False)
    result = calculate_column_actual_moment_of_inertia(material, dim,load)
    expected = (0.396,0.493)
    assert result['ratio'][0],3 == pytest.approx(expected[0])
    assert result['ratio'][1],3 == pytest.approx(expected[1])

def test_calculate_Cm():
    m1 = -0.464
    m2 = 2.727
    assert round(calculate_Cm(m1,m2),3) == pytest.approx(0.532)

def test_calculate_Ise():
    assert round(calculate_Ise(7,16,250,50)) == pytest.approx(12635938.042)


def test_calculate_column_actual_moment_of_inertia_test_2():
    material = Material(32,420)
    dim = Section_Dimensions(250,800,40,0.0141,7,2,16)
    load = (Load_Case(Pu=1385.0853,Mu_22=2.727,Mu_33=300,Pu_sustained=1150.0993)).import_from_etabs(flip_axial_sign=False)
    result = calculate_column_actual_moment_of_inertia(material, dim,load)
    expected = (0.875,0.719)
    assert result['ratio'][0] == pytest.approx(expected[0])
    assert result['ratio'][1] == pytest.approx(expected[1])

def test_calculate_minor_delta_ns():
    material = Material(32,420)
    dim = Section_Dimensions(250,800,40,0.0141,7,2,16)
    load = (Load_Case(Pu=1385.0853,Mu_22=2.727,Mu_33=300,Pu_sustained=1150.0993)).import_from_etabs(flip_axial_sign=False)
    col = Column(4800,4800,1,1)

    result = calculate_minor_delta_ns(col,material,dim,load,0.532)
    assert round(result['Etabs'],3) == pytest.approx(1.849)
    assert round(result['Method_B'],3) == pytest.approx(24.492)
    assert round(result['Method_C'],3) == pytest.approx(1.000)
    '''
    Etabs: delta_ns = 1.8492169879887108
    Method B: delta_ns = 24.492010806874397
    Method C: delta_ns = 1
    '''