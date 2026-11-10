#!/bin/bash
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
echo "=== D4 traceback (first 45 lines) ==="
sed -n '1,45p' /home/user/dline/prog/logs/D4_budget_curve.log
echo
echo "=== minimal reproduction: all-NaN feature column ==="
python - <<'PY'
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
rng = np.random.default_rng(0)
n = 200
X = rng.normal(size=(n, 3))
X[:, 2] = np.nan                     # entire column undefined
y = X[:, 0] * 2 + rng.normal(size=n)
try:
    HistGradientBoostingRegressor(max_iter=50, random_state=0).fit(X, y)
    print("all-NaN column: OK")
except Exception as e:
    print("all-NaN column: FAILS ->", type(e).__name__, e)
X2 = X.copy(); X2[:5, 2] = 1.0       # at least one finite value
try:
    HistGradientBoostingRegressor(max_iter=50, random_state=0).fit(X2, y)
    print("partially-NaN column: OK")
except Exception as e:
    print("partially-NaN column: FAILS ->", type(e).__name__, e)
print("sklearn", __import__("sklearn").__version__)
PY
echo
echo "=== status of the other scripts ==="
ps -ef | grep "[p]ython -u D" | awk '{print $8, $9}'
for f in /home/user/dline/prog/logs/D1_deconfound.log /home/user/dline/prog/logs/D7_stability.log /home/user/dline/prog/logs/D8_audit.log; do
  echo "--- $(basename $f)"; tail -n 6 "$f"
done
