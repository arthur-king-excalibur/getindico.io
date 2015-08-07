"""Add event menu related tables

Revision ID: 2a595947d232
Revises: 3778dc365e54
Create Date: 2015-08-04 17:18:05.032169
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.layout.models.menu import MenuEntryType


# revision identifiers, used by Alembic.
revision = '2a595947d232'
down_revision = '3778dc365e54'


def upgrade():
    op.create_table(
        'menu_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('visible', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('new_tab', sa.Boolean(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=True),
        sa.Column('plugin', sa.String(), nullable=True),
        sa.Column('page_id', sa.Integer(), nullable=True),
        sa.Column('type', PyIntEnum(MenuEntryType), nullable=False),
        sa.CheckConstraint('((type = 2 OR type = 4) AND endpoint IS NOT NULL) OR'
                           ' (type in (1, 3, 5) AND endpoint is NULL)', name=op.f('ck_menu_entries_valid_endpoint')),
        sa.CheckConstraint('(type = 1 AND endpoint IS NULL AND page_id is NULL) OR'
                           ' (type in (2, 3, 4) AND endpoint IS NOT NULL AND page_id is NULL) OR'
                           ' (type = 5 AND endpoint IS NULL AND page_id is NOT NULL)',
                           name=op.f('ck_menu_entries_valid_type')),
        sa.CheckConstraint('(type = 4 AND plugin IS NOT NULL) OR plugin is NULL',
                           name=op.f('ck_menu_entries_valid_plugin')),
        sa.ForeignKeyConstraint(['parent_id'], [u'events.menu_entries.id'],
                                name=op.f('fk_menu_entries_parent_id_menu_entries')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_menu_entries')),
        sa.UniqueConstraint('event_id', 'position', 'parent_id', name=u'uix_position_per_event'),
        schema='events'
    )
    op.create_index(op.f('ix_menu_entries_event_id'), 'menu_entries', ['event_id'], unique=False, schema='events')
    op.create_index(op.f('ix_menu_entries_parent_id'), 'menu_entries', ['parent_id'], unique=False, schema='events')
    op.create_index('uix_name_per_event', 'menu_entries', ['event_id', 'name'], unique=True, schema='events',
                    postgresql_where=sa.text('(type = 2 OR type = 4)'))
    op.create_table(
        'menu_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('menu_entry_id', sa.Integer(), nullable=False),
        sa.Column('html', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['menu_entry_id'], [u'events.menu_entries.id'],
                                name=op.f('fk_menu_pages_menu_entry_id_menu_entries')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_menu_pages')),
        schema='events'
    )
    op.create_index(op.f('ix_menu_pages_menu_entry_id'), 'menu_pages', ['menu_entry_id'], unique=False, schema='events')
    op.create_foreign_key(None, 'menu_entries', 'menu_pages', ['page_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint('fk_menu_entries_page_id_menu_pages', 'menu_entries', schema='events')
    op.drop_index(op.f('ix_menu_pages_menu_entry_id'), table_name='menu_pages', schema='events')
    op.drop_table('menu_pages', schema='events')
    op.drop_index('uix_name_per_event', table_name='menu_entries', schema='events')
    op.drop_index(op.f('ix_menu_entries_parent_id'), table_name='menu_entries', schema='events')
    op.drop_index(op.f('ix_menu_entries_event_id'), table_name='menu_entries', schema='events')
    op.drop_table('menu_entries', schema='events')
