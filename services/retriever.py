import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import OrderedDict
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from elasticsearch import Elasticsearch
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
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chroma')

ES_URL = os.getenv("ES_URL")
ES_USER = os.getenv("ES_USER")
ES_PW = os.getenv("ES_PW")

class RetrieverManager():
    _retriever_doc_k = RETRIEVER_DOC_K
    _reranker_doc_k = RERANKER_DOC_K
    _chroma_persist_dir = CHROMA_DIR
    _chroma_collection_name = CHROMA_COLLECTION_NAME
    _es_index_name = ES_INDEX_NAME
    _embedding_model_name = EMBEDDING_MODEL_NAME

    _cache = OrderedDict()  # 캐시 저장소
    _cache_max_size = 5  # 캐시 최대 크기

    def __init__(self, game_name):
        self.game_name = game_name
        self.embedding = OpenAIEmbeddings(model=self._embedding_model_name)
        self.retriever = self.create_retriever()

    def create_es_retriever(self):
        print("ES 검색기 생성 중...")
        es_client = Elasticsearch(
            ES_URL,
            basic_auth=(ES_USER, ES_PW),
            verify_certs=False  # SSL 인증서 검증 비활성화
        )
        es_store = ElasticsearchStore(
            es_connection=es_client,
            index_name=self._es_index_name,
            query_field="content",
            strategy=CustomBM25Strategy(),
        )

        es_bm25_retriever = es_store.as_retriever(
            search_kwargs={
                'k': self._retriever_doc_k,
                'filter': {
                    "bool": {
                        "must": [
                            {"term": {"game_name.keyword": self.game_name}}
                        ]
                    }
                }
            }
        )

        print("ES 검색기 생성 완료!")
        return es_bm25_retriever

    def create_chroma_retriever(self):
        print("Chroma 검색기 생성 중...")
        chroma_store = Chroma(persist_directory=self._chroma_persist_dir, embedding_function=self.embedding, collection_name=self._chroma_collection_name)
        chroma_retriever = chroma_store.as_retriever(search_kwargs={
            "k": self._retriever_doc_k,
            "filter": {
                "game_name": {
                    '$eq': self.game_name
                }
            }
        })

        print("Chroma 검색기 생성 완료!")
        return chroma_retriever

    def create_ensemble_retriever(self, chroma_retriever, es_retriever):
        ensemble_retriever = EnsembleRetriever(
            retrievers=[chroma_retriever, es_retriever],
            weights=[0.3, 0.7],
            id_key="id"
        )
        return ensemble_retriever
    
    def create_retriever(self):
        es_retriever = self.create_es_retriever()
        chroma_retriever = self.create_chroma_retriever()
        ensemble_retriever = self.create_ensemble_retriever(chroma_retriever, es_retriever)
        compressor = CohereRerank(model="rerank-multilingual-v3.0", top_n=self._reranker_doc_k)
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=ensemble_retriever
        )
        return retriever

if __name__ == "__main__":
    # 검색기 테스트
    retriever_manager = RetrieverManager(game_name="카탄")
    QUERY = "카탄 초보자를 위한 배치"
    results = retriever_manager.retriever.invoke(QUERY)
    for result in results:
        print(result)
