# -*- coding: utf-8 -*-
"""Wasserstoff.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/16Gt-mAZVIgpX-oMzM1WlbY8y2jiMJzKM
"""

import os
from PyPDF2 import PdfReader
import fitz
from operator import is_
from pdfminer.high_level import extract_text
from pymongo import MongoClient
import re
import spacy
import nltk
from spacy.lang.en.stop_words import STOP_WORDS
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
import string
import streamlit as st
import time
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


# Code for Text Summarization and Keyword Extraction from a folder containing certain files
# In my project I haven't considered the images if any present within the PDF
# URL's, emails, website links atc are removed

#Text and Metadata Extraction

#Reading Folder and path of different PDF files from the folder


# function to read all PDF files from a given folder

def read_pdf_from_folder(folder_path):
  # List to store the path of all pdf files from the folder
  pdf_files = []

  # root: current directory path; dirs: subdiectorie present within current directory; files: list of files present in current and subdirectory
  for root, dirs, files in os.walk(folder_path):

    # fetches each file and checks for format if it's that of pdf or not
    for file in files:
      # check if file ends with '.pdf' format
      if file.endswith('.pdf'):

        # if file in pdf format joins root and file forming a proper path for file
        pdf_files.append(os.path.join(root, file))

  # returns a list with path to all folders within a file
  return pdf_files

#from google.colab import files
#uploaded = files.upload()

#!unzip /content/Certificate.zip -d /content/

# Test my code for a folder
#files = read_pdf_from_folder('/content/Certificate')


#Ingest PDF's Metadata and Text"""



#Extract Metadata

# Fn to extract metadata from pdf
def extract_pdf_metadata(file_path):
    try:
        # extract the file size in bytes
        file_size = os.path.getsize(file_path)

        # extract the file name
        file_name = os.path.basename(file_path)

        # Initalizing a metadata dictionary which gets update as per pdf
        metadata = {
            'Document Name': file_name,
            'File Path': file_path,
            'File Size (bytes)': file_size,
            'Creation Date': 'Unknown',
            'Author': 'Unknown',
            'Title': 'Unknown',
            'Page Count': 0,
            'Language': 'Unknown',
            'Dimensions': 'Unknown'
        }

        # Opened the file and extracted metadata from it using PyPDF2
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            # extraction of metadata if available
            info = reader.metadata

            # update few keys from metadata dictionary with the values
            if info:
              metadata['Creation Date'] = info.get('/CreationDate', 'Unknown')
              metadata['Author'] = info.get('/Author', 'Unknown')
              metadata['Title'] = info.get('/Title', 'Unknown')
              metadata['Language'] = info.get('/Language', 'Unknown')

            # updating page count
            metadata['Page Count'] = len(reader.pages)

            # for dimensions used 1st page of pdf to extract
            if len(reader.pages) > 0:
                first_page = reader.pages[0]
                dimensions = first_page.mediabox
                metadata['Dimensions'] = f"{dimensions.upper_right[0]} x {dimensions.upper_right[1]} (w x h)"

        return metadata

    except Exception as e:
        # error msg if metadata extraction fails
        print(f"Error extracting metadata from {file_path}: {e}")
        return None



#Choose Text Extraction Method

# going to use 2 different libraries for text extraction from pdf
# choice among two will be based on the complexity of the pdf, which will be determined with the function defined below
# 2 libraries:
# 1. PyMuPDF: when there is single font, less images, and simple layout. This is known for faster extraction compared to another
# 2. pdfminer.six : when there are multiple font, many images with annotations, and complex layouts. This is known for accurate and robust extraction compared to another but is slow


#Analyzing Fonts

# Analyzing Fonts

  # PyMuPDF

# Fn to analyze and extract unique font names from a pdf file
def analyze_fonts(file_path):
  try:
    doc = fitz.open(file_path)
  except Exception as e:
    # error msg if file is not found
    print(f"Error opening PDF: {e}")
    return None

  # check if file is encrypted and return if so
  if doc.is_encrypted:
    print("PDF is encrypted.")
    return None


  # Set to store unique font names
  font_list = set()

  # extract fonts from text spans
  for page in doc:
    for block in page.get_text("dict")["blocks"]:
      # skip non - text blocks
      if "type" in block and block["type"] != 0:
        continue

      # check if line exists in block
      if "lines" in block:
        for line in block["lines"]:
          if "spans" in line:
            for span in line["spans"]:
              # to considers spans with text only
              if span['text'].strip():
                font_list.add(span["font"])
      else:
        # Handle bolcks without lines
        for span in block["spans"]:
          if span['text'].strip():
              font_list.add(span["font"])

  # extract fonts of non-text elements
  for page in doc:
    fonts_from_page = page.get_fonts(full=True)
    for font in fonts_from_page:
      font_name = font[3]
      font_list.add(font_name)

  # return set of unique font names
  return font_list


#Analyze structure for images, tables, annotations"""


# fn to analyze str of PDF and count images, annotations and tables
def analyze_structure(file_path):
  try:
    doc = fitz.open(file_path)
  except Exception as e:
    # handle error if file can't be opened
    print(f"Error opening PDF: {e}")
    return None

  # check for file encryption
  if doc.is_encrypted:
    print("PDF is encrypted. Unable to analyze")
    return None

  # Initialize counters for image, annotations and tables
  img_cnt = 0
  annot_cnt = 0
  table_cnt = 0

  # Iterate through each page
  for page in doc:
    # Count presence of images
    img_cnt += len(page.get_images(full=True))

    annotation = list(page.annots())
    #check for presence of annots
    annot_cnt += len(annotation) if annotation else 0

    #check for presence of tables by analyzing text blocks
    text_blocks = page.get_text("dict")["blocks"]
    for block in text_blocks:
      if 'lines' in block:
        # consider a block table if it has >1 line
        if len(block['lines']) > 1:
          table_cnt += 1
          break # break after finding 1 table

  return img_cnt, annot_cnt, table_cnt



#Check for presence of Layers in PDF"""

# Fn to check presence of layers in PDF
def check_layers(file_path):
  try:
    doc = fitz.open(file_path)

    # initialize a flag to check for layers
    has_layers = False
    # Iterate through each page
    for page in doc:
      # Check if page has layers(is wrapped)
      if page.is_wrapped:
        has_layers = True
        break # exit if find one

    # return whether layers present or not
    return has_layers

  except FileNotFoundError:
    # handle error with lack of file
    print(f"Error: The file {file_path} was not found.")
    return None
    # Handle error where file is not a valid PDF
  except fitz.FileDataError:
    print(f"Error: The file {file_path} is not a valid PDF.")
    return None
    # Handle any other error
  except Exception as e:
    print(f"An error occurred while checking for layers: {e}")
    return None



#Analyze Layout Complexity(Text and Layout Coordinates)"""

# Analyze for complexity in PDF
def analyze_layout_complexity(file_path):
  try:
    doc = fitz.open(file_path)
  except Exception as e:
    # Handle error if PDF can't be opened
    print(f"Error opening PDF: {e}")
    return None

  # Initialize 0 complexity score
  complexity_score = 0

  # Iterate through each page
  for page_num, page in enumerate(doc):
    # Get text blocks from page
    blocks = page.get_text("dict")["blocks"]
    # Filter non empty blocks with lines
    non_empty_blocks = [block for block in blocks if 'lines' in block and block['lines']]

    # Increase complexity_score if number of non_empty_blocks exceeds the threshold
    if len(non_empty_blocks) > 5:  #Arbitary threshold for complexity
      complexity_score += 1
       # print(f"{page_num+1} contributes to complexity")

  #return final complexity score
  return complexity_score


#Decision Making among 2 libraries"""

# decide which library to choose for text extraction with a thought that complex PDF's go with pdfminer.six and simple ones go with PyMuPDF
def select_extraction_method(file_path):
  # Call for above defined functions and store values in variables
  fonts = analyze_fonts(file_path)
  img_count, annot_count, table_count = analyze_structure(file_path)
  has_layers = check_layers(file_path)
  layout_complexity = analyze_layout_complexity(file_path)

  # defined threshold for complexity
  is_complex = (
      len(fonts) > 3 or  # >3 unique fonts show complexity
      img_count > 5 or   # > 5 images indicates complexity
      annot_count > 3 or  # >3 annotations indicate complexity
      table_count > 3 or  # > 3 tables show complexity
      layout_complexity > 2 or  # > 2 layers show complexity
      has_layers         # presence of layers show complexity

  )

  # Return extraction method based on complexity analysis
  if is_complex:
    return 'pdfminer.six' # (best for complex PDF: PDF is complex)
  else:
    return 'PyMuPDF' # (Fast for simple PDF: PDF is simple)


#Extract Text





def clean_text(text):
  # Remove form feed characters and other unwanted non-printable characters
  cleaned_text = text.replace('\x0c', '').strip()
  return cleaned_text


def extracting_text(file_path):
  # Select text extraction method based on complexity of PDF
  method = select_extraction_method(file_path)

  # Use PyMuPDF for simple ones
  if method == 'PyMuPDF':
    doc = fitz.open(file_path)
    text = ''

    # Iterate through each page and extract text
    for page in doc:
      text += page.get_text()

  # Use pdfminer.six for complex ones
  elif method == 'pdfminer.six':
    text = extract_text(file_path)

    # Clean up the extracted text using fn
    cleaned_text = clean_text(text)
    return  cleaned_text
  # Handle error
  else:
    raise ValueError("Invalid extraction method")

  return text



#Final extraction of metadata and text"""

def full(folder_path):
  # Get list of all PDF's from a folder
  pdf_files = read_pdf_from_folder(folder_path)

  # List to store metadata and text of each PDF
  metadata_list = []
  text_list = []

  # Iterate through each PDF file
  for i in pdf_files:
    # Extract Metadata
    metadata = extract_pdf_metadata(i)

    # Extract Text
    text = extracting_text(i)

    # Append to respective lists
    metadata_list.append(metadata)
    text_list.append(text)

  return metadata_list, text_list

#Test
#from google.colab import files
#uploaded = files.upload()



#Transfer of metadata to MongoDB"""

# Going to use MongoDB Atlas as it is a good option to work with when comes to a project associated with the team ,
# mongodb+srv://wasserstoff:wasserstoff@wasserstoff.ql0x5.mongodb.net/?retryWrites=true&w=majority&appName=Wasserstoff





# Create connectiion to MongoDB using connection string
client = MongoClient('mongodb+srv://wasserstoff:wasserstoff@wasserstoff.ql0x5.mongodb.net/pdf_db?retryWrites=true&w=majority')

# Access pdf_db database
db = client['pdf_db']

# Access pdf_files collection within database
collection = db['pdf_files']

# To check if connection is successful
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

def get_existing_file_paths():
  # Fetch all existing file paths from MongoDB
  existing_documents = collection.find({}, {'File Path': 1, '_id': 0})

  # Store files in a set to check for duplicates
  existing_paths = {doc['File Path'] for doc in existing_documents}
  return existing_paths

def insert_metadata_to_mongodb(meta_data):
  # Get all existing file paths in the database
  existing_paths = get_existing_file_paths()

  # List to store IDs of newly inserted documents
  inserted_ids = []

  # Loop through metadata and insert to MongoDB
  for i in meta_data:
        # Check if the file path already exists
      if i['File Path'] in existing_paths:
        print(f"Document with File Path '{i['File Path']}' already exists. Skipping insertion.")
      else:
            # Insert the new document if not a duplicate
        try:
          result = collection.insert_one(i)
          inserted_ids.append(result.inserted_id)
          print(f"Inserted document '{i['Document Name']}' successfully.")
        except Exception as e:
          # Handle error if any
          print(f"Error inserting document: {e}")

  return inserted_ids


# Fetch all documents in the collection
documents = collection.find()

# Iterate over and print each document
#for document in documents:
 #   print(document)

#Summarization and Keyword Extraction

#Text Preprocessing



#Basic Requirements for Keyword and Summary"""





nlp = spacy.load("en_core_web_md")

def preprocess(text):
  # turn text to lowercase
  txt = text.lower()

  # remove hlml tags if any
  txt = re.sub(r'<.*?>', ' ', txt)

  #remove mail_ids
  txt = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+',' ',txt)

  # Remove urls
  txt = re.sub(r'https?://[^\s]+|www\.[^\s]+',' ',txt)

  # Remove any special characters
  txt = re.sub(r'[^a-zA-Z0-9\s\.\!\?]',' ', txt) # included these three characters as they will be useful later in sent_tokenization

  # Remove extra white spaces
  txt = re.sub(r'\s+', ' ', txt)

  return txt


# get size of pdf in terms of number of words
def get_pdf_size(text):
  return len(text.split())

# fn to set vectorization parameters
def set_vectorization_params(text):
  size = get_pdf_size(text)

  #very short PDFs
  if size < 100:
    ngram_range = (1,1) #Unigram
    max_features = 5000 # Max 5000 unique features

  #short PDFs
  elif 100 <= size < 1000:
    ngram_range = (1,2) # Unigram and Bigram
    max_features = 10000 # Max 10000 unique features

  #long PDFs
  else:
    ngram_range = (1,3) # Uni, Bi, Tri-grams
    max_features = 15000  # # Max 15000 unique features

  # Return ngram_range and max_features
  return ngram_range, max_features

#Keyword Extraction"""

def lemma_stopword_KE(text):

  # remove stop words and punctuations
  doc = nlp(text)
  txt = ' '.join([token.text for token in doc if not token.is_stop and not token.is_punct])

  # Lemmatization
  doc = nlp(txt)
  txt = ' '.join([token.lemma_ for token in doc])

  # Return text after lemmatization and stopword and punctuation removal
  return txt

#Vectorization"""


# Vectorization and TF-IDF
def vectorize(text):

  # Set factors based on PDF size
  ngram_range, max_features = set_vectorization_params(text)

  # Initialize CV with specified parameters
  cv = CountVectorizer(max_features=max_features, ngram_range=ngram_range)

  # create a vocabulary and word count vectors
  word_count_vectors = cv.fit_transform([text])

  # Using TF-IDF
  tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
  tfidf_transformer.fit(word_count_vectors)

  return cv, tfidf_transformer

#From TF-IDF"""

def get_dynamic_topk_and_threshold(text):
  # Get pdf size based on word count
  size = get_pdf_size(text)
  """Function to set top-k and threshold based on PDF size."""
  # PDF with less than 100 words
  if size < 100:
    return 10, 0.1  # Small PDF: 5 keywords, higher threshold

  # PDF with words between 100 and 500
  elif 100 <= size < 500:
    return 30, 0.05  # Medium PDF: 10 keywords, lower threshold

  # PDF with words more than 100
  else:
    return 100, 0.03

def sort_coo(coo_matrix):

  # Pair each column with its corresponding value from coo matrix
  tuples = zip(coo_matrix.col, coo_matrix.data)

  # Sort tuples by values (desc) and index (for ties)
  return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

def extract_topn_with_threshold(feature_names, sorted_items, topn, threshold):
    # Dict to add keywords and its scores
    results = {}
    count = 0

    # Iterate through sorted keywords and check threshold
    for idx, score in sorted_items:
        if count < topn and score > threshold:
            results[feature_names[idx]] = round(score, 3) # Add keyword and score
            count += 1
        # Stop when topn limit is reached
        if count >= topn:
            break

    return results

def get_keywords_with_combined_approach(text):

  # Get top-k and threshold
  topk, threshold = get_dynamic_topk_and_threshold(text)

  # get vectorizer and TF-IDF transformer for specific text
  cv, tfidf = vectorize(text)

  # generate word count
  word_count_vector = cv.transform([text])

  # generate TF-IDF vector
  tf_idf_vector = tfidf.transform(cv.transform([text]))

  # Sort the TF-IDF values
  sorted_items = sort_coo(tf_idf_vector.tocoo())

  # Extract the top n keywords
  feature_names = cv.get_feature_names_out()
  keywords = extract_topn_with_threshold(feature_names, sorted_items, topk, threshold)

  # Filter keywords to include only alphabetic characters
  filtered_keywords = {k: v for k, v in keywords.items() if k.isalpha()}

  return filtered_keywords

#Keywords based on POS tag and NER"""

# Filter keywords using POS and NER
def filter_keywords_by_pos_and_ner(text):
  # Pass text to spacy libraries defined nlp
  doc = nlp(text)

  # list to store keywords
  keywords = []

  # List of pos_tags want to consider
  relevant_pos_tags = ['NOUN', 'PROPN', 'ADJ', 'VERB', 'NUM', 'SYM']

  # List of NER want to consider
  relevant_entity_labels = [
    'ORG',            # Organizations
    'GPE',            # Geopolitical Entities
    'PERSON',         # People
    'PRODUCT',        # Products
    'EVENT',          # Events
    'DATE',           # Dates
    'DISEASE',        # Medical Conditions
    'DRUG',           # Drugs/Medications
    'LEGISLATION',    # Laws or Legal Statutes
    'FINANCIAL_TERM', # Financial Terms
    'EDUCATIONAL_TERM',# Educational Terms
    'EMAIL'           # Email Addresses
]
  # Iterate over each word in text
  for token in doc:
    # Check if the token has a relevant POS tag
    if token.pos_ in relevant_pos_tags:
      keywords.append(token.text) # If relevant POS_tag then append to list

    # Check if the token is part of a named entity with a relevant label
    if token.ent_iob_ != 0 and token.ent_type_ in relevant_entity_labels:
      keywords.append(token.text) # If yes append to list

  # Return list of keywords
  return keywords

#Combined Keywords from Both Approach"""

# I'm not going to use this as based on trials this approach of POS & NER requires domain specific list of what to be included in keywords, and this project
# more being general for now doesn't go well with this approach
# so will ahead with vectorizer approach only
def combined_keywords(text):

  # Get keyword absed on TF-IDF
  keywords_from_tfidf = set(get_keywords_with_combined_approach(text).keys())

  # Get keywords based on POS & NER
  keywords_from_pos_and_ner = set(filter_keywords_by_pos_and_ner(text))

  # Combine both keywords while excluding duplicates
  combined_keywords = keywords_from_tfidf.union(keywords_from_pos_and_ner)
  return combined_keywords

#Main fn for keywords"""

def main_keyword(text):
  # Pass text to 2nd level preprocessing
  txt = lemma_stopword_KE(text)

  # Pass text to get keywords based on TF-IDF only as one with POS and NER is not a better set unless domain specified
  keywords = set(get_keywords_with_combined_approach(txt).keys())
  return list(keywords)


#Text Summarization"""



#Processing"""

def lemma_stopword_TS(text):

  # remove stop words and punctuations
  doc = nlp(text)
  txt = ' '.join([token.text for token in doc if not token.is_stop])

  # Lemmatization
  doc = nlp(txt)
  txt = ' '.join([token.lemma_ for token in doc])

  # removing punct apart from one that mark sent ending
  sent_end_punct = {'.','!','?'}

 # Lit of punct that has to be removed
  punct_to_remove = set(string.punctuation) - sent_end_punct


  def remove_non_sent_ending_punct(text):
    # Process input text using NLP Model
    doc = nlp(text)

    filtered_tokens = []

    # Iterate through tokens to filter out unwanted punctuations
    for token in doc:
      if token.is_punct: # Check if token is punct
        if token.text in sent_end_punct: # keep only sentence ending punct
          filtered_tokens.append(token.text)
      else:
        filtered_tokens.append(token.text)  # Keep not punct tokens

    # Join filter tokens to a string
    return ' '.join(filtered_tokens)

  # Apply above fn to text
  txt = remove_non_sent_ending_punct(txt)

  return txt

#Vectorization"""

def vectorize_for_summary(text):
  doc = nlp(text)

  # Extract sentences
  sentences = [sent.text for sent in doc.sents]

  # Apply lemma_stopword on each sentence
  preprocessed_sentences = [lemma_stopword_TS(sent) for sent in sentences]

  # remove remaining punct
  sentences = [sent.rstrip('.!?') for sent in sentences]

  # set vectorization parameters
  ngram_range, max_features = set_vectorization_params(text)

  # use CV on sentences
  cv = CountVectorizer(max_features=max_features, ngram_range=ngram_range)

  # Word Count Vectors for sentences
  word_count_vectors = cv.fit_transform(sentences)

  # Apply TF-IDF to word count vectors
  tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
  tfidf_transformer.fit(word_count_vectors)

  return cv, tfidf_transformer, sentences, preprocessed_sentences

#Ranking text based on TF-IDF score"""

def determine_summary_length(size):

  # For docs with size less than 1000
  if size <= 1000:
    # 1 to 10 sentences
    return max(1, size // 100) # 1 sent for every 100 words

  # For docs with size between 1000 and 10k
  elif 1000 < size <= 10000:
    # 10 to 30 sentences
    return max(10, min(size // 300, 30)) # 1 sent for every 300 words

  # For docs with size between 10k and 1Lakh
  elif 10000 < size <= 100000:
    # 30 to 100 sentences
    return max(30, min(size // 1000, 100)) # 1 sent for every 1000 words

  # For extremely large PDFs (1Lakh+):
  else:
    return max(100, (min(size // 10000, 1000))) # 1 sent for every 1000 words

def rank_sentences_for_summary(cv, tfidf_transformer, preprocessed_sentences):

  # Generate TF-IDF vectors for sentences
  word_count_vectors = cv.transform(preprocessed_sentences)
  tfidf_vectors = tfidf_transformer.transform(word_count_vectors)

  # Sum TF-IDF scores for each sentences
  sentence_scores = tfidf_vectors.sum(axis=1).A1 # Convert to 1D array

  # list of (sentence, score) tuples
  sorted_sentences = [(i, score) for i, score in enumerate(sentence_scores)]

  # Sort sentences by their scores
  sorted_sentences = sorted(sorted_sentences, key=lambda x: x[1], reverse=True)

  return sorted_sentences

def select_top_sentences(sorted_sentences, sentences, summary_length):
  # Get indices of top ranked sentences
  top_sentence_indices = [sentence for sentence, score in sorted_sentences[:summary_length]]

  # Return original sentence
  top_sentences = [sentences[i] for i in top_sentence_indices]

  return top_sentences

#Generate Summary"""

def generate_summary(text):
  cv, tfidf_transformer, sentences, preprocessed_sentences = vectorize_for_summary(text)

  # determine PDF size and Dynamic Summary length
  size = get_pdf_size(text)
  summary_length = determine_summary_length(size)

  # Rank sentences based on preprocessing
  sorted_sentences = rank_sentences_for_summary(cv, tfidf_transformer, preprocessed_sentences)

  # select top sentences from original text
  top_sentences = select_top_sentences(sorted_sentences, sentences, summary_length)

  # Combine the top sentences with spaces, keeping their original punctuation intact
  summary = ' '.join([sent.strip().capitalize() + '.' if not sent.endswith('.') else sent for sent in top_sentences])

  return summary


#Main fn for summary"""

def main_summary(text):
  # pass text for 2nd level of preprocessing
  txt = lemma_stopword_TS(text)

  # Get summary by passing processed text to fn
  summary = generate_summary(txt)

  # Returns summary
  return summary



#Final fn for both text and summary"""

def summary_and_keyword(text):
  # Pass text to respective fn to get summary and text
  summary = main_summary(text)
  keywords = main_keyword(text)

  # Return summary and text
  return summary, keywords



#Update Summary and Keyword to MongoDB"""

def update_mongodb_with_summary_and_keywords(inserted_id, summary, keywords):

  # Code to update MongoDB with the summary and keywords
  collection.update_one({"_id": inserted_id}, {"$set": {"summary": summary, "keywords": keywords}})

#Final Project

#Final Project Code Summary:***

#This code processes PDF documents to extract summaries and keywords from their text. Key features include:

#Text Processing**: Prepares text for summary and keyword extraction.

#Concurrency**: Uses ThreadPoolExecutor to handle multiple PDFs simultaneously for improved efficiency.

#Error Handling:** Implements try-except blocks to manage errors without disrupting the pipeline.

#MongoDB Integration:** Uploads extracted summaries, keywords, and metadata to a MongoDB database named pdf_db.

#Performance Logging:** Tracks processing time for each document.

#The final_project(folder_path) function serves as the entry point, allowing users to process all PDFs in a specified folder and receive performance metrics, summary, keywords and updation of same in MongDB alongwith Metadata.



def process_text_and_update(id_text_tuple):
    """Function to process text, extract summary and keywords, and update MongoDB."""
    inserted_id, text = id_text_tuple
    start_time = time.time()

    try:

        # Preprocess text
        text = preprocess(text)

        # Generate summary and keywords
        summary, keywords = summary_and_keyword(text)
        print(f"Summary: {summary}")
        print(f"Keywords: {keywords}")

        # Update MongoDB with summary and keywords
        update_mongodb_with_summary_and_keywords(inserted_id, summary, keywords)

        end_time = time.time()
        processing_time = end_time - start_time

        # Log processing time
        logging.info(f"Processed document ID {inserted_id} in {processing_time:.2f} seconds.")

        # Return metrics for the task
        return {
            'Document ID': inserted_id,
            'Start Time': start_time,
            'End Time': end_time,
            'Processing Time (sec)': processing_time,
            'Status': 'Success',
            'Summary': summary,  # Include summary
            'Keywords': keywords #include keywords
        }

    except Exception as e:
        end_time = time.time()
        logging.error(f"Error processing document ID {inserted_id}: {e}")

        # Return metrics indicating failure
        return {
            'Document ID': inserted_id,
            'Start Time': start_time,
            'End Time': end_time,
            'Processing Time (sec)': end_time - start_time,
            'Status': f"Failed - {e}",
            'Summary': None,  # Ensure Summary is included
            'Keywords': None  # Ensure Keywords is included
        }

def final_project(folder_path):
    try:
        # Extract metadata and text for all PDFs within a folder
        metadata_list, text_list = full(folder_path)

        # Add metadata to MongoDB
        inserted_ids_list = insert_metadata_to_mongodb(metadata_list)

        performance_metrics = []
        summaries = []  # List to hold summaries
        keywords = []  # List to hold keywords

        # Use ThreadPoolExecutor to process each PDF concurrently
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_text_and_update, (inserted_ids_list[i], text_list[i]))
                       for i in range(len(text_list))]

            # Collect results as tasks are completed
            for future in as_completed(futures):
                result = future.result()
                performance_metrics.append(result)

                # Append the summary and keywords to respective lists
                summaries.append(result['Summary'])
                keywords.append(result['Keywords'])

        # Create a DataFrame from the performance metrics
        performance_metrics_df = pd.DataFrame(performance_metrics)

        # Log overall performance
        logging.info("Processing complete for all documents.")
        print(performance_metrics_df)

        # Return performance metrics DataFrame, summaries, and keywords
        return performance_metrics_df, summaries, keywords

    except Exception as e:
        logging.error(f"Error in final_project: {e}")
        return None, None, None  # Return None for all if an error occurs

 #final_project('/content/w_test_folder')

#Test: Check for updation in MongoDB
# Fetch all documents in the collection
documents = collection.find()

# Iterate over and print each document
#for document in documents:
 #   print(document)

# Delete all documents
# delete_result = collection.delete_many({})

# Print the number of documents deleted
# print(f"Deleted {delete_result.deleted_count} documents.")

def main():
    st.title("PDF Keyword and Summary Generator")

    # Input for folder path
    folder_path = st.text_input("Enter the folder path containing PDF files:")

    if st.button("Process PDFs"):
        if not os.path.isdir(folder_path):
            st.error("Invalid path. Please make sure the folder exists.")
        else:
            # Call the final_project function and unpack the results
            performance_df, summaries, keywords = final_project(folder_path)

            # Display processing results
            st.success("Processing completed!")

            # Display performance metrics
            st.write("Performance Metrics:")
            if performance_df is not None:
                st.dataframe(performance_df)  # Display the performance metrics DataFrame
            else:
                st.error("No performance metrics returned.")

            # Display summaries
            st.write("Summaries:")
            if summaries:
                for i, summary in enumerate(summaries):
                    st.write(f"Document {i + 1}: {summary if summary else 'Processing failed or summary unavailable.'}")
            else:
                st.write("No summaries returned.")

            # Display keywords
            st.write("Keywords:")
            if keywords:
                for i, keyword in enumerate(keywords):
                    st.write(
                        f"Document {i + 1}: {keyword if keyword else 'Processing failed or keywords unavailable.'}")
            else:
                st.write("No keywords returned.")


# Check if the script is run directly (not imported)
if __name__ == "__main__":
    main()

