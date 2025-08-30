"""Question generator module for video transcriptions."""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Load OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class SuggestedQuestion(BaseModel):
    """Model for a suggested question."""
    question: str = Field(description="The suggested question text")
    context: str = Field(description="Brief context or reason for suggesting this question")
    start_time: str = Field(description="Start time of the segment")
    end_time: str = Field(description="End time of the segment")
    
class SuggestedQuestions(BaseModel):
    """Model for suggested questions output."""
    questions: List[SuggestedQuestion] = Field(description="List of suggested questions")

class QuestionGenerator:
    """Generate suggested questions from video transcriptions."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the question generator.
        
        Args:
            model_name: OpenAI model to use
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=OPENAI_API_KEY
        )
        
        # Create output parser
        self.parser = PydanticOutputParser(pydantic_object=SuggestedQuestions)
        
        # Create prompt template
        template = """
        You are an AI assistant that generates insightful questions based on educational video content.
        
        Below is a transcript from a video. Please identify 1-3 key concepts that:
        1. Are mentioned but not fully explained
        2. Might be difficult to understand without prior knowledge
        3. Would benefit from further explanation
        
        For each concept, generate a question that a student might ask to learn more.
        
        TRANSCRIPT:
        {transcript}
        
        TIMESTAMP RANGE:
        Start: {start_time} seconds
        End: {end_time} seconds
        
        {format_instructions}
        """
        
        self.prompt = PromptTemplate(
            input_variables=["transcript", "start_time", "end_time"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template=template
        )
        
        # Create the chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds into MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def generate_questions(self, 
                          transcript: str, 
                          start_time: float, 
                          end_time: float) -> List[Dict[str, str]]:
        """Generate suggested questions from a transcript chunk.
        
        Args:
            transcript: The transcript text
            start_time: Start time of the chunk in seconds
            end_time: End time of the chunk in seconds
            
        Returns:
            List of suggested questions with context
        """
        try:
            # If transcript is too short, don't generate questions
            if len(transcript.split()) < 20:
                return []
            
            # Generate questions
            result = self.chain.run(
                transcript=transcript,
                start_time=start_time,
                end_time=end_time
            )
            
            # Parse the output
            parsed_output = self.parser.parse(result)
            
            # Format timestamps for display
            start_formatted = self._format_timestamp(start_time)
            end_formatted = self._format_timestamp(end_time)
            
            # Convert to list of dictionaries with timestamps
            questions = [
                {
                    "question": q.question,
                    "context": q.context,
                    "start_time": start_formatted,
                    "end_time": end_formatted
                }
                for q in parsed_output.questions
            ]
            
            return questions
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return []
