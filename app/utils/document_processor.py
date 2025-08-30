"""Document processor for handling PDF and video files."""
import os
import tempfile
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import whisper
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import json
import os
from dotenv import load_dotenv
from app.utils.question_generator import QuestionGenerator
from app.database.mongodb import MongoDB, SUGGESTED_QUESTIONS_COLLECTION

# Load environment variables
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
# Specific index names for different document types
PINECONE_PDF_INDEX = "edu-pdf"
PINECONE_VIDEO_INDEX = "edu-video"

class DocumentProcessor:
    """Document processor for handling PDF and video files."""
    
    def __init__(self):
        """Initialize the document processor."""
        # Text splitter for documents
        self.text_splitter = self.get_text_splitter(chunk_size=5000, chunk_overlap=500)
        
        # Initialize Whisper model for video transcription
        self.whisper_model = None  # Lazy loading to save resources
        
        # Initialize question generator for video content
        self.question_generator = QuestionGenerator()
        
        # Initialize vector store
        self.init_vector_store()
    
    def init_vector_store(self):
        """Initialize the vector store connection."""
        try:
            if not PINECONE_API_KEY:
                print("Warning: PINECONE_API_KEY not set. Vector storage will not be available.")
                self.vector_store_available = False
                return
                
            if not OPENAI_API_KEY:
                print("Warning: OPENAI_API_KEY not set. Vector storage will not be available.")
                self.vector_store_available = False
                return
                
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=PINECONE_API_KEY)
            
            # Connect to PDF and Video indexes
            try:
                self.pdf_index = self.pc.Index(PINECONE_PDF_INDEX)
                self.video_index = self.pc.Index(PINECONE_VIDEO_INDEX)
                self.vector_store_available = True
                print(f"Connected to Pinecone indexes: {PINECONE_PDF_INDEX} and {PINECONE_VIDEO_INDEX}")
            except Exception as e:
                print(f"Error connecting to Pinecone indexes: {str(e)}")
                self.vector_store_available = False
        except Exception as e:
            print(f"Error initializing vector store: {str(e)}")
            self.vector_store_available = False
    
    def get_text_splitter(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> RecursiveCharacterTextSplitter:
        """Get a configured text splitter for document chunking."""
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def process_pdf(self, file_path: str, document_id: str, original_filename: str) -> Dict[str, Any]:
        """Process PDF document and return chunks."""
        try:
            # Process PDF with PyPDF2
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                documents = []
                chunk_id = 0
                
                # Process each page separately
                for page_num, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text() or ""
                    
                    # Split page text into chunks
                    chunks = self.text_splitter.split_text(page_text)
                    
                    # Create document objects for each chunk
                    for chunk in chunks:
                        metadata = {
                            "document_id": document_id,
                            "filename": os.path.basename(file_path),
                            "original_filename": original_filename,
                            "chunk_id": str(chunk_id),
                            "page": page_num,
                            "source": "pdf",
                            "created_at": datetime.now().isoformat(),
                        }
                        doc = Document(page_content=chunk, metadata=metadata)
                        documents.append(doc)
                        chunk_id += 1
                
                print(f"Created {len(documents)} document objects from PDF")
                
                # Store documents in vector store if available
                if self.vector_store_available:
                    self.store_documents(documents, document_type="pdf")
                
                return {
                    "status": "success",
                    "message": "PDF processed successfully",
                    "document_id": document_id,
                    "filename": os.path.basename(file_path),
                    "chunks_created": len(documents),
                    "total_pages": len(reader.pages),
                    "documents": documents
                }
                
        except Exception as e:
            error_message = f"Error processing PDF: {str(e)}"
            print(error_message)
            return {
                "status": "error",
                "message": error_message,
                "document_id": document_id,
                "filename": os.path.basename(file_path)
            }
    
    async def process_video(self, file_path: str, document_id: str, original_filename: str, file_id: str = None, organization_id: str = None, display_name: str = None) -> Dict[str, Any]:
        """Process video file and return transcription chunks."""
        try:
            # Lazy load Whisper model
            if self.whisper_model is None:
                print("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                print("Whisper model loaded")
            
            # Transcribe video
            result = self.whisper_model.transcribe(file_path)
            
            # Process transcription
            documents = []
            full_text = result["text"]
            segments = result["segments"]
            detected_language = result.get("language", "unknown")
            
            # Create text position to timestamp mapping
            text_positions = []
            current_pos = 0
            
            for segment in segments:
                segment_text = segment["text"]
                start_time = segment["start"]
                end_time = segment["end"]
                
                text_positions.append({
                    "start_pos": current_pos,
                    "end_pos": current_pos + len(segment_text),
                    "start_time": start_time,
                    "end_time": end_time
                })
                current_pos += len(segment_text)
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            # Process each chunk and prepare for suggested questions
            current_pos = 0
            time_segments = []
            
            for i, chunk in enumerate(chunks):
                chunk_start = full_text.find(chunk, current_pos)
                chunk_end = chunk_start + len(chunk)
                current_pos = chunk_end
                
                # Find timestamps for chunk
                start_time, end_time = self._find_chunk_timestamps(
                    chunk_start, chunk_end, text_positions
                )
                
                # Format timestamps
                start_formatted = self._format_timestamp(start_time)
                end_formatted = self._format_timestamp(end_time)
                
                # Create document for vector store
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "document_id": document_id,
                        "filename": os.path.basename(file_path),
                        "original_filename": original_filename,
                        "chunk_id": f"{i}",
                        "source": "video",
                        "language": detected_language,
                        "created_at": datetime.now().isoformat(),
                        "timestamp_metadata": json.dumps({
                            "start_time": start_formatted,
                            "end_time": end_formatted,
                            "timestamp_range": f"{start_formatted} - {end_formatted}"
                        })
                    }
                )
                documents.append(doc)
                
                # Generate suggested questions for this chunk
                # Only generate questions for chunks with substantial content (every 2-3 chunks)
                if i % 3 == 0 and len(chunk.split()) > 50:
                    try:
                        questions = self.question_generator.generate_questions(
                            transcript=chunk,
                            start_time=start_time,
                            end_time=end_time
                        )
                        
                        if questions:
                            # Each question already has its own timestamps and context
                            # Just add the segment context for reference
                            for question in questions:
                                question["segment_context"] = chunk
                                
                            time_segments.append({
                                "questions": questions
                            })
                    except Exception as qe:
                        print(f"Error generating questions for chunk {i}: {str(qe)}")
            
            print(f"Created {len(documents)} document objects from video transcription")
            print(f"Generated suggested questions for {len(time_segments)} segments")
            
            # Store documents in vector store if available
            if self.vector_store_available:
                self.store_documents(documents, document_type="video")
            
            # Store suggested questions in MongoDB if we have organization_id and file_id
            if organization_id and file_id and time_segments:
                try:
                    # Create suggested questions document
                    suggested_questions_doc = {
                        "document_id": document_id,
                        "file_id": file_id,
                        "organization_id": organization_id,
                        "filename": original_filename,
                        "display_name": display_name or original_filename,
                        "segments": time_segments,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                    
                    # Store in MongoDB
                    questions_collection = MongoDB.get_collection(SUGGESTED_QUESTIONS_COLLECTION)
                    await questions_collection.insert_one(suggested_questions_doc)
                    print(f"Stored suggested questions for document {document_id} in MongoDB")
                except Exception as me:
                    print(f"Error storing suggested questions in MongoDB: {str(me)}")
            
            return {
                "status": "success",
                "message": "Video processed successfully",
                "document_id": document_id,
                "filename": os.path.basename(file_path),
                "chunks_created": len(documents),
                "questions_segments": len(time_segments),
                "documents": documents
            }
            
        except Exception as e:
            error_message = f"Error processing video: {str(e)}"
            print(error_message)
            return {
                "status": "error",
                "message": error_message,
                "document_id": document_id,
                "filename": os.path.basename(file_path)
            }
    
    def _find_chunk_timestamps(self, chunk_start, chunk_end, text_positions):
        """Find timestamps for a chunk of text."""
        start_timestamp = None
        end_timestamp = None
        
        for pos in text_positions:
            if pos["start_pos"] <= chunk_start and pos["end_pos"] > chunk_start:
                start_timestamp = pos["start_time"]
            if pos["start_pos"] < chunk_end and pos["end_pos"] >= chunk_end:
                end_timestamp = pos["end_time"]
                break
        
        if start_timestamp is None and text_positions:
            start_timestamp = text_positions[0]["start_time"]
        if end_timestamp is None and text_positions:
            end_timestamp = text_positions[-1]["end_time"]
        
        return start_timestamp or 0.0, end_timestamp or 0.0
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def store_documents(self, documents: List[Document], document_type: str = "pdf") -> Dict[str, Any]:
        """Store documents in the vector store."""
        try:
            if not documents:
                return {
                    "status": "warning",
                    "message": "No documents to store",
                    "chunks_stored": 0
                }
                
            if not self.vector_store_available:
                return {
                    "status": "warning",
                    "message": "Vector store not available, skipping vector store upload",
                    "chunks_stored": 0
                }
                
            # Select the appropriate index based on document type
            index_to_use = self.pdf_index if document_type == "pdf" else self.video_index
            index_name = PINECONE_PDF_INDEX if document_type == "pdf" else PINECONE_VIDEO_INDEX
            
            print(f"Storing {len(documents)} documents in Pinecone index '{index_name}'")
            
            try:
                vector_store = PineconeVectorStore(
                    index=index_to_use,
                    embedding=self.embeddings,
                    text_key="text"
                )
                
                # Add documents in smaller batches to avoid potential issues
                batch_size = 10
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i+batch_size]
                    print(f"Adding batch {i//batch_size + 1} of {(len(documents)-1)//batch_size + 1} to Pinecone")
                    vector_store.add_documents(batch)
                    print(f"Successfully added batch {i//batch_size + 1}")
                
                print(f"Successfully added all {len(documents)} documents to vector store")
                return {
                    "status": "success",
                    "message": f"Successfully stored {len(documents)} chunks in vector store",
                    "chunks_stored": len(documents)
                }
            except Exception as pinecone_error:
                print(f"Error adding documents to Pinecone: {str(pinecone_error)}")
                # Try with a single-threaded approach
                try:
                    print("Attempting single-threaded approach with direct OpenAI embeddings...")
                    # Get embeddings directly
                    texts = [doc.page_content for doc in documents]
                    metadatas = [doc.metadata for doc in documents]
                    embeddings = self.embeddings.embed_documents(texts)
                    
                    # Create vector records manually
                    records = []
                    for i, (text, metadata, embedding) in enumerate(zip(texts, metadatas, embeddings)):
                        records.append({
                            'id': f"{metadata.get('document_id')}-{i}",
                            'values': embedding,
                            'metadata': {**metadata, 'text': text}
                        })
                    
                    # Upsert directly to Pinecone
                    index_to_use = self.pdf_index if document_type == "pdf" else self.video_index
                    print(f"Upserting {len(records)} records directly to Pinecone")
                    index_to_use.upsert(vectors=records)
                    print("Successfully added documents using direct approach")
                    return {
                        "status": "success",
                        "message": f"Successfully stored {len(documents)} chunks in vector store using direct approach",
                        "chunks_stored": len(documents)
                    }
                except Exception as direct_error:
                    print(f"Direct Pinecone upload also failed: {str(direct_error)}")
                    return {
                        "status": "error",
                        "message": f"Failed to add documents to Pinecone: {str(direct_error)}",
                        "chunks_stored": 0
                    }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error storing documents: {str(e)}",
                "chunks_stored": 0
            }
    
    def retrieve_documents(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve documents from vector store based on query."""
        try:
            if not self.vector_store_available:
                return []
            
            results = []
            
            # If document_type is specified, search only in that index
            if document_type == "pdf":
                indexes_to_search = [self.pdf_index]
            elif document_type == "video":
                indexes_to_search = [self.video_index]
            else:
                # Search in both indexes if no specific type is requested
                indexes_to_search = [self.pdf_index, self.video_index]
            
            for index in indexes_to_search:
                vector_store = PineconeVectorStore(
                    index=index,
                    embedding=self.embeddings,
                    text_key="text"
                )
                
                # Perform similarity search
                try:
                    index_results = vector_store.similarity_search_with_score(
                        query=query,
                        k=limit,
                        filter=filters
                    )
                    
                    # Format results
                    for doc, score in index_results:
                        results.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "score": score
                        })
                except Exception as e:
                    print(f"Error searching in index: {str(e)}")
                    continue
            
            # Sort results by score (ascending order - lower is better)
            results.sort(key=lambda x: x["score"])
            
            # Limit total results
            return results[:limit]
            
            # Perform similarity search
            results = vector_store.similarity_search_with_score(
                query=query,
                k=limit,
                filter=filters
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []
