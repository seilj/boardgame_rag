import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import OrderedDict
from langchain_openai import OpenAIEmbeddings
from services.db_manager import get_es_store, get_chroma_store
from langchain.retrievers import EnsembleRetriever
from langchain_cohere import CohereRerank
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever

from dotenv import load_dotenv
load_dotenv()

RETRIEVER_DOC_K = 5
RERANKER_DOC_K = 5
CHROMA_COLLECTION_NAME = "rulebook"
ES_INDEX_NAME = "rulebooks-index-latest"
# ES_INDEX_NAME = "srt-test-latest"

class RetrieverManager():
    _retriever_doc_k = RETRIEVER_DOC_K
    _reranker_doc_k = RERANKER_DOC_K
    _chroma_collection_name = CHROMA_COLLECTION_NAME
    _es_index_name = ES_INDEX_NAME

    _cache = OrderedDict()  # 캐시 저장소
    _cache_max_size = 5  # 캐시 최대 크기

    def __init__(self, game_name):
        self.game_name = game_name
        if game_name in self._cache:
            self.retriever = self._cache[game_name]
            self._cache.move_to_end(game_name)
        else:
            self.retriever = self.create_retriever()
            self._cache[game_name] = self.retriever
            if len(self._cache) > self._cache_max_size:
                self._cache.popitem(last=False)  # 가장 오래된 항목 제거

    def create_es_retriever(self):
        print("ES 검색기 생성 중...")
        es_store = get_es_store(self._es_index_name)

        es_bm25_retriever = es_store.as_retriever(
            search_kwargs={
                'k': self._retriever_doc_k,
                'filter': {
                    "bool": {
                        "must": [
                            {"term": {"metadata.game_name.keyword": self.game_name}}
                        ]
                    }
                }
            }
        )

        print("ES 검색기 생성 완료!")
        return es_bm25_retriever

    def create_chroma_retriever(self):
        print("Chroma 검색기 생성 중...")
        chroma_store = get_chroma_store(self._chroma_collection_name)
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
        print("앙상블 검색기 생성 중...")
        ensemble_retriever = EnsembleRetriever(
            retrievers=[chroma_retriever, es_retriever],
            weights=[0.3, 0.7],
            id_key="id"
        )
        print("앙상블 검색기 생성 완료!")
        return ensemble_retriever
    
    def create_retriever(self):
        print(f"{self.game_name} 규칙서 검색기 생성을 시작합니다.")
        es_retriever = self.create_es_retriever()
        chroma_retriever = self.create_chroma_retriever()
        ensemble_retriever = self.create_ensemble_retriever(chroma_retriever, es_retriever)
        compressor = CohereRerank(model="rerank-multilingual-v3.0", top_n=self._reranker_doc_k)
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=ensemble_retriever
        )
        print("검색기 생성이 완료되었습니다.")
        return retriever

if __name__ == "__main__":
    # 검색기 테스트
    retriever_manager = RetrieverManager(game_name="달무티")
    QUERY = "달무티"
    results = retriever_manager.retriever.invoke(QUERY)
    for result in results:
        print(result)
