import requests
from bs4 import BeautifulSoup

# Step 1: Define the target URL
def get_headlines(url="https://www.nytimes.com/section/todayspaper"):

    # Step 2: Send a GET request
    response = requests.get(url)

    # Step 3: Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Step 4: Find all elements with the desired class
    target_class = 'css-tskdi9 e1hr934v5'
    elements = soup.find_all(class_=target_class)

    # Step 5: Print the extracted elements
    headlines = ""
    for element in elements:
        print(element.text)
        headlines += f" {element.text} Next:"
        print('---')  # separator between elements
    return headlines
