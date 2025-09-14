# POLARIS Backend

API de backend para o sistema POLARIS - Planning Operations & Legal Analysis for Revenue & International Structures.

## Descrição

O POLARIS é uma ferramenta de inteligência artificial especializada em wealth planning (planejamento patrimonial) que automatiza a criação de documentos jurídicos complexos para advogados tributaristas.

## Tecnologias

- **Framework**: Flask (Python)
- **Banco de Dados**: PostgreSQL (produção) / SQLite (desenvolvimento)
- **ORM**: SQLAlchemy
- **CORS**: Flask-CORS
- **Autenticação**: JWT (futuro)

## Estrutura do Projeto

```
polaris_backend/
├── src/
│   ├── models/          # Modelos de dados SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── cliente.py
│   │   ├── template_documento.py
│   │   └── documento_gerado.py
│   ├── routes/          # Endpoints da API
│   │   ├── user.py
│   │   └── cliente.py
│   ├── static/          # Arquivos estáticos
│   └── main.py          # Aplicação principal
├── venv/                # Ambiente virtual
├── requirements.txt     # Dependências
└── README.md
```

## Modelos de Dados

### User
- Usuários do sistema (advogados, consultores)
- Campos: username, email, password_hash, first_name, last_name

### Cliente
- Clientes dos usuários
- Dados pessoais, financeiros, objetivos de planejamento
- Informações sobre estruturas offshore existentes

### TemplateDeDocumento
- Templates de documentos jurídicos
- Categorias: Trust, Estate, International, Corporate
- Placeholders para personalização

### DocumentoGerado
- Documentos criados pelo sistema
- Histórico, versões, status de assinatura
- Metadados de auditoria

## Endpoints da API

### Clientes (`/api/clientes`)

- `GET /api/clientes` - Listar clientes (com paginação e busca)
- `GET /api/clientes/{id}` - Obter cliente específico
- `POST /api/clientes` - Criar novo cliente
- `PUT /api/clientes/{id}` - Atualizar cliente
- `DELETE /api/clientes/{id}` - Excluir cliente (soft delete)
- `POST /api/clientes/{id}/restore` - Restaurar cliente excluído
- `GET /api/clientes/stats` - Estatísticas dos clientes

### Health Check

- `GET /api/health` - Verificação de saúde da API

## Configuração

### Variáveis de Ambiente

```bash
# Banco de dados (opcional - usa SQLite se não definido)
DATABASE_URL=postgresql://user:password@localhost/polaris

# Chave secreta (obrigatório em produção)
SECRET_KEY=sua-chave-secreta-super-segura
```

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/carlossilvatbh/polaris_backend.git
cd polaris_backend
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\\Scripts\\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente (opcional):
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Execute a aplicação:
```bash
python src/main.py
```

A API estará disponível em `http://localhost:5000`

## Desenvolvimento

### Estrutura de Resposta da API

Todas as respostas seguem o padrão JSON:

```json
{
  "data": {},
  "error": "mensagem de erro (se houver)",
  "pagination": {} // apenas em listagens
}
```

### Códigos de Status HTTP

- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Erro de validação
- `404` - Não encontrado
- `409` - Conflito (ex: email duplicado)
- `500` - Erro interno do servidor

### Paginação

Endpoints de listagem suportam paginação:

```
GET /api/clientes?page=1&per_page=10&search=termo
```

### Filtros

Todos os endpoints requerem `user_id` para isolamento de dados entre usuários.

## Segurança

- CORS configurado para permitir requisições de qualquer origem
- Soft delete para preservar dados
- Validação de entrada em todos os endpoints
- Isolamento de dados por usuário

## Próximos Passos

1. Implementar autenticação JWT
2. Adicionar endpoints para TemplateDeDocumento
3. Adicionar endpoints para DocumentoGerado
4. Implementar geração de documentos com IA
5. Adicionar testes automatizados
6. Configurar CI/CD

## Contribuição

Este projeto foi desenvolvido com Manus AI como equipe de engenharia autônoma.

## Licença

Propriedade privada - Todos os direitos reservados.

