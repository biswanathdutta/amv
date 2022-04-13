# Importing libraries
import sys
import re
import urllib
from bs4 import BeautifulSoup as BS
from selenium import webdriver
import pandas as pd
import numpy as np

# 1. Extracting the inforamtion
url = "https://algorist.com/algorist.html" # Traget website url. ie. The Stony Brook Algorithm Repository
driver = webdriver.Chrome() # Instantiating chrome driver to control the browser
driver.get(url) # Opening a browser session of the target url

a_tags = driver.find_elements(webdriver.common.by.By.CSS_SELECTOR, 'a')
algorithms = []
for i in a_tags:
    link = i.get_attribute('href')
    if re.search('https://algorist.com/problems/', link):
        if link not in algorithms:
            algorithms.append(link)     # Collecting the URLs for each algorithm
print("{} URLs for algorithms stored".format(len(algorithms)))

# Dictionary to collect the metadata elements
algos_dict = dict(problem = [], problem_url = [], problem_type = [],  input_image = [], output_image = [], input_decription = [], problem_statement = [], description = [], recommended_books = [], related_problems = [])

# Populating problem_type of algos_dict
sections = []
for i in a_tags:
    link = i.get_attribute('href')
    if re.search('https://algorist.com/sections/', link):
        if link not in sections:
            sections.append(link)
driver.quit() # Closing the browser session
for url in sections:
    driver = webdriver.Chrome()
    driver.get(url)
    c = len(driver.find_elements(webdriver.common.by.By.CSS_SELECTOR, "div.boxes")[0].find_elements(webdriver.common.by.By.CSS_SELECTOR, "td"))
    algos_dict['problem_type'].extend(c * [url.split("sections/")[-1][:-5]])
    driver.close()

# Collecting metadata elements from each URL of algorithmic problems
for index, url in enumerate(algorithms):
    try:
        if index % 5 == 0:
            print(index,
                  " set of algorithmic problems metadata extracted out of ",
                  len(algorithms)) # Printing status 
            
        soup = BS(urllib.request.urlopen(url), 'lxml') # BeatifulSoup soup object whuch contains the HTML code in a heirarchical manner.
        problem_ = soup.select('h1')[1].text # Title of the algorithmic problem
        input_image_ = 'https://algorist.com' + soup.select('table td div img')[0].get('src')[2:] # Input image
        output_image_ = 'https://algorist.com' + soup.select('table td div img')[1].get('src')[2:] # Output image
        input_decription_ = soup.select('p.lead')[0].text.split('Problem: ')[0][20:] # Input decription
        problem_statement_ = soup.select('p.lead')[0].text.split('Problem: ')[1] # Problem statement
        
        description_ = ''
        for i in soup.select('p')[2:]:
            description_ = description_ + i.text + '\n'
        description_ = description_.strip() # Description
        
        related_problems_ = ''
        for i in soup.select_one('div.boxes').select('a'):
            related_problems_ = related_problems_ + i.text.strip('\n') + ' | ' + 'https://algorist.com' + i.get('href')[2:] + '\n'
        related_problems_ = related_problems_.strip('\n') # Realated problems
        
        # Addind all the collected metadta elements to algos_dict 
        algos_dict['problem_url'].append(url)
        algos_dict['input_image'].append(input_image_)
        algos_dict['problem'].append(problem_)
        algos_dict['output_image'].append(output_image_)
        algos_dict['input_decription'].append(input_decription_)
        algos_dict['problem_statement'].append(problem_statement_)
        algos_dict['description'].append(description_)
        algos_dict['related_problems'].append(related_problems_)
        
        # For recommended books, there can be algorithmic problems which doesn't have any recommended books field. To handle this we use Try-Except block
        try:
            recommended_books_ = ''
            for i in soup.select_one('table.books').select('a'):
                recommended_books_ = recommended_books_ + i.text + ' | ' + i.get('href') + '\n'
            recommended_books_ = recommended_books_.strip('\n')
            
            algos_dict['recommended_books'].append(recommended_books_)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
            print('Error getting recommended books at : ')
            print(index, ' : ', url)
            print('Adding blank in recommended_books feature')
            algos_dict['recommended_books'].append('')
            next
        
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(index, ' : ', url)
print("{} set of algorithmic problems metadata extracted.".format(len(algorithms)))

# Adding implementation language
print("Adding Implementation in language inforamtion.")
languages = []
url = "https://algorist.com/algorist.html"
driver = webdriver.Chrome()
driver.get(url)
a_tags = driver.find_elements(webdriver.common.by.By.CSS_SELECTOR, 'a')
for i in a_tags:
    link = i.get_attribute('href')
    if re.search('https://algorist.com/languages/', link):
        if link not in languages:
            languages.append(link)
driver.quit()

dict_75 = {i:'' for i in algos_dict['problem_url']}

for url in languages:
    driver = webdriver.Chrome()
    driver.get(url)
    p_lang_name = re.findall('languages/(.+)\.html',url)[0]
    
    th = driver.find_elements(webdriver.common.by.By.CSS_SELECTOR, "th") + driver.find_elements(webdriver.common.by.By.CSS_SELECTOR, "td")
    
    for block in th:
        imp_block = block.find_elements(webdriver.common.by.By.CSS_SELECTOR, "a")[0]
        pblm_blocks = block.find_elements(webdriver.common.by.By.CSS_SELECTOR, "a")[1:]
        
        rating = imp_block.text.split()[-1]
        imp_name = ' '.join(imp_block.text.split()[:-1])
        imp_url = imp_block.get_attribute('href')
        imp_detail = ' | '.join((imp_name, rating, imp_url, p_lang_name))
        
        for pbl_blk in pblm_blocks:
            key = pbl_blk.get_attribute('href')
            try:
                dict_75[key] = dict_75[key] + imp_detail + '\n'     
            except KeyError:
                Error_correction = {"https://algorist.com/problems/Eulerian_Cycle/Chinese_Postman.html":"https://algorist.com/problems/Eulerian_Cycle_Chinese_Postman.html",
                                    "https://algorist.com/problems/Feedback_Edge/Vertex_Set.html":"https://algorist.com/problems/Feedback_Edge_Vertex_Set.html",
                                    "https://algorist.com/problems/Longest_Common_Substring/Subsequence.html":"https://algorist.com/problems/Longest_Common_Substring.html"}
                dict_75[Error_correction[key]] = dict_75[Error_correction[key]] + imp_detail + '\n'
    driver.quit()

df_imp = pd.DataFrame({'problem_url':dict_75.keys(),'imple_details':dict_75.values()})   

def joiner(line):
    if len(line) < 3:
        return ''
    else:
        prev = ''
        out = []
        for i in np.sort(list(set([i for i in line.split('\n') if len(i) > 2]))):
            if i.split(' | ')[:3] == prev.split(' | ')[:3]:
                t = ' | '.join(i.split(' | ')[:3] + prev.split(' | ')[3:] + i.split(' | ')[3:])
                _ = out.pop()
                out.append(t)
                prev = t
            else:
                out.append(i)
                prev = i
        return '\n'.join(out)

df_imp['implementations'] = df_imp["imple_details"].apply(joiner)
print("Implementation in language inforamtion added.")

df = pd.DataFrame(algos_dict)
Problems = pd.merge(df, df_imp[["implementations", "problem_url"]], on = "problem_url" )


Problems = Problems[['problem', 'problem_url', 'problem_type', 'input_image',
                     'output_image','input_decription','problem_statement',
                     'description','recommended_books', 'implementations',
                     'related_problems']]
try:
   filename = sys.argv[1]
except IndexError:
   filename = "Problem(75).csv"
print("Creating CSV file ({})...".format(filename))
Problems.to_csv(filename, index=False)  
print("\n CSV file with {} columns is saved in the name :{}".format(Problems.shape[1], filename))


# 2. Processing the extracted data
import re
import numpy as np
import pandas as pd

# Splitting Implementation column
max = 0 # Finding maximum number of implementations
for i in Problems[['implementations']].values:
    l=len(i[0].split('\n'))
    if l > max:
        max = l
print('maximum number of implementaion for a problem :',max)

# Splitting the entities
imp = []
for i in Problems[['implementations']].values:
    l=len(i[0].split('\n'))
    t = i[0].split('\n')
    if l < max:
        d = max-l
        for i in range(d):
            t.append('')
    imp.append(t)

# Creating column names
columns = []
for i in range(1,max+1):
    columns.append('implementation_' + str(i))

imp_sparse = pd.DataFrame(np.array(imp),columns=columns)
df_impl = pd.concat([Problems,imp_sparse],axis=1).drop(['implementations'],axis=1)
print("{} number of implementation columns are created".format(max))

# Splitting recommended books column
max = 0 # Finding maximum number of recommended books
for i in Problems[['recommended_books']].replace(np.nan, '').values:
    l=len(i[0].split('\n'))
    if l > max:
        max = l
print('maximum number of recommended_books for a problem :',max)
max_recommended_book = max

rec = []
for i in Problems[['recommended_books']].replace(np.nan, '').values:
    l=len(i[0].split('\n'))
    t = i[0].split('\n')
    if l < max:
        d = max-l
        for i in range(d):
            t.append('')
    rec.append(t)

columns = []
for i in range(1,max+1):
    columns.append('recommended_book_' + str(i))

rec_sparse = pd.DataFrame(np.array(rec),columns=columns)
df_impl_rec = pd.concat([df_impl,rec_sparse],axis=1).drop(['recommended_books'],axis=1)
print("{} number of recommended book columns are created".format(max))

# Splitting related problem column
max = 0 # Finding maximum number of related problem
for i in Problems[['related_problems']].values:
    l=len(i[0].split('\n'))
    if l > max:
        max = l
print('maximum number of related_problems for a problem : ',max)

rel = []
for i in Problems[['related_problems']].values:
    l=len(i[0].split('\n'))
    t = i[0].split('\n')
    if l < max:
        d = max-l
        for i in range(d):
            t.append('')
    rel.append(t)

columns = []
for i in range(1,max+1):
    columns.append('related_problem_' + str(i))

rel_sparse = pd.DataFrame(np.array(rel),columns=columns)
df_impl_rec_rel = pd.concat([df_impl_rec,rel_sparse],axis=1).drop(['related_problems'],axis=1)
print("{} number of related problem columns are created".format(max))

# Splitting implementation into name, rating, url
Problems = df_impl_rec_rel
Problems.replace(np.nan, '', inplace=True)

def implementation_splitter(x,tag):
    temp = x.split(' | ')
    if (len(temp) > 2):
        if (tag != 3):
            return temp[tag]
        else:
            return " | ".join(temp[tag:])
    else:
        return ''

for imp in [i for i in Problems.columns.tolist() if re.search("implementation_[\d]+", i)]:
    Problems[imp + '_name'] = Problems[imp].apply(lambda x:implementation_splitter(x,0))
    Problems[imp + '_rating'] = Problems[imp].apply(lambda x:implementation_splitter(x,1))
    Problems[imp + '_url'] = Problems[imp].apply(lambda x:implementation_splitter(x,2))
    Problems[imp + '_languages'] = Problems[imp].apply(lambda x:implementation_splitter(x,3))
    Problems.drop(imp, axis=1, inplace=True)

# Splitting languages into multiple columns    
lang_cols = [i for i in Problems.columns.tolist() if re.search('implementation_[\d]+_languages', i)]
for ci in lang_cols:
    max = 0 # Finding maximum number of languages in implementations
    for i in Problems[[ci]].values:
        l=len(i[0].split(' | '))
        if l > max:
            max = l
    print('maximum number of implementaion for a {} :'.format(ci),max)
    
    columns = []
    for i in range(1,max+1):
        columns.append(ci[:-1] + "_" + str(i))
        
    imp_languages = []
    for i in Problems[[ci]].values:
        l=len(i[0].split(' | '))
        t = i[0].split(' | ')
        if l < max:
            d = max-l
            for i in range(d):
                t.append('')
        imp_languages.append(t)
    lang_sparse = pd.DataFrame(np.array(imp_languages),columns=columns)
    Problems = pd.concat([Problems,lang_sparse],axis=1).drop([ci],axis=1)
    

# Splitting recommended_book into name, url
def recommended_book_splitter(x,tag):
    temp = x.split(' | ')
    if len(temp) > 1:
        return temp[tag]
    else:
        return ''

for rec in [i for i in Problems.columns.tolist() if re.search("recommended_book_[\d]+", i)]:
    Problems[rec + '_name'] = Problems[rec].apply(lambda x:recommended_book_splitter(x,0))
    Problems[rec + '_url'] = Problems[rec].apply(lambda x:recommended_book_splitter(x,1))
    Problems.drop(rec, axis=1, inplace=True)

# Splitting related_problems into name, url
def related_problem_splitter(x,tag):
    temp = x.split(' | ')
    if len(temp) > 1:
        return temp[tag]
    else:
        return ''

for rel in [i for i in Problems.columns.tolist() if re.search("related_problem_[\d]+", i)]:
    Problems[rel + '_name'] = Problems[rel].apply(lambda x:related_problem_splitter(x,0))
    Problems[rel + '_url'] = Problems[rel].apply(lambda x:related_problem_splitter(x,1))
    Problems.drop(rel, axis=1, inplace=True)

# Splitting book column
df_books = Problems[[i for i in Problems.columns.tolist() if re.search("recommended_book_[\d]+_name", i)]]

def book_split_name_authors(x,idx):
    if type(x) == float:
        l = [np.nan, np.nan]
        return(l[idx])
    else:
        l = x.split(' by ')
        if len(l) == 2:
            return(l[idx].strip())
        else:
            l = [x,x]
            return(l[idx])

df_new = pd.DataFrame()
for i in df_books.columns:
    df_new[i] = df_books[i].apply(lambda x:book_split_name_authors(x, 0))
    df_new[i[:-4] + 'authors'] = df_books[i].apply(lambda x:book_split_name_authors(x, 1))
    df_new[i[:-4] + 'url'] = Problems[i[:-4] + 'url']

max_number_of_authors = 4
def authors_split(x,idx):
    global max_number_of_authors
    if type(x) == float:
        l = [np.nan] * max_number_of_authors
        return(l[idx])
    else:
        lt = re.split(" and |,", x)
        l = [w.strip() for w in lt if len(w) > 2]
        if len(l) > max_number_of_authors:
            print("Error in definition(Function: 'authors_split')\n",x)
        if len(l) == 2:
            l.append(np.nan)
            l.append(np.nan)
            return(l[idx])
        if len(l) == 1:
            l.append(np.nan)
            l.append(np.nan)
            l.append(np.nan)
            return(l[idx])
        if len(l) == 3:
            l.append(np.nan)
            return(l[idx])
        if len(l) == 4:
            return(l[idx])

for i in [i[:-4] + 'authors' for i in df_books.columns]:
    for j in range(max_number_of_authors):
        df_new[i[:-7] + 'author_' + str(j+1)] = df_new[i].apply(lambda x:authors_split(x,j))

book_cols = []
for i in range(1,max_recommended_book + 1):
    book_cols.append('recommended_book_' + str(i) + '_name')
    for j in range(1,max_number_of_authors+1):
        book_cols.append('recommended_book_' + str(i) + '_author_' + str(j))
    book_cols.append('recommended_book_' + str(i) + '_url')    
other_cols = [i for i in Problems.columns.tolist() if not re.search("recommended_book_", i)]

Processed = pd.concat([Problems[other_cols],df_new[book_cols]], axis=1)
try:
   processedname = sys.argv[2]
except IndexError:
   processedname = "RDFMapReadyFile.csv"
# Ordering the columns
imp_cols = [i for i in Processed.columns.tolist() if "implementation" in i]
COLS_part_1 = [i for i in Processed.columns.tolist() if "implementation" not in i]
COLS_part_2 = []
for i in range(1,13):
    COLS_part_2.extend([j for j in imp_cols if "implementation_"+ str(i) + "_" in j])
Processed = Processed[COLS_part_1 + COLS_part_2]    

# Exporting
Processed.to_csv(processedname, index=False)
print("Processed CSV file saved in the name :{}".format(processedname))
print("This File contains {} rows in {} columns".format(Processed.shape[0], Processed.shape[1]))