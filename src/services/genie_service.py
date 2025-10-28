import os
from databricks.sdk import WorkspaceClient
from typing import Dict, List, Optional
import json  # For debug logging

class GenieService:
    def __init__(self):
        # Use PAT if available (needed for Genie access), otherwise OAuth client credentials
        databricks_token = os.getenv("DATABRICKS_TOKEN")
        
        if databricks_token:
            # Use personal access token for Genie (user-level access)
            self.w = WorkspaceClient(
                host=os.getenv("DATABRICKS_HOST"),
                token=databricks_token
            )
        else:
            # Fall back to OAuth client credentials
            self.w = WorkspaceClient(
                host=os.getenv("DATABRICKS_HOST"),
                client_id=os.getenv("DATABRICKS_CLIENT_ID"),
                client_secret=os.getenv("DATABRICKS_CLIENT_SECRET")
            )
        
        # Get Genie space ID from environment variable
        self.genie_space_id = os.getenv("GENIE_SPACE_ID")
        if not self.genie_space_id:
            raise ValueError("GENIE_SPACE_ID environment variable is required")
        self.conversation_id = None

    def get_query_result(self, statement_id):
        """Fetch query result from statement_id, adapted from example without Pandas"""
        try:
            # Get the statement
            statement = self.w.statement_execution.get_statement(statement_id)
            
            # Get status - check both possible attribute names
            status = getattr(statement, 'status', None) or getattr(statement, 'state', None)
            if status is None and hasattr(statement, 'execution'):
                status = getattr(statement.execution, 'state', None)
            
            # Wait for completion if needed
            import time
            while status and hasattr(status, 'state') and status.state in ['PENDING', 'RUNNING']:
                time.sleep(1)
                statement = self.w.statement_execution.get_statement(statement_id)
                status = getattr(statement, 'status', None) or getattr(statement, 'state', None)
                if status is None and hasattr(statement, 'execution'):
                    status = getattr(statement.execution, 'state', None)
            
            # Check if we have results
            if hasattr(statement, 'result') and statement.result:
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
                state_str = str(status) if status else "UNKNOWN"
                return {"error": f"Statement state: {state_str}"}
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
        # Debug: Print all response attributes
        print(f"DEBUG: Response type: {type(response)}")
        print(f"DEBUG: Response attributes: {dir(response)}")
        
        result = {
            "query": getattr(response, 'query', '') if hasattr(response, 'query') else "",
            "results": [],
            "execution_time_ms": getattr(response, 'execution_time_ms', 0),
            "data_source": "genie_space"
        }

        # Check for direct message content first
        if hasattr(response, 'message') and response.message:
            message_content = getattr(response.message, 'content', None)
            if message_content:
                print(f"DEBUG: Message content: {message_content}")
                result["results"].append({
                    "type": "text",
                    "content": message_content
                })

        # Check if response has query_result at top level
        if hasattr(response, 'query_result') and response.query_result:
            print(f"DEBUG: Found query_result at response level: {response.query_result}")
            if hasattr(response.query_result, 'statement_id'):
                print(f"DEBUG: Statement ID at response level: {response.query_result.statement_id}")

        # Process attachments like the example
        attachments = getattr(response, 'attachments', [])
        print(f"DEBUG: Processing {len(attachments)} attachments")
        for idx, i in enumerate(attachments):
            print(f"DEBUG: Attachment {idx} type: {type(i)}")
            print(f"DEBUG: Attachment {idx} attributes: {dir(i)}")
            
            # Check if attachment has text content
            if hasattr(i, 'text') and i.text:
                content = getattr(i.text, 'content', '')
                print(f"A: {content}")
                result["results"].append({
                    "type": "text",
                    "content": content
                })
            
            # Check if attachment ALSO has query (not elif - an attachment can have both!)
            if hasattr(i, 'query') and i.query:
                print(f"DEBUG: Found query attachment")
                print(f"DEBUG: Query object attributes: {dir(i.query)}")
                
                description = getattr(i.query, 'description', 'Generated query')
                query_text = getattr(i.query, 'query', '')
                print(f"A: {description}")
                
                # Check for query result - could be in attachment or at response level
                statement_id = None
                
                # First check the attachment itself for query_result
                if hasattr(i.query, 'query_result') and i.query.query_result:
                    print(f"DEBUG: Found query_result in i.query")
                    statement_id = getattr(i.query.query_result, 'statement_id', None)
                    print(f"DEBUG: Statement ID from i.query.query_result: {statement_id}")
                
                # Check if it's directly on the attachment
                if not statement_id and hasattr(i, 'query_result') and i.query_result:
                    print(f"DEBUG: Found query_result directly on attachment")
                    statement_id = getattr(i.query_result, 'statement_id', None)
                    print(f"DEBUG: Statement ID from i.query_result: {statement_id}")
                
                # Fall back to response level
                if not statement_id and hasattr(response, 'query_result') and response.query_result:
                    print(f"DEBUG: Using query_result from response level")
                    statement_id = getattr(response.query_result, 'statement_id', None)
                    print(f"DEBUG: Statement ID from response.query_result: {statement_id}")
                
                if statement_id:
                    query_result = self.get_query_result(statement_id)
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
                # Try to extract any content we can
                att_str = str(i)
                print(f"Unknown attachment type: {att_str[:100]}")
                # Check for common attribute patterns
                for attr in ['content', 'text', 'value', 'data']:
                    if hasattr(i, attr):
                        val = getattr(i, attr)
                        if val and isinstance(val, str):
                            result["results"].append({
                                "type": "text",
                                "content": val
                            })
                            break

        return result

# Singleton instance
genie_service = GenieService()
