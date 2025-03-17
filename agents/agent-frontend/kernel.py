from typing import TypedDict, Annotated
import asyncio, json, os

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from typing import List, Optional
import aiohttp
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

class TenKParserPlugin:
    @kernel_function
    async def extract_fields(self, file_url) -> dict:
        """Parses the 10K PDF and extract the relevant fields from the document. Also produces a markdown representation of the document for adding to a vector store for RAG"""
        async with aiohttp.ClientSession() as session:
            template = """
            {
              "analyzer_id":"financial-analyzer20",
              "file_url": "${file_url}",
              "schema": {
              "description": "My custom 10K analyzer",  
              "tags": {
                "createdBy": "Vinod"
              },
              "config": {
                "enableFace": false,
                "enableOcr": true,
                "enableLayout": true,
                "enableBarcode": true,
                "enableFormula": false,
                "returnDetails": true
              },
              "fieldSchema": {
                "fields": {
                  "CompanyName": {
                    "type": "string",
                    "method": "extract",
                    "description": "Name of the company"
                  },
                  "TickerSymbol": {
                    "type": "string",
                    "method": "extract",
                    "description": "The symbol the company trades under"
                  },
                  "YearEnding": {
                    "type": "date",
                    "method": "extract",
                    "description": "The financial year ending date for this 10K filing" 
                  },
                  "CompanyAddress": {
                    "type": "string",
                    "method": "extract",
                    "description": ""
                  },
                  "TotalCurrentAssets": {
                    "type": "number",
                    "method": "extract",
                    "description": "The total current assets for the company for the current year from the balance sheet"
                  },
                  "TotalAssets": {
                    "type": "number",
                    "method": "extract",
                    "description": "The total  assets for the company for the current year from the balance sheet"
                  },
                  "TotalCurrentLiabilities": {
                    "type": "number",
                    "method": "extract",
                    "description": "The total current liabilities for the company for the current year from the balance sheet"
                  },
                  "TotalLiabilities": {
                    "type": "number",
                    "method": "extract",
                    "description": "The total liabilities for the company for the current year from the balance sheet"
                  },
                  "TotalStockholderEquity": {
                    "type": "number",
                    "method": "extract",
                    "description": "The total stockholder equity for the company for the current year from the balance sheet"
                  },
                  "NetEarnings": {
                    "type": "number",
                    "method": "extract",
                    "description": "The net earnings for the company for the current year from the income statement"
                  },
                  "NetEarningsPerShareDiluted": {
                    "type": "number",
                    "method": "extract",
                    "description": "The net earnings per share for the company for the current year from the income statement"
                  },
                  "NetEarningsPerShareBasic": {
                    "type": "number",
                    "method": "extract",
                    "description": "The net earnings per share for the company for the current year from the income statement"
                  },
                  "ComprehensiveIncome": {
                    "type": "number",
                    "method": "extract",
                    "description": "The comprehensive income for the company for the current year from the income statement"
                  },
                  "NetCashFlowFromOperatingActivities": {
                    "type": "number",
                    "method": "extract",
                    "description": "The net cash flow from operating activities for the company for the current year from the cash flow statement"
                  },
                  "NetCashFlowFromInvestingActivities": {
                    "type": "number",
                    "method": "extract",
                    "description": "The net cash flow from investing activities for the company for the current year from the cash flow statement"
                  },
                  "NetCashFlowFromFinancingActivities": {
                    "type": "number",
                    "method": "extract",
                    "description": "The net cash flow from financing activities for the company for the current year from the cash flow statement"
                  }, 
                  "IncomeStatement": {
                    "type": "array",
                    "method": "extract",
                    "items": {
                      "type": "object",
                      "properties": {
                        "CashAndCashEquivalents": {
                          "type": "number",
                          "method": "extract",
                          "description": "cash and cash equivalents for the current year from the income statement"
                        },
                        "ShortTermInvestments": {
                          "type": "number",
                          "method": "extract",
                          "description": "Short term investments for the current year from the income statement"
                        }, 
                        "AccountsReceivable": {
                          "type": "number",
                          "method": "extract",
                          "description": "Accounts receivable for the current year from the income statement"
                        }, 
                        "Inventory": {
                          "type": "number",
                          "method": "extract",
                          "description": "Inventory for the current year from the income statement"
                        },
                        "PrepaidExpenses": {
                          "type": "number",
                          "method": "extract",
                          "description": "Prepaid expenses for the current year from the income statement"
                        },
                        "OtherCurrentAssets": {
                          "type": "number",
                          "method": "extract",
                          "description": "Other current assets for the current year from the income statement"
                        },
                        "PropertyPlantAndEquipment": {
                          "type": "number",
                          "method": "extract",
                          "description": "Property plant and equipment for the current year from the income statement"
                        },
                        "Goodwill": {
                          "type": "number",
                          "method": "extract",
                          "description": "Goodwill for the current year from the income statement"
                        },
                        "IntangibleAssets": {
                          "type": "number",
                          "method": "extract",
                          "description": "Intangible assets for the current year from the income statement"
                        },
                        "LongTermInvestments": {
                          "type": "number",
                          "method": "extract",
                          "description": "Long term investments for the current year from the income statement"
                        },
                        "OtherAssets": {
                          "type": "number",
                          "method": "extract",
                          "description": "Other assets for the current year from the income statement"
                        },
                        "TotalAssets": {
                          "type": "number",
                          "method": "extract",
                          "description": "Total assets for the current year from the income statement"
                        },
                        "AccountsPayable": {
                          "type": "number",
                          "method": "extract",
                          "description": "Accounts payable for the current year from the income statement"
                        },
                        "AccruedLiabilities": {
                          "type": "number",
                          "method": "extract",
                          "description": "Accrued liabilities for the current year from the income statement"
                        },
                        "ShortTermDebt": {
                          "type": "number",
                          "method": "extract",
                          "description": "Short term debt for the current year from the income statement"
                        },
                        "LongTermDebt": {
                          "type": "number",
                          "method": "extract",
                          "description": "Long term debt for the current year from the income statement"
                        },
                        "DeferredRevenue": {
                          "type": "number",
                          "method": "extract",
                          "description": "Deferred revenue for the current year from the income statement"
                        },
                        "OtherLiabilities": {
                          "type": "number",
                          "method": "extract",
                          "description": "Other liabilities for the current year from the income statement"
                        },
                        "TotalLiabilities": {
                          "type": "number",
                          "method": "extract",
                          "description": "Total liabilities for the current year from the income statement"
                        },
                        "TotalStockholderEquity": {
                          "type": "number",
                          "method": "extract",
                          "description": "Total stockholder equity for the current year from the income statement"
                        }

                      }
                    }
                  }

                },
                "definitions": {}
              },
              "scenario": "document"
            }
            }

          """
            
            # Handle file_url being passed as a dictionary with a url property
            actual_url = file_url
            if isinstance(file_url, dict) and 'url' in file_url:
                actual_url = file_url['url']
            
            # Replace the file_url placeholder with the actual file_url
            template = template.replace("${file_url}", actual_url)
            
            # Convert the template string to a JSON object
            payload = json.loads(template)
            
            url = os.getenv("CU_PLUGIN_URL")
            
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"API request failed with status {response.status}: {error_text}")
                        return {
                            "error": f"API request failed with status {response.status}",
                            "details": error_text
                        }
                    
                    response_json = await response.json()
                    
                    if "fields" not in response_json:
                        print(f"Unexpected API response: {response_json}")
                        return {
                            "error": "Unexpected API response format",
                            "response": str(response_json)
                        }
                    
                    company_name = response_json["fields"].get("CompanyName", {})
                    company_address = response_json["fields"].get("CompanyAddress", {})
                    
                    return {
                        "CompanyName": company_name.get("valueString", "Unknown"),
                        "CompanyAddress": company_address.get("valueString", "Unknown"),
                        "FullResponse": response_json  # Include full response for debugging
                    }
            except Exception as e:
                print(f"Error calling document analysis API: {str(e)}")
                return {
                    "error": f"Error processing document: {str(e)}"
                }

# Singleton class to manage Semantic Kernel and chat session
class ChatSingleton:
    _instance = None
    _initialized = False
    _kernel = None
    _chat_completion = None
    _history = None
    _execution_settings = None
    _agent = None
    
    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = ChatSingleton()
            await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        if self._initialized:
            return
        
        #########################################
        # 1. Create the instance of the Kernel to register the plugin and service
        service_id = "agent"
        kernel = Kernel()
        kernel.add_plugin(TenKParserPlugin(), plugin_name="TenKParser")
        kernel.add_service(AzureChatCompletion(service_id=service_id, deployment_name=os.getenv("AOAI_DEPLOYMENT_NAME"), base_url=os.getenv("AOAI_BASE_URL"), api_key=os.getenv("AOAI_KEY")))


        # 2. Configure the function choice behavior to auto invoke kernel functions
        # so that the agent can automatically execute the menu plugin functions when needed
        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        # 3. Create the agent
        self._agent = ChatCompletionAgent(
            kernel=kernel,
            name="Host",
            instructions=os.getenv("AGENT_PROMPT"),
            arguments=KernelArguments(settings=settings),
        )

        # 4. Create a chat history to hold the conversation
        self._history = ChatHistory()
        
        # Enable planning
        self._execution_settings = AzureChatPromptExecutionSettings()
        self._execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        

        self._initialized = True
    
    def get_kernel(self):
        return self._kernel
    
    def get_chat_completion(self):
        return self._chat_completion
    
    def get_history(self):
        return self._history
    
    def get_execution_settings(self):
        return self._execution_settings
    
    def get_agent(self):
        return self._agent
    
    def clear_history(self):
        self._history = ChatHistory()

# Legacy function for backward compatibility, but now uses the singleton
async def init_kernel():
    chat_singleton = await ChatSingleton.get_instance()
    return (
        chat_singleton.get_kernel(),
        chat_singleton.get_chat_completion(),
        chat_singleton.get_history(),
        chat_singleton.get_execution_settings(),
        chat_singleton.get_agent()
    )
