# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

source_urls = [
	{'category': 'Registered capital market operator', 'url': 'http://www.sec.gov.ng/files/CMO%20DATA/CMO_Registered.htm'},
	{'category': 'Capital market operator with incomplete registration', 'url': 'http://www.sec.gov.ng/files/CMO%20DATA/CMO_Incomplete%20registration.htm'},
	{'category': 'Capital market operator with expired fidelity bond', 'url': 'http://www.sec.gov.ng/files/CMO%20DATA/CMO_Expired%20fidelity%20bond.htm'},
	{'category': 'Approved fund manager', 'url': 'http://www.sec.gov.ng/files/CMO%20DATA/FUND%20MANAGERS.htm'},
	{'category': 'Illegal operator', 'url': 'http://www.sec.gov.ng/files/CMO%20DATA/ILLEGAL%20OPERATORS.htm'},
]

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#load the page
for source in source_urls:
	try:
		table = get_doc(source['url']).table
		tr_list = table.find_all('tr')

		#extract the headers into a list from the first row
		headers = ['id', 'name'] #the first two are always the same
		try: #have to deal with some pages having "last updated" as top row instead of headers
			header_row = 0
			header_td_list = tr_list[header_row].find_all('td') + tr_list[header_row].find_all('th')
			for header_td in header_td_list[2:]: #only look at the remaining ones
				header = header_td.string.strip().lower().replace(" ", "_").replace("__", "_").replace("\n", "")
				headers.append(header)
		except:
			header_row = 1
			header_td_list = tr_list[header_row].find_all('td') + tr_list[header_row].find_all('th')
			for header_td in header_td_list[2:]: #only look at the remaining ones
				header = header_td.string.strip().lower().replace(" ", "_").replace("__", "_").replace("\n", "")
				headers.append(header)

		#is this a page that has subheading rows to split up tables? Normally no, but approved fund managers do
		fund_type_page = False
		fund_type = ""

		for tr in tr_list[(header_row + 1):]:
			try:
				td_list = tr.find_all('td')

				#check for fund_types
				if ((len(td_list[0].string.strip()) == 0) and (len(td_list[2].string.strip()))):
					fund_type_page = True
					fund_type = td_list[2].string.strip().replace("\n", "").replace("  ", " ").lower().capitalize()

				#skip header lines
				if ((td_list[0].string.strip() == "S/N") and (td_list[1].string.strip() == "FUND MANAGER")):
					continue

				output = { #object to store results
					'name': td_list[1].string.strip().replace("\n", ""),
					'sample_date': sample_date,
					'category': source['category'],
					'source_url': source['url']
				}

				if (fund_type_page):
					output['fund_type'] = fund_type

				for col in xrange(2, len(headers)):
					try:
						value = td_list[col].string.strip().replace("\n", "")

						#deal with dates - reformat into dd-mm-yyyy
						if (value.count("/") == 2):
							value_parts = value.split("/")
							if (value_parts[0].isnumeric() and value_parts[1].isnumeric() and value_parts[2].isnumeric()):
								value = value_parts[1].zfill(2) + "-" + value_parts[0].zfill(2) + "-" + value_parts[2]

						if (len(value) > 0):
							output[headers[col]] = value
					except:
						continue

				#store result if required
				if (len(output['name']) > 0):
					print(json.dumps(output))
			
			except:
				continue

	except:
		continue

turbotlib.log("Finished run on " + sample_date)