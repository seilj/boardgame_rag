import sys, os
from collections import OrderedDict
from elasticsearch import Elasticsearch
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_elasticsearch import ElasticsearchStore
from services.custom_es_store import CustomBM25Strategy
from langchain.retrievers import EnsembleRetriever
from langchain_cohere import CohereRerank
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever

from dotenv import load_dotenv
load_dotenv()

RETRIEVER_DOC_K = 10
RERANKER_DOC_K = 5
EMBEDDING_MODEL_NAME = "text-embedding-3-large"
CHROMA_COLLECTION_NAME = "rulebook"
ES_INDEX_NAME = "rulebooks-index-latest"

ES_URL = os.getenv("ES_URL")
ES_USER = os.getenv("ES_USER")
ES_PW = os.getenv("ES_PW")
