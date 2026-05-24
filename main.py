from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from domain.entidades import Arquivo, Pasta
from adapters.repositorio_sqlite import SQLiteArquivoRepository

app = FastAPI()
db_path = "banco_ingestao.sqlite"
repo = SQLiteArquivoRepository(db_path)

# Modelo para o Front-end enviar os dados de uma nova pasta
class PastaCreate(BaseModel):
    nome: str
    projeto_id: int

# 1. Rota para CRIAR uma pasta
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

# 2. Rota para LISTAR pastas de um projeto
@app.get("/api/pastas/{projeto_id}")
def listar_pastas(projeto_id: int):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, projeto_id FROM pastas WHERE projeto_id = ?", (projeto_id,))
        rows = cursor.fetchall()
        return [{"id": r[0], "nome": r[1], "projeto_id": r[2]} for r in rows]

# 3. Rota para MOVER um arquivo para dentro de uma pasta
@app.patch("/api/arquivos/{arquivo_id}/mover")
def mover_arquivo(arquivo_id: int, pasta_id: Optional[int] = None):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE arquivos SET pasta_id = ? WHERE id = ?", (pasta_id, arquivo_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Arquivo não encontrado")
            return {"status": "sucesso", "mensagem": "Arquivo movido com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mantenha aqui suas rotas existentes de upload e listagem de arquivos...