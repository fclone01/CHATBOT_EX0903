import logging

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create loggers
    loggers = [
        "doc_retrieval_api",
        "doc_retrieval_api.index_manager",
        "doc_retrieval_api.llm_service",
        "doc_retrieval_api.text_processor"
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
    return logging.getLogger("doc_retrieval_api")