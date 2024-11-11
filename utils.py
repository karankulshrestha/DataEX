import os
from dotenv import load_dotenv
import requests
from tavily import TavilyClient
from strictjson import strict_json, strict_json_async
from openai import OpenAI
import serpapi


# Load environment variables from .env file
load_dotenv()



TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SERP_API_KEY = os.getenv('SERP_API_KEY')
SCARPI_API_KEY = os.getenv('SCARPI_API_KEY')


# Initialize Tavily client with API key
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)




def llm(system_prompt: str, user_prompt: str):

    response = openai_client.chat.completions.create(
        model='gpt-4o-mini',
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content


async def async_llm(system_prompt: str, user_prompt: str):
    ''' Here, we use OpenAI for illustration, you can change it to your own LLM '''
    # ensure your LLM imports are all within this function
    from openai import AsyncOpenAI
    
    # define your own LLM here
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model='gpt-4o-mini',
        temperature = 0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content




def generate_entities(user_question):

    prompt = f"""
                        Analyze the question and generate a list of entities like email, phone number and others etc mentioned by users for extracting relevant information.
                        Also analyze whether the question is about extracting information or general question.
                        if the question is about extracting information then return True. Otherwise False.

                        **user question:**

                        "{user_question}"
              """

    res = strict_json(system_prompt='You are a question anaylsis expert',
                      user_prompt=prompt,
                      output_format={
                          'question_status': f'if the question: {user_question} is about extracting information contains entity like email, phone, address or something like this then return True. Otherwise False, type: bool', 'entities': f'This list includes entities like email, phone numbers, and other details mentioned in the users question do not have space betwen the entities used underscore _ {user_question} for extraction., type: List[str]'},
                      llm=llm
                      )

    return res




async def extract_information(information, entities):

    prompt = f"""
                Extract information from the given information and make sure proper key and value is present in the output without any ##.

                **Information:**

                "{information}"
              """
    
    extract_data_format = {}
    
    for entity in entities:
        entity_prompt = f'Extract {entity} from the given information {information} and if not present return null, type: str'
        extract_data_format[entity] = entity_prompt
              

    res = await strict_json_async(system_prompt='You are a expert information extraction system',
                      user_prompt=prompt,
                      output_format=extract_data_format,
                      llm=async_llm
                      )

    return res



def get_serp(query):
    serpapi_client = serpapi.Client(api_key=SERP_API_KEY)
    
    results = serpapi_client.search({
        'engine': 'google',
        'q': query,
    })

    return results


def get_scrapi(query):
    payload = {'api_key': SCARPI_API_KEY, 'query': query, 'country_code': 'US', 'tld': 'TLD'}
    r = requests.get('https://api.scraperapi.com/structured/google/search', params=payload)
    return r




async def search_contact_details(query, entities):
    try:
        response = tavily_client.search(query)
        # serp_response = get_serp(query)
        scrapi_response = get_scrapi(query)
        dict_string = str(response) + " " + str(scrapi_response)
        extracted_data = await extract_information(dict_string, entities)
        return dict_string, extracted_data
    except Exception as e:
        return {"error": str(e)}