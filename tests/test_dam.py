import unittest

import jdep

# Comparison data generated from https://jupiter-probability-tool.obspm.fr/
# NOTE: Probabilties are rough guesses from looking at the color map
_DATA = {'2024/10/08 18:31:00': {'cml': 315.53 - 60,
                                 'io': 360 - (97.96 - 10),
                                 'ganymede': 360 - (35.08 - 10),
                                 'all_prob': 15,
                                 'nonio_prob': 15,
                                 'regions': ['non-Io']
                                },
         '2024/10/10 09:31:00': {'cml': 290.26 - 60,
                                 'io': 360 - (127.1 - 10),
                                 'ganymede': 360 - (313.47 - 10),
                                 'all_prob': 60,
                                 'nonio_prob': 15,
                                 'regions': ['Io A']
                                },
         '2024/10/12 03:31:00': {'cml': 373.83 - 60,
                                 'io': 360 - (130.93 - 10),
                                 'ganymede': 360 - (225.56 - 10),
                                 'all_prob': 65,
                                 'nonio_prob': 5,
                                 'regions': ['Io A"', 'Io C']
                                },
         '2025/03/08 22:31:00': {'cml': 157.16 - 60,
                                 'io': 360 - (289.25 - 10),
                                 'ganymede': 360 - (340.27 - 10),
                                 'all_prob': 45,
                                 'nonio_prob': 0,
                                 'regions': ['Io B']
                                },
         '2025/03/08 23:31:00': {'cml': 193.42 - 60,
                                 'io': 360 - (280.79 - 10),
                                 'ganymede': 360 - (338.38 - 10),
                                 'all_prob': 65,
                                 'nonio_prob': 5,
                                 'regions': ['Io B', "non-Io B'"]
                                },
         '2025/03/09 13:31:00': {'cml': 341.13 - 60,
                                 'io': 360 - (162.72 - 10),
                                 'ganymede':360 - (309.15 - 10),
                                 'all_prob': 15,
                                 'nonio_prob': 10,
                                 'regions': ['non-Io']
                                }
        }


class dam_tests(unittest.TestCase):
    def test_cml(self):
        """Test determining Jupiter's central meridian longitude"""
        
        for date,values in _DATA.items():
            self.assertTrue(abs(values['cml']-jdep.get_jupiter_cml(date)) < 3)
        
    def test_io_phase(self):
        """Test determining the phase of Io"""
        
        for date,values in _DATA.items():
            self.assertTrue(abs(values['io']-jdep.get_io_phase(date)) < 3)
        
    def test_ganymede_phase(self):
        """Test determining the phase of Ganymede"""
        
        for date,values in _DATA.items():
            self.assertTrue(abs(values['ganymede']-jdep.get_ganymede_phase(date)) < 3)
            
    def test_emission_probability(self):
        """Test determining the probability of decametric emission"""
        
        with self.subTest(emission_type='all'):
            for date,values in _DATA.items():
                self.assertTrue(abs(values['all_prob']-jdep.get_dam_probability(date, 'all')) < 5)
            
        with self.subTest(emission_type='non-io'):
            for date,values in _DATA.items():
                self.assertTrue(abs(values['nonio_prob']-jdep.get_dam_probability(date, 'non-io')) < 5)
                
    def test_emission_regions(self):
        """Test determining the likely emission regions for decametric emission"""
        
        with self.subTest(emission_type='all'):
            for date,values in _DATA.items():
                self.assertEqual(values['regions'], jdep.get_dam_regions(date, 'all'))


class dam_test_suite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        
        loader = unittest.TestLoader()
        self.addTests(loader.loadTestsFromTestCase(dam_tests))
                

if __name__ == '__main__':
    unittest.main()
