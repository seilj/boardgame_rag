from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import uuid
import os
from collections import OrderedDict
from langchain_teddynote import logging as logging_teddynote

from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    print("code for rag chain")