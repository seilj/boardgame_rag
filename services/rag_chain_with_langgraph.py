import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.retriever_manager import RetrieverManager
from typing import List, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain.schema import Document
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import StreamWriter

class RAGState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    messages: Annotated[List[BaseMessage], add_messages]
    game_name: str
    retrieved_docs: List[Document]

def retrieve(state: RAGState):
    question = state["messages"]
    game_name = state["game_name"]
    retriever_manager = RetrieverManager(game_name)
    retrieved_docs = retriever_manager.retriever.invoke(question)

    return {
        "game_name": game_name,
        "retrieved_docs": retrieved_docs
    }

def answer_generate(state: RAGState, writer: StreamWriter):
    messages = state["messages"]
    docs = state["retrieved_docs"]

    system_prompt_text = """
    당신은 보드게임 규칙에 대한 질문에 답변하는 전문가입니다.
    주어진 rule_document를 토대로 주어진 question에 답하여주세요. 답변 시 아래 가이드를 **반드시** 참고합니다.
    - 질문과 관련있는 rule_document가 없는 경우 "죄송합니다. 관련 내용을 규칙서에서 확인할 수 없습니다."라고 답변합니다.
    - rule_document에서 게임 규칙과 관련없는 내용은 무시하며, 직접적으로 게임 규칙에 대해 설명하는 부분만을 참고합니다.
    - rule_document에 존재하는 내용으로만 답변하며, 절대 추측성, 주관적 내용을 답변에 포함해서는 안됩니다.
    """

    user_prompt_text = """
    ### rule_document
    {rule_document}
    ### question
    {question}
    """

    prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_text),
                ("user", user_prompt_text)
            ]
        )
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    chain = prompt | llm | StrOutputParser()

    full_response = ""
    for chunk in chain.stream():
        writer(chunk)
        full_response += chunk

    return {"messages": [AIMessage(content=full_response)]}


def create_rag_graph():
    
    workflow = StateGraph(RAGState)

    # 노드 추가
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("answer_generate", answer_generate)
    
    # 엣지 연결
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "answer_generate")
    workflow.add_edge("answer_generate", END)

    # workflow.add_conditional_edges(
    #     "relevance_extract",
    #     relevance_evaluate,
    #     {"True": "answer_generate", "False": "rewrite_query"}
    # )

    # workflow.add_edge("rewrite_query", "keyword_extract")
    
    # 컴파일
    return  workflow.compile()

if __name__ == "__main__":
    pass