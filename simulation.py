"""A bounded, illustrative feedback model; no biological calibration implied."""
from dataclasses import dataclass
import random
import math
from hormone_profiles import PROFILES, SOURCES
from vision import visual_features
from hormone_dynamics import HormoneDynamics

SIZE = 100
MAX_CONCENTRATION = 0.05
NAMES = [p[0] for p in PROFILES]
EMOTION_COLORS = {'Joy': '#FFD166', 'Calm': '#70C1B3', 'Bonding': '#F78FB3',
                  'Tension': '#E63946', 'Anger': '#FF5722', 'Interest': '#56CCF2', 'Low mood': '#9381FF'}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


@dataclass(frozen=True)
class Hormone:
    name: str
    factor: float
    color: tuple
    role: str
    source: str
    driver: str
    emotion_weights: dict


class Simulation:
    def __init__(self, seed=42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.hormones = [Hormone(name, gain, tuple(bytes.fromhex(color[1:])),
                                role, SOURCES[source], driver, weights)
                         for name, color, role, source, gain, driver, weights in PROFILES]
        self.concentrations = [0.012 + (i % 5) * 0.004 for i in range(20)]
        self.grid = [[-1] * SIZE for _ in range(SIZE)]
        self.reconcile()
        self.inputs = self.stimulus('noise', 1.0)
        self.outputs = self.inputs[:]
        self.history = []
        self.cycle = 0
        self.last_path = []
        self.context = 'neutral'
        self.drives = {}
        self.sensitivity = 12.0
        self.channel_baselines = None
        self.emotion_history = []
        self.visual_mode = False
        self.visual_features = {}
        self.frustration = 0.
        self.attention = 0.
        self.low_stimulation = 0.
        self.dynamics = HormoneDynamics()
        self.interpretation = {}
        self.evaluated_emotion = None
        self.regulation_history = []

    def reconcile(self):
        """Preserve existing cells; randomly remove excess and fill vacancies."""
        locations = [[] for _ in range(20)]
        empty = []
        for y, row in enumerate(self.grid):
            for x, h in enumerate(row):
                (empty if h < 0 else locations[h]).append((y, x))
        targets = [round(clamp(c, 0, MAX_CONCENTRATION) * SIZE * SIZE)
                   for c in self.concentrations]
        for h, cells in enumerate(locations):
            self.rng.shuffle(cells)
            excess = max(0, len(cells) - targets[h])
            for y, x in cells[:excess]:
                self.grid[y][x] = -1
                empty.append((y, x))
            locations[h] = cells[excess:]
        self.rng.shuffle(empty)
        for h, cells in enumerate(locations):
            for _ in range(targets[h] - len(cells)):
                y, x = empty.pop()
                self.grid[y][x] = h
        # Concentrations represent actual occupancy, at 0.0001 resolution.
        self.concentrations = [n / (SIZE * SIZE) for n in targets]

    def shift_left(self):
        self.grid = [row[1:] + [-1] for row in self.grid]

    def stimulus(self, kind, strength):
        strength = clamp(strength)
        if kind == 'noise':
            return [self.rng.random() * strength for _ in range(SIZE)]
        if kind == 'wave':
            return [strength * (0.5 + 0.5 * math.sin(i * math.tau / SIZE))
                    for i in range(SIZE)]
        if kind == 'pulse':
            return [strength if 35 <= i < 65 else 0.0 for i in range(SIZE)]
        return [strength] * SIZE

    def step(self, inputs):
        if len(inputs) != SIZE or any(not math.isfinite(v) for v in inputs):
            raise ValueError('Expected 100 finite signal values.')
        previous = self.inputs[:]
        self.inputs = [clamp(v) for v in inputs]
        self.visual_features = visual_features(self.inputs, previous)
        signals = self.inputs[:]
        self.last_path = []
        # Hormones remain stationary throughout all 100 signal steps.
        for x in range(SIZE):
            for y in range(SIZE):
                h = self.grid[y][x]
                if h >= 0:
                    factor = self.hormones[h].factor
                    signals[y] = clamp(signals[y] + factor)
            self.last_path.append(signals[:])
        self.outputs = signals
        mean = sum(signals) / SIZE
        spread = math.sqrt(sum((v - mean) ** 2 for v in signals) / SIZE)
        # Signal amplitude has no inherent valence. Context supplies its meaning.
        # These response equations are modeling choices, not clinical equations.
        intensity = clamp(mean)
        variability = clamp(spread * 2)
        # Interleaved receptor groups preserve differences lost in a global mean.
        # Neutral channels are synthetic meanings, not inferred biological valence.
        channels = [sum(signals[i::4]) / 25 for i in range(4)]
        if self.channel_baselines is None:
            self.channel_baselines = [mean] * 4
        responses = [clamp(.5 + .5 * math.tanh(self.sensitivity * (v - baseline)))
                     for v, baseline in zip(channels, self.channel_baselines)]
        self.channel_baselines = [.96 * b + .04 * v
                                  for b, v in zip(self.channel_baselines, channels)]
        threat = intensity if self.context == 'threat' else 0.
        safety = (1 - threat) * (1 - variability)
        reward = intensity if self.context == 'reward' else 0.
        social = intensity if self.context == 'social' else 0.
        darkness = intensity if self.context == 'night' else 0.
        food = intensity if self.context == 'meal' else 0.
        if self.context == 'neutral':
            reward, threat, social, calm = responses
            safety = clamp(calm * (1 - .5 * threat))
            if self.visual_mode:
                v = self.visual_features
                # Explicit demo rules: motion/expansion -> alarm, smile -> reward.
                # Output channel response modulates each visual interpretation.
                threat = clamp(v['motion'] * 2 + v['looming'] * 3 + v['frown'] * .65)
                threat *= .5 + .5 * responses[1]
                reward = clamp(v['smile'] * .8 + v['brightness'] * .15 +
                               v['edges'] * (1 - threat) * .4) * (.5 + .5 * responses[0])
                social = v['smile'] * (.5 + .5 * responses[2])
                safety = clamp(1 - threat - v['motion']) * (.5 + .5 * responses[3])
        old = [c / MAX_CONCENTRATION for c in self.concentrations]
        # The SAME evidence is interpreted using the pre-update chemical state.
        self.interpretation = self.interpret_stimulus(reward, threat, social, safety, old)
        reward, threat, social, safety = (self.interpretation[k]
                                        for k in ('reward', 'threat', 'social', 'safety'))
        v = self.visual_features
        if self.visual_mode and self.context == 'neutral':
            frustration = clamp(v['frown'] + .35 * threat - .5 * reward)
            attention = clamp(3 * v['motion'] + 2 * v['edges']) * (1 - .5 * threat)
            low_stimulation = clamp(1 - 2 * v['brightness'] - 3 * v['motion'] - reward)
        else:
            frustration = clamp(threat * (1 - reward))
            attention = clamp(variability + reward)
            low_stimulation = clamp(1 - intensity - reward)
        self.frustration = .7 * self.frustration + .3 * frustration
        self.attention = .7 * self.attention + .3 * attention
        self.low_stimulation = .94 * self.low_stimulation + .06 * low_stimulation
        self.drives = {
            'reward': reward, 'safety': safety, 'social': social,
            'stress': clamp(.7 * threat + .3 * variability), 'threat': threat,
            'arousal': clamp(.65 * threat + .35 * variability),
            'relief': clamp(.5 * threat + .5 * reward), 'darkness': darkness,
            'hydration': .35, 'baseline': .4,
            'prolactin': clamp(.4 - .25 * old[0] + .15 * old[10]),
            'food': food, 'fasting': 1 - food,
            'satiety': clamp(.7 * old[15] + .3 * food),
            'hunger': clamp(1 - food - .5 * old[15]),
            'growth': clamp(.4 + .3 * darkness + .2 * old[16]),
        }
        # Evaluate the whole emotion vector BEFORE secretion, not just its winner.
        self.evaluated_emotion = self.emotion()
        scores = self.evaluated_emotion[1]
        for driver, label in (('reward', 'Joy'), ('safety', 'Calm'), ('social', 'Bonding'),
                              ('stress', 'Tension'), ('threat', 'Anger'), ('arousal', 'Interest')):
            self.drives[driver] = clamp(.70 * self.drives[driver] + .30 * scores[label])
        self.concentrations = [MAX_CONCENTRATION * c for c in
                               self.dynamics.advance(old, self.drives)]
        self.shift_left()
        self.reconcile()
        self.cycle += 1
        self.history.append((self.cycle, self.concentrations[:], mean))
        self.history = self.history[-240:]
        self.emotion_history.append(self.evaluated_emotion[1].copy())
        self.emotion_history = self.emotion_history[-240:]
        self.regulation_history.append({'cycle': self.cycle,
            'interpretation': self.interpretation.copy(),
            'emotion': self.evaluated_emotion,
            'concentrations_before': [c * MAX_CONCENTRATION for c in old],
            'concentrations_after': self.concentrations[:], **self.dynamics.last})
        self.regulation_history = self.regulation_history[-240:]

    def interpret_stimulus(self, reward, threat, social, safety, levels=None):
        """Synthetic state-dependent appraisal; accepts fixed evidence for experiments."""
        c = levels if levels is not None else [v / MAX_CONCENTRATION
                                               for v in self.concentrations]
        alarm = .5 * c[3] + .3 * c[4] + .2 * c[5]
        buffering = .5 * c[1] + .25 * c[2] + .25 * c[6]
        return {'reward': clamp(reward * (.65 + .8 * c[0]) * (1 - .35 * alarm)),
                'threat': clamp(threat * (.45 + 1.3 * alarm) * (1 - .65 * buffering)),
                'social': clamp(social * (.6 + .8 * c[2]) * (1 - .3 * alarm)),
                'safety': clamp(safety * (.45 + 1.1 * buffering) * (1 - .55 * alarm))}

    def emotion(self):
        c = [v / MAX_CONCENTRATION for v in self.concentrations]
        scores = {}
        for label in ('Joy', 'Calm', 'Bonding', 'Tension'):
            weights = [h.emotion_weights.get(label, 0.) for h in self.hormones]
            scores[label] = clamp(sum(v * w for v, w in zip(c, weights)) /
                                  sum(w for w in weights if w > 0))
        # Exploratory labels, not diagnoses. Hormone levels plus stimulus memory.
        scores['Anger'] = clamp((.5 * c[3] + .3 * c[4] + .2 * c[5] - .2 * c[1]) *
                              (.4 + 1.1 * self.frustration))
        scores['Interest'] = clamp((.55 * c[0] + .45 * c[5]) * (.4 + self.attention))
        scores['Low mood'] = clamp((.45 * (1 - c[0]) + .35 * (1 - c[1]) + .2 * c[3]) *
                              self.low_stimulation)
        ordered = sorted(scores, key=scores.get, reverse=True)
        label = 'Mixed' if scores[ordered[0]] - scores[ordered[1]] < .04 else ordered[0]
        return label, scores

    def body_state(self):
        c = [v / MAX_CONCENTRATION for v in self.concentrations]
        return {'Sleepiness': c[7], 'Hunger': clamp(c[16] - .5 * c[15]),
                'Arousal': clamp((c[4] + c[5]) / 2 - .4 * c[7])}
