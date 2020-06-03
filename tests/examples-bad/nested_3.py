def main(url):
    import requests, html
    print(html.escape("<body>"))
    html = requests.get(url)  ## bad: overwrites imported package name
    return html
    
