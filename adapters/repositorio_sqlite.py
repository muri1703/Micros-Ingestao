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
        # Repara que não existe 'FOREIGN KEY' restrita ao outro banco de dados.
        # Em microsserviços, o 'projeto_id' é apenas um número inteiro para referência.
        query = """
                CREATE TABLE IF NOT EXISTS arquivos \
                ( \
                    id \
                    INTEGER \
                    PRIMARY \
                    KEY \
                    AUTOINCREMENT, \
                    nome_original \
                    TEXT \
                    NOT \
                    NULL, \
                    projeto_id \
                    INTEGER \
                    NOT \
                    NULL, \
                    tipo \
                    TEXT, \
                    tamanho_bytes \
                    INTEGER, \
                    data_ingestao \
                    TIMESTAMP
                ) \
                """
        with self._conectar() as conn:
            conn.execute(query)

    def salvar_metadados(self, arquivo: Arquivo) -> Arquivo:
        with self._conectar() as conn:
            cursor = conn.cursor()

            if arquivo.id:
                query = """
                        UPDATE arquivos
                        SET nome_original = ?, \
                            projeto_id    = ?, \
                            tipo          = ?, \
                            tamanho_bytes = ?
                        WHERE id = ? \
                        """
                cursor.execute(query, (
                    arquivo.nome_original, arquivo.projeto_id,
                    arquivo.tipo, arquivo.tamanho_bytes, arquivo.id
                ))
            else:
                query = """
                        INSERT INTO arquivos (nome_original, projeto_id, tipo, tamanho_bytes, data_ingestao)
                        VALUES (?, ?, ?, ?, ?) \
                        """
                cursor.execute(query, (
                    arquivo.nome_original, arquivo.projeto_id,
                    arquivo.tipo, arquivo.tamanho_bytes, arquivo.data_ingestao
                ))
                arquivo.id = cursor.lastrowid

            conn.commit()
        return arquivo

    def buscar_por_projeto(self, projeto_id: int) -> List[Arquivo]:
        query = """
                SELECT id, nome_original, projeto_id, tipo, tamanho_bytes, data_ingestao
                FROM arquivos \
                WHERE projeto_id = ? \
                ORDER BY data_ingestao DESC
                """
        arquivos = []
        with self._conectar() as conn:
            cursor = conn.cursor()
            linhas = cursor.execute(query, (projeto_id,)).fetchall()

            for linha in linhas:
                # Criamos a entidade sem carregar o binário, pois aqui só queremos os metadados para listar na UI
                arq = Arquivo(
                    nome_original=linha[1],
                    projeto_id=linha[2],
                    conteudo_binario=b""
                )
                arq.id = linha[0]
                arq.tipo = linha[3]
                arq.tamanho_bytes = linha[4]
                arq.data_ingestao = linha[5]
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
        query = """
                SELECT id, nome_original, projeto_id, tipo, tamanho_bytes, data_ingestao
                FROM arquivos
                WHERE id = ?
                """
        with self._conectar() as conn:
            cursor = conn.cursor()
            linha = cursor.execute(query, (arquivo_id,)).fetchone()

            if not linha:
                return None

            # Criamos a entidade
            arq = Arquivo(
                nome_original=linha[1],
                projeto_id=linha[2],
                conteudo_binario=b""
            )
            arq.id = linha[0]
            arq.tipo = linha[3]
            arq.tamanho_bytes = linha[4]
            arq.data_ingestao = linha[5]

            return arq