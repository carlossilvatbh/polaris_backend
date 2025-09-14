from flask import Blueprint, request, jsonify
from src.models import db, Cliente
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import traceback

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/clientes', methods=['GET'])
def get_clientes():
    """
    Listar todos os clientes
    Query parameters:
    - page: número da página (default: 1)
    - per_page: itens por página (default: 10, max: 100)
    - search: busca por nome ou email
    - user_id: filtrar por usuário (obrigatório)
    """
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '')
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # Query base
        query = Cliente.query.filter_by(user_id=user_id, is_active=True)
        
        # Filtro de busca
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                (Cliente.nome_completo.ilike(search_filter)) |
                (Cliente.email.ilike(search_filter))
            )
        
        # Paginação
        clientes_paginated = query.order_by(Cliente.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'clientes': [cliente.to_summary_dict() for cliente in clientes_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': clientes_paginated.total,
                'pages': clientes_paginated.pages,
                'has_next': clientes_paginated.has_next,
                'has_prev': clientes_paginated.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar clientes: {str(e)}'}), 500

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
def get_cliente(cliente_id):
    """Obter um cliente específico por ID"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        cliente = Cliente.query.filter_by(
            id=cliente_id, 
            user_id=user_id, 
            is_active=True
        ).first()
        
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        return jsonify(cliente.to_dict())
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar cliente: {str(e)}'}), 500

@cliente_bp.route('/clientes', methods=['POST'])
def create_cliente():
    """Criar um novo cliente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Validação de campos obrigatórios
        required_fields = ['nome_completo', 'email', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se já existe cliente com mesmo email para o usuário
        existing_cliente = Cliente.query.filter_by(
            email=data['email'], 
            user_id=data['user_id'],
            is_active=True
        ).first()
        
        if existing_cliente:
            return jsonify({'error': 'Já existe um cliente com este email'}), 409
        
        # Criar novo cliente
        cliente = Cliente()
        
        # Campos básicos
        cliente.nome_completo = data['nome_completo']
        cliente.email = data['email']
        cliente.user_id = data['user_id']
        
        # Campos opcionais
        optional_fields = [
            'telefone', 'nacionalidade', 'cpf', 'passaporte', 'rg',
            'endereco_completo', 'cidade', 'estado', 'cep', 'pais',
            'profissao', 'empresa', 'cargo', 'renda_anual', 'patrimonio_total',
            'origem_patrimonio', 'residente_fiscal_brasil', 'residente_fiscal_eua',
            'outros_paises_residencia', 'objetivos_planejamento', 'tolerancia_risco',
            'horizonte_investimento', 'possui_offshore', 'detalhes_offshore',
            'possui_trust', 'detalhes_trust'
        ]
        
        for field in optional_fields:
            if field in data:
                setattr(cliente, field, data[field])
        
        # Data de nascimento (conversão de string para date)
        if 'data_nascimento' in data and data['data_nascimento']:
            try:
                cliente.data_nascimento = datetime.strptime(
                    data['data_nascimento'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({'error': 'Formato de data_nascimento inválido. Use YYYY-MM-DD'}), 400
        
        db.session.add(cliente)
        db.session.commit()
        
        return jsonify(cliente.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'Erro de integridade dos dados'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar cliente: {str(e)}'}), 500

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
def update_cliente(cliente_id):
    """Atualizar um cliente existente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # Buscar cliente
        cliente = Cliente.query.filter_by(
            id=cliente_id, 
            user_id=user_id, 
            is_active=True
        ).first()
        
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        # Verificar se email já existe (exceto para o próprio cliente)
        if 'email' in data and data['email'] != cliente.email:
            existing_cliente = Cliente.query.filter_by(
                email=data['email'], 
                user_id=user_id,
                is_active=True
            ).filter(Cliente.id != cliente_id).first()
            
            if existing_cliente:
                return jsonify({'error': 'Já existe um cliente com este email'}), 409
        
        # Atualizar campos
        updatable_fields = [
            'nome_completo', 'email', 'telefone', 'nacionalidade', 'cpf', 
            'passaporte', 'rg', 'endereco_completo', 'cidade', 'estado', 
            'cep', 'pais', 'profissao', 'empresa', 'cargo', 'renda_anual', 
            'patrimonio_total', 'origem_patrimonio', 'residente_fiscal_brasil', 
            'residente_fiscal_eua', 'outros_paises_residencia', 'objetivos_planejamento', 
            'tolerancia_risco', 'horizonte_investimento', 'possui_offshore', 
            'detalhes_offshore', 'possui_trust', 'detalhes_trust'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(cliente, field, data[field])
        
        # Data de nascimento
        if 'data_nascimento' in data:
            if data['data_nascimento']:
                try:
                    cliente.data_nascimento = datetime.strptime(
                        data['data_nascimento'], '%Y-%m-%d'
                    ).date()
                except ValueError:
                    return jsonify({'error': 'Formato de data_nascimento inválido. Use YYYY-MM-DD'}), 400
            else:
                cliente.data_nascimento = None
        
        cliente.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(cliente.to_dict())
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'Erro de integridade dos dados'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar cliente: {str(e)}'}), 500

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    """Excluir um cliente (soft delete)"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        cliente = Cliente.query.filter_by(
            id=cliente_id, 
            user_id=user_id, 
            is_active=True
        ).first()
        
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        # Soft delete
        cliente.is_active = False
        cliente.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Cliente excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir cliente: {str(e)}'}), 500

@cliente_bp.route('/clientes/<int:cliente_id>/restore', methods=['POST'])
def restore_cliente(cliente_id):
    """Restaurar um cliente excluído"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        cliente = Cliente.query.filter_by(
            id=cliente_id, 
            user_id=user_id, 
            is_active=False
        ).first()
        
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado ou já está ativo'}), 404
        
        cliente.is_active = True
        cliente.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(cliente.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao restaurar cliente: {str(e)}'}), 500

@cliente_bp.route('/clientes/stats', methods=['GET'])
def get_clientes_stats():
    """Obter estatísticas dos clientes"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # Estatísticas básicas
        total_clientes = Cliente.query.filter_by(user_id=user_id, is_active=True).count()
        total_patrimonio = db.session.query(db.func.sum(Cliente.patrimonio_total)).filter_by(
            user_id=user_id, is_active=True
        ).scalar() or 0
        
        # Clientes por tolerância ao risco
        tolerancia_stats = db.session.query(
            Cliente.tolerancia_risco, 
            db.func.count(Cliente.id)
        ).filter_by(user_id=user_id, is_active=True).group_by(Cliente.tolerancia_risco).all()
        
        # Clientes com offshore
        clientes_offshore = Cliente.query.filter_by(
            user_id=user_id, is_active=True, possui_offshore=True
        ).count()
        
        return jsonify({
            'total_clientes': total_clientes,
            'total_patrimonio': float(total_patrimonio),
            'clientes_offshore': clientes_offshore,
            'tolerancia_risco': dict(tolerancia_stats)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter estatísticas: {str(e)}'}), 500

