
import re
import pandas as pd
import bs4
import requests
import spacy
from spacy import displacy

from spacy.matcher import Matcher 
from spacy.tokens import Span 

from fuzzywuzzy import fuzz

import networkx as nx

import matplotlib.pyplot as plt
from tqdm import tqdm



def search(nome=None, lim=50):
    if nome:
        nlp = spacy.load('en_core_web_sm')

        pd.set_option('display.max_colwidth', 200)
        #%matplotlib inline


        # import wikipedia sentences
        candidate_sentences = pd.read_csv("wiki_sentences_v2.csv")
        candidate_sentences.shape

        doc = nlp("the drawdown process is governed by astm standard d823")

        for tok in doc:
          print(tok.text, "...", tok.dep_)

        def get_entities(sent):
          ## chunk 1
          ent1 = ""
          ent2 = ""

          prv_tok_dep = ""    # dependency tag of previous token in the sentence
          prv_tok_text = ""   # previous token in the sentence

          prefix = ""
          modifier = ""

          #############################################################
          
          for tok in nlp(sent):
            ## chunk 2
            # if token is a punctuation mark then move on to the next token
            if tok.dep_ != "punct":
              # check: token is a compound word or not
              if tok.dep_ == "compound":
                prefix = tok.text
                # if the previous word was also a 'compound' then add the current word to it
                if prv_tok_dep == "compound":
                  prefix = prv_tok_text + " "+ tok.text
              
              # check: token is a modifier or not
              if tok.dep_.endswith("mod") == True:
                modifier = tok.text
                # if the previous word was also a 'compound' then add the current word to it
                if prv_tok_dep == "compound":
                  modifier = prv_tok_text + " "+ tok.text
              
              ## chunk 3
              if tok.dep_.find("subj") == True:
                ent1 = modifier +" "+ prefix + " "+ tok.text
                prefix = ""
                modifier = ""
                prv_tok_dep = ""
                prv_tok_text = ""      

              ## chunk 4
              if tok.dep_.find("obj") == True:
                ent2 = modifier +" "+ prefix +" "+ tok.text
                
              ## chunk 5  
              # update variables
              prv_tok_dep = tok.dep_
              prv_tok_text = tok.text
          #############################################################

          return [ent1.strip(), ent2.strip()]

        entity_pairs = []

        for i in tqdm(candidate_sentences["sentence"]):
          entity_pairs.append(get_entities(i))

        entity_pairs[10:20]

        def get_relation(sent):

          doc = nlp(sent)

          # Matcher class object 
          matcher = Matcher(nlp.vocab)

          #define the pattern 
          pattern = [{'DEP':'ROOT'}, 
                    {'DEP':'prep','OP':"?"},
                    {'DEP':'agent','OP':"?"},  
                    {'POS':'ADJ','OP':"?"}] 

          matcher.add("matching_1", None, pattern) 

          matches = matcher(doc)
          k = len(matches) - 1

          span = doc[matches[k][1]:matches[k][2]] 

          return(span.text)

        all_relations = [get_relation(i) for i in tqdm(candidate_sentences['sentence'])]

        pd.Series(all_relations).value_counts()[:50]

        # extract subject
        all_source = [i[0] for i in entity_pairs]

        # extract object
        all_target = [i[1] for i in entity_pairs]
        count = 0
        source = []
        target = []
        relations = []
        for e in entity_pairs:
            if fuzz.ratio(e[1], nome) >= lim:
                source.append(e[0])
                relations.append(all_relations[count])
                target.append(nome)
            count = count + 1

        kg_df = pd.DataFrame({'source':source, 'target':target, 'edge':relations})


        print(kg_df)

        G=nx.from_pandas_edgelist(kg_df[kg_df['target'].str.contains(nome)], "source", "target", 
                                  edge_attr=True, create_using=nx.MultiDiGraph())

        plt.figure(figsize=(12,12))
        pos = nx.spring_layout(G, k = 0.5) # k regulates the distance between nodes
        nx.draw(G, with_labels=True, node_color='skyblue', node_size=1500, edge_cmap=plt.cm.Blues, pos = pos)
        plt.show()
    else:
        raise Exception("Insira algum nome como parâmetro")