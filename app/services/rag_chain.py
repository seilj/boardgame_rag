import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import uuid
from services.retriever_manager import RetrieverManager

from dotenv import load_dotenv
load_dotenv()

store = {}

def limit_chat_history(chat_history):
    limit_turns = 3
    return chat_history[-2*limit_turns:]

def get_session_history(session_ids):
    print(f"[대화 세션ID]: {session_ids}")
    if session_ids not in store:
        store[session_ids] = ChatMessageHistory()
    return store[session_ids]

class RAGChain:
    # _system_prompt_text = """
    # 당신은 보드게임 규칙에 대한 질문에 답변하는 전문가입니다.
    # 주어진 rule_document를 토대로 주어진 question에 답하여주세요. 답변 시 아래 가이드를 **반드시** 참고합니다.
    # - 질문과 관련있는 rule_document가 없는 경우 "죄송합니다. 관련 내용을 규칙서에서 확인할 수 없습니다."라고 답변합니다.
    # - rule_document에서 게임 규칙과 관련없는 내용은 무시하며, 직접적으로 게임 규칙에 대해 설명하는 부분만을 참고합니다.
    # - rule_document에 존재하는 내용으로만 답변하며, 절대 추측성, 주관적 내용을 답변에 포함해서는 안됩니다.
    # """

    _system_prompt_text = """
    당신은 보드게임 규칙에 대한 질문에 답변하는 전문가입니다.
    주어진 rule_document를 토대로 주어진 question에 답하여주세요. 답변 시 아래 가이드를 **반드시** 참고합니다.
    - rule_document는 srt파일 형식을 지니고 있습니다. 주어진 rule_document의 text 부분을 참고하여 질문에 답변하고, 답변에 참고한 text의 start 값과 metadata의 vid 값을 이용해 다음과 같이 해당 설명의 링크를 표시해주세요:
        <영상주소: https://www.youtube.com/watch?v={{vid}}&t={{start}}s>
    - 질문과 관련있는 rule_document가 없는 경우 "죄송합니다. 관련 내용을 규칙서에서 확인할 수 없습니다."라고 답변합니다.
    - rule_document에서 게임 규칙과 관련없는 내용은 무시하며, 직접적으로 게임 규칙에 대해 설명하는 부분만을 참고합니다.
    - rule_document에 존재하는 내용으로만 답변하며, 절대 추측성, 주관적 내용을 답변에 포함해서는 안됩니다.
    """

    _user_prompt_text = """
    ### rule_document
    {rule_document}
    ### question
    {question}
    """
    
    def __init__(self, retriever_manager: RetrieverManager):
        self.retriever_manager = retriever_manager
        self.answer_generator = self.create_chain()

    def create_chain(self, model_name="gpt-4o-mini"):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._system_prompt_text),
                ("user", self._user_prompt_text)
            ]
        )
        llm = ChatOpenAI(model=model_name, temperature=0)
        chain =(
            {
                "question": itemgetter("question"),
                "rule_document": itemgetter("rule_document"),
                "chat_history": lambda x: limit_chat_history(x["chat_history"]),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        chain_with_history_session = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        return chain_with_history_session

    def invoke(self):
        pass

    def stream(self, input_dict):
        question = input_dict.get("question")
        session_id = input_dict.get("session_id", str(uuid.uuid4()))
        retrieved_docs = self.retriever_manager.retriever.invoke(question)

        for chunk in self.answer_generator.stream(
            {"rule_document": retrieved_docs, "question": question},
            config = {"configurable": {"session_id": session_id}}
        ):
            yield chunk

if __name__ == "__main__":
    # rag chain 테스트
    QUERY = "카드 구성이 어떻게 돼?"
    game_name = "달무티"
    retriever_manager = RetrieverManager(game_name)
    rag_chain = RAGChain(retriever_manager)
    for chunk in rag_chain.stream({"question": QUERY}):
        print(chunk, end="")