from pymongo import MongoClient
from bs4 import BeautifulSoup
import json
import requests
import os

def db_connect():
    client = MongoClient(
    "mongodb+srv://<db_username>:<db_password>@hwcluster.atmq6.mongodb.net/?retryWrites=true&w=majority&appName=HWcluster")
    db = client["authors_quotes"]
    return db
#збирання інфи з сайту
def get_author_info(author_url):
    base_url = "http://quotes.toscrape.com"
    response = requests.get(base_url + author_url)
    soup = BeautifulSoup(response.text, 'lxml')
    author_name = soup.h3.text.strip()
    birth_date = soup.find(class_="author-born-date").text.strip()
    birth_place = soup.find(class_="author-born-location").text.strip()
    description = soup.find(class_="author-description").text.strip()

    return {
        "fullname": author_name,
        "birth_date": birth_date,
        "birth_place": birth_place,
        "description": description
    }
def get_quotes():
    url = "https://quotes.toscrape.com/"
    page_url = "/page/1/"
    quotes_data = []
    authors_data = []
    visited_authors = set()

    while page_url:
        response = requests.get(url + page_url)
        soup = BeautifulSoup(response.text, 'lxml')

        quotes = soup.find_all(class_="quote")
        for quote in quotes:
            quote_text = quote.find(class_="text").text.strip()
            quote_author = quote.find(class_="author").text.strip()
            quote_tags = [tag.text for tag in quote.find_all(class_="tag")]

            quotes_data.append({
                "quote": quote_text,
                "author": quote_author,
                "tags": quote_tags
            })

def to_json_format():
    with open('qoutes.json', 'w', encoding='utf-8') as q_file:
        json.dump(quotes_data, q_file, ensure_ascii=False, indent=4)
    
    with open('authors.json', 'w', encoding='utf-8') as a_file:
        json.dump(authors_data, a_file, ensure_ascii=False, indent=4)

#завантаження авторів
def load_authors(db):
    with open('authors.json', 'r', encoding='utf-8') as f:
        authors_data = json.load(f)
        authors_collection = db.authors
        for author_data in authors_data:
            if not authors_collection.find_one({"fullname": author_data['fullname']}):  # Перевіряємо, чи існує вже автор
                authors_collection.insert_one(author_data)

#завантаження цитат
def load_quotes(db):
    with open('qoutes.json', 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)
        authors_collection = db.authors
        quotes_collection = db.quotes
        for quote_data in quotes_data:
            author = authors_collection.find_one({"fullname": quote_data['author']})
            if author:
                quote_data['author_id'] = author['_id']
                quotes_collection.insert_one(quote_data)

#пошук за різними атрибутами
def search_by_tag(db, tag):
    quotes_collection = db.quotes
    quotes = quotes_collection.find({"tags": tag})
    for quote in quotes:
        author = db.authors.find_one({"_id": quote["author_id"]})
        print(f'{quote["quote"]} - {author["fullname"]}')

def search_by_tags(db, tags):
    quotes_collection = db.quotes
    tag_list = tags.split(',')
    quotes = quotes_collection.find({"tags": {"$in": tag_list}})
    for quote in quotes:
        author = db.authors.find_one({"_id": quote["author_id"]})
        print(f'{quote["quote"]} - {author["fullname"]}')

def search_by_author(db, name):
    authors_collection = db.authors
    quotes_collection = db.quotes
    author = authors_collection.find_one({"fullname": name})
    if author:
        quotes = quotes_collection.find({"author_id": author['_id']})
        for quote in quotes:
            print(f'{quote["quote"]} - {name}')
    else:
        print(f'Author "{name}" not found')

def main():
    quotes_data, authors_data = scrape_quotes()
    save_to_json(quotes_data, authors_data)
    print("Authors and qoutes saved at: qoutes.json and authors.json.")
    db = db_connect()
    print("DataBase conection success")
    
    load_authors(db)
    load_quotes(db)

#команди
    while True:
        command = input("Enter your command (e.g., name: Albert Einstein, tag:life, tags:life,miracles, exit to quit): ")
        if command.startswith("name:"):
            name = command.split("name:")[1].strip()
            search_by_author(db, name)
        elif command.startswith("tag:"):
            tag = command.split("tag:")[1].strip()
            search_by_tag(db, tag)
        elif command.startswith("tags:"):
            tag = command.split("tags:")[1].strip()
            search_by_tags(db, tags)
        elif command == "exit":
            print("Exiting in progress")
            break
        else:
            print("Invalid command")

if __name__ == "__main__":
    main()