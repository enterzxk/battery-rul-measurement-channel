#!/bin/bash
echo "HOST=$(hostname) NPROC=$(nproc)"
echo "PY=$(python3 -V 2>&1)"
python3 - <<'PY'
mods = ["numpy", "scipy", "sklearn", "pandas", "pyarrow"]
for m in mods:
    try:
        mod = __import__(m)
        print("  ok  %-10s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as e:
        print("  MISS %-10s %s" % (m, e))
PY
echo "--- candidate work dirs ---"
ls -d "$HOME"/rul* "$HOME"/rulb "$HOME"/battery* 2>/dev/null
echo "--- look for existing battery data ---"
for p in "$HOME" /data /mnt /srv /opt; do
  [ -d "$p" ] && find "$p" -maxdepth 5 \( -name 'RPT_json.zip' -o -name 'data_cc_1.pkl' \) 2>/dev/null | head -5
done
echo "--- disk ---"
df -h "$HOME" | tail -2
