import app
print('PLAYWRIGHT_IMPORT_CHECK')
try:
    from playwright.sync_api import sync_playwright
    print('PLAYWRIGHT_IMPORT_OK')
except Exception as exc:
    print('PLAYWRIGHT_IMPORT_FAIL', repr(exc))

try:
    html = app._fetch_ehub_via_playwright('https://efhub.com/players/106799999081429')
    print('FETCH_LEN', len(html))
    print('HAS_PLAYER_TEXT', any(k in html.lower() for k in ['morita', 'hidemasa', 'country', 'weak foot usage']))
    print(html[:400])
except Exception as exc:
    print('FETCH_ERROR', type(exc).__name__, exc)
