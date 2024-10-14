import json
import os #so we can loop through the folder of documents
from bs4 import BeautifulSoup
import nltk
from nltk.stem import SnowballStemmer
import re
from zipfile import ZipFile
import warnings
from bs4 import MarkupResemblesLocatorWarning
from bs4.builder import XMLParsedAsHTMLWarning

# If SnowballStemer not downloaded, download it
#nltk.download('punkt')
#nltk.download('snowball_data')

#questions:
#-what should we put for the document id? Since all the urls are  unique is it fine to use that?
#"ask if it has to be 2 charachters or more" ?
    # example: " I added an  8% increase in price of my art work" 
    # would the tokens be "I" "added" "an" "8" "increase" "in" "price" "of" "my" "art" "work" 
    # OR "added" "an" "increase" "in" "price" "of" "my" "art" "work"

# Suppress warnings
warnings.filterwarnings("error")

# Custom warning handler to print the file name
def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
    if category == MarkupResemblesLocatorWarning:
        print(f"MarkupResemblesLocatorWarning in file: {filename}")

# Register custom warning handler
warnings.showwarning = custom_warning_handler


class Posting:
    def __init__(self, docid, tfidf, fields):
        self.docid = docid #store the document ID that the token was seen in 
        self.tfidf = tfidf # use freq counts for now
        self.fields = fields 

def simplify_token(token):
  #remove http:// or https://
    token = re.sub(r'https?://', '', token)
    token = re.sub(r'http?://', '', token)
    #remove www.
    token = re.sub(r'www\.', '', token)
    #slash and path
    token = token.split('/')[0]
    #remove the domain extensions (.com, .org) 
    token = re.sub(r'\.[a-zA-Z]+$', '', token)
    #remove anything none alphanumeric
    token = re.sub(r'[^a-zA-Z0-9]', '', token)
    return token


def get_tokens_noise_removed(documentPath):

        # 1. Open the JSON file
    with open(documentPath, 'r') as json_file:
        data = json.load(json_file)
    # Extract the HTML content from the 'content' key
    html_content = data['content']
    find_encoding = data['encoding']

    #now open with correct encoding 
    with open(documentPath, 'r', encoding=find_encoding) as json_file:
        data = json.load(json_file)

    # decoded_data = html_content.decode(found_encoding)
    tokens = []
    if html_content != None:
        try:
            if os.path.isfile(html_content):
                print(f"Processing file: {documentPath}")
                with open(html_content, 'r') as file:
                    soup = BeautifulSoup(file, 'html.parser')
            else:
                soup = BeautifulSoup(html_content, 'html.parser')
        except MarkupResemblesLocatorWarning as e:
            print(f"MarkupResemblesLocatorWarning in file: {documentPath}")
            #raise RuntimeError(f"Error processing file: {documentPath}") from e #this line kills the program
            # Continue execution without raising an error
            # Return empty list of tokens
            return []
        except XMLParsedAsHTMLWarning:
            print(f"XMLParsedAsHTMLWarning in file: {documentPath}")
            return []
        #this is the list of noise_tags
        noise_tags = ['style', 'img', 'iframe', 'script', 'aside', 'footer', 'nav', 'video', 
                      'button','input', 'form', 'div', 'section', 'span','a', 'link',
                        'menu', 'meta', 'time', 'i', 'small', 'head', 'noscript', 'object', 'embed', 'canvas',
                        'applet', 'map', 'area']
        noise_classes = ['ad', 'advertisement', 'ad-container'] 
        tokens = []
   
        for tag in soup.find_all(): #get all the tags in soup
            # print(tag.name)
            if tag.name not in noise_tags and not any(class_name in tag.get('class', []) for class_name in noise_classes):
                # print("tag:: ", tag.name)
                tag_text = tag.get_text(separator=' ') #get the text inside the tag
                # print(tag_text)
                tag_tokens = tokenize(tag_text) #tokenize the tag
                # print(tag_tokens)
                tokens.extend(tag_tokens) #add the new tokens to the list
                # print(tokens)
        # else:
        #     with open("noise_text.txt", 'a') as file:
        #         file.write(tag.name + tag.get_text(separator=' ') + "\n")
    return tokens
# Now 'data' contains the contents of the JSON file as a Python dictionary
def tokenize(text_data):
    #split the text 
    final_tokens = []
    tokens = text_data.split()
    
    #the final tokens
    for token in tokens:
        #if the word is 2 or more charachters long or is a digit or i 
        if token.isdigit() or token.lower() in ["i", "a"]:
            final_tokens.append(token.lower())
        elif len(token) >=2  and token not in ['click', 'here']:
            #if the word contains the puncutation we combine it 
            if "n't" in token:
                token = token.replace("n't", "")
                final_tokens.append("not")
            elif "'ll" in token: 
                token = token.replace("'ll", "")
                final_tokens.append("will")
            elif "'m" in token:
                token = token.replace("'m", "")
                final_tokens.append("am")
            elif "'ve" in token:
                token = token.replace("'ve", "")
                final_tokens.append("have")
            elif "let's" in token:
                token = token.replace("'s", "")
                final_tokens.append("us")
            elif "'re" in token:
                token = token.replace("'re", "")
                final_tokens.append("are")
            elif token in ["there's", "what's", "that's"]:
                token = token.replace("'s", "")
                final_tokens.append("is")
            elif "." in token:
                parts = token.split('.')
                token = ''.join(parts)
            token = simplify_token(token)
            final_tokens.append(token.lower())
    return final_tokens

#return a dictionary with tokens (that we stem) as keys and frequency as the values
def count_stem(tokens):
    stemmer = SnowballStemmer("english")
    counts =dict()

    for token in tokens:
        stemmed_token = stemmer.stem(token)
        counts[stemmed_token] = counts.get(stemmed_token, 0) + 1
    return counts


#Step 3 Tokenize text can use libraries - NLTK
#i would like to make a hybrid algorithmic dictionary - Krovetz stemmer. But rn its a porter stemmer
# def fun_stemmer(tokens):
#     # Create an instance of the Snowball stemmer with the desired language
#     stemmer = SnowballStemmer("english")

#     #loop through the tokens and stem each one
#     #create a map that contains their counts along with the stemmed token
#     final_tokens = dict()
#     for token, frequency in tokens.items():
#         final_tokens[stemmer.stem(token)] = frequency

#     return final_tokens

#     singles = [stemmer.stem(token) for token in tokens]
#     print(' '.join(singles))


# Step 4 - Build inverted index, this is in-memory code. In future cant store in hash table, must store in text file
def buildIndex(folderPath):
    #create hash table to store the Iverted Index
    hash_table = {}
    #counter n that stores documentID
    n = 0

    #loop through the json files in the folder
    for root, dirs, files in os.walk(folderPath):

        for filename in files:
            if filename.endswith('json'):
                n = n+1 
                filePath = os.path.join(root, filename)
                #call the tokenize function 
                pre_tokens = get_tokens_noise_removed(filePath)
                #function that gets rid of duplicate tokens, stems tokens, and counts them
                #final_tokens holds a map of [token, count]
                final_tokens = count_stem(pre_tokens)

                #loop through the final tokens and make them into postings
                for token, count in final_tokens.items():
                    #check if current token is in map
                    #if yes, the token already exists, so just add the "n" value as a posting into the list
                    if token in hash_table:
                        hash_table[token].append(Posting(docid=n, tfidf=count, fields=0))
                    #else no, add it to map with token as the key and the value is  a newly created list with no entries
                    else:
                        hash_table[token] = [Posting(docid=n, tfidf=count, fields=0)]

    return hash_table, n

def print_inverted_index(inverted_index):
    for token, postings in inverted_index.items():
        print(f"Token: {token}")
        for posting in postings:
            print(f"  DocID: {posting.docid}, TF-IDF: {posting.tfidf}, Fields: {posting.fields}")
        
def write_inverted_index_to_file(inverted_index, output_file):
    with open(output_file, 'w') as file:
        for token, postings in inverted_index.items():
            file.write(f"Token: {token}\n")
            for posting in postings:
                file.write(f"  DocID: {posting.docid}, TF-IDF: {posting.tfidf}, Fields: {posting.fields}\n")



if __name__ == "__main__":
    # 1. get the files 
    # 2. send the file path to the tokenize function 
    i, num_docs = buildIndex('/Users/mireyagonzalez/Desktop/CS121/M1_milestone1/DEV/cml_ics_uci_edu')
    #print_inverted_index(i)
    write_inverted_index_to_file(i, 'inverted_index.txt')
    print("Number of docs:", num_docs)