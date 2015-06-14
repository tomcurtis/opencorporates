# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

source_urls = [
	"http://www.bsib.org.np/index.php?option=institution&id=78",
	"http://www.bsib.org.np/index.php?option=institution&id=79",
	"http://www.bsib.org.np/index.php?option=institution&id=144",
	"http://www.bsib.org.np/index.php?option=cms&id=38"
]

#need to spoof user agent string - otherwise you get a 403 Forbidden error, and they block you from accessing the site at all
url_headers = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0'
}

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url, headers=url_headers)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#load the page
for url in source_urls:
	try:
		page = get_doc(url)
		header_span = None
		category = ""
		
		#first get the header
		span_list = page.find_all("span") + page.find_all("div")
		for span in span_list:
			if ('class' in span.attrs):
				if ("greenheader_eng" in span['class']):
					header_span = span
					category = span.string.strip()

		#elements we're looking for will be different depending on if we have a table or div page
		if (header_span.name == "div"):
			name_element = "span"
		else:
			name_element = "td"

		#find the names - first off, in tables
		if (name_element == "td"):
			tr_list = header_span.find_all_next("tr")
			for tr in tr_list:
				td_list = tr.find_all("td")
				output = { #object to store results
					'source_url': url,
					'sample_date': sample_date,
					'category': category,
					'regulator': "Insurance Regulatory Authority of Nepal"
				}

				try:
					output['name'] = td_list[0].a.string.strip()
					output['name_nepali'] = unicode(td_list[2].a.string.strip())
					output['url'] = td_list[0].a['href']

					print(json.dumps(output))

				except:
					continue

		#now when it's a page with two divs
		else:
			left_body = page.find(id="leftbodypart")
			right_body = page.find(id="rightnav")
			left_rows = left_body.find_all("span")[1:]
			right_rows = right_body.find_all("span")[1:] #ignore the header rows

			for row in left_rows:
				try:
					row_index = left_rows.index(row)
					right_row = right_rows[row_index]

					output = { #object to store results
						'source_url': url,
						'sample_date': sample_date,
						'category': category,
						'regulator': "Insurance Regulatory Authority of Nepal",
						'name': row.string.strip(),
						'name_nepali': right_row.string.strip()
					}

					if (len(output['name']) > 0):
						print(json.dumps(output))
				
				except:
					continue

	except:
		continue