import os
from databricks.sdk import WorkspaceClient
from typing import Dict, List, Optional
import streamlit as st  # Remove if not needed for FastAPI

class GenieService:
    def __init__(self):
        self.w = WorkspaceClient()
        self.genie_space_id = "01f09fd408c91da4be95c7e1afc6efc9"  # From the provided URL
        self.conversation_id = None

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
            "query": response.query if hasattr(response, 'query') else "",
            "results": [],
            "execution_time_ms": getattr(response, 'execution_time_ms', 0),
            "data_source": "genie_space"
        }

        for attachment in getattr(response, 'attachments', []):
            if hasattr(attachment, 'text') and attachment.text:
                result["results"].append({
                    "type": "text",
                    "content": attachment.text.content
                })
            elif hasattr(attachment, 'query') and attachment.query:
                # Handle query results - would need to fetch data from statement_execution
                result["results"].append({
                    "type": "query",
                    "description": attachment.query.description,
                    "query": attachment.query.query,
                    "data": []  # Would populate with actual data
                })

        return result

# Singleton instance
genie_service = GenieService()
