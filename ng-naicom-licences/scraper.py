# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

source_urls = [
	{'category': 'Insurers and reinsurer', 'url': 'http://naicom.gov.ng/companies'},
	{'category': 'Insurance agent', 'url': 'http://naicom.gov.ng/companies?q=agents'},
	{'category': 'Insurance broker', 'url': 'http://naicom.gov.ng/companies?q=brokers'},
	{'category': 'Loss adjuster', 'url': 'http://naicom.gov.ng/companies?q=adjusters'},
]

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

for source in source_urls:
	try:
		page = get_doc(source['url'])
		table = page.find("table") #only appears to be one per page. And the source code appears to include all rows, even if not all shown on screen
		tr_list = table.find_all("tr")

		#identify the headings
		headers = []
		th_list = tr_list[0].find_all("th")
		for th in th_list:
			heading = th.string.strip().lower().replace(" ", "_")
			if ((heading == "company_name") or (heading == "agent_name")):
				heading = "name"
			headers.append(heading)

		#extract the data
		for tr in tr_list[1:]:
			#object to store the result
			output = {
				'source_url': source['url'],
				'sample_date': sample_date,
				'category': source['category']
			}

			td_list = tr.find_all('td')
			for td in td_list:
				try:
					col = td_list.index(td)
					label = headers[col]
					value = td.string.strip()

					if (len(value) > 0):
						output[label] = value

				except:
					continue

			if (len(output) > 3):
				print(json.dumps(output))

	except:
		continue
