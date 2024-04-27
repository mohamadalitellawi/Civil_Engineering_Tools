from mat_ceng import say_hi
import pathlib


module_folder = pathlib.Path(__file__).parents[1] / 'src' / 'mat_ceng'

def test_say_hi():
    print(f'{module_folder=}')
    assert say_hi() == 'Hello World'

