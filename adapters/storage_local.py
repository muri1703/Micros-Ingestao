import os
from ports.repositorio import IStorageService
from domain.entidades import Arquivo


class LocalStorageAdapter(IStorageService):
    """
    Este é o Adaptador de Armazenamento.
    Ele assina o contrato 'IStorageService' e a sua única responsabilidade
    é pegar em bytes e transformá-los num ficheiro físico no disco.
    """

    def __init__(self, diretorio_base: str = "armazenamento_local"):
        self.diretorio_base = diretorio_base
        # Garante que a pasta principal existe quando o adaptador é iniciado
        os.makedirs(self.diretorio_base, exist_ok=True)

    def salvar_fisico(self, arquivo: Arquivo) -> str:
        # 1. Cria uma subpasta com o ID do projeto para manter os ficheiros organizados
        caminho_projeto = os.path.join(self.diretorio_base, f"projeto_{arquivo.projeto_id}")
        os.makedirs(caminho_projeto, exist_ok=True)

        # 2. Define o caminho final do ficheiro
        caminho_completo = os.path.join(caminho_projeto, arquivo.nome_original)

        # 3. Grava os bytes diretamente no disco
        with open(caminho_completo, "wb") as f:
            f.write(arquivo.conteudo_binario)

        # Devolve o caminho onde o ficheiro foi guardado,
        # para que possa ser registado na base de dados (se necessário)
        return caminho_completo

    def deletar_fisico(self, caminho_arquivo: str) -> bool:
        """Remove o ficheiro físico do disco, caso seja necessário apagar."""
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            return True
        return False