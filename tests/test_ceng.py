from ceng import say_hi
import pathlib


module_folder = pathlib.Path(__file__).parents[1] / 'src' / 'ceng'

def test_say_hi():
    print(f'{module_folder=}')
    assert say_hi() == 'Hello World'

def test_excel_runner():
    assert 1 == 1