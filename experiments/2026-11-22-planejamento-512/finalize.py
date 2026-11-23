"""Consolida os relatórios preservados sem alterar a análise editorial."""
import json
from pathlib import Path

from minicode.planning_data import plan_score

root = Path(__file__).resolve().parent
summary = {}
for mode in ('padrao', 'base', 'lora'):
    report = json.loads((root / mode / 'report.json').read_text())
    scores = []
    for case in report['cases']:
        trace = root / mode / case['case'] / 'project' / '.minicode' / 'runs'
        plan = sorted(trace.glob('*/plan.md'))[-1]
        scores.append({'case': case['case'], **plan_score(plan.read_text())})
    summary[mode] = {
        **{k: v for k, v in report.items() if k != 'cases'},
        'plan_scores': scores,
    }
(root / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(root / 'CONCLUIDO.txt').write_text('Avaliações concluídas; análise em docs/analise-final.md.\n')
print('Relatórios consolidados.', flush=True)
