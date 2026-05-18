from domain.entidades import Arquivo
from ports.repositorio import IArquivoRepository, IStorageService


class UploadArquivoUseCase:
    """
    Orquestra o fluxo de entrada de um novo ficheiro no sistema.
    Ele não sabe NADA sobre FastAPI, Django, SQLite ou AWS.
    Ele apenas confia nas Portas que lhe são injetadas.
    """

    def __init__(self, repositorio: IArquivoRepository, storage: IStorageService):
        self.repositorio = repositorio
        self.storage = storage

    def executar(self, nome_original: str, projeto_id: int, conteudo_binario: bytes) -> Arquivo:
        # 1. Cria a Entidade Pura
        arquivo = Arquivo(
            nome_original=nome_original,
            projeto_id=projeto_id,
            conteudo_binario=conteudo_binario
        )

        # 2. Executa as regras de negócio absolutas (Validação e extração de tipo)
        arquivo.validar()

        # 3. Usa a Porta de Storage para guardar o ficheiro físico
        # Se isto falhar (ex: disco cheio), o código para aqui e não suja a base de dados
        caminho_fisico = self.storage.salvar_fisico(arquivo)

        # Como o núcleo é nosso, podemos guardar o caminho de volta no objeto
        # (se decidires adicionar esse atributo na entidade mais tarde) ou apenas
        # delegar ao repositório para o gravar.

        # 4. Usa a Porta do Repositório para gravar os metadados (nome, data, etc.)
        arquivo_salvo = self.repositorio.salvar_metadados(arquivo)

        return arquivo_salvo


class ListarArquivosUseCase:
    """
    Caso de uso simples para devolver os ficheiros de um determinado projeto.
    """
    def __init__(self, repositorio: IArquivoRepository):
        self.repositorio = repositorio

    def executar(self, projeto_id: int):
        return self.repositorio.buscar_por_projeto(projeto_id)