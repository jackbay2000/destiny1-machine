@echo off
start "" /min powershell -NoProfile -Command "while ($true) { $p = Get-Process -Name 'chiaki*' -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { $_.PriorityClass = 'High' }; break }; Start-Sleep -Seconds 2 }"
python destiny1-mk.py
pause
