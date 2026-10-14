"""Reproducible constant-input experiments; writes CSV, JSON and SVG traces."""
import csv
import json
from pathlib import Path
from hormone_dynamics import HormoneDynamics
from simulation import Simulation, MAX_CONCENTRATION


def run():
    output = Path('experiments')
    output.mkdir(exist_ok=True)
    fixed_drives = {h.driver: 1. for h in Simulation().hormones}
    traces, summary = {}, {}
    for enabled in (True, False):
        model = HormoneDynamics()
        model.enabled = enabled
        c, rows = [.1] * 20, []
        for cycle in range(1, 241):
            c = model.advance(c, fixed_drives)
            rows.append({'cycle': cycle, 'dopamine': c[0], 'cortisol': c[3],
                         'endorphin': c[6], 'dopamine_regulator': model.regulators[0],
                         'dopamine_secretion': model.last['secretion'][0]})
        name = 'regulated' if enabled else 'unregulated'
        traces[name] = rows
        peak = max(rows, key=lambda row: row['dopamine'])
        summary[name] = {'peak': peak['dopamine'], 'peak_cycle': peak['cycle'],
                         'final': rows[-1]['dopamine'],
                         'final_regulator': rows[-1]['dopamine_regulator']}

    # Identical raw pixels, context, seed and initial grid. Only levels differ.
    # Grid is frozen empty before each step to isolate appraisal from placement.
    for state in ('calm', 'alarm'):
        sim, rows = Simulation(), []
        sim.context = 'threat'
        sim.concentrations[1:7] = ([.045, .045, .005, .005, .005, .045]
                                    if state == 'calm' else
                                    [.005, .005, .045, .045, .045, .005])
        for _ in range(160):
            sim.grid = [[-1] * 100 for _ in range(100)]
            sim.step([.6] * 100)
            rows.append({'cycle': sim.cycle, 'threat': sim.interpretation['threat'],
                         'anger': sim.evaluated_emotion[1]['Anger'],
                         'calm': sim.evaluated_emotion[1]['Calm'],
                         'cortisol': sim.concentrations[3] / MAX_CONCENTRATION,
                         'endorphin': sim.concentrations[6] / MAX_CONCENTRATION})
        traces[state] = rows
        summary[state] = {'first': rows[0], 'last': rows[-1]}

    for name, rows in traces.items():
        with (output / f'{name}.csv').open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                       encoding='utf-8')
    # Standalone fixed-axis chart, no external packages or network resources.
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" '
             'viewBox="0 0 1000 650"><rect width="1000" height="650" fill="#101827"/>']
    panels = [('Constant secretion drive: delayed regulation',
               [('regulated', 'dopamine', '#66d9da'),
                ('unregulated', 'dopamine', '#ff9d76'),
                ('regulated', 'dopamine_regulator', '#c4a7e7')]),
              ('Identical stimulus: different initial hormone states',
               [('calm', 'anger', '#66d9da'), ('alarm', 'anger', '#ff9d76'),
                ('alarm', 'endorphin', '#c4a7e7')])]
    for panel, (title, series) in enumerate(panels):
        top, left, width, height = 55 + panel * 320, 60, 890, 190
        parts.append(f'<text x="60" y="{top-20}" fill="white" font-size="19">{title}</text>')
        for value in (0., .25, .5, .75, 1.):
            y = top + height * (1-value)
            parts.append(f'<path d="M {left} {y} h {width}" stroke="#344155"/>')
            parts.append(f'<text x="15" y="{y+5}" fill="#b6c4d9">{value:.2f}</text>')
        for j, (name, metric, color) in enumerate(series):
            rows = traces[name]
            points = ' '.join(f'{left+i*width/(len(rows)-1):.2f},'
                              f'{top+height*(1-row[metric]):.2f}'
                              for i, row in enumerate(rows))
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
            parts.append(f'<text x="{left+j*290}" y="{top+height+32}" '
                         f'fill="{color}" font-size="14">{name}: {metric}</text>')
        parts.append(f'<text x="60" y="{top+height+55}" fill="#b6c4d9">'
                     f'Cycles 1–{len(traces[series[0][0]])}; normalized levels 0–1</text>')
    parts.append('</svg>')
    (output / 'regulation.svg').write_text('\n'.join(parts), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
