# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests
import string

search_url = "http://ers.seccom.com.my/public/Default.aspx?menu=2&formname=frmSearchCom&field=name&companyname="
detail_url = "http://ers.seccom.com.my/public/CompanyGeneralInfo.aspx?LicenceID="

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

def parse_entity(entity_id):
	turbotlib.log("Parsing entity " + entity_id)
	try:
		entity_page = get_doc(detail_url + entity_id)

		#create object to store output
		output = {
			'sample_date': sample_date,
			'source_url': detail_url + entity_id,
			'source': "Securities Commission, Malaysia"
		}
		added_info = False

		#now get general info
		name = entity_page.find(id="StdPageLayout1_lblLicenceHolder").text.strip()
		if (len(name) > 0):
			output['name'] = name
			added_info = True

		licence_number = entity_page.find(id="StdPageLayout1_lblLicenceNo").text.strip()
		if (len(licence_number) > 0):
			output['licence_number'] = licence_number
			added_info = True

		regulated_activity_list = entity_page.find(id="StdPageLayout1_lblRegulatedAct")
		regulated_activity = []
		for item in regulated_activity_list.stripped_strings:
			activity = item.replace("&nbsp&nbsp-", "").strip()
			regulated_activity.append(activity)
		if (len(regulated_activity) > 0):
			output['regulated_activities'] = regulated_activity
			added_info = True

		start_date = entity_page.find(id="StdPageLayout1_lblLicenceSince").text.strip()
		if (len(start_date) > 0):
			output['start_date'] = start_date
			added_info = True

		anniversary_date = entity_page.find(id="StdPageLayout1_lblAnniversaryDate").text.strip()
		if (len(anniversary_date) > 0):
			output['anniversary_date'] = anniversary_date
			added_info = True

		status = entity_page.find(id="StdPageLayout1_lblStatus").text.strip()
		if (len(status) > 0):
			output['status'] = status
			added_info = True

		licensed_reps = entity_page.find(id="StdPageLayout1_lblNoOfLicenceRep").text.strip()
		if (len(licensed_reps) > 0):
			output['number_of_licensed_representatives'] = licensed_reps
			added_info = True

		#then go through specific tabs. first up, is licences
		licences = []
		licence_table = entity_page.find(id="tabs-1").table
		licence_rows = licence_table.find_all("tr")
		for tr in licence_rows[1:]:
			td_list = tr.find_all("td")
			licence = {} #make an object then see if we need to add it to the list
			#first off, licence number
			number = td_list[0].text.strip()
			if (len(number) > 0):
				licence['number'] = number
			#second cell: list of activities
			activities = []
			for item in td_list[1].stripped_strings:
				activity_string = item.replace("&nbsp&nbsp-", "").replace(u"•", "").strip()
				if (len(item) > 0):
					activities.append(activity_string)
			if (len(activities) > 0):
				licence['activities'] = activities
			#third cell: anniversary date
			anniversary_date = td_list[2].text.strip()
			if (len(anniversary_date) > 0):
				licence['anniversary_date'] = anniversary_date
			#fourth cell: status
			status = td_list[3].text.strip()
			if (len(status) > 0):
				licence['status'] = status

			#now add to the result
			if (len(licence) > 0):
				licences.append(licence)

		#now append to list
		if (len(licences) > 0):
			output['licences'] = licences
			added_info = True

		#second tab: Associate persons
		associates = []
		associates_table = entity_page.find(id="tabs-3").table
		associates_rows = associates_table.find_all("tr")
		for tr in associates_rows[1:]:
			associate = {}
			td_list = tr.find_all("td")
			#first cell = name, second cell = designation, third cell = sub-designation
			name = td_list[0].text.strip()
			if (len(name) > 0):
				associate['name'] = name
			designation = td_list[1].text.strip()
			if (len(designation) > 0):
				associate['designation'] = designation
			sub_designation = td_list[2].text.strip()
			if (len(sub_designation) > 0):
				associate['subdesignation'] = sub_designation
			if (len(associate) > 0):
				associates.append(associate)
		if (len(associates) > 0):
			output['associate_persons'] = associates
			added_info = True

		#third tab: business address
		address_table = entity_page.find(id="tabs-4").table
		address_rows = address_table.find_all("tr")
		for tr in address_rows[1:]:
			td_list = tr.find_all("td")
			label = td_list[0].text.strip().lower().replace(" ", "_")

			#address is different - need to extract it line-by-line
			if (label == "address"):
				address_lines = []
				for line in td_list[1].stripped_strings:
					address_lines.append(line)
				address = ", ".join(address_lines)
				if (len(address) > 0):
					output['address'] = address
					added_info = True

			else:
				value = td_list[1].text.strip()
				if ((len(value) > 0) and (len(label) > 0)):
					output[label] = value
					added_info = True

		#fourth tab: name changes
		name_change_table = entity_page.find(id="tabs-5").table
		name_change_rows = name_change_table.find_all("tr")
		name_changes = []
		for tr in name_change_rows[1:]:
			td_list = tr.find_all("td")
			if (len(td_list) == 2):
				effective_date = td_list[0].text.strip()
				previous_name = td_list[1].text.strip()
				if ((len(previous_name) > 0) and (len(effective_date) > 0)):
					name_change = {
						'previous_name': previous_name,
						'effective_date': effective_date
					}
					name_changes.append(name_change)
		if (len(name_changes) > 0):
			output['previous_names'] = name_changes
			added_info = True

		#fifth tab: licensed reps
		reps_table = entity_page.find(id="tabs-6").table
		reps_rows = reps_table.find_all("tr")
		reps = []
		for tr in reps_rows[1:]:
			rep = {}
			td_list = tr.find_all("td")
			name = td_list[0].text.strip()
			if (len(name) > 0):
				rep['name'] = name
			licence_number = td_list[1].text.strip()
			if (len(licence_number) > 0):
				rep['licence_number'] = licence_number
			#extra info in hyperlink for name
			if (td_list[0].a != None):
				href = td_list[0].a['href']
				licence_id_start = href.find("=")
				licence_id_end = href.find("&")
				licence_id = href[licence_id_start + 1: licence_id_end]
				if (len(licence_id) > 0):
					rep['licence_id'] = licence_id
					rep['detail_url'] = "http://ers.seccom.com.my/public/LicenceGeneralInfo.aspx?LicenceID=" + licence_id
			if (len(rep) > 0):
				reps.append(rep)
		if (len(reps) > 0):
			output['licensed_representatives'] = reps
			added_info = True

		#got to the end, save the results
		if (added_info):
			print(json.dumps(output))

	except:
		pass

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#Step 1: make a list of letter pairs to iterate through, and work out which entities are in the database
entities = [] #store results so we don't do them twice
letter_pairs = [] #store what we're iterating over
for first_letter in string.lowercase:
	for second_letter in string.lowercase:
		letter_pair = first_letter + second_letter
		turbotlib.log("Now searching for pair '" + letter_pair + "'")
		try:
			search_page = get_doc(search_url + letter_pair)
			rows = search_page.find_all(attrs={"class": "stdrow"}) + search_page.find_all(attrs={"class": "stdrow-1"})

			for row in rows:
				td_list = row.find_all("td")
				for td in td_list:
					if (td.a != None):
						href = td.a['href']
						entity_id = href[href.find("=") + 1:]
						if (entity_id not in entities):
							parse_entity(entity_id)
							entities.append(entity_id)
						break
		except:
			turbotlib.log("Unable to search for pair '" + letter_pair + "'")
	
turbotlib.log("Finished run")