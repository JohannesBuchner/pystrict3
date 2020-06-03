def main(url):
    import requests, html
    print(html.parse("<body>"))
    html = requests.get(url)  ## bad: overwrites imported package name
    return html
    
