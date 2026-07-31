import runpy
import sys
import os

# Ensure analytics-service is on sys.path
here = os.path.dirname(__file__)
analytics_dir = os.path.abspath(os.path.join(here, '..'))
if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

g = runpy.run_path(os.path.join(analytics_dir, 'scripts', 'eval_runner.py'))
run_benchmark = g.get('run_benchmark')
if not run_benchmark:
    print('run_benchmark not found')
else:
    run_benchmark(limit=5, top_k=5, run_agent_answers=False)
