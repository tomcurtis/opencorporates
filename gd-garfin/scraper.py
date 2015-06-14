# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

source_urls = [
	{'url': "http://www.garfin.org/creditunion.html", 'category': "Credit union"},
	{'url': "http://www.garfin.org/geninscompanies.html", 'category': "General insurance"},
	{'url': "http://www.garfin.org/longinscompanies.html", 'category': "Long-term insurance"},
	{'url': "http://www.garfin.org/brokers.html", 'category': "Insurance broker"},
	{'url': "http://www.garfin.org/agents.html", 'category': "Insurance agent"},
	{'url': "http://www.garfin.org/salespersons.html", 'category': "Insurance salesperson"},
	{'url': "http://www.garfin.org/moneyservices.html", 'category': "Money services"}
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

#go through the pages one by one
for source in source_urls:
	#monitor progress
	count = source_urls.index(source) + 1
	turbotlib.log("Parsing category " + str(count) + "/" + str(len(source_urls)))

	#load page
	source_page = get_doc(source['url'])
	entities = source_page.find(attrs={"class": "deptContent"}).ol.find_all("li")
	
	#now go through the names one by one
	for entity in entities:
		#make object to store result temporarily
		output = {
			'sample_date': sample_date,
			'source_url': source['url'],
			'source': "Grenada Authority for the Regulation of Financial Institutions (GARFIN)",
			'category': source['category']
		}

		name = entity.text.strip()
		if (len(name) > 0):
			output['name'] = name

		#if there's no link, there's no further details to expand - let's cope with what we have
		if (entity.a == None):
			if ('name' in output):
				print(json.dumps(output))

		#otherwise, need to extract the details from the expandable part
		else:
			details_div = entity.find_next("div")
			

			#Insurance salespersons is a different kettle of fish to the others, so deal with it separately
			if (source['category'] == "Insurance salesperson"):
				#extract list of salespeople from either the table or ol in the div
				salespersons = []
				if (details_div.ol != None):
					li_list = details_div.ol.find_all("li")
					for li in li_list:
						person = li.text.strip()
						if (len(person) > 0):
							salespersons.append(person)
				else:
					td_list = details_div.table.find_all("td")
					for td in td_list:
						text = td.text.strip()
						stop = text.find(".")
						person = text[stop + 1:].strip()
						if (len(person) > 0):
							salespersons.append(person)
				
				#add result to output
				if (len(salespersons) > 0):
					output['salespersons'] = salespersons
					print(json.dumps(output))

			#in the other cases, details are labelled up in label: value entries. anything without a label is part of the address
			else:
				p_list = details_div.find_all("p")
				address_parts = []
				added_info = False
				for p in p_list:
					text = p.text.strip()
					#if there's a colon, get the separate label and value, add to output
					if (":" in text):
						colon = text.find(":")
						label = text[:colon].strip()
						value = text[colon + 1:].strip()

						if ((len(value) > 0) and (len(label) > 0)):
							output[label] = value
							added_info = True

					#sometimes it's name, job
					elif ((text[0] == "M") and (text[2] == ".") and ("," in text)):
						comma = text.find(",")
						label = text[comma + 1:].strip()
						value = text[:comma].strip()
						if ((len(label) > 0) and (len(value) > 0)):
							output[label] = value
							added_info = True

					else: #otherwise, add it to the list of address components
						address_parts.append(text)

				#combine the address
				address = ", ".join(address_parts).strip()
				if (len(address) > 0):
					output['address'] = address
					added_info = True

				#return result if we have added any new info
				if (added_info):
					print(json.dumps(output))

turbotlib.log("Finished run")