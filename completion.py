from enum import Enum
from dataclasses import dataclass
import openai
from openai import OpenAI

client = OpenAI()
from moderation import moderate_message
from typing import Optional, List
from constants import (
    BOT_INSTRUCTIONS,
    BOT_NAME,
    EXAMPLE_CONVOS,
)
import discord
from base import Message, Prompt, Conversation
from utils import split_into_shorter_messages, close_thread, logger

import tiktoken
import os
from dotenv import load_dotenv

import MySQLdb
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import time
from requests.exceptions import Timeout

import asyncio

load_dotenv()

encoding = tiktoken.encoding_for_model("gpt-4")

def simple_token_counter(text):
    token_count = 0
    for word in text.split():
        # Very simplified: count every character or punctuation as a separate token
        token_count += len(word)
    return token_count

def limit_tokens(strings, max_tokens):
    total_tokens = 0
    limited_strings = []
    for string in strings:
        tokens_in_string = simple_token_counter(string)
        if total_tokens + tokens_in_string > max_tokens:
            break
        total_tokens += tokens_in_string
        limited_strings.append(string)
    return limited_strings

def limit_string_tokens(string, max_tokens):
    if len(string) > max_tokens:
        string = string[:max_tokens]
    return string

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = len(encoding.encode(string))
    return num_tokens

MY_BOT_NAME = BOT_NAME
MY_BOT_EXAMPLE_CONVOS = EXAMPLE_CONVOS

class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3
    MODERATION_FLAGGED = 4
    MODERATION_BLOCKED = 5


@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]
