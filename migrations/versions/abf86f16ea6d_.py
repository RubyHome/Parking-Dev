"""empty message

Revision ID: abf86f16ea6d
Revises: e049876634fa
Create Date: 2016-10-15 16:40:35.744525

"""

# revision identifiers, used by Alembic.
revision = 'abf86f16ea6d'
down_revision = 'e049876634fa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_address_distance_address_a_id', table_name='address_distance')
    op.drop_index('ix_address_distance_address_b_id', table_name='address_distance')
    op.drop_index('ix_address_distance_mapbox_response', table_name='address_distance')
    op.drop_index('ix_address_distance_speed_scala', table_name='address_distance')
    op.add_column('users', sa.Column('confirm_code', sa.Unicode(length=50), nullable=True))
    op.drop_column('users', 'place_id')
    op.drop_column('users', 'spot_id')
    op.drop_column('users', 'spot_avail')
    op.drop_column('users', 'dest_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('dest_id', sa.VARCHAR(length=50), nullable=True))
    op.add_column('users', sa.Column('spot_avail', sa.BOOLEAN(), nullable=True))
    op.add_column('users', sa.Column('spot_id', sa.VARCHAR(length=50), nullable=True))
    op.add_column('users', sa.Column('place_id', sa.VARCHAR(length=50), nullable=True))
    op.drop_column('users', 'confirm_code')
    op.create_index('ix_address_distance_speed_scala', 'address_distance', ['speed_scala'], unique=False)
    op.create_index('ix_address_distance_mapbox_response', 'address_distance', ['mapbox_response'], unique=False)
    op.create_index('ix_address_distance_address_b_id', 'address_distance', ['address_b_id'], unique=False)
    op.create_index('ix_address_distance_address_a_id', 'address_distance', ['address_a_id'], unique=False)
    ### end Alembic commands ###
