import sqlite3
from typing import List
from domain.entidades import Arquivo
from ports.repositorio import IArquivoRepository


class SQLiteArquivoRepository(IArquivoRepository):
    """
    Adaptador de Base de Dados para o Microsserviço de Ingestão.
    Ele assina o contrato 'IArquivoRepository' e traduz os comandos
    do nosso núcleo para SQL puro.
    """

    def __init__(self, caminho_banco: str = "banco_ingestao.sqlite"):
        self.caminho_banco = caminho_banco
        self._criar_tabela_se_nao_existir()

    def _conectar(self):
        return sqlite3.connect(self.caminho_banco)

    def _criar_tabela_se_nao_existir(self):
        # Adicionada a coluna pasta_id
        query = """
                CREATE TABLE IF NOT EXISTS arquivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_original TEXT NOT NULL,
                    projeto_id INTEGER NOT NULL,
                    tipo TEXT,
                    tamanho_bytes INTEGER,
                    data_ingestao TIMESTAMP,
                    pasta_id INTEGER
                )
                """
        with self._conectar() as conn:
            conn.execute(query)

    def salvar_metadados(self, arquivo: Arquivo) -> Arquivo:
        with self._conectar() as conn:
            cursor = conn.cursor()

            if arquivo.id:
                query = """
                        UPDATE arquivos
                        SET nome_original = ?,
                            projeto_id    = ?,
                            tipo          = ?,
                            tamanho_bytes = ?,
                            pasta_id      = ?
                        WHERE id = ?
                        """
                cursor.execute(query, (
                    arquivo.nome_original, arquivo.projeto_id,
                    arquivo.tipo, arquivo.tamanho_bytes, getattr(arquivo, 'pasta_id', None), arquivo.id
                ))
            else:
                query = """
                        INSERT INTO arquivos (nome_original, projeto_id, tipo, tamanho_bytes, data_ingestao, pasta_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """
                cursor.execute(query, (
                    arquivo.nome_original, arquivo.projeto_id,
                    arquivo.tipo, arquivo.tamanho_bytes, arquivo.data_ingestao, getattr(arquivo, 'pasta_id', None)
                ))
                arquivo.id = cursor.lastrowid

            conn.commit()
        return arquivo

    def buscar_por_projeto(self, projeto_id: int) -> List[Arquivo]:
        # Adicionado o pasta_id no SELECT
        query = """
                SELECT id, nome_original, projeto_id, tipo, tamanho_bytes, data_ingestao, pasta_id
                FROM arquivos 
                WHERE projeto_id = ? 
                ORDER BY data_ingestao DESC
                """
        arquivos = []
        with self._conectar() as conn:
            cursor = conn.cursor()
            try:
                linhas = cursor.execute(query, (projeto_id,)).fetchall()
            except sqlite3.OperationalError:
                # Caso o banco de dados antigo ainda não tenha a coluna, retorna vazio para evitar quebrar tudo
                return []

            for linha in linhas:
                arq = Arquivo(
                    nome_original=linha[1],
                    projeto_id=linha[2],
                    conteudo_binario=b""
                )
                arq.id = linha[0]
                arq.tipo = linha[3]
                arq.tamanho_bytes = linha[4]
                arq.data_ingestao = linha[5]
                arq.pasta_id = linha[6] if len(linha) > 6 else None
                arquivos.append(arq)

        return arquivos

    def deletar_metadados(self, arquivo_id: int) -> bool:
        query = "DELETE FROM arquivos WHERE id = ?"
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (arquivo_id,))
            conn.commit()
            return cursor.rowcount > 0

    def buscar_por_id(self, arquivo_id: int) -> Arquivo:
        # Adicionado o pasta_id no SELECT
        query = """
                SELECT id, nome_original, projeto_id, tipo, tamanho_bytes, data_ingestao, pasta_id
                FROM arquivos
                WHERE id = ?
                """
        with self._conectar() as conn:
            cursor = conn.cursor()
            try:
                linha = cursor.execute(query, (arquivo_id,)).fetchone()
            except sqlite3.OperationalError:
                return None

            if not linha:
                return None

            arq = Arquivo(
                nome_original=linha[1],
                projeto_id=linha[2],
                conteudo_binario=b""
            )
            arq.id = linha[0]
            arq.tipo = linha[3]
            arq.tamanho_bytes = linha[4]
            arq.data_ingestao = linha[5]
            arq.pasta_id = linha[6] if len(linha) > 6 else None

            return arq
