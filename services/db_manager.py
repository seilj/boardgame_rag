import os, json
from datetime import datetime
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from elasticsearch import Elasticsearch, helpers
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
load_dotenv()

ES_URL = os.getenv("ES_URL")
ES_USER = os.getenv("ES_USER")
ES_PW = os.getenv("ES_PW")
CHROMA_COLLECTION_NAME = "rulebook"
EMBEDDING_MODEL_NAME = "text-embedding-3-large"

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rulebooks')
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chroma')

def load_rulebook():
    rulebooks_info = []
    for root, _, files in os.walk(PDF_DIR):
        for file in files:
            if not file.endswith('.pdf'):
                continue
            relative_path = os.path.relpath(root, PDF_DIR)
            path_parts = relative_path.split(os.sep)  # 디렉토리 계층 분리
            file_path = os.path.join(root, file)
            rulebooks_info.append({"file_path": file_path, "game_name": path_parts[0]})

    return rulebooks_info

def split_rulebook(info):
    file_path = info["file_path"]
    game_name = info["game_name"]
    loader = PyMuPDFLoader(file_path)
    document = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splitted_docs = text_splitter.split_documents(document)
    chunks = [{"content": doc.page_content, "metadata": {"page": doc.metadata["page"] + 1, "file_path": file_path, "game_name": game_name}} for doc in splitted_docs]
    return get_context(document, chunks)

def get_context(document, chunks):
    context_prompt = """
    <document>
    {document}
    </document>
    보드게임 규칙과 관련된 document가 있습니다. 위 document의 일부에 해당하는 context가 주어집니다.
    전체 document 내 chunk의 검색결과를 개선하기 위해 두 문장 이내의 간결한 context를 제공하세요.
    또, 주어진 chunk가 document의 어느 부분을 설명하고 있는지 "게임 소개", "구성물 및 준비", "게임 진행", "종료 및 승리 조건" 네 category 중 하나로 분류해주세요.
    다음 가이드라인을 **반드시** 지켜 주세요.
    - chunk가 flavor text나 credit 등 게임 규칙과 직접적으로 관련이 없는 텍스트인 경우 context와 category 모두 "None"으로 출력해주세요.
    - context와 category를 key로 가지는 json형식으로 출력해주세요. json 출력외에 불필요한 정보는 아무것도 출력하지 마세요.
        출력예시: {{{{ "context": "context content", "category": "category content" }}}}
    - context에는 chunk의 전후 맥락, chunk가 설명하는 대상이나 포함된 섹션 등의 global한 정보를 document를 참고하여 간결하게 작성하세요.
    """
    document_content = ""
    for page in document:
        document_content += page.page_content
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", context_prompt.format(document=document_content)),
            ("user", "#chunk: {chunk}")
        ]
    )

    chain = prompt | llm | StrOutputParser()

    context_chunks = []
    for chunk in chunks:
        response = chain.invoke({"chunk": chunk["content"]})
        print(f"chunk: {chunk["content"]}\nresponse: {response}")
        response_dict = json.loads(response)
        metadata = chunk["metadata"]
        metadata["category"] = response_dict.get("category")
        context_chunks.append(
            {
                "content": f"#본문: {chunk["content"]}\n#설명: {response_dict.get("context")}",
                "metadata": metadata
            }
        )
    
    return context_chunks



def index_rulebook(chunks, update=False):
    """
    룰북 데이터를 Elasticsearch에 인덱싱하고, alias를 업데이트합니다.

    Args:
        chunks (list): Elasticsearch에 인덱싱할 문서 데이터 목록.
    """
    print(f"<룰북 데이터 Elasticsearch 색인> 시작")

    # Elasticsearch 클라이언트 설정
    es = Elasticsearch(
        [ES_URL],
        basic_auth=(ES_USER, ES_PW)
    )

    # 고유한 인덱스 이름 생성 (현재 시간 기반)
    current_time = datetime.now()
    current_time_str = current_time.strftime("%Y.%m.%d-%H.%M.%S.%f")[:-3]
    INDEX_NAME = f"rulebooks-index-{current_time_str}"

    if(update):
        existing_data = [hits["_source"] for hits in es.search(index=INDEX_NAME, size=10000)["hits"]["hits"]]
        chunks.extend(existing_data)
    
    # id = 0
    # for chunk in chunks:
    #     chunk["id"] = id
    #     id += 1

    # Elasticsearch 문서 생성
    es_docs = [
        {"_index": INDEX_NAME, "_source": chunk}
        for chunk in chunks
    ]

    # 색인 작업 수행
    print(f"└ 색인 이름: {INDEX_NAME}")
    success, failed = helpers.bulk(
        es,
        es_docs,
        raise_on_error=False,
        raise_on_exception=False
    )
    print(f"└ 성공한 문서 수: {success}")
    print(f"└ 실패한 문서 수: {failed}")

    # Alias 업데이트
    print(f"<alias 변경> 시작")
    ALIAS_NAME = "rulebooks-index-latest"

    # 기존 alias 제거
    if es.indices.exists_alias(name=ALIAS_NAME):
        old_index = es.indices.get_alias(name=ALIAS_NAME)
        for old_index_name in list(old_index.keys()):
            es.indices.delete_alias(index=old_index_name, name=ALIAS_NAME)
        print("└ 기존 alias 삭제")

    # 새 인덱스에 alias 설정
    es.indices.put_alias(index=INDEX_NAME, name=ALIAS_NAME)
    print(f"<alias 변경> 완료")

    print(f"<룰북 데이터 Elasticsearch 색인> 완료")

def save_to_chroma(chunks, update=False):
    print("Chroma db 저장중...")
    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
    chroma_store = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding, collection_name=CHROMA_COLLECTION_NAME)
    if not update:
        all_ids = chroma_store.get()["ids"]
        if all_ids:
            chroma_store.delete(ids=all_ids)
    docs = [Document(
        page_content=chunk["content"],
        metadata=chunk["metadata"]
    ) for chunk in chunks]
    chroma_store.add_documents(docs)
    print("Chroma db 저장 완료")

def set_db():
    rulebooks_info = load_rulebook()
    chunks = []
    for info in rulebooks_info:
        chunks.extend(split_rulebook(info))

    for id, chunk in enumerate(chunks):
        chunk["metadata"]["id"] = id
        
    index_rulebook(chunks)
    save_to_chroma(chunks)

def es_to_chroma():
    es = Elasticsearch(ES_URL, basic_auth=(ES_USER, ES_PW))
    es_data = es.search(index="rulebooks-index-latest", size=10000)
    chunks = [hits["_source"] for hits in es_data["hits"]["hits"]]
    save_to_chroma(chunks)

if __name__ == "__main__":
    set_db()
    # es_to_chroma()