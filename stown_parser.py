# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# stown_parser.py
# 
# Parses the HTML transcripts of the S-Town Podcast episodes from the 
# website of S-Town.
#
# Authored by Landon Robinson, 2017-05-31
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

# Imports to Support Data Export
import json
import csv

# Global Variables
episodes = ["chapter1", "chapter2", "chapter3", "chapter4", "chapter5", "chapter6", "chapter7"]

# Parses HTML of an episode transcript (stored in 'episodes/' folder)
def parse_episode(episode):

	# First get all the lines
	lines = []
	nextLineIsDialog = False
	nextLineisSpeaker = False
	nextLineisItalicTitle = False
	nextLineisItalicTitleEnd =  False
	currSpeaker = ''
	prevSpeaker = ''
	lineCounter = 1
	# create lines per character and then have a dictionary of key (speaker) to value (list of lines)
	with open (episode, "rb") as episode:
		for line in episode:
			line = line.strip()
			if line != '':
				for line in line.split("<"):
					for line in line.split(">"):
						line = line.strip()

						if line == '' or line == 'i':
							continue

						if '/' in line or 'div class' in line:
							continue

						if nextLineIsDialog:
							
							if line == 'h4' or line == 'i' or line == '/i' or 'p begin' in line:
								nextLineIsDialog = False
								
							else:
								record = []
								record.append(lineCounter)
								record.append(currSpeaker[:-1])
								record.append(line)
								lines.append(record)
								lineCounter+=1

						if nextLineisSpeaker:
							prevSpeaker = currSpeaker
							currSpeaker = line
							nextLineisSpeaker = False
							nextLineIsDialog = False

						if nextLineisItalicTitle:
							nextLineisItalicTitle = False

						if nextLineisItalicTitleEnd:
							nextLineisItalicTitleEnd = False

						if 'h4' in line:
							nextLineisSpeaker = True
							nextLineIsDialog = False
							nextLineisItalicTitle = False
							nextLineisItalicTitleEnd = False

						if 'p begin' in line:
							nextLineIsDialog = True
							nextLineisSpeaker = False
							nextLineisItalicTitle = False
							nextLineisItalicTitleEnd = False

						if line.strip() == 'i':
							nextLineisItalicTitle = True

						if '/i' in line.strip():
							nextLineisItalicTitleEnd = True
	return lines

# Denormalizes lines when speaker continuously speaks (used on output of parse_episode())
def line_adjuster(lines):
	adjusted_lines = []
	stream_of_consciousness = []
	count=1
	for num in range(len(lines)):

		# store current line
		line = lines[num]
		speaker = line[1]
		message = line[2]
		type = "unassigned"
		
		# if first line
		if num == 0:
			adjusted_lines.append([count, speaker, message])
			type = "first line"
			count+=1

		# if last line
		elif num == len(lines)-1:
			#print stream_of_consciousness
			if len(stream_of_consciousness)>0:
				
				for line in stream_of_consciousness:
					new_line = ""
					for line in stream_of_consciousness:
						new_line+= " " + line

				if "[MUSIC - THE ZOMBIES, \"A ROSE FOR EMILY]" in new_line:
					split_last_line = new_line.split("[MUSIC - THE ZOMBIES, \"A ROSE FOR EMILY]")
					last_dialog = split_last_line[0]

					adjusted_lines.append([count, speaker, last_dialog])
					
					count+=1
					continue


				if "[MUSIC - \"A ROSE FOR EMILY\" BY THE ZOMBIES\"]" in new_line:
					split_last_line = new_line.split("[MUSIC - \"A ROSE FOR EMILY\" BY THE ZOMBIES\"]")
					last_dialog = split_last_line[0]

					adjusted_lines.append([count, speaker, last_dialog])
			
					count+=1
					continue

				if "[MUSIC - \"A ROSE FOR EMILY,\" BY THE ZOMBIES\"]" in new_line:
					split_last_line = new_line.split("[MUSIC - \"A ROSE FOR EMILY,\" BY THE ZOMBIES\"]")
					last_dialog = split_last_line[0]
					adjusted_lines.append([count, speaker, last_dialog])
					count+=1
					continue

				if "[MUSIC - \"A ROSE FOR EMILY\" BY THE ZOMBIES]" in new_line:
					split_last_line = new_line.split("[MUSIC - \"A ROSE FOR EMILY\" BY THE ZOMBIES]")
					last_dialog = split_last_line[0]
					adjusted_lines.append([count, speaker, last_dialog])
					count+=1
					continue
		# if any line in between
		else:

			#store prev and next speakers
			previousSpeaker = lines[num-1][1]
			nextSpeaker = lines[num+1][1]

			# if previous speaker was same as current, build dialog
			if speaker == previousSpeaker:
				stream_of_consciousness.append(message)
				# print line
			# if current speaker is not same as previous
			else:

				# if this speaker has another line forthcoming, build dialog
				if speaker == nextSpeaker:
					stream_of_consciousness = []
					stream_of_consciousness.append(message)

				# if this new speaker has just one line
				else:

					# compile collected dialog of previous speaker
					new_line = ""
					for line in stream_of_consciousness:
						new_line+= " " + line

					# add that dialog to the data
					if len(new_line)>0:
						adjusted_lines.append([count, previousSpeaker, new_line.strip()])
						count+=1
						type = "accumulated data"

					# clear consciousness
					stream_of_consciousness = []

					# add current message
					adjusted_lines.append([count, speaker, message])
					type = "building line"
					count+=1

		# if type == "unassigned":
		# 	print line
	return adjusted_lines

# Dump Data to Json
def dump_to_json(name, lines):
	with open ("data/json/"+name+"_data.json", "wb") as json_file:
		json.dump(lines, json_file)

# Dump Data to CSV
def dump_to_delimited_file(name, lines, delimiter):
	with open ("data/delimited/csv/"+name+"_data.csv", "wb") as write_file:
		writer = csv.writer(write_file, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

		for row in lines:
			writer.writerow(row)

# Go!
seasonLineCount=0
for episode in episodes:

	# Parse Episode
	lines = parse_episode("episodes/"+ episode)
	
	# Clean the Data
	clean_lines = line_adjuster(lines)

	# Export the Data
	for line in clean_lines:
		print line, "\n"
		seasonLineCount+=1

	dump_to_json(episode, clean_lines)
	dump_to_delimited_file(episode, clean_lines, ',')

print "Total Lines of Dialog: ", seasonLineCount


# thoughts
# how long does each character talk on average per episode/full season
# who has the most lines in the show?
# who is the topic of discussion most in the show?
# What places are mentioned?

# NLP Functions (coming soon)
# Takes Lines Object Returns Counts of Unique Words Within
# def count_words(episode_lines):
# 	wordCounts = {}
# 	# filter out stopwords
# 	for line in lines:
# 		tokenized_sentence = line[2].split(" ")
# 		for word in tokenized_sentence:
# 			if word not in wordCounts:
# 				wordCounts[word] = 1
# 			else:
# 				wordCounts[word] = wordCounts[word]+1

# 	wc = sorted(wordCounts.items(),key=lambda (word, count): count,reverse=True)
# print "finding top 10 words..."
# topWords = []
# topWordsAndValues=[]
# for num in range(10):
# 	currentHighest=0
# 	for num in range(len(wordCounts)-1):
# 		words = sorted(wordCounts)
# 		word = words[num]
# 		count = wordCounts[word]
		
# 		if (count >= currentHighest) and word not in topWords and len(word)>2:
# 			currentHighest = count
# 			currentHighestWord = word

# 	topWords.append(currentHighestWord)
# 	topWordsAndValues.append(currentHighestWord + ": " + str(currentHighest))

# for word in topWordsAndValues:
# 	print word

# #adhoc word counter
# # wordCounter=0
# # phrase="john"
# # for line in lines:
# # 	if phrase in line[2].lower():
# # 		wordCounter+=1
# # 		print line

# # print "The phrase '" + phrase + "' occurs " + str(wordCounter) + " times."