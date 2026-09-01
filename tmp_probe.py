import sys
print('PYTHON=', sys.executable)
try:
    import playwright
    print('PLAYWRIGHT_OK=', playwright.__version__)
except Exception as exc:
    print('PLAYWRIGHT_IMPORT_ERROR=', repr(exc))

try:
    import app
    print('APP_IMPORTED_OK')
    info = app.extract_full_player_info('https://efhub.com/players/106799999082154')
    print('PLAYER=', info.get('Player'))
    print('RATING=', info.get('Rating'))
    print('NATION=', info.get('Nation'))
    print('CLUB=', info.get('Club'))
    print('DEBUG=', info.get('_debug_error'))
except Exception as exc:
    print('APP_ERROR=', type(exc).__name__, exc)
