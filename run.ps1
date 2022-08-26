# Bot runtime entry point
try { python bot/main.py }
# Cleanup
finally { Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse }