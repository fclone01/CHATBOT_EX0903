from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from be.models import Chat, Message, File, Vote, engine
import shutil, os
from sqlalchemy.ext.declarative import declarative_base
from be.schemas import *
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
router = APIRouter()
import uuid
from ai.schemas import *
from ai.ai_init import index_manager
import ai.handle_all as ai_handle_all
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# APIs
def create_routes_be():
    @router.get("/chats")
    def get_chats(db: Session = Depends(get_db)):
        chats = db.query(Chat).order_by(Chat.created_at.desc()).all()
        return chats

    @router.post("/chats")
    def create_chat(chatCreate: ChatCreate, db: Session = Depends(get_db)):
        name = chatCreate.name
        new_chat = Chat(name=name)
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return new_chat

    @router.get("/chats/{chat_id}")
    def get_chat(chat_id: str, db: Session = Depends(get_db)):
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        messages = db.query(Message).filter(Message.chat_id == chat_id).all()
        files = db.query(File).filter(File.chat_id == chat_id).all()
        chat.messages = messages
        chat.files = files
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat

    @router.post("/messages")
    async def post_message( messageCreate : MessageCreate, db: Session = Depends(get_db)):
        chat_id, content, role = messageCreate.chat_id, messageCreate.content, "user"
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        message = Message(chat_id=chat_id, content=content, role=role)
        db.add(message)
        db.commit()
        db.refresh(message)

        
        # Bot reply simulation
        if role == "user":
            all_messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()

            


            bot_reply_content = (await ai_handle_all.query_documents_handler(query = content, chat_id=chat_id))["answer"]
            if bot_reply_content:
               bot_reply =  Message(chat_id=chat_id, content=bot_reply_content, role="ai")
            # bot_reply = Message(chat_id=chat_id, content=f"Bot trả lời cho: '{content}'", role="ai")
            db.add(bot_reply)
            db.commit()

        return {"status": "success"}

    @router.post("/upload")
    async def upload_file(chat_id: str = Form(...), file: UploadFile = None, db: Session = Depends(get_db)):
        file_extension = os.path.splitext(file.filename)[1]
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        file_id = str(uuid.uuid4())
        save_path = os.path.join(UPLOAD_FOLDER, file_id + file_extension)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        embedding_infor, description = await ai_handle_all.upload_document_handler(file_id+ file_extension, chat_id=chat_id)
        
        db_file = File(id = file_id, chat_id=chat_id, file_name=file.filename , description=description, embedding_infor=embedding_infor)
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return {"file_name": db_file.file_name, "embedding_infor": embedding_infor}

    @router.delete("/files/{file_id}")
    def delete_file(file_id:str, db: Session = Depends(get_db)):
        db_file = db.query(File).filter(File.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")

        # file_path = os.path.join(UPLOAD_FOLDER, db_file.file_name)
        # if os.path.exists(file_path):
        #     os.remove(file_path)

        db.delete(db_file)
        db.commit()
        return {"deleted": db_file.file_name}

    @router.post("/vote")
    def vote_message(message_id: str, type: int, db: Session = Depends(get_db)):
        if type not in (-1, 1):
            raise HTTPException(status_code=400, detail="Invalid vote type")

        vote = Vote(message_id=message_id, type=type)
        db.add(vote)
        db.commit()
        db.refresh(vote)
        return {"status": "voted"}

    return router

