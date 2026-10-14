"""Reviewed functional descriptions, with deliberately synthetic model weights.

Sources describe physiology, NOT the numerical gains or concentration equations.
All concentrations are dimensionless grid occupancy, not blood measurements.
"""
BASE = 'https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/'
SOURCES = {
    'reward': 'https://health.clevelandclinic.org/happy-hormones',
    'serotonin': 'https://my.clevelandclinic.org/health/articles/22572-serotonin',
    'alert': 'https://my.clevelandclinic.org/health/articles/22610-norepinephrine-noradrenaline',
    'adrenal': BASE + 'adrenal-hormones', 'brain': BASE + 'brain-hormones',
    'reproduction': BASE + 'reproductive-hormones', 'pancreas': BASE + 'pancreas-hormones',
    'appetite': BASE + 'endocrine-related-organs-and-hormones',
    'thyroid': BASE + 'thyroid-and-parathyroid-hormones',
}
# name, fixed display color, physiological role, source, synthetic signal gain,
# feedback driver, emotional contribution. Neutral hormones have no emotion weight.
PROFILES = [
    ('Dopamine', '#FFD166', 'Reward learning, motivation, motor control', 'reward', .10, 'reward', {'Joy': 1.0}),
    ('Serotonin', '#70C1B3', 'Mood, sleep, appetite regulation', 'serotonin', -.04, 'safety', {'Calm': 1.0}),
    ('Oxytocin', '#F78FB3', 'Social bonding, childbirth, milk release', 'reward', -.04, 'social', {'Bonding': 1.0}),
    ('Cortisol', '#E63946', 'Stress response and metabolism', 'adrenal', .09, 'stress', {'Tension': 1.0, 'Calm': -.3}),
    ('Adrenaline', '#FF7F11', 'Acute fight-or-flight response', 'adrenal', .16, 'threat', {'Tension': .8}),
    ('Norepinephrine', '#F4A261', 'Alertness, attention, sympathetic response', 'alert', .12, 'arousal', {'Tension': .5}),
    ('Endorphin', '#B8E986', 'Pain relief and well-being', 'reward', -.07, 'relief', {'Joy': .6, 'Calm': .3}),
    ('Melatonin', '#9381FF', 'Circadian and sleep signaling in darkness', 'brain', -.12, 'darkness', {}),
    ('Vasopressin', '#56CCF2', 'Water retention and fluid balance', 'brain', 0., 'hydration', {}),
    ('Testosterone', '#A98467', 'Reproduction and sexual development', 'reproduction', 0., 'baseline', {}),
    ('Estradiol', '#E879F9', 'Reproduction and sexual development', 'reproduction', 0., 'baseline', {}),
    ('Progesterone', '#C4A7E7', 'Reproductive cycle and pregnancy support', 'reproduction', 0., 'baseline', {}),
    ('Prolactin', '#F5CBA7', 'Milk production; inhibited by dopamine', 'brain', 0., 'prolactin', {}),
    ('Insulin', '#06D6A0', 'Blood glucose reduction and energy storage', 'pancreas', -.03, 'food', {}),
    ('Glucagon', '#118AB2', 'Blood glucose elevation during low glucose', 'pancreas', .03, 'fasting', {}),
    ('Leptin', '#90BE6D', 'Energy balance and appetite suppression', 'appetite', -.02, 'satiety', {}),
    ('Ghrelin', '#D4A017', 'Appetite stimulation and growth hormone release', 'appetite', .02, 'hunger', {}),
    ('Thyroxine', '#00B4D8', 'Metabolism and growth regulation', 'thyroid', .02, 'baseline', {}),
    ('Growth hormone', '#CED4DA', 'Growth and metabolism regulation', 'brain', 0., 'growth', {}),
    ('Aldosterone', '#7986CB', 'Sodium retention and fluid balance', 'adrenal', 0., 'hydration', {}),
]
CONTEXTS = [('neutral', 'Neutral'), ('reward', 'Reward'), ('threat', 'Threat'),
            ('social', 'Social'), ('night', 'Night'), ('meal', 'Meal')]
