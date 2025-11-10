import os
from databricks.sdk import WorkspaceClient
from typing import Dict, List, Optional
import json  # For debug logging

class GenieService:
    def __init__(self):
        # Initialize with default HQ context
        self._role = 'hq'
        self._property = None
        
        # Get Genie space ID from environment variable
        self.genie_space_id = os.getenv("GENIE_SPACE_ID")
        if not self.genie_space_id:
            raise ValueError("GENIE_SPACE_ID environment variable is required")
        
        # Initialize workspace client
        self.w = self._get_workspace_client()
        self.conversation_id = None
    
    def set_auth_context(self, role: str = 'hq', property: str = None):
        """Set authentication context and reinitialize workspace client"""
        self._role = role
        self._property = property
        self.w = self._get_workspace_client()
        # Reset conversation when context changes
        self.conversation_id = None
        print(f"🔐 Genie auth context set to: role={role}, property={property}")
    
    def _get_sp_credentials(self, role: str = 'hq', property: str = None) -> tuple:
        """Get service principal credentials based on role and property"""
        if role == 'pm' and property:
            # Property Manager - use property-specific credentials
            property_key = property.split(',')[0].strip().upper().replace(' ', '_')  # e.g., "Austin, TX" -> "AUSTIN"
            client_id = os.getenv(f"{property_key}_SP_CLIENT_ID")
            client_secret = os.getenv(f"{property_key}_SP_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                print(f"⚠️ Service principal credentials not found for {property_key}, falling back to HQ")
                role = 'hq'  # Fallback to HQ
        
        if role == 'hq':
            # HQ - use HQ credentials
            client_id = os.getenv("HQ_SP_CLIENT_ID")
            client_secret = os.getenv("HQ_SP_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError(f"Service principal credentials not found for role={role}, property={property}")
        
        return client_id, client_secret
    
    def _get_workspace_client(self) -> WorkspaceClient:
        """Create workspace client with appropriate credentials"""
        # Check if PAT is available (for backward compatibility)
        databricks_token = os.getenv("DATABRICKS_TOKEN")
        server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME") or os.getenv("DATABRICKS_HOST")
        
        # if databricks_token:
        #     # Use personal access token for Genie (user-level access)
        #     print(f"🔐 Using PAT for Genie authentication")
        #     return WorkspaceClient(
        #         host=f"https://{server_hostname}" if not server_hostname.startswith('https://') else server_hostname,
        #         token=databricks_token
        #     )
        # else:
        try:
            # Use service principal based on role/property
            client_id, client_secret = self._get_sp_credentials(self._role, self._property)
            print(f"🔐 Using Service Principal for Genie: role={self._role}, property={self._property}")
            return WorkspaceClient(
                host=f"https://{server_hostname}" if not server_hostname.startswith('https://') else server_hostname,
                client_id=client_id,
                client_secret=client_secret
            )
        except Exception as e:
            print(f"⚠️ Could not get service principal credentials: {str(e)}, using PAT for Genie authentication")
            return WorkspaceClient(
                host=f"https://{server_hostname}" if not server_hostname.startswith('https://') else server_hostname,
                token=databricks_token
            )
    
    def reset_conversation(self):
        """Reset conversation to start fresh"""
        self.conversation_id = None
        return {"success": True, "message": "Conversation reset"}
    
    def get_suggested_questions(self) -> List[str]:
        """Get suggested questions from the Genie space"""
        try:
            # Get the Genie space details
            space = self.w.genie.get_space(self.genie_space_id)
            
            # Extract suggested questions if available
            suggested = []
            if hasattr(space, 'instructions') and space.instructions:
                # Some spaces have instructions that include suggested questions
                print(f"DEBUG: Space instructions: {space.instructions[:200] if space.instructions else 'None'}")
            
            # Try to get from space attributes
            if hasattr(space, 'sample_questions') and space.sample_questions:
                suggested = list(space.sample_questions)
            
            # Default suggested questions if none from API
            if not suggested:
                suggested = [
                    "How many issues are there?",
                    "What are the top 5 aspects with the most issues?",
                    "Show me issues by location",
                    "What's the average sentiment score?"
                ]
            
            print(f"✨ Suggested questions: {suggested}")
            return suggested
            
        except Exception as e:
            print(f"⚠️ Could not get suggested questions: {str(e)}")
            # Return default questions
            return [
                "How many issues are there?",
                "What are the top 5 aspects with the most issues?",
                "Show me issues by location",
                "What's the average sentiment score?"
            ]

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
                    # If no columns but we have data, generate column names
                    if not columns and statement.result.data_array:
                        first_row = statement.result.data_array[0]
                        columns = [f'col_{i}' for i in range(len(first_row))]
                        print(f"DEBUG: Generated column names: {columns}")
                    
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
            "data_source": "genie_space",
            "follow_up_questions": []
        }

        # Check for top-level content field (direct message content)
        if hasattr(response, 'content') and response.content:
            print(f"DEBUG: Found top-level content: {response.content}")
            result["results"].append({
                "type": "text",
                "content": response.content
            })

        # Check for direct message content
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
        print(f"DEBUG: Full attachments object: {attachments}")
        
        for idx, i in enumerate(attachments):
            print(f"\n{'='*60}")
            print(f"DEBUG: Processing attachment {idx}")
            print(f"DEBUG: Attachment {idx} type: {type(i)}")
            print(f"DEBUG: Attachment {idx} attributes: {dir(i)}")
            print(f"{'='*60}\n")
            
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
                    print(f"DEBUG: Query result received: {query_result.keys() if isinstance(query_result, dict) else 'NOT A DICT'}")
                    if "error" in query_result:
                        print(f"Query error: {query_result['error']}")
                        result["results"].append({
                            "type": "text",
                            "content": f"Query error: {query_result['error']}"
                        })
                    else:
                        data = query_result.get('data', [])
                        columns = query_result.get('columns', [])
                        print(f"DEBUG: Columns extracted: {columns}")
                        print(f"DEBUG: Column count: {len(columns)}")
                        print(f"Data: {len(data)} rows")  # Summary like example
                        print(f"Generated code: {query_text}")
                        
                        # If no columns but we have data, try to infer columns from first row
                        if not columns and data and len(data) > 0:
                            columns = list(data[0].keys())
                            print(f"DEBUG: Inferred columns from data: {columns}")
                        
                        result["results"].append({
                            "type": "table",
                            "description": description,
                            "query": query_text,
                            "columns": columns,
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

        # Extract follow-up questions if available
        if hasattr(response, 'suggested_follow_ups') and response.suggested_follow_ups:
            result["follow_up_questions"] = list(response.suggested_follow_ups)
            print(f"✨ Found {len(result['follow_up_questions'])} follow-up questions")
        elif hasattr(response, 'follow_up_questions') and response.follow_up_questions:
            result["follow_up_questions"] = list(response.follow_up_questions)
            print(f"✨ Found {len(result['follow_up_questions'])} follow-up questions")
        else:
            # Generate smart follow-up questions based on the query context
            if result.get('results'):
                has_table = any(item['type'] == 'table' for item in result['results'])
                if has_table:
                    result["follow_up_questions"] = [
                        "Show me more details",
                        "What about the trend over time?",
                        "Break this down by location"
                    ]
                else:
                    result["follow_up_questions"] = [
                        "Can you provide more details?",
                        "What are the top categories?",
                        "Show me a breakdown"
                    ]
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"✅ FINAL RESULTS SUMMARY:")
        print(f"   Total items captured: {len(result['results'])}")
        for i, item in enumerate(result['results']):
            print(f"   [{i}] Type: {item['type']}")
            if item['type'] == 'text':
                print(f"       Content preview: {item['content'][:100]}...")
            elif item['type'] == 'table':
                print(f"       Description: {item.get('description', 'N/A')}")
                print(f"       Rows: {len(item.get('data', []))}")
                print(f"       Columns: {len(item.get('columns', []))}")
            elif item['type'] == 'query':
                print(f"       Description: {item.get('description', 'N/A')}")
        print(f"   Follow-up questions: {len(result['follow_up_questions'])}")
        print(f"{'='*60}\n")

        return result

# Singleton instance
genie_service = GenieService()
