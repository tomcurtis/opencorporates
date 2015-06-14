# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests
import xlrd
import subprocess
import os

#SOURCES
base_url = "http://www.afn.kz"

sources = [
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=480", 'category': "Banking operation", 'type': "Licence register", 'file': 'excel'},
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=575", 'category': "Insurance activity", 'type': "Licence register", 'file': 'excel'},
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=801", 'category': "Banking operation", 'type': "Licence register", 'file': 'excel'},
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=1380", 'category': "Microfinancial organisation", 'type': "Licence register", 'file': 'excel'},
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=639", 'category': "Securities market activity", 'file': 'word'},
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=747", 'category': "Attraction of pension contributions and making pension payments", 'file': 'word'},
	{'url': "http://www.afn.kz/index.cfm?switch=eng&docid=879", 'category': "Credit bureau activity", 'file': 'word'}
]

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#from k-nut's sierra leone bot (https://github.com/k-nut/sierra-leone-banks/blob/master/scraper.py)
def download(link, savepath):
    #""" This downloads the file and stores it to the local disk"""
    with open(savepath, "wb") as handle:
        response = requests.get(link)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)


#load an excel file - return a list of information
def parse_excel(excel_content, formatting, source_url, category):
	#load in the document
	document = xlrd.open_workbook(file_contents=excel_content, formatting_info=formatting)
	excel_records = []

	for sheet_num in xrange(0, document.nsheets):
		sheet = document.sheet_by_index(sheet_num)
		turbotlib.log("Processing sheet " + str(sheet_num + 1) + "/" + str(document.nsheets))

		# skip sheet if top-left is blank
		check_cells = []
		for row in xrange(0, min(10, sheet.nrows)):
			for col in xrange(0, min(10, sheet.ncols)):
				check_cell = unicode(sheet.cell_value(row, col)).strip()
				if (len(check_cell) > 0):
					check_cells.append(check_cell)
		if (len(check_cells) == 0):
			continue

		#find the start of the headers - where there is something in column A and column B
		header_start_row = -1
		for row in xrange(0,sheet.nrows):
			if (len(sheet.cell_value(row, 0)) > 0):
				if (len(sheet.cell_value(row, 1)) > 0):
					header_start_row = row
					break

		#try to find out the end of the headers using formatting information. however, this won't work for xlsx or xlsb files due to xlrd's limitations
		header_end_row = -1
		if (formatting):
			#find the end of the headers - first attempt is where the background colour changes
			header_xf_index = sheet.cell_xf_index(header_start_row, 0)
			header_xf = document.xf_list[header_xf_index]
			header_background = header_xf.background.background_colour_index
			#go through all subsequent rows until we find one with a different background colour
			for row in xrange(header_start_row, sheet.nrows):
				row_xf_index = sheet.cell_xf_index(row, 0)
				row_xf = document.xf_list[row_xf_index]
				row_background = row_xf.background.background_colour_index
				if (row_background != header_background):
					header_end_row = row - 1
					break
			
			#second attempt - if that didn't work, find out where it changed from bold to unbold
			if (header_end_row == -1):
				for row in xrange(header_start_row, sheet.nrows):
					row_xf_index = sheet.cell_xf_index(row, 0)
					row_xf = document.xf_list[row_xf_index]
					row_font_index = row_xf.font_index
					row_font = document.font_list[row_font_index]
					if (row_font.weight == 400): #standard weight is 400 for normal, 700 for bold
						header_end_row = row - 1
						break
		
		#otherwise have to try to infer it from other factors- first use of number '1' in column A
		else:
			for row in xrange(header_start_row, sheet.nrows):
				if (sheet.cell_value(row, 0) == 1):
					header_end_row = row - 1

		#now work out how many columns we have in the final headers row - look for column with no values in the header rows
		header_end_col = -1
		for col in xrange(0, sheet.ncols):
			#check if all header rows in this column are blank (which they will be for merged cells, except for the first column)
			cell_contents = []
			for row in xrange(header_start_row, header_end_row + 1):
				cell_content = unicode(sheet.cell_value(row, col)).strip()
				#if we have formatting information and a blank cell, check for merged cells
				if (formatting and (len(cell_content) == 0)):
					for merge_range in sheet.merged_cells:
						r_low, r_high, c_low, c_high = merge_range
						#check if our cell is in the middle of a merged row
						if ((row >= r_low) and (row <= r_high)):
							if ((col >= c_low) and (col <= c_high)):
								cell_content = unicode(sheet.cell_value(r_low, c_low)).strip()
				#add our result to the list
				cell_contents.append(cell_content)

			#check if all are empty/blank
			empty_count = 0
			for cell in cell_contents:
				if (len(cell) == 0):
					empty_count += 1
			if (empty_count == len(cell_contents)):
				header_end_col = col - 1
				break	

		#fallback - if didn't find an end, then use ncols
		if (header_end_col == -1):
			header_end_col = sheet.ncols - 1

		#now we know where the headers are - time to find the end of the data
		data_start_row = header_end_row + 1 #starts one after the headers, unsurprisingly
		data_end_row = -1
		for row in xrange(data_start_row, sheet.nrows):
			#go through all columns - first row where they're all blank means you've reached the end
			row_contents = []
			for col in xrange(0, header_end_col):
				cell_content = unicode(sheet.cell_value(row, col)).strip()
				row_contents.append(cell_content)
			empty_count = 0
			for cell in row_contents:
				if (len(cell) == 0):
					empty_count += 1
			if (empty_count == len(row_contents)):
				data_end_row = row - 1
				break

		if (data_end_row == -1):
			data_end_row = sheet.nrows - 1

		#extract the headers - taking account of merged cells
		headers = []
		for col in xrange(0, header_end_col):
			#combine all headers in a column into one string
			header_cells = []
			for row in xrange(header_start_row, header_end_row + 1):
				check_col = col
				header_string = ""
				while ((len(header_string) == 0) and (check_col > 0)):
					header_string = unicode(sheet.cell_value(row, check_col)).strip()
					check_col -= 1 #go back a column to get the value of a merged cell
				if (len(header_string) > 0):
					header_cells.append(header_string)

			#cope with merged cells at the end - just take the main value
			if ((len(header_cells) > 0) and (header_cells[0] == header_cells[-1])):
				header = header_cells[0]
			else:
				if (category == "Banking operation"):
					end = -1
				else:
					end = len(header_cells)
				header = " - ".join(header_cells[:end])
			headers.append(header)

		#now get the data
		for row in xrange(data_start_row, data_end_row + 1):
			#one record per row - with metadata
			record = {
				'sample_date': sample_date,
				'source_url': source_url,
				'source_sheet': sheet.name,
				'category': category
			}
			#load in value for each column
			for col in xrange(0, header_end_col):
				label = headers[col].replace("\n", " ").replace("\t", "").replace("  ", "")
				if (len(label) == 0):
					label = "id"
				if (label == "Name"):
					label = "name"
				value = unicode(sheet.cell_value(row, col)).strip().replace("\n", " ").replace("\t", "").replace("  ", "")
				if (len(value) > 0):
					record[label] = value
			excel_records.append(record)

	#spit it out at the end
	return excel_records

#iterative function for coping with merged cells - at least for this case where they are at the end of rows only!
def merged_header(start_cell, start_row, tr_list, current_headers):
	colspan = start_cell.attrs['colspan']
	current_row = start_row + 1
	next_row = tr_list[current_row].find_all("td") #get the next bunch of cells
	
	headers = []

	#go through cells on the row below
	for index in xrange(0, min(colspan, len(next_row))):
		next_cell = next_row[index]
		current_header_text = next_row[index].text.strip().replace("\n", " ").replace("\t", "")
		new_headers = current_headers + [current_header_text]

		if ('colspan' not in next_cell.attrs):
			#reached the end so return a result
			header = " - ".join(new_headers)
			headers.append(header)

		else:
			#iterate through remaining rows and keep adding new results
			new_header_list = merged_header(next_cell, current_row, tr_list, new_headers)
			for x in new_header_list:
				if x not in headers:
					headers.append(x)

	return headers


#similar function to process a word document
def parse_word(word_content, source_url, category):
 	word_records = [] #container for results
 	#process each table into records
 	for table in word_content.find_all("table"):
 		tr_list = table.find_all("tr")
 		#extract the headers first - need to cope with merged cells!
 		headers = []
 		data_start = 1 #start with this assumption
 		for td in tr_list[0].find_all("td"):
 			#check for maximum row_span
 			if ('rowspan' in td.attrs):
 				if (td.attrs['rowspan'] > data_start):
 					data_start = td.attrs['rowspan']

 		#now go back and check for 
 		for td in tr_list[0].find_all("td"):
 			#simple case - just one row of headers
 			if (data_start == 1):
 				header_text = td.text.strip().replace("\n", " ").replace("\t", "")
 				headers.append(header_text)

 			#also need to cope with merged cells
 			else:
 				#ordinary ones are easy
 				if ('colspan' not in td.attrs):
 					header_text = td.text.strip().replace("\n", " ").replace("\t", "")
	 				headers.append(header_text)

	 			#but let's deal with multiple columns
		 		else:
		 			current_header_text = td.text.strip().replace("\n", " ").replace("\t", "")
		 			header_list = merged_header(td, 0, tr_list, [current_header_text])
		 			headers += header_list
		 			data_start = int(data_start)

 		#now process the rows
 		for tr in tr_list[data_start:]:
 			td_list = tr.find_all("td")
 			record = {
 				'source_url': source_url,
 				'sample_date': sample_date,
 				'category': category
 			}
 			for td in td_list:
 				#record anything with a non-blank value
 				td_text = td.text.strip().replace("\n", " ").replace("\t", "")
 				if (len(td_text) > 0):
 					td_index = td_list.index(td)
 					header = headers[td_index]
 					record[header] = td_text.strip().replace("\n", " ").replace("\t", "")

 			#check we found something
 			if (len(record) > 3):
 				word_records.append(record)
 	
 	return word_records

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#first load the excel files
for source in sources:
	turbotlib.log("Loading file " + str(sources.index(source) + 1) + "/" + str(len(sources)))
	source_page = get_doc(source['url'])
	source_links = source_page.find_all("a")
	for link in source_links:
		#find the link on the page which leads to the right 
		if (source['file'] == "excel"):
			if ('.xls' in link['href']):
				#can't use formatting information for more recent file formats in xlrd
				if (('.xlsx' in link['href']) or ('.xlsb' in link['href'])):
					formatting = False
				else:
					formatting = True

				source_url = base_url + link['href']
				excel_file = requests.get(source_url).content
				excel_results = parse_excel(excel_file, formatting, source_url, source['category'])
				for result in excel_results:
					if ('name' in result):
						print(json.dumps(result))

		#same sort of idea but for word files
		if (source['file'] == "word"):
			if ('.doc' in link['href']):
				#download the file to the turbot working directory
				source_url = base_url + link['href']
				file_name = link['href'].split("/")[-1]
				word_location = turbotlib.data_dir() + "/" + file_name
				word_file = download(source_url, word_location)

				#find out what the html file will be called
				file_extension_start = word_location.rfind(".")
				file_basename = word_location[:file_extension_start]
				output_folder = turbotlib.data_dir()
				html_location = file_basename + ".html"

				#convert the file to html using libreoffice
				subprocess.call(['libreoffice', '--headless', '--convert-to', 'html', word_location, '--outdir', output_folder])
				html_file = open(html_location, "r")
				html_document = BeautifulSoup(html_file)
				
				#now process the document and print it out
				word_results = parse_word(html_document, source_url, source['category'])
				for result in word_results:
					if ('name' in result):
						print(json.dumps(result))