import runpy
import sys
import os

# Ensure analytics-service is on sys.path so `app` imports resolve
here = os.path.dirname(__file__)
analytics_dir = os.path.abspath(os.path.join(here, '..'))
if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

# Execute the eval_runner module and call run_benchmark for full run
g = runpy.run_path(os.path.join(analytics_dir, 'scripts', 'eval_runner.py'))
run_benchmark = g.get('run_benchmark')
if not run_benchmark:
    print('run_benchmark not found in eval_runner.py')
else:
    # full run: no limit, top_k=5, call agent answers
    run_benchmark(limit=None, top_k=5, run_agent_answers=True)
