import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()

class RAGService:
    def __init__(self):
        print("Initialisation du RAGService...")

        # --- MODIFICATION CLÉ : CONSTRUIRE DES CHEMINS ABSOLUS ---
        # 'os.path.dirname(__file__)' donne le chemin du dossier où se trouve ce script (chatbot_app)
        current_script_directory = os.path.dirname(os.path.abspath(__file__))

        # On construit le chemin complet vers les dossiers, ce qui est infaillible.
        self.KNOWLEDGE_BASE_DIR = os.path.join(current_script_directory, "knowledge_base")
        self.DB_FAISS_PATH = os.path.join(current_script_directory, "db_faiss")
        
        # On vérifie que le dossier knowledge_base existe bien à cet endroit
        if not os.path.isdir(self.KNOWLEDGE_BASE_DIR):
            # Cette erreur est plus précise et arrêtera le programme si le dossier n'est pas là.
            raise FileNotFoundError(f"ERREUR: Le dossier knowledge_base n'a pas été trouvé au chemin attendu: {self.KNOWLEDGE_BASE_DIR}")
        # -------------------------------------------------------------

        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.2, convert_system_message_to_human=True)
        
        self._load_or_create_vector_store()
        self._create_qa_chain()
        
        print("RAGService prêt.")

    def _load_or_create_vector_store(self):
        # Le reste du code n'a pas besoin de changer car il utilise les variables de classe
        if os.path.exists(self.DB_FAISS_PATH):
            print("INFO: Chargement de la base de données FAISS existante...")
            self.vector_store = FAISS.load_local(self.DB_FAISS_PATH, self.embeddings, allow_dangerous_deserialization=True)
        else:
            print("INFO: Création de la base de données FAISS (cela peut prendre un moment)...")
            loader = DirectoryLoader(self.KNOWLEDGE_BASE_DIR, glob="**/*.txt", show_progress=True)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
            texts = text_splitter.split_documents(documents)
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
            self.vector_store.save_local(self.DB_FAISS_PATH)
            print("INFO: Base de données FAISS créée et sauvegardée.")

    def _create_qa_chain(self):
        # ... (le reste de la fonction est identique)
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})
        
        prompt_template = """
        Tu es "UPL-Bot", l'assistant IA officiel de l'Université Protestante de Lubumbashi.
        Ton ton doit être professionnel, serviable et précis.
        Réponds à la question de l'utilisateur en te basant STRICTEMENT sur le CONTEXTE fourni ci-dessous.
        Si l'information n'est pas présente dans le contexte, réponds poliment : "Je ne dispose pas de cette information dans ma base de données."
        Ne réponds jamais à des questions qui sortent du cadre de l'université.

        CONTEXTE:
        {context}

        QUESTION:
        {question}

        RÉPONSE:
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": prompt}
        )

    def ask(self, query: str) -> str:
        # ... (le reste de la fonction est identique)
        if not query or not query.strip():
            return "Veuillez poser une question valide."
        
        print(f"INFO: Réception de la question : '{query}'")
        result = self.qa_chain.invoke({"query": query})
        print(f"INFO: Réponse générée : '{result['result']}'")
        return result['result']