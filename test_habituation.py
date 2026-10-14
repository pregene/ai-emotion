import unittest
from simulation import Simulation
from vision import face


class HabituationTests(unittest.TestCase):
    def test_static_bright_and_smiling_inputs_lose_interest(self):
        for frame in ([1.] * 100, face(True)):
            sim = Simulation()
            sim.visual_mode = True
            trace = []
            for _ in range(160):
                sim.step(frame)
                trace.append((sim.evaluated_emotion[1], sim.concentrations[:]))
            early, late = trace[10], trace[-1]
            self.assertGreater(late[0]['Boredom'], early[0]['Boredom'] + .2)
            self.assertLess(late[0]['Interest'], early[0]['Interest'] * .65)
            self.assertLess(late[1][0], early[1][0])
            self.assertGreater(sim.familiarity, .99)

    def test_changed_screen_restores_interest_and_releases_boredom(self):
        sim = Simulation()
        sim.visual_mode = True
        for _ in range(160):
            sim.step(face(True))
        before = sim.evaluated_emotion[1].copy()
        sim.step([1.] * 100)
        self.assertGreater(sim.novelty, .9)
        self.assertLess(sim.familiarity, .15)
        for _ in range(5):
            sim.step([1.] * 100)
        after = sim.evaluated_emotion[1]
        self.assertGreater(after['Interest'], before['Interest'] + .03)
        self.assertLess(after['Boredom'], before['Boredom'] - .15)

    def test_noise_does_not_build_static_familiarity(self):
        sim = Simulation()
        for _ in range(100):
            sim.step(sim.stimulus('noise', 1.))
        self.assertLess(sim.familiarity, .1)
        self.assertLess(sim.boredom, .1)


if __name__ == '__main__':
    unittest.main()
