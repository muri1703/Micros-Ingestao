import os
from ports.repositorio import IArquivoRepository, IStorageService


class DeletarArquivoUseCase:
    """
    Orquestra a exclusão de um arquivo.
    Garante que o arquivo seja removido fisicamente antes de apagar os metadados.
    """

    def __init__(self, repositorio: IArquivoRepository, storage: IStorageService):
        self.repositorio = repositorio
        self.storage = storage

    def executar(self, projeto_id: int, arquivo_id: int) -> bool:
        # 1. Buscar os metadados para sabermos o nome original do ficheiro
        arquivo = self.repositorio.buscar_por_id(arquivo_id)

        if not arquivo or arquivo.projeto_id != projeto_id:
            raise ValueError("Arquivo não encontrado ou não pertence a este projeto.")

        # 2. Montar o caminho físico esperado (baseado na regra do LocalStorageAdapter)
        caminho_fisico = os.path.join(
            self.storage.diretorio_base,
            f"projeto_{projeto_id}",
            arquivo.nome_original
        )

        # 3. Usa a Porta de Storage para apagar o ficheiro físico do disco
        self.storage.deletar_fisico(caminho_fisico)

        # 4. Usa a Porta de Repositório para apagar o registo da base de dados
        sucesso_banco = self.repositorio.deletar_metadados(arquivo_id)

        return sucesso_banco