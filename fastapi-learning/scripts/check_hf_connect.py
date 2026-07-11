import urllib.request, sys
url = 'https://huggingface.co'
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        print('OK', r.status)
except Exception as e:
    print('ERR', repr(e))
    sys.exit(2)
