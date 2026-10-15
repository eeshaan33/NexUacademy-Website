import urllib.request, re
req = urllib.request.Request('https://www.youtube.com/@NexUacademypvtltd', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
match = re.search(r'channelId"\s*:\s*"([^"]+)"', html)
if match:
    print("Found channelId:", match.group(1))
else:
    match2 = re.search(r'browseId"\s*:\s*"([^"]+)"', html)
    if match2:
        print("Found browseId:", match2.group(1))
    else:
        print("Not found")
