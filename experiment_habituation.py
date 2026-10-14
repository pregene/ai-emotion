"""Export fixed-input habituation and ordered/random input comparisons."""
import csv
import json
import random
from pathlib import Path
from simulation import Simulation
from vision import VisualScene, face


def run():
    output = Path('experiments')
    output.mkdir(exist_ok=True)
    sim, rows = Simulation(), []
    sim.visual_mode = True
    for cycle in range(166):
        sim.step(face(True) if cycle < 160 else [1.] * 100)
        rows.append({'cycle': sim.cycle, 'phase': 'static' if cycle < 160 else 'changed',
                     **sim.habituation_state(),
                     'interest': sim.evaluated_emotion[1]['Interest'],
                     'anxiety': sim.evaluated_emotion[1]['Anxiety'],
                     'dopamine': sim.concentrations[0],
                     'norepinephrine': sim.concentrations[5]})
    with (output / 'habituation.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    summary = {'static_early': rows[10], 'static_late': rows[159], 'changed': rows[-1]}
    for kind in ('wave', 'noise'):
        sim, scene = Simulation(), VisualScene(seed=100)
        sim.visual_mode = True
        scene.kind = kind
        for cycle in range(80):
            sim.step(scene.frame(cycle))
        summary[kind] = {**sim.habituation_state(), **sim.evaluated_emotion[1]}
    (output / 'habituation-summary.json').write_text(json.dumps(summary, indent=2),
                                                   encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    run()
