import os
from databricks.sdk import WorkspaceClient
from typing import Dict, List, Optional
import json  # For debug logging

class GenieService:
    def __init__(self):
        self.w = WorkspaceClient()
        self.genie_space_id = "01f09fd408c91da4be95c7e1afc6efc9"  # From the provided URL
        self.conversation_id = None

    def get_query_result(self, statement_id):
        """Fetch query result from statement_id, adapted from example without Pandas"""
        try:
            # Get the statement
            statement = self.w.statement_execution.get_statement(statement_id)
            
            # Wait for completion if needed
            while hasattr(statement, 'execution') and statement.execution.state in ['PENDING', 'RUNNING']:
                import time
                time.sleep(1)
                statement = self.w.statement_execution.get_statement(statement_id)
            
            if (hasattr(statement, 'execution') and 
                statement.execution.state == 'SUCCEEDED' and 
                hasattr(statement, 'result') and 
                statement.result):
                
                # Extract columns from manifest.schema.columns
                columns = []
                if (hasattr(statement.result, 'manifest') and 
                    statement.result.manifest and 
                    hasattr(statement.result.manifest, 'schema') and 
                    hasattr(statement.result.manifest.schema, 'columns')):
                    columns = [col.name for col in statement.result.manifest.schema.columns]
                
                # Extract data from data_array (list of lists to list of dicts)
                data_array = []
                if hasattr(statement.result, 'data_array') and statement.result.data_array:
                    for row_list in statement.result.data_array:
                        row_dict = dict(zip(columns, [str(val) if val is not None else '' for val in row_list]))
                        data_array.append(row_dict)
                
                return {
                    "columns": columns,
                    "data": data_array,
                    "num_rows": len(data_array)
                }
            else:
                return {"error": f"Statement state: {getattr(statement.execution, 'state', 'UNKNOWN')}"}
        except Exception as e:
            return {"error": str(e)}

    def start_conversation(self, prompt: str) -> Dict:
        try:
            conversation = self.w.genie.start_conversation_and_wait(
                self.genie_space_id, prompt
            )
            self.conversation_id = conversation.conversation_id
            return self._process_genie_response(conversation)
        except Exception as e:
            return {"error": str(e)}

    def continue_conversation(self, prompt: str) -> Dict:
        if not self.conversation_id:
            return self.start_conversation(prompt)
        
        try:
            conversation = self.w.genie.create_message_and_wait(
                self.genie_space_id, self.conversation_id, prompt
            )
            return self._process_genie_response(conversation)
        except Exception as e:
            return {"error": str(e)}

    def _process_genie_response(self, response) -> Dict:
        result = {
            "query": getattr(response, 'query', '') if hasattr(response, 'query') else "",
            "results": [],
            "execution_time_ms": getattr(response, 'execution_time_ms', 0),
            "data_source": "genie_space"
        }

        # Process attachments like the example
        attachments = getattr(response, 'attachments', [])
        print(f"DEBUG: Processing {len(attachments)} attachments")
        for i in attachments:
            if hasattr(i, 'text') and i.text:
                content = i.text.content
                print(f"A: {content}")
                result["results"].append({
                    "type": "text",
                    "content": content
                })
            elif hasattr(i, 'query') and i.query:
                description = getattr(i.query, 'description', 'Generated query')
                query_text = getattr(i.query, 'query', '')
                print(f"A: {description}")
                
                # Get query result
                if hasattr(response, 'query_result') and response.query_result and hasattr(response.query_result, 'statement_id'):
                    query_result = self.get_query_result(response.query_result.statement_id)
                    if "error" in query_result:
                        print(f"Query error: {query_result['error']}")
                        result["results"].append({
                            "type": "text",
                            "content": f"Query error: {query_result['error']}"
                        })
                    else:
                        data = query_result['data']
                        print(f"Data: {len(data)} rows")  # Summary like example
                        print(f"Generated code: {query_text}")
                        result["results"].append({
                            "type": "table",
                            "description": description,
                            "query": query_text,
                            "columns": query_result['columns'],
                            "data": data
                        })
                else:
                    print("No statement_id found for query result")
                    print(f"Generated code: {query_text}")
                    result["results"].append({
                        "type": "query",
                        "description": description,
                        "query": query_text,
                        "data": []
                    })
            else:
                print(f"Unknown attachment: {str(i)}")
                result["results"].append({
                    "type": "text",
                    "content": f"Unknown attachment: {str(i)[:200]}..."
                })

        return result

# Singleton instance
genie_service = GenieService()
