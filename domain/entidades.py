import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Pasta:
    nome: str
    projeto_id: int
    id: Optional[int] = None
    data_criacao: datetime = field(default_factory=datetime.now)

    def validar(self):
        if not self.nome:
            raise ValueError("A pasta precisa ter um nome.")
        if self.projeto_id <= 0:
            raise ValueError("ID de projeto inválido.")

@dataclass
class Arquivo:
    nome_original: str
    projeto_id: int  # Nota: Ele só conhece o ID do projeto, não a entidade Projeto inteira!
    conteudo_binario: bytes
    pasta_id: Optional[int] = None  # Novo campo para o relacionamento com a Pasta
    tipo: Optional[str] = None
    tamanho_bytes: int = field(init=False)
    id: Optional[int] = None
    data_ingestao: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Método executado automaticamente pelo dataclass após a inicialização."""
        self.tamanho_bytes = len(self.conteudo_binario)
        if not self.tipo:
            self.extrair_tipo()

    def extrair_tipo(self):
        """Extrai a extensão do ficheiro e guarda como o 'tipo'."""
        _, extensao = os.path.splitext(self.nome_original)
        self.tipo = extensao.lower().replace('.', '') if extensao else 'desconhecido'

    def validar(self):
        """
        Regras de negócio absolutas para a ingestão.
        Se um ficheiro violar isto, o núcleo rejeita a operação.
        """
        if not self.nome_original:
            raise ValueError("O arquivo tem de ter um nome.")

        if self.tamanho_bytes == 0:
            raise ValueError("O arquivo está vazio (0 bytes).")

        # Opcional: Limitar os tipos de ficheiros aceites logo na raiz do negócio
formatos_permitidos = [
            # Documentos
            'pdf', 'txt', 'docx', 'doc', 'odt', 'rtf', 'md',
            # Dados
            'csv', 'json', 'xlsx', 'xls', 'yaml', 'yml', 'xml',
            # Código-Fonte
            'py', 'js', 'ts', 'html', 'css', 'java', 'cpp', 'c', 'h', 
            'cs', 'go', 'rs', 'php', 'rb', 'sh'
        ]
        if self.tipo not in formatos_permitidos:
            raise ValueError(f"Formato não suportado: {self.tipo}. Apenas aceitamos: {formatos_permitidos}")
