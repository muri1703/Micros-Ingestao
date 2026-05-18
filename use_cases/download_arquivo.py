import os
from ports.repositorio import IArquivoRepository


class DownloadArquivoUseCase:
    """
    Caso de uso responsável por localizar um arquivo físico no disco
    a partir dos seus metadados salvos no banco de dados.
    """

    def __init__(self, repositorio: IArquivoRepository):
        self.repositorio = repositorio
        # O diretório base deve ser o mesmo que configuramos no adaptador de storage
        self.diretorio_base = "armazenamento_local"

    def executar(self, projeto_id: int, arquivo_id: int) -> str:
        # 1. Busca todos os metadados dos arquivos daquele projeto no banco
        arquivos_do_projeto = self.repositorio.buscar_por_projeto(projeto_id)

        # 2. Procura na lista o arquivo exato que o usuário quer baixar
        arquivo = None
        for arq in arquivos_do_projeto:
            if arq.id == arquivo_id:
                arquivo = arq
                break

        # Se não encontrar o registro no banco, dispara um erro de negócio
        if not arquivo:
            raise ValueError(f"Arquivo com ID {arquivo_id} não encontrado no projeto {projeto_id}.")

        # 3. Reconstrói o caminho físico (ex: armazenamento_local/projeto_1/relatorio.pdf)
        caminho_completo = os.path.join(self.diretorio_base, f"projeto_{projeto_id}", arquivo.nome_original)

        # 4. Verifica se o arquivo físico realmente existe lá antes de prometer entregá-lo
        if not os.path.exists(caminho_completo):
            raise FileNotFoundError("O registro existe no banco, mas o arquivo físico sumiu do disco.")

        # Devolve apenas a String com o caminho. Quem vai ler e enviar para a web é o FastAPI depois.
        return caminho_completo