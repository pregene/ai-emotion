# Hormone model

## Scope and units

The model uses 20 chemical signal profiles. The interface calls them hormones for convenience, including neurotransmitters such as dopamine and serotonin. Concentrations are dimensionless grid occupancy, not blood measurements. Profile descriptions reference physiological functions; numerical gains, emotional weights, interaction edges, and time constants are synthetic modeling choices.

Each species occupies up to 500 cells of a 100 x 100 grid. Concentration ranges from 0 to 0.050 with a resolution of 0.0001 after occupancy reconciliation. Internal dynamics use levels normalized by 0.050. A cycle is model time and has no calibrated conversion to physiological seconds.

## Profiles

| Profile | Functional description | Model role |
|---|---|---|
| Dopamine | Reward learning and motivation | Reward drive, Joy |
| Serotonin | Mood, sleep, appetite regulation | Safety drive, Calm |
| Oxytocin | Bonding, childbirth, milk release | Social drive, Bonding |
| Cortisol | Stress response and metabolism | Stress drive, Anxiety |
| Adrenaline | Acute fight-or-flight response | Threat drive, Anxiety, Arousal |
| Norepinephrine | Alertness and attention | Arousal drive, Anxiety, Interest |
| Endorphin | Pain relief and well-being | Relief drive, Joy, Calm |
| Melatonin | Circadian and sleep signaling | Darkness drive, Sleepiness |
| Vasopressin | Water retention and fluid balance | Fixed hydration drive |
| Testosterone | Reproduction and sexual development | Baseline drive |
| Estradiol | Reproduction and sexual development | Baseline drive, prolactin influence |
| Progesterone | Reproductive cycle and pregnancy support | Baseline drive |
| Prolactin | Milk production | Dopamine and estradiol influence |
| Insulin | Glucose reduction and energy storage | Meal drive |
| Glucagon | Glucose elevation | Fasting drive |
| Leptin | Energy balance and appetite suppression | Satiety drive |
| Ghrelin | Appetite stimulation | Hunger drive |
| Thyroxine | Metabolism and growth | Baseline drive |
| Growth hormone | Growth and metabolism | Growth drive |
| Aldosterone | Sodium retention and fluid balance | Fixed hydration drive |

## Stimulus interpretation and emotion feedback

The cycle follows `current concentrations -> stimulus interpretation -> complete emotion evaluation -> secretion -> next concentrations`.

Visual features include brightness, motion, edges, positive area expansion, and similarity to synthetic smiling/frowning templates. They provide illustrative evidence for reward, threat, social engagement, and safety. Four interleaved output channels modulate that evidence relative to moving baselines. Explicit contexts assign meanings to signal intensity.

A concentration-dependent alarm combination and buffering combination modify interpretation. Frustration, attention, and low-stimulation memories provide temporal context. Joy, Calm, Bonding, and Anxiety use weighted concentrations; Anger, Interest, and Low mood combine concentrations with these memories. All scores range from 0 to 1. A difference below 0.04 between the two highest scores produces Mixed.

The full emotion vector influences secretion. Selected drives combine 70% interpreted stimulus response and 30% associated emotion score. The evaluated emotion is retained for display and history before concentrations advance.

## Habituation and signal order

Raw inputs are compared with a moving reference independently of hormone-modified outputs. Repeated input accumulates familiarity with a 4% update; unexpected changes release familiarity. Familiarity reduces reward and arousal drives, which lowers modeled dopamine and norepinephrine secretion. Boredom accumulates gradually using familiarity, current chemical engagement, and interpreted threat. It is a separate score from Low mood. Interest uses hormone concentrations, attention, and boredom rather than novelty alone.

Spatial order is estimated from the strongest absolute horizontal or vertical correlation at offsets of one to three pixels. This recognizes smooth and alternating patterns; a uniform field has maximal order. Disorder combines weak spatial correlation with temporal novelty. Disorder raises threat evidence, suppresses safety and reward, and reduces Interest. Predictable novelty can restore engagement. Anxiety is the concentration-based stress score formerly labeled Tension.

These rules and constants are synthetic. Short-range correlation is an illustrative pattern detector, not a general measure of meaningful structure or a biological model of anxiety. Repeated animated patterns are not yet learned as complete sequences.

### Attention duration

The default habituation rate of 0.04 per cycle deliberately represents a short attention duration. Identical inputs need not lose interest at the same rate across modeled individuals: a lower `Simulation.habituation_rate` slows familiarity accumulation, reward/arousal reduction, and boredom onset. This is a configurable model parameter, not a calibrated measurement or diagnosis of a person's attention. Time is measured in cycles, and the interface currently has no attention-duration presets.

## Delayed interaction network

`hormone_dynamics.py` defines directed stimulation and suppression edges. All edges and coefficients are exploratory assumptions; the references below do not validate this numerical network. Secondary secretion increases another modeled species and does not represent chemical conversion or metabolic byproduct production.

The network includes synthetic cortisol/adrenaline stimulation of endorphin secretion, endorphin/serotonin/oxytocin buffering, dopamine and estradiol effects on prolactin, and appetite-related connections. Edge activity approaches the source concentration with time constants of 4 to 15 cycles.

Each species also has an abstract delayed inhibitory signal. It is an internal control variable, not a newly identified biological hormone. Its target is the normalized excess above 0.60, scaled by 0.40. It approaches that target with a 12-cycle time constant. Sustained elevated concentration accumulates inhibition; inhibition persists temporarily after concentrations fall and then releases.

For normalized concentration `c`:

```text
activation = 0.15 + 0.95 * drive + stimulation
production = rate * activation / (1 + suppression + 8 * delayed_inhibition)
clearance_rate = 0.45 * rate
dc/dt = production * (1 - c) - clearance_rate * c
```

The rate is 0.30 for profiles with emotion weights and 0.08 for other profiles. Twenty internal Euler substeps integrate each cycle using frozen states for simultaneous updates. Secretion saturation and concentration-dependent clearance operate separately. The G toggle disables interaction edges and delayed inhibitory signals while retaining basic secretion, clearance, and emotion feedback.

## Experiment outputs

`experiment_regulation.py` produces two comparisons:

- Constant secretion drives for 240 cycles with regulation enabled and disabled.
- Identical 100-pixel inputs of 0.6 in the Threat context for 160 cycles with Calm and alarm-biased initial concentrations. The grid is cleared before each cycle to isolate appraisal from spatial placement.

CSV files contain the complete traces. The JSON file contains summary values, and the SVG chart uses fixed 0-to-1 vertical axes. Tests cover delayed peak suppression, secondary response timing, stimulus removal and inhibitory release, initial-state-dependent interpretation, emotion recovery, 2,000-cycle bounds, and convergence between 20 and 80 integration substeps.

## References

- [Cleveland Clinic: reward, mood, bonding, and pain-related signals](https://health.clevelandclinic.org/happy-hormones)
- [Cleveland Clinic: serotonin](https://my.clevelandclinic.org/health/articles/22572-serotonin)
- [Cleveland Clinic: norepinephrine](https://my.clevelandclinic.org/health/articles/22610-norepinephrine-noradrenaline)
- [Endocrine Society: adrenal hormones](https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/adrenal-hormones)
- [Endocrine Society: brain hormones](https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/brain-hormones)
- [Endocrine Society: reproductive hormones](https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/reproductive-hormones)
- [Endocrine Society: pancreas hormones](https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/pancreas-hormones)
- [Endocrine Society: endocrine-related organs and hormones](https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/endocrine-related-organs-and-hormones)
- [Endocrine Society: thyroid and parathyroid hormones](https://www.endocrine.org/patient-engagement/endocrine-library/hormones-and-endocrine-function/thyroid-and-parathyroid-hormones)
