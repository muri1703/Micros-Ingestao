from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

# Importações da Arquitetura Limpa
from use_cases.upload_arquivo import UploadArquivoUseCase, ListarArquivosUseCase
from use_cases.download_arquivo import DownloadArquivoUseCase
from use_cases.deletar_arquivo import DeletarArquivoUseCase
from adapters.repositorio_sqlite import SQLiteArquivoRepository
from adapters.storage_local import LocalStorageAdapter
from domain.entidades import Arquivo, Pasta

app = FastAPI(title="Microsserviço de Ingestão e Armazenamento")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_path = "banco_ingestao.sqlite"

# --- GARANTIR TABELAS NO ARRANCQUE ---
def inicializar_banco():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pastas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                projeto_id INTEGER NOT NULL
            )
        """)
        conn.commit()

inicializar_banco()

repositorio_db = SQLiteArquivoRepository(caminho_banco=db_path)
storage_disco = LocalStorageAdapter(diretorio_base="armazenamento_local")

# Instâncias dos Casos de Uso
upload_use_case = UploadArquivoUseCase(repositorio=repositorio_db, storage=storage_disco)
listar_use_case = ListarArquivosUseCase(repositorio=repositorio_db)
download_use_case = DownloadArquivoUseCase(repositorio=repositorio_db)
deletar_use_case = DeletarArquivoUseCase(repositorio=repositorio_db, storage=storage_disco)

# DTOs
class ArquivoResponse(BaseModel):
    id: int
    nome_original: str
    projeto_id: int
    tipo: str
    tamanho_bytes: int
    data_ingestao: datetime
    pasta_id: Optional[int] = None

class PastaCreate(BaseModel):
    nome: str
    projeto_id: int

# --- ROTAS DE PASTAS (Novas) ---

@app.post("/api/pastas")
def criar_pasta(pasta: PastaCreate):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pastas (nome, projeto_id) VALUES (?, ?)",
                (pasta.nome, pasta.projeto_id)
            )
            return {"status": "sucesso", "pasta_id": cursor.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pastas/{projeto_id}")
def listar_pastas(projeto_id: int):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, projeto_id FROM pastas WHERE projeto_id = ?", (projeto_id,))
        rows = cursor.fetchall()
        return [{"id": r[0], "nome": r[1], "projeto_id": r[2]} for r in rows]

@app.patch("/api/arquivos/{arquivo_id}/mover")
def mover_arquivo(arquivo_id: int, pasta_id: Optional[int] = None):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE arquivos SET pasta_id = ? WHERE id = ?", (pasta_id, arquivo_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Arquivo não encontrado")
            return {"status": "sucesso", "mensagem": "Arquivo movido"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# NOVA ROTA: Deletar Pasta
@app.delete("/api/pastas/{pasta_id}")
def deletar_pasta(pasta_id: int):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verifica se a pasta existe
            cursor.execute("SELECT id FROM pastas WHERE id = ?", (pasta_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Pasta não encontrada")
            
            # Move os arquivos da pasta para a raiz (pasta_id = NULL)
            cursor.execute("UPDATE arquivos SET pasta_id = NULL WHERE pasta_id = ?", (pasta_id,))
            
            # Deleta a pasta
            cursor.execute("DELETE FROM pastas WHERE id = ?", (pasta_id,))
            
            conn.commit()
            return {"status": "sucesso", "mensagem": "Pasta excluída e arquivos movidos para a raiz"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ROTAS DE ARQUIVOS (Originais) ---

@app.post("/api/postarquivos/projeto/{projeto_id}", response_model=ArquivoResponse)
async def fazer_upload(projeto_id: int, file: UploadFile = File(...)):
    conteudo_binario = await file.read()
    return upload_use_case.executar(file.filename, projeto_id, conteudo_binario)

@app.get("/api/getarquivos/projeto/{projeto_id}", response_model=List[ArquivoResponse])
def listar_arquivos(projeto_id: int):
    return listar_use_case.executar(projeto_id)

@app.get("/api/arquivos/download/{projeto_id}/{arquivo_id}")
def baixar_arquivo(projeto_id: int, arquivo_id: int):
    caminho = download_use_case.executar(projeto_id, arquivo_id)
    return FileResponse(path=caminho)

@app.delete("/api/arquivos/{projeto_id}/{arquivo_id}")
def deletar_arquivo(projeto_id: int, arquivo_id: int):
    if deletar_use_case.executar(projeto_id, arquivo_id):
        return {"mensagem": "Excluído com sucesso"}
    raise HTTPException(status_code=400, detail="Erro na exclusão")
