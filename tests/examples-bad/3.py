import requests, html
print(html.parse("<body>"))
html = requests.get("https://example.com/")  ## bad: overwrites imported package name
print(html)
