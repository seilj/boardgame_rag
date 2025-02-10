from elasticsearch.helpers.vectorstore import BM25Strategy
from typing import Any, Dict, Optional, Tuple, List

class CustomBM25Strategy(BM25Strategy):

    def es_query(
        self,
        *,
        query: Optional[str],
        query_vector: Optional[List[float]],
        text_field: str,
        vector_field: str,
        k: int,
        num_candidates: int,
        filter: List[Dict[str, Any]] = [],
    ) -> Dict[str, Any]:
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                text_field: {
                                    "query": query,
                                }
                            },
                        },
                    ],
                    "filter": filter,
                },
            },
        }


    def es_mappings_settings(
        self,
        *,
        text_field: str,
        vector_field: str,
        num_dimensions: Optional[int],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        
        similarity_name = "custom_bm25"

        mappings: Dict[str, Any] = {
            "properties": {
                text_field: {
                    "type": "text",
                    "similarity": similarity_name,
                    "term_vector": "with_positions_offsets_payloads",
                    "analyzer": "nori_analyzer",
                },
            },
        }

        bm25: Dict[str, Any] = {
            "type": "BM25",
        }
        if self.k1 is not None:
            bm25["k1"] = self.k1
        if self.b is not None:
            bm25["b"] = self.b
        settings = {
            "similarity": {
                similarity_name: bm25,
            },
        }

        return mappings, settings