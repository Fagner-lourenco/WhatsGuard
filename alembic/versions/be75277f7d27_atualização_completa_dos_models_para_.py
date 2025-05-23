"""Atualização completa dos models para fluxo WhatsGuard

Revision ID: be75277f7d27
Revises: 1852bc232af9
Create Date: 2025-04-21 21:57:09.267124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be75277f7d27'
down_revision: Union[str, None] = '1852bc232af9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('avaliacoes_cliente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('profissional_id', sa.Integer(), nullable=False),
    sa.Column('nota', sa.Float(), nullable=False),
    sa.Column('comentario', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['profissional_id'], ['professionals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_avaliacoes_cliente_id'), 'avaliacoes_cliente', ['id'], unique=False)
    op.add_column('service_requests', sa.Column('scheduled_datetime', sa.DateTime(), nullable=True))
    op.add_column('service_requests', sa.Column('service_type', sa.String(), nullable=False))
    op.add_column('service_requests', sa.Column('agent_count', sa.Integer(), nullable=False))
    op.add_column('service_requests', sa.Column('duration_hours', sa.Integer(), nullable=False))
    op.add_column('service_requests', sa.Column('attire', sa.String(), nullable=False))
    op.add_column('service_requests', sa.Column('equipments', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('service_requests', 'equipments')
    op.drop_column('service_requests', 'attire')
    op.drop_column('service_requests', 'duration_hours')
    op.drop_column('service_requests', 'agent_count')
    op.drop_column('service_requests', 'service_type')
    op.drop_column('service_requests', 'scheduled_datetime')
    op.drop_index(op.f('ix_avaliacoes_cliente_id'), table_name='avaliacoes_cliente')
    op.drop_table('avaliacoes_cliente')
    # ### end Alembic commands ###
