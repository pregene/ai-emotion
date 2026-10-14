"""Synthetic interaction network, not a calibrated endocrine model.

Regulators are abstract delayed control signals, NOT named biological hormones.
Secondary secretion uses existing modeled species; it is not chemical conversion.
All rates are per simulation cycle, all levels normalized to MAX_CONCENTRATION.
"""
from hormone_profiles import PROFILES

INDEX = {p[0]: i for i, p in enumerate(PROFILES)}
# source, target, signed secretion influence, response time (cycles)
INTERACTIONS = (
    ('Cortisol', 'Endorphin', .35, 10.),
    ('Adrenaline', 'Endorphin', .25, 6.),
    ('Endorphin', 'Cortisol', -.35, 5.),
    ('Endorphin', 'Adrenaline', -.30, 4.),
    ('Serotonin', 'Adrenaline', -.25, 4.),
    ('Oxytocin', 'Cortisol', -.20, 8.),
    ('Dopamine', 'Prolactin', -.25, 8.),
    ('Estradiol', 'Prolactin', .15, 12.),
    ('Leptin', 'Ghrelin', -.25, 15.),
    ('Ghrelin', 'Growth hormone', .20, 12.),
)


def bounded(v):
    return max(0., min(1., v))


class HormoneDynamics:
    def __init__(self):
        self.enabled = True
        self.substeps = 20
        self.threshold = .60
        self.regulator_tau = 12.
        self.inhibition_strength = 8.
        self.regulators = [0.] * len(PROFILES)
        self.edge_activity = [0.] * len(INTERACTIONS)
        self.last = {}

    def advance(self, levels, drives):
        """Integrate one cycle with simultaneous explicit Euler substeps."""
        dt = 1. / self.substeps
        c = list(levels)
        for _ in range(self.substeps):
            # Freeze every state before computing derivatives (order independent).
            old, regulators, edges = c[:], self.regulators[:], self.edge_activity[:]
            promoted, suppressed = [0.] * len(c), [0.] * len(c)
            for k, (source, target, weight, tau) in enumerate(INTERACTIONS):
                if self.enabled:
                    activity = edges[k] + dt * (old[INDEX[source]] - edges[k]) / tau
                    self.edge_activity[k] = activity
                    values = promoted if weight > 0 else suppressed
                    values[INDEX[target]] += abs(weight) * activity
                else:
                    self.edge_activity[k] = 0.
            secretion, removal, inhibition = [], [], []
            for i, profile in enumerate(PROFILES):
                excess = bounded((old[i] - self.threshold) / (1 - self.threshold))
                self.regulators[i] = (regulators[i] + dt *
                                      (excess - regulators[i]) / self.regulator_tau
                                      if self.enabled else 0.)
                rate = .30 if profile[6] else .08
                # Saturating production and first-order clearance avoid rail pinning.
                activation = .15 + .95 * drives[profile[5]] + promoted[i]
                brake = suppressed[i] + self.inhibition_strength * regulators[i]
                production = rate * activation / (1 + brake)
                clearance = rate * .45 * old[i]
                c[i] = bounded(old[i] + dt * (production * (1 - old[i]) - clearance))
                secretion.append(production * (1 - old[i]))
                removal.append(clearance)
                inhibition.append(brake)
        self.last = {'regulators': self.regulators[:],
                     'edge_activity': self.edge_activity[:],
                     'secretion': secretion, 'clearance': removal,
                     'inhibition': inhibition}
        return c

    def snapshot(self):
        return {'enabled': self.enabled, 'substeps': self.substeps,
                'threshold': self.threshold, 'regulator_tau': self.regulator_tau,
                'inhibition_strength': self.inhibition_strength,
                'interactions': INTERACTIONS, **self.last}
