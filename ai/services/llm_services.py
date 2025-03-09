import logging
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("doc_retrieval_api.llm_service")

class LLMService:
    def __init__(self, model_name, temperature=0, max_tokens=5000, timeout=30, max_retries=3):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries
        )
    
    def generate_answer(self, query, retrieved_docs):
        """Generate an answer based on the query and retrieved documents"""
        try:
            # Create context from documents
            context = "\n\n".join([f"Đoạn {i+1}: {doc.content}" for i, (doc, _) in enumerate(retrieved_docs)])
            
            # Create prompt
            prompt = f"""Câu hỏi: {query}

                Thông tin liên quan:
                {context}

                Hãy trả lời câu hỏi trên dựa trên thông tin đã cung cấp. Nếu không có đủ thông tin để trả lời, hãy nói rõ rằng bạn không thể tìm thấy câu trả lời trong tài liệu. Trả lời cần trung thực, chính xác và dựa trên các thông tin được cung cấp.

                Trả lời:"""
            
            # Call LLM
            response = self.llm.invoke(prompt)
            answer = response.content
            
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"Xảy ra lỗi khi tạo câu trả lời: {str(e)}"
        
        

    def create_description_short_for_file(self, first_content_of_file, last_content_of_file):
        prompt = f"""
            I will provide you with the first paragraph and last paragraph of a document. 
            Based on this introduction, clearly describe the main content and purpose of the entire document. 
            Your description should be clear, informative, and no longer than 100 words. 
            The first paragraph content of the document is as follows:
                {first_content_of_file}"
            The last paragraph content of the document is as follows:
                {last_content_of_file}
            """

        response = self.llm.invoke(prompt)
        return response.content

        pass

    