import json
from pathlib import Path
import pygame
from simulation import Simulation, SIZE, NAMES, EMOTION_COLORS
from hormone_profiles import CONTEXTS
from vision import VisualScene, SCENES

WIDTH, HEIGHT = 1640, 1040
BG, PANEL, TEXT, MUTED = '#0b101b', '#131d2d', '#e7edf7', '#8e9eb8'


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Emotion Lab · Signal and Hormone Simulation')
    font_path = pygame.font.match_font('segoeui,arial,dejavusans')
    fonts = {size: pygame.font.Font(font_path, size) for size in (14, 16, 18, 22, 30)}
    clock = pygame.time.Clock()
    sim = Simulation()
    scene = VisualScene()
    sim.visual_mode = True
    sim.inputs = scene.frame(0)
    sim.outputs = sim.inputs[:]
    running, alive, strength, kind, speed = False, True, 1.0, 'noise', 5
    selected = 0
    signal_view = False
    elapsed = 0
    status = 'Ready: 100 signal steps -> appraisal -> hormone shift'

    def text(value, x, y, size=16, color=TEXT, max_width=None):
        rendered = fonts[size].render(str(value), True, color)
        if max_width and rendered.get_width() > max_width:
            ratio = max_width / rendered.get_width()
            rendered = pygame.transform.smoothscale(rendered,
                (max_width, max(1, round(rendered.get_height() * ratio))))
        screen.blit(rendered, (x, y))

    def button(rect, label, active=False):
        pygame.draw.rect(screen, '#284c69' if active else '#213047', rect, border_radius=7)
        text(label, rect.x + 12, rect.y + 9, max_width=rect.width - 24)

    controls = [(pygame.Rect(34, 92, 125, 40), 'Run / Pause'),
                (pygame.Rect(169, 92, 115, 40), 'Step'),
                (pygame.Rect(294, 92, 100, 40), 'Reset'),
                (pygame.Rect(404, 92, 120, 40), 'Signal View'),
                (pygame.Rect(534, 92, 110, 40), 'Save JSON')]
    presets = [('moving', 'Moving'), ('wave', 'Wave'), ('flash', 'Flash'), ('noise', 'Noise')]
    preset_rects = [pygame.Rect(760 + i * 100, 92, 90, 40) for i in range(4)]
    slider = pygame.Rect(765, 159, 270, 10)
    grid_rect = pygame.Rect(90, 216, 600, 600)
    context_rect = pygame.Rect(1160, 92, 205, 40)
    scene_rects = [pygame.Rect(1405, 465 + i * 39, 215, 33) for i in range(len(SCENES))]

    def advance():
        sim.step(scene.frame(sim.cycle + 1, strength))

    def reset():
        model = Simulation()
        model.visual_mode = True
        model.inputs = scene.frame(0, strength)
        model.outputs = model.inputs[:]
        return model

    def draw_image(values, x, y, cell):
        for i, value in enumerate(values):
            light = round(value * 255)
            pygame.draw.rect(screen, (light, light, light),
                             (x + i % 10 * cell, y + i // 10 * cell, cell - 1, cell - 1))

    while alive:
        dt = clock.tick(30) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                alive = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running = not running
                elif event.key == pygame.K_RIGHT:
                    advance()
                elif event.key == pygame.K_r:
                    sim, running = reset(), False
                elif event.key == pygame.K_g:
                    sim.dynamics.enabled = not sim.dynamics.enabled
                elif event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                    sim.sensitivity = min(30., sim.sensitivity + 2.)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    sim.sensitivity = max(2., sim.sensitivity - 2.)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for rect, (value, _) in zip(scene_rects, SCENES):
                    if rect.collidepoint(pos):
                        scene.kind = value
                if context_rect.collidepoint(pos):
                    keys = [key for key, _ in CONTEXTS]
                    sim.context = keys[(keys.index(sim.context) + 1) % len(keys)]
                for i, (rect, _) in enumerate(controls):
                    if rect.collidepoint(pos):
                        if i == 0:
                            running = not running
                        elif i == 1:
                            advance()
                        elif i == 2:
                            sim, running = reset(), False
                        elif i == 3:
                            signal_view = not signal_view
                        else:
                            try:
                                path = Path('simulation_snapshot.json')
                                path.write_text(json.dumps({'cycle': sim.cycle, 'seed': sim.seed,
                                    'hormones': dict(zip(NAMES, sim.concentrations)),
                                    'context': sim.context, 'drives': sim.drives,
                                    'sensitivity': sim.sensitivity,
                                    'scene': scene.kind, 'visual_features': sim.visual_features,
                                    'emotion_memory': {'frustration': sim.frustration,
                                        'attention': sim.attention, 'low_stimulation': sim.low_stimulation},
                                    'emotion_history': sim.emotion_history,
                                    'emotion': sim.evaluated_emotion or sim.emotion(),
                                    'regulation': sim.dynamics.snapshot(),
                                    'regulation_history': sim.regulation_history,
                                    'interpretation': sim.interpretation,
                                    'habituation': sim.habituation_state(),
                                    'body_state': sim.body_state(),
                                    'grid': sim.grid, 'inputs': sim.inputs, 'outputs': sim.outputs,
                                    'history': sim.history}, ensure_ascii=False, indent=2), encoding='utf-8')
                                status = f'Saved: {path.resolve()}'
                            except OSError as error:
                                status = f'Save failed: {error}'
                for rect, (value, _) in zip(preset_rects, presets):
                    if rect.collidepoint(pos):
                        kind = value
                        scene.kind = value
                for i in range(20):
                    if pygame.Rect(760, 255 + i * 22, 590, 22).collidepoint(pos):
                        selected = i
            elif event.type == pygame.MOUSEWHEEL:
                speed = max(1, min(20, speed + event.y))
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if 149 <= my <= 179 and 755 <= mx <= 1045:
                strength = max(0, min(1, (mx - slider.x) / slider.width))
        elapsed += dt
        if running and elapsed >= 1 / speed:
            advance()
            elapsed = 0

        screen.fill(BG)
        text('EMOTION LAB', 34, 24, 30)
        text('Signals, Hormones and Feedback', 285, 34, 18, MUTED)
        text(f'CYCLE {sim.cycle:05d}   ·   {"RUNNING" if running else "PAUSED"}', 1090, 34, 18)
        for i, (rect, label) in enumerate(controls):
            button(rect, label, running if i == 0 else signal_view if i == 3 else False)
        for rect, (value, label) in zip(preset_rects, presets):
            button(rect, label, scene.kind == value)
        button(context_rect, 'Context: ' + dict(CONTEXTS)[sim.context] + ' ↻')
        text(f'Input strength  {strength:.3f}', 760, 137)
        pygame.draw.rect(screen, '#26354b', slider, border_radius=5)
        pygame.draw.circle(screen, '#66d9da', (int(slider.x + slider.width * strength), slider.centery), 8)
        text(f'{speed} cycles/s - scroll to adjust', 1060, 151, 16, MUTED)
        text('Input →', 32, 186, 16, '#66d9da')
        text('100 × 100   /   ' + ('Signal path' if signal_view else 'Hormone grid ←'), 160, 186, 18)
        text('→ Output', 670, 186, 16, '#66d9da')
        surface = pygame.Surface((SIZE, SIZE))
        for y in range(SIZE):
            for x in range(SIZE):
                h = sim.grid[y][x]
                if signal_view and sim.last_path:
                    v = sim.last_path[x][y]
                    color = (int(35 + v * 180), int(40 + v * 190), int(65 + v * 100))
                else:
                    color = sim.hormones[h].color if h >= 0 else (24, 34, 49)
                surface.set_at((x, y), color)
        screen.blit(pygame.transform.scale(surface, grid_rect.size), grid_rect)
        for y in range(SIZE):
            for x, value in ((62, sim.inputs[y]), (706, sim.outputs[y])):
                pygame.draw.rect(screen, (int(value * 95), int(value * 230), int(value * 240)),
                                 (x, 216 + y * 6, 16, 5))
        mx, my = pygame.mouse.get_pos()
        if grid_rect.collidepoint((mx, my)):
            x, y = (mx - 90) // 6, (my - 216) // 6
            h = sim.grid[y][x]
            text(f'Cell ({x:02d}, {y:02d}) · {NAMES[h] if h >= 0 else "Empty cell"}', 90, 825)
        else:
            text('Signal -> 100 columns -> appraisal -> concentration update -> shift left', 90, 825, 14, MUTED)

        pygame.draw.rect(screen, PANEL, (750, 210, 615, 506), border_radius=12)
        text('Hormone concentrations', 770, 224, 18, max_width=280)
        text('0.000 ~ 0.050  /  max 500 cells', 1060, 230, 14, MUTED)
        for i, h in enumerate(sim.hormones):
            y = 255 + i * 22
            if selected == i:
                pygame.draw.rect(screen, '#25344a', (760, y, 590, 22), border_radius=3)
            pygame.draw.circle(screen, h.color, (778, y + 10), 4)
            text(h.name, 791, y, 14, max_width=132)
            pygame.draw.rect(screen, '#2b374a', (933, y + 6, 265, 9), border_radius=3)
            pygame.draw.rect(screen, h.color, (933, y + 6, int(265 * sim.concentrations[i] / .05), 9), border_radius=3)
            text(f'{sim.concentrations[i]:.3f}', 1214, y, 14)
            text(f'{round(sim.concentrations[i]*10000):3d} cells', 1270, y, 14, MUTED)
        emotion, scores = sim.evaluated_emotion or sim.emotion()
        text(f'Current emotion · {emotion}', 770, 737, 22, '#66d9da')
        for j, (label, value) in enumerate(scores.items()):
            text(f'{label} {value:.2f}', 770 + (j % 4) * 145, 766 + (j // 4) * 20,
                 14, EMOTION_COLORS[label], max_width=135)
        text('Body: ' + ' / '.join(f'{k} {v:.2f}' for k, v in sim.body_state().items()),
             770, 808, 14, MUTED, max_width=580)
        h = sim.hormones[selected]
        text(f'{h.name} · Signal gain {h.factor:+.3f}', 770, 831, 16)
        text(f'{h.role} / inhibition {sim.dynamics.regulators[selected]:.2f}',
             770, 854, 14, h.color, max_width=590)
        text('Exploratory simulation with synthetic coefficients', 34, 870, 14, MUTED)
        text(status, 34, 894, 14, MUTED)
        text(f'Emotion history - last 240 cycles    Sensitivity {sim.sensitivity:.0f}  (+ / − keys)', 34, 921, 16)
        chart = pygame.Rect(34, 949, 1330, 66)
        pygame.draw.rect(screen, PANEL, chart, border_radius=6)
        colors = EMOTION_COLORS
        for j, (label, color) in enumerate(colors.items()):
            text(label, 730 + j * 90, 921, 14, color)
            points = [(chart.x + round(i * chart.width / 239),
                       chart.bottom - 2 - round(scores[label] * (chart.height - 4)))
                      for i, scores in enumerate(sim.emotion_history)]
            if len(points) > 1:
                pygame.draw.lines(screen, color, False, points, 2)
        text(f'G: Regulation {"ON" if sim.dynamics.enabled else "OFF"} · '
             f'Familiarity {sim.familiarity:.2f} · Novelty {sim.novelty:.2f} · '
             f'Boredom {sim.boredom:.2f} · Order {sim.order:.2f} · Disorder {sim.disorder:.2f}', 34, 1019, 14, MUTED)
        pygame.draw.rect(screen, PANEL, (1395, 210, 235, 815), border_radius=12)
        text('Visual input · 10 × 10', 1405, 225, 18)
        draw_image(sim.inputs, 1415, 260, 20)
        for rect, (value, label) in zip(scene_rects, SCENES):
            button(rect, label, scene.kind == value)
        text('Input: last completed frame', 1405, 781, 14, MUTED, max_width=215)
        text('Processed output · 10 × 10', 1405, 809, 16, max_width=215)
        draw_image(sim.outputs, 1440, 838, 15)
        v = sim.visual_features
        text(f'Motion {v.get("motion", 0):.2f}  Looming {v.get("looming", 0):.2f}',
             1405, 995, 14, max_width=215)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
