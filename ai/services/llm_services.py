import logging
from langchain_google_genai import ChatGoogleGenerativeAI
import json
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
        
        
    def create_question_template(self, chat_all_information: dict):
        """
        Đọc toàn bộ thông tin cuộc hội thoại và dùng LLM để viết lại câu hỏi cuối cùng của người dùng.
        
        Tham số:
        chat_all_information: dict chứa thông tin về cuộc trò chuyện (messages)
        
        Trả về:
        str: Câu hỏi được LLM viết lại, đầy đủ ý nghĩa và rõ ràng, giới hạn 10 - 70 từ.
        """
        messages = chat_all_information["messages"]
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        latest_query = user_messages[-1].get("content", "").strip()

        try:
            if not chat_all_information or "messages" not in chat_all_information:
                return "Không có dữ liệu cuộc trò chuyện để tạo câu hỏi."

            # messages = chat_all_information["messages"]

            # Tìm câu hỏi cuối cùng của người dùng

            # Xây dựng nội dung toàn bộ hội thoại
            conversation_text = ""
            for idx, msg in enumerate(messages[:-1]):
                role:str = msg.get("role", "unknown").capitalize()
                content = msg.get("content", "").strip()
                conversation_text += f"{role.upper()}: {content}\n"

            files_text = ""
            if "files" in chat_all_information:
                files = chat_all_information["files"]
                for idx, file in enumerate(files):
                    file_name = file.get("file_name", "")
                    description = file.get("description", "")
                    files_text += f"File {idx+1}: {file_name}. Mô tả: {description}\n"

            # Tạo prompt chi tiết cho LLM
            prompt = (
                "Bạn là một chuyên gia ngôn ngữ. Bạn được cung cấp toàn bộ cuộc trò chuyện giữa một người dùng và một hệ thống AI.\n"
                "Dưới đây là toàn bộ cuộc hội thoại giữa User và AI.\n\n"
                "-------------------\n"
                f"{conversation_text}\n\n"
                f"Câu hỏi cuối cùng của người dùng: {latest_query}\n\n"
                "-------------------\n\n"
                "Dưới đây là toàn bộ các file được cung cấp trong đoạn chat và mô tả của chúng.\n"
                "-------------------\n"
                f"{files_text}"
                "-------------------\n\n"

                "Nhiệm vụ của bạn:\n"
                "- Đọc kỹ toàn bộ nội dung cuộc trò chuyện.\n"
                "- Viết lại câu hỏi cuối cùng của người dùng một cách đầy đủ, rõ ràng, dễ hiểu.\n"
                "- Đảm bảo câu hỏi mới vẫn giữ nguyên ý nghĩa câu hỏi gốc.\n"
                "- Câu hỏi viết lại nên tối ưu cho hệ thống tìm kiếm embedding.\n"
                "- Yêu cầu độ dài câu hỏi từ 10 đến 70 từ.\n\n"
                "- Ưu tiên viết lại câu hỏi với ngôn ngữ của tài liệu liên quan. \n\n"
                "Câu hỏi viết lại là:"
            )
            print("PROMPT: ---\n\n")
            print(prompt)

            # Gọi LLM để sinh câu hỏi
            response = self.llm.invoke(prompt)
            rewritten_question = response.content.strip()
            print(rewritten_question)
            print("END  ---\n\n")

            # Kiểm tra độ dài câu hỏi (phòng trường hợp LLM không tuân thủ)
            # word_count = len(rewritten_question.split())
            # if word_count < 10:
            #     rewritten_question += " Xin cung cấp thêm chi tiết để làm rõ ý định của người dùng."
            # elif word_count > 70:
            #     rewritten_question = " ".join(rewritten_question.split()[:70])

            return rewritten_question

        except Exception as e:
            logger.error(f"Lỗi trong create_question_template: {str(e)}")
            return latest_query


    def create_description_short_for_file(self, first_content_of_file, last_content_of_file):
        prompt = f"""
            Tôi sẽ cung cấp cho bạn đoạn đầu tiên và đoạn cuối cùng của một tài liệu.
            Dựa trên phần giới thiệu này, hãy mô tả rõ ràng nội dung chính và mục đích của toàn bộ tài liệu.
            Hãy nêu ra ngôn ngữ của tài liệu, mô tả cần ngắn gọn, dễ hiểu, đầy đủ thông tin và không dài quá 100 từ.
            Nội dung đoạn đầu tiên của tài liệu như sau:
                {first_content_of_file}
            Nội dung đoạn cuối cùng của tài liệu như sau:
                {last_content_of_file}
            """

        response = self.llm.invoke(prompt)
        return response.content

        pass

    