import unittest
from hormone_dynamics import HormoneDynamics, INDEX
from hormone_profiles import PROFILES
from simulation import Simulation


def drives(value=1.):
    return {p[5]: value for p in PROFILES}


class RegulationTests(unittest.TestCase):
    def test_same_evidence_different_state(self):
        calm, alarm = Simulation(), Simulation()
        calm.concentrations[1:7] = [.045, .045, .005, .005, .005, .045]
        alarm.concentrations[1:7] = [.005, .005, .045, .045, .045, .005]
        a = calm.interpret_stimulus(.3, .6, .3, .6)
        b = alarm.interpret_stimulus(.3, .6, .3, .6)
        self.assertGreater(b['threat'], a['threat'] + .2)
        self.assertGreater(a['safety'], b['safety'] + .2)

    def test_delayed_peak_and_suppression_under_constant_drive(self):
        regulated, unregulated = HormoneDynamics(), HormoneDynamics()
        unregulated.enabled = False
        a = b = [.1] * 20
        trace = []
        fixed = drives()
        for _ in range(240):
            a = regulated.advance(a, fixed)
            b = unregulated.advance(b, fixed)
            trace.append(a[0])
        peak = max(trace)
        self.assertGreater(peak, trace[-1] + .02)
        self.assertGreater(b[0], a[0] + .08)
        self.assertGreater(regulated.regulators[0], 0.)
        self.assertLess(trace.index(peak), 100)

    def test_secondary_response_has_delay(self):
        low, high = HormoneDynamics(), HormoneDynamics()
        a, b = [.1] * 20, [.1] * 20
        b[INDEX['Cortisol']] = .95
        fixed = drives(0.)
        first = high.advance(b, fixed)[6] - low.advance(a, fixed)[6]
        low, high = HormoneDynamics(), HormoneDynamics()
        for _ in range(8):
            a, b = low.advance(a, fixed), high.advance(b, fixed)
        self.assertGreater(b[6] - a[6], first + .01)

    def test_clearance_after_input_stops_and_regulator_release(self):
        model = HormoneDynamics()
        c = [.1] * 20
        for _ in range(100):
            c = model.advance(c, drives())
        peak, brake = c[0], model.regulators[0]
        for _ in range(180):
            c = model.advance(c, drives(0.))
        self.assertLess(c[0], peak - .1)
        self.assertLess(model.regulators[0], brake * .1)

    def test_substep_convergence(self):
        a, b = HormoneDynamics(), HormoneDynamics()
        b.substeps = 80
        ca = cb = [.1] * 20
        fixed = drives()
        for _ in range(120):
            ca, cb = a.advance(ca, fixed), b.advance(cb, fixed)
        self.assertLess(max(abs(x-y) for x, y in zip(ca, cb)), .003)

    def test_long_run_finite_and_bounded(self):
        model = HormoneDynamics()
        c = [1.] * 20
        fixed = drives()
        for _ in range(2000):
            c = model.advance(c, fixed)
            self.assertTrue(all(0 <= v <= 1 for v in c + model.regulators))
        self.assertLess(max(c), .95)

    def test_emotion_evaluated_before_secretion(self):
        sim = Simulation()
        sim.step([.7] * 100)
        self.assertEqual(sim.emotion_history[-1], sim.evaluated_emotion[1])
        record = sim.regulation_history[-1]
        self.assertNotEqual(record['concentrations_before'], record['concentrations_after'])
        self.assertEqual(record['concentrations_after'], sim.concentrations)

    def test_same_input_anger_recovers_with_secondary_secretion(self):
        sim = Simulation()
        sim.context = 'threat'
        sim.concentrations[1:7] = [.005, .005, .045, .045, .045, .005]
        for _ in range(120):
            sim.grid = [[-1] * 100 for _ in range(100)]
            sim.step([.6] * 100)
        first, last = sim.regulation_history[0], sim.regulation_history[-1]
        self.assertGreater(first['emotion'][1]['Anger'], last['emotion'][1]['Anger'] + .2)
        self.assertGreater(last['emotion'][1]['Calm'], first['emotion'][1]['Calm'] + .2)
        self.assertGreater(last['concentrations_after'][6], first['concentrations_before'][6])


if __name__ == '__main__':
    unittest.main()
