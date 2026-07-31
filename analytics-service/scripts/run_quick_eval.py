import runpy
import sys
import os

# Ensure analytics-service is on sys.path so `app` imports resolve
here = os.path.dirname(__file__)
analytics_dir = os.path.abspath(os.path.join(here, '..'))
if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

g = runpy.run_path(os.path.join(analytics_dir, 'scripts', 'eval_runner.py'))
run_benchmark = g.get('run_benchmark')
if not run_benchmark:
    print('run_benchmark not found in eval_runner.py')
else:
    # quick run: 10 entries, top_k=5, CALL agent answers
    run_benchmark(limit=10, top_k=5, run_agent_answers=True)
