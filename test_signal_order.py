import random
import math
import unittest
from simulation import Simulation
from vision import signal_order


class SignalOrderTests(unittest.TestCase):
    def test_order_distinguishes_uniform_alternating_and_random(self):
        rng = random.Random(100)
        self.assertEqual(signal_order([.5] * 100), 1.)
        self.assertGreater(signal_order([float((x+y) % 2) for y in range(10) for x in range(10)]), .99)
        self.assertLess(signal_order([rng.random() for _ in range(100)]), .4)

    def test_random_input_increases_anxiety_not_interest(self):
        regular, noise = Simulation(), Simulation()
        regular.visual_mode = noise.visual_mode = True
        rng = random.Random(100)
        for cycle in range(80):
            # Both inputs use the same range and refresh every cycle.
            regular.step([.5 + .5 * math.sin(x*.7 + y*.3-cycle*.25)
                          for y in range(10) for x in range(10)])
            noise.step([rng.random() for _ in range(100)])
        a, b = regular.evaluated_emotion[1], noise.evaluated_emotion[1]
        self.assertGreater(b['Anxiety'], a['Anxiety'] + .05)
        self.assertGreater(a['Calm'], b['Calm'] + .05)
        self.assertGreater(a['Interest'], b['Interest'] + .05)


if __name__ == '__main__':
    unittest.main()
