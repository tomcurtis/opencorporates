# -*- coding: utf-8 -*-

#for everything else
import json
from datetime import date
import datetime
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

#for pdfs
from StringIO import StringIO
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTRect, LTLine, LTTextBoxHorizontal
from pdfminer.converter import PDFPageAggregator

#CONSTANTS
sample_date = str(date.today()) # record when we looked
base_url = "http://www.nbs.sk" # links appear to be stored relative to this url
exclusionURLs = ["/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/commercial-and-savings-banks/annex-i-of-directive-2013-36-eu-of-the-european-parliament-and-of-the-council-of-26-june-2013-on-a"] #list of links not to process - regulatory information and not entity-related
date_fields = ["date_of_licence_issue", "commenced_operation", "date_of_registration", "expiry_date", "date_of_registration", "licence_date", "cessation_of_a_licence", "return_of_a_licence", "termination_of_the_licence", "date_of_entry_in_the_commercial_register", "licence_validity_date", "licence_issue_date", "licence_ceased", "date_of_closing_the_licence", "date_of_notification's_delivery_to_the_nbs", "date_of_notification's_delivery_to_the_member_state", "licence_issued_on", "licence_valid_from", "maturity", "date_of_issue", "date_of_final_decision", "date_of_notification", "date_of_service_of_notification", "effective_as_of", "finish_a_period_of_validity", "date_of_publish", "date_of_the_validity_of_the_decision", "date_of_the_issue_of_the_decision"]
replacement_labels = {
	'date_of_validiity': 'date_of_validity',
	u'dôvod_zániku_povolenia': 'reason_for_licence',
	u'sídlo': 'address',
	'adress': 'address',
	'deputy_of_mortgage_controllerr': 'deputy_of_mortgage_controller',
	'number_of_empolyees': 'number_of_employees',
	u'povolenie_číslo': 'licence_number',
	u'dátum_právoplatnosti_rozhodnutia': 'date_of_registration',
	u'dátum_udelenia_povolenia': 'licence_date',
	u'ičo': 'company_number',
	u'názov_spoločnosti': 'name',
	u'dátum_zániku_povolenia': 'expiry_date',
	"business_name": "name",
	"name_of_company": "name",
	"no._of_licence": "licence_number",
	"bider": "name",
	"name_of_the_issuer": "name",
	u'commercial_name_-_name_of_person,_that_have_approbation_nbs_on_the_application_laws_of_squeeze_out': "name"
}

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#parse an integer from text
def parse_int(input):
	value = input.replace(",", "") #remove commas
	value = ''.join(value.split()) #remove all whitespace
	return int(value)

#parse an floating number from text - deals with decimal points and commas. Remove parameter is an optional list of strings to remove
def parse_float(input, remove=[]):
	value = input
	value = ''.join(value.split()) #remove all whitespace
	for removeItem in remove: #remove the items we want to remove
		value = value.replace(removeItem, "")
	#is it commas for thousands and decimal points, or spaces for thousands and decimal commas?
	if ("." in value): 
		value = value.replace(",", "")
	else: #decimal commas, remove spaces and convert to point
		value = value.replace(",", ".")
	return float(value) * 1000

#parse date in text form	
def parse_date(input):
	#extract the first three words - which will be the date bit only and not extra commentary
	dateWords = input.split(" ") #split into words
	value = " ".join(dateWords[:3])
	value = value.replace("Jule", "July") #am aware of the typo
	#It would be nice if they used one format, but there are several we need to cope with...
	try:
		value = datetime.datetime.strptime(value, "%d %B %Y")
	except ValueError:
		try:
			value = datetime.datetime.strptime(value, "%d.%m.%Y")
		except ValueError:
			try:
				value = datetime.datetime.strptime(value, "%d. %B %Y")
			except ValueError:
				try:
					value = datetime.datetime.strptime(value, "%B %d, %Y")
				except ValueError:
					try:
						value = datetime.datetime.strptime(value, "%d %B, %Y")
					except ValueError:
						try:
							value = datetime.datetime.strptime(value, "%Y")
						except:
							#return a list of parsed dates
							if ("," in value):
								dateList = value.split(",")
								i = 0
								while i < len(dateList):
									dateList[i] = parse_date(dateList[i].strip())
									i += 1
								value = dateList
							else:
								return value #give up!

	if (isinstance(value, list)):
		return value
	else:
		return value.strftime("%Y-%m-%d")

def parse_text(input, label=False):
	output = ""
	if (len(input) > 0): #do stuff if there's any text to parse
		for item in input:
			contents = item
			count = 0
			#deal with links in the text...
			while (isinstance(contents, bs4.element.Tag)):
				if (len(contents.contents) == 0):
					contents = " "
					break #deal with empty tags
				contents = parse_text(contents)
				count += 1
				if (count == 100):
					break
			output += contents

	output = " ".join(output.split())
	output = output.strip()
	output = output.rstrip(":") #remove punctuation/whitespace
	if (label): #make it suitable for use as a field name
		output = output.replace(" ", "_")
		output = output.lower()
		
		#swap over any errors/translations types
		if (output in replacement_labels):
			output = replacement_labels[output]
	
	return output.strip()

#add the value to the object. If there's already a value, then make a list
def add_field(data, label, value):
	if (label in data):
		#check we're not duplicating anything
		if (data[label] != value):
			#if there's already a list, add this to it
			if (isinstance(data[label], list)):
				data[label].append(value)
			#otherwise, have to start a list with the existing value and the new one
			else:
				data[label] = [data[label], value]
	else:
		data[label] = value


#recursively go through elements and add all child strings -> hoping it works to alter list outside its own scope
def append_children(input_tag, existing_list):
	if (isinstance(input_tag, bs4.element.Tag)):
		for child in input_tag.children:
			#base case - there is some text to read
			if (child.string != None):
				child_text = parse_text(child.string)
				if (len(child_text) > 0):
					if (child_text.find("<xml>") == -1): #ignore anything that looks like html comments
						if (len(existing_list) > 0):
							if (child_text.replace(" ", "").replace("-", "").replace("_", "").isnumeric()): #if it's all numbers, and so is the last item, merge them 
								if (existing_list[len(existing_list) - 1].replace(" ", "").replace("-", "").replace("_", "").isnumeric()):
									existing_list[len(existing_list) - 1] += " " + child_text
								else:
									#split it by colon if there is one
									if (child_text.find(":") != -1):
										find_point = child_text.find(":")
										existing_list.append(child_text[:find_point])
										existing_list.append(child_text[find_point + 1:].strip())
									else: #otherwise add it as normal
										existing_list.append(child_text)
							else:
								existing_list.append(child_text)
						else:
							existing_list.append(child_text)
			else:
				append_children(child, existing_list)


#start from a given element and return a list of subsequent elements
def gather_element_list(startingElement, stopList=[]):
	elements = []
	element = startingElement
	while (not (isinstance(element, bs4.element.Tag) and (element.name == "h1"))):
		#we're only after actual tags
		if (isinstance(element, bs4.element.Tag)):
			#have an override buffer - if we run into one of the specified tags, we've gone too far and must stop
			if (element.name in stopList):
				return elements
			elements.append(element)
		if (element.next_sibling is None):
			break
		element = element.next_sibling
	return elements

#print out the object list in a nice, readable format
def print_objects(objects):
	for item in objects:
		if ('name' in item):
			print(unicode(item['name']) + ":")
		else:
			print("unnamed item:")
		for pair in item.items():
			if (unicode(pair[0]) != "name"):
				print(u"    " + unicode(pair[0]) + u": " + unicode(pair[1]))
		print("")

#print out a list of labels from the object list, and highlight any with weird labels
def print_labels(objects):
	label_list = []
	naughty_object_list = []
	for item in objects:
		for label in item:
			if (label not in label_list):
				label_list.append(label)
	for label in label_list:
		print(label)
	if (len(naughty_object_list) > 0):
		print("")
		print_objects(naughty_object_list)

#print all the unique values for a given field
def print_field(objects, field):
	field_values = []
	for item in objects:
		if (field in item):
			if (item[field] not in field_values):
				field_values.append(item[field])
	for value in field_values:
		print(value)

#START DOING STUFF
verbose = False #debugging output toggle

if (verbose):
	turbotlib.log("Starting run on " + sample_date + "...") # Optional debug logging

#Output containers
primary_data = [] #store results at the end

#PDFs
pdfURLs = [
	["http://www.nbs.sk/_img/Documents/_Dohlad/DirectoryProvidersBankingServices_Banks.pdf", "Banks providing banking services on the cross-border basis"],
	["http://www.nbs.sk/_img/Documents/_Dohlad/DirectoryProvidersBankingServices_CreditCoop.pdf", "Credit cooperatives providing banking services on the cross-border basis"],
	["http://www.nbs.sk/_img/Documents/_Dohlad/DirectoryProvidersBankingServices_ForeFinanInst.pdf", "Foreign financial institutions providing banking services on the cross-border basis"],
	["http://www.nbs.sk/_img/Documents/_Dohlad/PaymentInstitutions-cross.pdf", "Slovak payment institutions providing payment services on the cross-border basis abroad"],
	["http://www.nbs.sk/_img/Documents/_Dohlad/ForeignPaymentInstitutions.pdf", "Foreign payment institutions providing payment services on the cross-border basis"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/DirectoryProvidersBankingServices_ElectMoneyInst.pdf", "Electronic money institutions providing services on the cross-border basis"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/InsuranceCompanyInSR.pdf", "Insurance companies with registered office in the Slovak Republic"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/InsuranceCompaniesReinsurance.pdf", "Insurance companies having licence for reinsurance activities for non-life insurance"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/ZoznamPoistVSR_en.pdf", "Insurance companies with head office in the Slovak Republic providing activities in another member state"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/ZoznamPoistMimoSR_en.pdf", "Insurance companies from other EU member states providing activities in the Slovak Republic"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/InsuranceCompaniesOutSR.pdf", "Insurance companies from other EU member states providing services through a branch on the cross-border basis"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/ListPlacesForeignExch.pdf", "List of places granted a foreign exchange licence"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/EPCP_en.pdf", "List of prospectuses for securities approved since 2005-08-01"],
	# ["http://www.nbs.sk/_img/Documents/_Dohlad/IC_eng.pdf", "List of approved prospectuses for investment certificates"],
]


if (verbose):
	print("Scraping PDF files")
	if (verbose and len(pdfURLs) == 0):
		print("None found")
pdfCount = 1
pdf_parse_epsilon = 0.2 #margin for error in terms of lining up coordinates
for pdfURL in pdfURLs:
	if (verbose):
		print("Processing " + str(pdfCount) + "/" + str(len(pdfURLs)) + " - " + pdfURL[1])
	response = requests.get(pdfURL[0])
	memoryfile = StringIO(response.content)

	#default start up bits from http://www.unixuser.org/~euske/python/pdfminer/programming.html, http://denis.papathanasiou.org/2010/08/04/extracting-text-images-from-pdf-files/
	parser = PDFParser(memoryfile)
	document = PDFDocument(parser)
	rsrcmgr = PDFResourceManager()
	laparams = LAParams()
	device = PDFPageAggregator(rsrcmgr, laparams=laparams)
	interpreter = PDFPageInterpreter(rsrcmgr, device)

	#load the document and then process its pages
	for page in PDFPage.create_pages(document):
		interpreter.process_page(page)
		layout = device.get_result()
		
		#create a container for the info on the page -> structure is a list of rows, each of which contains cells. Row objects need to have top/bottom bounds, so we can tell if a given cell belongs on this row or a new one
		grid_horizontal = []
		grid_vertical = []
		rows = [] #container for rows
		text_lines = []
		rectangles = []
		used_text = []
		perfect_grid = True #switch used to determine how we fit the text boxes into the grid later
		for page_element in layout:
			#work out where the grid lines are -> find vertical and horizontal lines
			if (isinstance(page_element, LTLine)):
				if (page_element.y0 == page_element.y1):
					grid_horizontal.append(page_element.y0)
				if (page_element.x0 == page_element.x1):
					grid_vertical.append(page_element.x0)
			#also hoover up the text boxes for later
			if (isinstance(page_element, LTTextBox)):
				for line in page_element:
					text_lines.append(line)
			#and rectangles too
			if (isinstance(page_element, LTRect)):
				rectangles.append(page_element)
		#sort them into order and make pairs -> these are cell boundaries
		grid_horizontal.sort(reverse=True)
		grid_vertical.sort()
		rows = []
		#make a data structure to mirror our table -> a list of rows, each of which contains a list of cells
		for i in xrange(0, len(grid_horizontal) - 1):
			new_row = {
				'top': grid_horizontal[i],
				'bottom': grid_horizontal[i + 1],
				'cells': []
			}
			for j in xrange(0, len(grid_vertical) - 1):
				new_cell = {
					'left': grid_vertical[j],
					'right': grid_vertical[j + 1],
					'content': None #by default -> will override if we find owt
				}
				new_row['cells'].append(new_cell)
			rows.append(new_row)

		#deal with case where there were no horiz/vertical lines, just rectangles. Make a list of rows only - don't worry about cells.
		if (len(rows) == 0):
			perfect_grid = False

		#now go back over the text boxes and put them where they belong
		if (perfect_grid):
			#typical case -> we have a grid that works
			for text_box in text_lines:
				box_top = min(text_box.y0, text_box.y1)
				box_bottom = max(text_box.y0, text_box.y1)
				box_left = min(text_box.x0, text_box.x1)
				box_right = max(text_box.x0, text_box.x1)

				#find where to put it
				found_cell = False
				for row in rows: #check each row - is this between the bounds
					if ((box_top <= (row['top'] + pdf_parse_epsilon)) and (box_bottom >= (row['bottom'] - pdf_parse_epsilon))):
						if (text_box in used_text): #don't reuse a text box twice
							break
						for cell in row['cells']: #if it fits, check each cell in the row
							if (text_box in used_text): #don't reuse text
								break
							if ((box_left >= (cell['left']) - pdf_parse_epsilon) and (box_right <= (cell['right'] + pdf_parse_epsilon))):
								#does this text box fit within the walls of the cell?
								if (cell['content'] == None): #if the cell was blank
									cell['content'] = parse_text(text_box.get_text())
								else:
									cell['content'] = cell['content'] + " " + parse_text(text_box.get_text()) #if already used, append to the end
									cell['content'] = cell['content'].strip()
									cell['left'] = min(cell['left'], box_left)
									cell['right'] = max(cell['right'], box_right)
								found_cell = True
								used_text.append(text_box)
								break
						if (found_cell):
							break

		#we didn't have a grid, so we have to infer one from the text boxes themselves
		else:
			for text_box in text_lines:
				#get the mid point of the text box
				box_top = min(text_box.y0, text_box.y1)
				box_bottom = max(text_box.y0, text_box.y1)
				box_left = min(text_box.x0, text_box.x1)
				box_right = max(text_box.x0, text_box.x1)
				box_mid_height = ((text_box.y0 + text_box.y1) / 2)
				box_mid_width = ((text_box.x0 + text_box.x1) / 2)

				#make the rows using the boxes themselves and their mid points
				found_row = False
				for row in rows:
					if ((box_mid_height >= row['top']) and (box_mid_height <= row['bottom'])):
						found_row = True
						if (text_box in used_text): #don't reuse text
							break
						found_cell = False
						for cell in row['cells']:
							if (text_box in used_text):
								break
							if (abs(box_left - cell['left']) < 10):
								cell['content'] = cell['content'] + " " + text_box.get_text()
								cell['content'] = cell['content'].strip()
								found_cell = True
						if (not found_cell):
							new_cell = {
								'left': box_left,
								'right': box_right,
								'mid': box_mid_width,
								'content': text_box.get_text().strip()
							}
							row['cells'].append(new_cell)
						used_text.append(text_box)
				if (not found_row):
					new_row = {
						'header': False,
						'top': box_top,
						'bottom': box_bottom,
						'cells': []
					}
					new_cell = {
						'left': min(text_box.x0, text_box.x1),
						'right': max(text_box.x0, text_box.x1),
						'mid': box_mid_width,
						'content': text_box.get_text().strip()
					}
					new_row['cells'].append(new_cell)
					rows.append(new_row)

			#sort the rows and cells
			rows.sort(key=lambda x:x['top'], reverse=True)
			for row in rows:
				row['cells'].sort(key=lambda x:x['left'])

			#first row with multiple cells is the header
			for row in rows:
				if (len(row['cells']) > 1):
					row['header'] = True
					header_row = row
					break

			#deal with missing columns -> add them back in
			for row in rows:
				if (not row['header']):
					if (len(row['cells']) < len(header_row['cells'])):
						if (len(row['cells']) > 2):
							for header_cell in header_row['cells']:
								found_cell = False
								for row_cell in row['cells']:
									#check if we have a cell with its mid point between 
									# if ((row_cell['mid'] >= header_cell['left']) and (row_cell['mid'] <= header_cell['right'])):
									if (((row_cell['mid'] >= (header_cell['left'] - 5)) and (row_cell['mid'] <= (header_cell['right'] + 5))) or ((row_cell['right'] >= (header_cell['left'] - 5)) and (row_cell['left'] <= (header_cell['left'] + 5))) or ((row_cell['left'] <= (header_cell['right'] + 5)) and (row_cell['right'] >= (header_cell['right'] - 5)))):
										found_cell = True
										break
								#if can't find anything that matches, add a dummy cell and re-sort it into place
								if (not found_cell):
									new_cell = {
										'left': header_cell['mid'],
										'right': header_cell['mid'],
										'mid': header_cell['mid'],
										'content': None
									}
									row['cells'].append(new_cell)
									row['cells'].sort(key=lambda x:x['left'])

			#split v long columns
			for row in rows:
				if (not row['header']):
					if (len(row['cells']) < len(header_row['cells'])):
						if (len(row['cells']) > 2):
							for cell in row['cells']:
								cell_index = row['cells'].index(cell)
								#don't bother in the final column
								if (cell_index == (len(row['cells']) -1)):
									break
								#does this cell extend beyond its header
								if (cell['right'] > header_row['cells'][cell_index]['right']):
									#and also beyond the start of the next header
									if (cell['right'] > header_row['cells'][cell_index + 1]['right']):
										#assumption is that it splits at the word "article" or a number
										wide_text = cell['content']
										split_point = wide_text.find("Article")
										pre_text = wide_text[:split_point].strip()
										post_text = wide_text[split_point:].strip()

										#change the old cell text
										cell['contents'] = pre_text

										#add a new cell and re-sort the list
										header_cell = header_row['cells'][cell_index + 1]
										new_cell = {
											'left': header_cell['mid'],
											'right': header_cell['mid'],
											'content': post_text
										}
										row['cells'].append(new_cell)
										row['cells'].sort(key=lambda x:x['left'])

		#now that we've put text in the cells, let's process them into objects and add to our data store
		if (len(rows) == 0):
			continue
		headers = []
		if (perfect_grid):
			header_row = rows[0]
		for header_cell in header_row['cells']:
			if (header_cell['content'] == None):
				headers.append("Unknown!!!")
			else:
				headers.append(parse_text(header_cell['content'], True))
		#header row first, then real data
		for row_number in xrange(rows.index(header_row) + 1, len(rows)):
			row = rows[row_number]
			if (len(row['cells']) == len(headers)):
				new_fields = False
				data = {
					"source_url": pdfURL[0],
					"sample_date": sample_date,
					"scope": pdfURL[1]
				}
				cell_number = 0
				for cell in row['cells']:
					if (cell['content'] != None):
						header = headers[cell_number]
						if (header in date_fields):
							add_field(data, header, parse_date(cell['content'])) #we've already parsed the text by this point
							new_fields = True
						else:
							add_field(data, header, cell['content'])
							new_fields = True
					cell_number += 1

				if (new_fields):
					primary_data.append(data)
	pdfCount += 1

for item in primary_data:
	print(json.dumps(item))