# -*- coding: utf-8 -*-

import json
import datetime
import csv
import urllib
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

#Where do we look for info?
csv_url = "http://www.cenbank.org/Functions/export.asp?tablename=FinancialInstitutions"
branch_url = "http://www.cenbank.org/Supervision/fiBranches.asp?name="
directors_url = "http://www.cenbank.org/Supervision/fiDirectors.asp?FinancialInstname="

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#converts date to yyyy-mm-dd or returns original string
def parse_date(value):
	if ("/" in value):
		value_parts = value.split("/")
		if (len(value_parts) == 3):
			return (value_parts[2] + "-" + value_parts[0].zfill(2) + "-" + value_parts[1].zfill(2))
		else:
			return value
	else:
		return value

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#load the main details from the csv file
csv_doc = requests.get(csv_url).content.splitlines()
reader = csv.DictReader(csv_doc)
for row in reader:
	# create an object to store the details
	output = {
		'source_url': csv_url,
		'sample_date': sample_date,
		'source': "Central Bank of Nigeria"
	}

	#add new data to the object
	for field, value in row.items():
		if (field is not None):
			if (len(str(value)) > 0):
				if (value != "1/1/1900"):
					#convert key to standard jsonish type
					key_name = str(field).lower().replace(" ", "_")
					
					#translate name
					if value == "NGN":
						value = "Nigeria"

					output[key_name] = parse_date(value)

	#no point carrying on if it doesn't have a name
	if "name" not in output:
		continue

	#attempt to get director info
	url_name = urllib.quote_plus(output['name'])
	try:
		directors_page = get_doc(directors_url + url_name)
		if (directors_page.title.string is not None):
			if (directors_page.title.string[:3] != "500"): #check there's no errors
				table_list = directors_page.find_all("table", attrs={"class": "othertables"})
				for table in table_list: #find only the relevant tables
					if ("id" not in table.attrs):
						directors = [] #store results in a list of individuals
						director = {}

						current_bg = "" #check when it's a new person because we get a new colour
						tr_list = table.find_all("tr")
						for tr in tr_list:
							if 'bgcolor' in tr.attrs:
								new_bg = tr['bgcolor']
								if (current_bg == ""):
									current_bg = new_bg

								#if a new colour, add old person to list and start a new one
								if (current_bg != new_bg):
									if (len(director) > 0):
										directors.append(director)
									director = {}
								current_bg = new_bg

								#get the info and result
								td_list = tr.find_all("td")
								field = td_list[0].b.string.strip()
								value = parse_date(td_list[1].string.strip())
								director[field] = value

						directors.append(director) #add the last result to the list

				if (len(directors) > 0):
					output['directors'] = directors
	except:
		continue

	if (len(output) > 3):
		print(json.dumps(output))