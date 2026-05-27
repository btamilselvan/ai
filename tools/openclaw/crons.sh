openclaw cron add \
  --name "PERM Tracker" \
  --cron "15 11 * * *" \
  --tz "America/New_York" \
  --session isolated \
  --message "Track PERM processing estimate for submission date 2025-11-11 and employer name starting with S" \
  --announce \
  --channel telegram \