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
    
    def _format_property_name(self, property_id: str) -> str:
        """Convert property ID like 'austin-tx' to display name like 'Austin, TX'"""
        if not property_id:
            return property_id
        
        # Split by hyphen and capitalize each part
        parts = property_id.split('-')
        if len(parts) >= 2:
            city = " ".join(parts[:-1]).replace('_', ' ').title()  # Handle underscores if any
            state = parts[-1].upper()
            return f"{city}, {state}"
        
        # Fallback: just capitalize
        return property_id.replace('-', ' ').replace('_', ' ').title()
    
    def get_suggested_questions(self) -> List[str]:
        """Get suggested questions from the Genie space"""
        try:
            import json
            
            # Get the Genie space details
            space = self.w.genie.get_space(self.genie_space_id)

            # Extract sample questions from serialized_space JSON
            suggested = []
            
            if hasattr(space, 'serialized_space') and space.serialized_space:
                try:
                    # Parse the JSON string
                    space_config = json.loads(space.serialized_space)
                    print(f"DEBUG: Space config: {space_config}")
                    # Navigate to config.sample_questions
                    if 'config' in space_config and 'sample_questions' in space_config['config']:
                        sample_questions = space_config['config']['sample_questions']
                        print(f"DEBUG: Sample questions: {sample_questions}")
                        # Extract question from each sample_question object
                        for sq in sample_questions:
                            if 'question' in sq:
                                # question can be a string or array
                                question = sq['question']
                                if isinstance(question, list):
                                    suggested.extend(question)
                                else:
                                    suggested.append(question)
                        
                        print(f"✅ Found {len(suggested)} sample questions from space")
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse serialized_space JSON: {str(e)}")
                except Exception as e:
                    print(f"⚠️  Error extracting sample questions: {str(e)}")
            
            # Default suggested questions if none from API
            if not suggested:
                print("⚠️  No sample questions in space, using defaults")
                
                # Make questions property-aware if property is selected
                if self._property:
                    # Property-specific questions
                    property_name = self._format_property_name(self._property)  # e.g., "Austin, TX"
                    suggested = [
                        f"How many issues are there in {property_name}?",
                        f"What are the top 5 aspects with the most issues in {property_name}?",
                        f"Show me issue trends for {property_name}",
                        f"What's the average sentiment score for {property_name}?"
                    ]
                else:
                    # Generic/portfolio-wide questions (HQ without property selection)
                    suggested = [
                        "How many issues are there?",
                        "What are the top 5 aspects with the most issues?",
                        "Show me issues by location",
                        "What's the average sentiment score?"
                    ]
            
            return suggested
            
        except Exception as e:
            print(f"⚠️ Could not get suggested questions: {str(e)}")
            # Return default questions based on property context
            if self._property:
                property_name = self._format_property_name(self._property)
                return [
                    f"How many issues are there in {property_name}?",
                    f"What are the top 5 aspects with the most issues in {property_name}?",
                    f"Show me issue trends for {property_name}",
                    f"What's the average sentiment score for {property_name}?"
                ]
            else:
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
            
            # Extract columns from manifest (sibling of result, not inside it)
            columns = []
            if (hasattr(statement, 'manifest') and statement.manifest and
                hasattr(statement.manifest, 'schema') and statement.manifest.schema and
                hasattr(statement.manifest.schema, 'columns')):
                columns = [col.name for col in statement.manifest.schema.columns]
                print(f"✅ Extracted {len(columns)} columns: {columns}")
            
            # Extract data from result.data_array
            data_array = []
            if hasattr(statement, 'result') and statement.result:
                if hasattr(statement.result, 'data_array') and statement.result.data_array:
                    # If no columns but we have data, generate column names
                    if not columns and statement.result.data_array:
                        first_row = statement.result.data_array[0]
                        columns = [f'col_{i}' for i in range(len(first_row))]
                        print(f"⚠️  No columns in schema, generated: {columns}")
                    
                    for row_list in statement.result.data_array:
                        row_dict = dict(zip(columns, [str(val) if val is not None else '' for val in row_list]))
                        data_array.append(row_dict)
                    
                    print(f"✅ Processed {len(data_array)} rows")
                
                return {
                    "columns": columns,
                    "data": data_array,
                    "num_rows": len(data_array)
                }
            else:
                # Handle case where result doesn't exist
                state_str = str(status) if status else "UNKNOWN"
                return {"error": f"No result available. Statement state: {state_str}"}
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
        print(f"DEBUG: Response: {response}")
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
                
                description = getattr(i.query, 'description', 'Generated query')
                query_text = getattr(i.query, 'query', '')
               
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

        # Extract follow-up questions from attachments
        # API structure: attachments[].suggested_questions.questions[]
        result["follow_up_questions"] = []
        
        for attachment in attachments:
            # Check for suggested_questions object with questions array
            if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                if hasattr(attachment.suggested_questions, 'questions') and attachment.suggested_questions.questions:
                    result["follow_up_questions"] = list(attachment.suggested_questions.questions)
                    print(f"✨ Found {len(result['follow_up_questions'])} suggested questions from attachment")
                    break  # Use first set of suggested questions found
        
        # Fallback: check at response level (in case API structure varies)
        if not result["follow_up_questions"]:
            if hasattr(response, 'suggested_questions') and response.suggested_questions:
                if hasattr(response.suggested_questions, 'questions') and response.suggested_questions.questions:
                    result["follow_up_questions"] = list(response.suggested_questions.questions)
                    print(f"✨ Found {len(result['follow_up_questions'])} suggested questions from response")
        
        # Generate smart follow-up questions if none found
        if not result["follow_up_questions"]:
            print("⚠️  No suggested questions found, generating defaults")
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
