from ai.services.index_manager import FAISSIndexManager
import config

index_manager = FAISSIndexManager(
    embedding_model_name=config.EMBEDDING_MODEL_NAME,
    index_data_dir=config.INDEX_DATA_DIR
)
index_manager.load_from_disk()
