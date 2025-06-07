# Copyright 2025 Claudionor N. Coelho Jr

import os
import time
import concurrent.futures
from functools import lru_cache

import anthropic
from boltons.iterutils import backoff
from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from requests.exceptions import HTTPError

from .utils import fatal_error

MAX_TOKENS = int(os.getenv('UNITTENX_MAX_TOKENS', 8192))
USE_RATE_LIMITER = int(os.getenv('UNITTENX_USE_RATE_LIMITER', 0))

@lru_cache(maxsize=4)
def get_model(model_name:str, temperature:float=0):
    if USE_RATE_LIMITER:
        rate_limiter = InMemoryRateLimiter(
            requests_per_second=1,  # <-- Super slow! We can only make a request once every 10 seconds!!
            check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
            max_bucket_size=10,  # Controls the maximum burst size.
        )
    else:
        rate_limiter = None

    if model_name == "azure":
        open_api_key = os.environ.get("AZURE_OPENAI_KEY", "")
        azure_endpoint = (
                os.environ["AZURE_OPENAI_API_ENDPOINT"] +
                "/openai/deployments/gpt-4o/chat/completions?"
                "api-version=2024-02-15-preview"
        )
        return AzureChatOpenAI(
            azure_deployment="gpt-4o",
            api_version=azure_endpoint,
            openai_api_key=open_api_key,
            temperature=temperature,
            max_retries=2,
            max_tokens=MAX_TOKENS
        )
    elif model_name == "openai":
        return ChatOpenAI(
            temperature=temperature,
            model_name="gpt-4o",
            max_tokens=MAX_TOKENS
        )
    elif model_name == "anthropic":
        return ChatAnthropic(
            temperature=temperature,
            model_name="claude-3-5-sonnet-20241022",
            max_tokens=MAX_TOKENS,
            rate_limiter=rate_limiter
        )
    elif "ollama:" in model_name:
        return ChatOpenAI(
            base_url="http://localhost:11434/v1",
            temperature=temperature,
            model_name=':'.join(model_name.split(':')[1:]),
            api_key="ollama",
            max_tokens=MAX_TOKENS,
            rate_limiter=rate_limiter
        )
    else:
        return ChatOllama(
            temperature=temperature,
            model=model_name,
            max_tokens=MAX_TOKENS
        )

class GetModel():
    def __init__(
            self,
            model_name: str,
            temperature:float=0,
            max_retries:int=5,
            backoff_factor:int=2,
            timeout:int=60):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.model_name = model_name
        self.model = get_model(model_name, temperature)

    def invoke(self, *largs, **kwargs):
        try:
            start_time = time.time()
            retries = 0
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.model.invoke, *largs, **kwargs)
                while retries < self.max_retries:
                    try:
                        return future.result(timeout=self.timeout)
                    except concurrent.futures.TimeoutError:
                        elapsed_time = time.time() - start_time
                        if elapsed_time > self.timeout:
                            print("Timeout reached. Stopping retries.")
                            fatal_error(self.model_name)
                        retries += 1
                        wait_time = self.backoff_factor ** retries
                        print(f"Timeout error: retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    except anthropic.RateLimitError:
                        retries += 1
                        wait_time = self.backoff_factor ** retries
                        elapsed_time = time.time() - start_time
                        if elapsed_time + wait_time > self.timeout:
                            print("Timeout reached. Stopping retries.")
                            fatal_error('exception in model')
                        print(f"Rate limit error: retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    except HTTPError as http_err:
                        if http_err.response.status_code in [429, 529]:  # Rate limit error, internal error
                            retries += 1
                            wait_time = self.backoff_factor ** retries
                            elapsed_time = time.time() - start_time
                            if elapsed_time + wait_time > self.timeout:
                                print("Timeout reached. Stopping retries.")
                                fatal_error('exception in model')
                            print(f"Rate limit error: retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"HTTP error occurred: {http_err}")
                            fatal_error('exception in model')
                    except Exception as err:
                        print(f"An error occurred: {err}")
                        fatal_error('exception in model')
        except Exception as err:
            fatal_error(err)


def _get_model(model_name: str, temperature=0):
    '''
        Returns model corresponding to model_name.

        :param model_name: model name (openai or anthropic).
        :param temperature: model temperature.

        :return: LangChain model.
    '''

    def get_model_with_retries_and_timeout(max_retries=5, backoff_factor=2, timeout=60):
        start_time = time.time()
        retries = 0
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(get_model)
            while retries < max_retries:
                try:
                    return future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > timeout:
                        print("Timeout reached. Stopping retries.")
                        break
                    retries += 1
                    wait_time = backoff_factor ** retries
                    print(f"Timeout error: retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                except anthropic.RateLimitError:
                    retries += 1
                    wait_time = backoff_factor ** retries
                    elapsed_time = time.time() - start_time
                    if elapsed_time + wait_time > timeout:
                        print("Timeout reached. Stopping retries.")
                        fatal_error('exception in model')
                    print(f"Rate limit error: retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                except HTTPError as http_err:
                    if http_err.response.status_code in [429, 529]:  # Rate limit error, internal error
                        retries += 1
                        wait_time = backoff_factor ** retries
                        elapsed_time = time.time() - start_time
                        if elapsed_time + wait_time > timeout:
                            print("Timeout reached. Stopping retries.")
                            fatal_error('exception in model')
                        print(f"Rate limit error: retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"HTTP error occurred: {http_err}")
                        fatal_error('exception in model')
                except Exception as err:
                    print(f"An error occurred: {err}")
                    fatal_error('exception in model')
        return None

    return get_model_with_retries_and_timeout()
