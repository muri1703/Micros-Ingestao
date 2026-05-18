from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entidades import Arquivo


class IArquivoRepository(ABC):
    """
    Porta 1: O Contrato da Base de Dados.
    Qualquer tecnologia que queira guardar os metadados do arquivo
    tem de assinar e cumprir este contrato.
    """

    @abstractmethod
    def salvar_metadados(self, arquivo: Arquivo) -> Arquivo:
        pass

    @abstractmethod
    def buscar_por_projeto(self, projeto_id: int) -> List[Arquivo]:
        pass

    @abstractmethod
    def buscar_por_id(self, arquivo_id: int) -> Optional[Arquivo]:
        """Busca os metadados de um ficheiro específico pelo seu ID."""
        pass

    @abstractmethod
    def deletar_metadados(self, arquivo_id: int) -> bool:
        pass


class IStorageService(ABC):
    """
    Porta 2: O Contrato de Armazenamento Físico.
    O nosso núcleo não sabe se vamos usar o disco local (C:\),
    um bucket na Amazon AWS (S3) ou o Google Cloud. Ele apenas
    exige que o ficheiro seja guardado e que o caminho seja devolvido.
    """

    @abstractmethod
    def salvar_fisico(self, arquivo: Arquivo) -> str:
        """Guarda o conteúdo binário e devolve o caminho/URL gerado."""
        pass

    @abstractmethod
    def deletar_fisico(self, caminho_arquivo: str) -> bool:
        """Apaga o ficheiro físico do disco/nuvem."""
        pass