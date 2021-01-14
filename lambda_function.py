from googlesearch import search
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from bs4.element import Comment
# from textblob import TextBlob
import boto3
import json
import sys
import asyncio
import concurrent.futures
import time

def get_search_res(query, numRes):
	list = []
	for j in search(query, tld="com", lang='en', num=numRes, stop=numRes, pause=2):
		list.append(j)
	return list

# attempts to get HTML/XML, returns text content, none otherwise
def get_url(url):
	try:
		with closing(get(url, stream=True)) as resp:
			if is_good_response(resp):
				return resp.content
			else:
				return None

	except RequestException as e:
		log_error('Error during requests to {0} : {1}'.format(url, str(e)))
		return None

# returns True if response seems to be HTML, False otherwise
def is_good_response(resp):
	content_type = resp.headers.get('Content-Type')
	if not content_type:
		return False
	content_type = content_type.lower()
	return (resp.status_code == 200 
			and content_type is not None 
			and content_type.find('html') > -1)

# prints errors
def log_error(e):
	print(e)

#returns True if tag is visible, False otherwise
def tag_visible(element):
	if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
		return False
	if isinstance(element, Comment):
		return False
	return True

def check_meta_review(soup):
	head = soup.find("head")
	if not head:
		return False
	metas = head.find_all("meta")
	for meta in metas:
		if 'content' in meta.attrs:
			content = meta['content']
			if (content.find('review') != -1 or content.find('Review') != -1) and not (content.find('preview') != -1 or content.find('Preview') != -1):
				return True
	return False

def get_pars(soup):
	pars = soup.find("body").find_all("p")

	allPars = []

	#for all p tags in the body, only retrieve those that meet the following criteria:
	for par in pars:
		if(len(par.attrs) == 0 and len(par.text) > 56 and (par.find("span") or par.find("a") or par.find("strong") or par.find("b") or par.find("i") or par.find("em") or (not par.findChild()))):
			allPars.append(par.text)
	return allPars

def lambda_handler(event, context):
	#parse out query string params
	query = event['query']

	print(event)

	print("query: ", query)

	#construct the body of the response object
	transactionResponse = {}
	transactionResponse['query'] = query
	transactionResponse['sentiment'] = prodSent(query)
	transactionResponse['message'] = 'query processed successfully'

	#construct http response object
	responseObject = {}
	responseObject['statusCode'] = 200
	responseObject['headers'] = {}
	responseObject['headers']['Access-Control-Allow-Origin'] = "*"
	responseObject['headers']['Access-Control-Allow-Credentials'] = True
	responseObject['headers']['Content-Type'] = 'application/json'
	responseObject['body'] = json.dumps(transactionResponse)

	#return the response object
	return responseObject

# main:
top_result = get_search_res('Champion Charters venice la tripadvisor reviews', 1)[0]
html = get_url(top_result)
soup = BeautifulSoup(html, features="html.parser")
spans = soup.find("body").find_all("q")
for span in spans:
	spanlist = span.find_all("span")
	review = ""
	for sub in spanlist:
		review += sub.text
	print('------------span------------')
	print(review)

