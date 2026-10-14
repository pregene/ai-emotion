import unittest
from simulation import Simulation
from vision import VisualScene, SCENES, visual_features, face


class SimulationTests(unittest.TestCase):
    def test_eight_emotions_and_distinct_responses(self):
        results = {}
        for kind in ('smile', 'frown', 'moving', 'still'):
            sim, scene = Simulation(), VisualScene()
            sim.visual_mode, scene.kind = True, kind
            sim.inputs = scene.frame(0)
            for cycle in range(1, 81):
                sim.step(scene.frame(cycle))
            results[kind] = sim.emotion()[1]
            self.assertEqual(set(results[kind]), {'Joy', 'Calm', 'Bonding', 'Anxiety', 'Anger', 'Interest', 'Low mood', 'Boredom'})
            self.assertTrue(all(0 <= value <= 1 for value in results[kind].values()))
        self.assertGreater(results['frown']['Anger'], results['smile']['Anger'])
        self.assertGreater(results['moving']['Interest'], results['still']['Interest'])

    def test_low_stimulation_depression_is_gradual(self):
        sim = Simulation()
        sim.visual_mode = True
        sim.inputs = [0.] * 100
        sim.step([0.] * 100)
        first = sim.emotion()[1]['Low mood']
        for _ in range(79):
            sim.step([0.] * 100)
        self.assertGreater(sim.emotion()[1]['Low mood'], first + .1)
        self.assertGreater(sim.low_stimulation, .9)

    def test_visual_frames_and_motion(self):
        scene = VisualScene()
        for kind, _ in SCENES:
            scene.kind = kind
            frame = scene.frame(12, .7)
            self.assertEqual(len(frame), 100)
            self.assertTrue(all(0 <= v <= .7 for v in frame))
        scene.kind = 'still'
        self.assertEqual(visual_features(scene.frame(1), scene.frame(0))['motion'], 0.)
        scene.kind = 'moving'
        self.assertGreater(visual_features(scene.frame(8), scene.frame(0))['motion'], 0.)
        self.assertEqual(visual_features(face(True), face(True))['smile'], 1.)

    def test_visual_scene_changes_emotion(self):
        results = {}
        for kind in ('smile', 'flash', 'still'):
            sim, scene = Simulation(), VisualScene()
            sim.visual_mode, scene.kind = True, kind
            sim.inputs = scene.frame(0)
            for cycle in range(1, 81):
                sim.step(scene.frame(cycle))
            results[kind] = sim.emotion()[1]
        self.assertGreater(results['smile']['Bonding'], results['still']['Bonding'] + .1)
        self.assertGreater(results['flash']['Anxiety'], results['still']['Anxiety'] + .05)

    def test_neutral_random_signals_sustain_anxiety_with_low_interest(self):
        sim = Simulation()
        for _ in range(240):
            sim.step(sim.stimulus('noise', 1.))
        settled = sim.emotion_history[80:]
        self.assertGreater(sum(s['Anxiety'] for s in settled) / len(settled), .4)
        self.assertLess(sum(s['Interest'] for s in settled) / len(settled), .2)

    def test_constant_signals_settle_without_invented_noise(self):
        sim = Simulation()
        sim.grid = [[-1] * 100 for _ in range(100)]
        sim.concentrations = [0.] * 20
        # Isolate feedback from the evolving hormone placement.
        for _ in range(240):
            sim.grid = [[-1] * 100 for _ in range(100)]
            sim.step([.5] * 100)
        for label in sim.emotion_history[-1]:
            tail = [scores[label] for scores in sim.emotion_history[-20:]]
            self.assertLess(max(tail) - min(tail), .005)

    def test_profiles_have_unique_colors_and_sources(self):
        sim = Simulation()
        self.assertEqual(len({h.color for h in sim.hormones}), 20)
        self.assertTrue(all(h.source.startswith('https://') and h.role for h in sim.hormones))

    def test_context_changes_feedback(self):
        reward, threat = Simulation(), Simulation()
        reward.context, threat.context = 'reward', 'threat'
        # Identical frozen initial grid and signals: only context differs.
        reward.step([.7] * 100)
        threat.step([.7] * 100)
        self.assertEqual(reward.outputs, threat.outputs)
        self.assertGreater(reward.concentrations[0], threat.concentrations[0])
        self.assertGreater(threat.concentrations[3], reward.concentrations[3])

    def test_body_hormones_do_not_imply_emotion(self):
        sim = Simulation()
        before = sim.emotion()
        sim.concentrations[8:] = [.05] * 12
        self.assertEqual(sim.emotion(), before)
        sim.concentrations[7] = .05
        self.assertEqual(sim.emotion(), before)
        self.assertEqual(sim.body_state()['Sleepiness'], 1.)

    def test_shift_direction_and_boundary(self):
        sim = Simulation()
        before = [r[:] for r in sim.grid]
        sim.shift_left()
        for old, new in zip(before, sim.grid):
            self.assertEqual(new, old[1:] + [-1])

    def test_full_occupancy_and_empty_occupancy(self):
        sim = Simulation()
        sim.concentrations = [.05] * 20
        sim.reconcile()
        self.assertEqual(sum(h >= 0 for row in sim.grid for h in row), 10000)
        sim.concentrations = [0] * 20
        sim.reconcile()
        self.assertTrue(all(h == -1 for row in sim.grid for h in row))

    def test_feedback_bounds_and_counts(self):
        sim = Simulation()
        for _ in range(30):
            sim.step(sim.stimulus('noise', 1))
        self.assertEqual(len(sim.last_path), 100)
        self.assertEqual(sim.cycle, 30)
        self.assertTrue(all(0 <= v <= 1 for col in sim.last_path for v in col))
        for i, c in enumerate(sim.concentrations):
            self.assertTrue(0 <= c <= .05)
            self.assertEqual(round(c * 10000), sum(row.count(i) for row in sim.grid))

    def test_signal_uses_stationary_grid_and_all_columns(self):
        sim = Simulation()
        sim.grid = [[0] * 100 for _ in range(100)]
        value = .5
        for _ in range(100):
            value = max(0, min(1, value + sim.hormones[0].factor))
        sim.step([.5] * 100)
        self.assertAlmostEqual(sim.outputs[0], value)
        self.assertEqual(sim.inputs, [.5] * 100)

    def test_random_inputs_refresh_each_cycle(self):
        sim = Simulation()
        first = sim.stimulus('noise', 1.)
        sim.step(first)
        second = sim.stimulus('noise', 1.)
        sim.step(second)
        self.assertNotEqual(first, second)
        self.assertEqual(sim.inputs, second)
        self.assertTrue(all(0 <= v <= 1 for v in first + second))

    def test_additive_gain_and_clipping(self):
        sim = Simulation()
        sim.grid = [[-1] * 100 for _ in range(100)]
        # Dopamine +0.10, serotonin -0.04, and blank cell pass-through.
        sim.grid[0][0], sim.grid[1][0] = 0, 1
        sim.grid[3][0], sim.grid[4][0] = 0, 1
        signals = [.5] * 100
        signals[3], signals[4] = .98, .01
        sim.step(signals)
        self.assertAlmostEqual(sim.outputs[0], .6)
        self.assertAlmostEqual(sim.outputs[1], .46)
        self.assertEqual(sim.outputs[2], .5)
        self.assertEqual(sim.outputs[3], 1.)
        self.assertEqual(sim.outputs[4], 0.)


if __name__ == '__main__':
    unittest.main()
