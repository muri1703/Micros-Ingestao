from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse  # 1. ALTERAÇÃO: Importado para enviar ficheiros físicos via HTTP
from pydantic import BaseModel
from typing import List
from datetime import datetime

# Importamos a nossa arquitetura limpa
from use_cases.upload_arquivo import UploadArquivoUseCase, ListarArquivosUseCase
from use_cases.download_arquivo import DownloadArquivoUseCase  # 2. ALTERAÇÃO: Importado o novo Caso de Uso
from adapters.repositorio_sqlite import SQLiteArquivoRepository
from adapters.storage_local import LocalStorageAdapter
from use_cases.deletar_arquivo import DeletarArquivoUseCase

# Configuração do Adaptador HTTP (FastAPI)
app = FastAPI(title="Microsserviço de Ingestão e Armazenamento")

# O Front-End exato que tem permissão para consumir esta API
origens_permitidas = [
    "https://projfrontend.azurewebsites.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas, 
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, DELETE, etc.
    allow_headers=["*"],
)

# Injeção de Dependências (Montagem das Peças)
repositorio_db = SQLiteArquivoRepository(caminho_banco="banco_ingestao.sqlite")
storage_disco = LocalStorageAdapter(diretorio_base="armazenamento_local")

# Injetamos os adaptadores nos Casos de Uso
upload_use_case = UploadArquivoUseCase(repositorio=repositorio_db, storage=storage_disco)
listar_use_case = ListarArquivosUseCase(repositorio=repositorio_db)
download_use_case = DownloadArquivoUseCase(repositorio=repositorio_db)
deletar_use_case = DeletarArquivoUseCase(repositorio=repositorio_db, storage=storage_disco)

# DTOs (Data Transfer Objects) para formatar a saída da API
class ArquivoResponse(BaseModel):
    id: int
    nome_original: str
    projeto_id: int
    tipo: str
    tamanho_bytes: int
    data_ingestao: datetime


# Rotas HTTP

@app.post("/api/postarquivos/projeto/{projeto_id}", response_model=ArquivoResponse)
async def fazer_upload(
        projeto_id: int = Form(...),
        file: UploadFile = File(...)
):
    """Recebe um ficheiro físico e envia os bytes para o núcleo de domínio."""
    try:
        conteudo_binario = await file.read()
        arquivo_salvo = upload_use_case.executar(
            nome_original=file.filename,
            projeto_id=projeto_id,
            conteudo_binario=conteudo_binario
        )
        return arquivo_salvo
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(erro)}")


@app.get("/api/getarquivos/projeto/{projeto_id}", response_model=List[ArquivoResponse])
def listar_arquivos_do_projeto(projeto_id: int):
    """Lista os metadados de todos os ficheiros pertencentes a um projeto."""
    return listar_use_case.executar(projeto_id=projeto_id)


# 4. ALTERAÇÃO: Nova rota HTTP mapeada diretamente para o nosso Caso de Uso de Download
@app.get("/api/arquivos/download/{projeto_id}/{arquivo_id}")
def baixar_arquivo(projeto_id: int, arquivo_id: int):
    """
    Substitui a antiga rota estática '/media/' do Django.
    Chama o Caso de Uso para localizar o arquivo e usa o FileResponse
    do FastAPI para o entregar de forma nativa ao navegador.
    """
    try:
        # O Caso de Uso atua como detetive e devolve apenas a String com o caminho do ficheiro
        caminho_fisico = download_use_case.executar(projeto_id=projeto_id, arquivo_id=arquivo_id)

        # O Adaptador HTTP (FastAPI) pega no caminho, lê os bytes e entrega ao cliente
        return FileResponse(path=caminho_fisico)

    except ValueError as erro:
        # Se o ficheiro não existir no banco de dados (Regra de Negócio)
        raise HTTPException(status_code=404, detail=str(erro))
    except FileNotFoundError as erro:
        # Se o registo existir no banco, mas o ficheiro físico tiver sido apagado do disco (Erro de Infraestrutura)
        raise HTTPException(status_code=404, detail=str(erro))


@app.delete("/api/arquivos/{projeto_id}/{arquivo_id}")
def deletar_arquivo(projeto_id: int, arquivo_id: int):
    """
    Remove o ficheiro físico do disco e apaga seus metadados do banco de dados.
    """
    try:
        sucesso = deletar_use_case.executar(projeto_id=projeto_id, arquivo_id=arquivo_id)
        if sucesso:
            return {"mensagem": "Arquivo excluído com sucesso."}
        else:
            raise HTTPException(status_code=400, detail="Não foi possível concluir a exclusão do arquivo.")

    except ValueError as erro:
        # Cai aqui se o ficheiro não for encontrado no banco ou não pertencer ao projeto
        raise HTTPException(status_code=404, detail=str(erro))
    except Exception as erro:
        # Cai aqui se houver um erro de permissão no disco (SO) ou erro no SQL
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(erro)}")
