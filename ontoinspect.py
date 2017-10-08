from rdflib import Graph,XSD,Literal
import datetime
import rdflib
from rdflib.namespace import Namespace,RDFS,RDF,FOAF
from rdflib.extras.describer import Describer
import ontospy
from rdflib import URIRef
import nltk
import rdflib
from nltk.tag import pos_tag
import re
import urllib.request
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from bisect import bisect_left
import urllib
import datetime
 
stop = stopwords.words('portuguese')
 
url = 'http://portalsaude.saude.gov.br/index.php/o-ministerio/principal/secretarias/svs/zika'
text = "O zika é uma doença viral aguda, transmitida principalmente, pelos mosquitos Ae. Aegypti e Ae. albopictus, caracterizada por exantema maculopapular pruriginoso, febre intermitente, hiperemia conjuntival não purulenta e sem prurido, artralgia, mialgia e dor de cabeça. A maior parte dos casos apresentam evolução benigna e os sintomas geralmente desaparecem espontaneamente após 3-7 dias. No entanto, observa-se a ocorrência de óbitos pelo agravo, aumento dos casos de microcefalia e de manifestações neurológicas associadas à ocorrência da doença."

#Extrair o texto visivel do html
def visible_text_from_url(url):
    req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    con = urllib.request.urlopen(req)
    soup = BeautifulSoup(con.read())
    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
    return soup.getText()
 
def ie_preprocess(document):
    document = ' '.join([i for i in document.split() if i not in stop])
    sentences = nltk.sent_tokenize(document)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    #sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences

def get_reifications(onto):
    reifications = []
    for i in onto.classes:
        if not i.children():
            reifications.insert(len(reifications),i)
    return reifications

def get_text_sentences(text):
    sentences = nltk.sent_tokenize(' '.join([i for i in text.split()]))
    return [nltk.word_tokenize(sent) for sent in sentences]

def article_annotation(document,concept,authorRef,presentation):
    AO = Namespace("http://smiy.sourceforge.net/ao/rdf/associationontology.owl")
    PAV = Namespace("http://cdn.rawgit.com/pav-ontology/pav/2.0/pav.owl")
    #ANN = Namespace("https://www.w3.org/2000/10/annotation-ns#annotates")
    AOF = Namespace("http://annotation-ontology.googlecode.com/svn/trunk/annotation-foaf.owl")

    graph = Graph()
    graph.bind('aof',AOF)
    graph.bind('ao',AO)
    #graph.bind('ann',ANN)
    graph.bind('pav',PAV)
    lang = 'pt'
    d = Describer(graph,base = "http://organizacao.com")
    d.value(RDFS.comment,presentation, lang=lang)
    
    #d.rel(RDF.type,ANN.base)#De onde eu tirei isso mds?
    #d.rel(RDF.type,ANN.Annotation)
    d.rel(RDF.type,AO.Annotation)
    d.rel(AOF.annotatesDocument,document)
    d.rel(AO.hasTopic,concept)
    d.rel(PAV.createdOn,Literal(datetime.datetime.now(),datatype=XSD.date))
    d.rel(PAV.createdB,authorRef)

    return d

def print_graph(g):
    for s, p, o in g:
        print((s, p, o))

def gen_article_annotations(text,concept_dict,base,author,description):
    sentences = get_text_sentences(text)
    concepts_found = list()
    search_remaining_concepts = [nltk.word_tokenize(i) for i in concept_dict.keys()]
    annotations = list()

    while len(search_remaining_concepts) > 0:
        biggest_concept_lenght = len(max(search_remaining_concepts,key = len))
        biggest_concept_items = [x for x in search_remaining_concepts if len(x) == biggest_concept_lenght]
        search_remaining_concepts = [x for x in search_remaining_concepts if x not in biggest_concept_items]

        for sentence in sentences:
            if len(sentence) >= biggest_concept_lenght:
                for k in range(0,len(sentence) - biggest_concept_lenght):
                    biggest_concept_items_cp = biggest_concept_items
                    for concept in biggest_concept_items_cp:
                        if concept not in concepts_found:
                            #Compara o conceito com os itens  de -(k + biggest_concept_lenght) até -k
                            if [i.upper() for i in concept] == [i.upper() for i in sentence[-(k + biggest_concept_lenght):-k]]:
                                concepts_found.insert(len(concepts_found),concept)
                                annotations.append(article_annotation(url,concept_dict[' '.join(concept)].uri,author,description).graph)
                                print('\n')
                                biggest_concept_items.remove(concept)
    return annotations

onto = ontospy.Ontospy("root-ontology.owl")
web_concepts = get_reifications(onto)
concept_dict = dict()

for i in web_concepts:
    text_concept = str(i.uri).partition('#')[-1].replace('_',' ')
    concept_dict[text_concept] = i

for g in gen_article_annotations(text,concept_dict,"www.semanticdev.com","Vitor Silva","Anotação semântica para textos jornalísticos"):
    g.commit()
    g.parse("base.rdf",format='xml')
    #g.serialize(destination='base.txt')


