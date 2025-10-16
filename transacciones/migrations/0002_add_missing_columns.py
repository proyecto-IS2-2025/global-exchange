# Generated manually to fix missing columns in database
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transacciones', '0001_initial'),
    ]

    operations = [
        # Agregar columna metodo_pago si no existe
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='transacciones_transaccion' 
                    AND column_name='metodo_pago'
                ) THEN
                    ALTER TABLE transacciones_transaccion 
                    ADD COLUMN metodo_pago VARCHAR(100) NULL;
                END IF;
            END $$;
            """,
            reverse_sql="ALTER TABLE transacciones_transaccion DROP COLUMN IF EXISTS metodo_pago;"
        ),
        
        # Agregar columna medio_pago_datos si no existe
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='transacciones_transaccion' 
                    AND column_name='medio_pago_datos'
                ) THEN
                    ALTER TABLE transacciones_transaccion 
                    ADD COLUMN medio_pago_datos JSONB NULL DEFAULT '{}'::jsonb;
                END IF;
            END $$;
            """,
            reverse_sql="ALTER TABLE transacciones_transaccion DROP COLUMN IF EXISTS medio_pago_datos;"
        ),
        
        # Agregar columna observaciones si no existe
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='transacciones_transaccion' 
                    AND column_name='observaciones'
                ) THEN
                    ALTER TABLE transacciones_transaccion 
                    ADD COLUMN observaciones TEXT NULL DEFAULT '';
                END IF;
            END $$;
            """,
            reverse_sql="ALTER TABLE transacciones_transaccion DROP COLUMN IF EXISTS observaciones;"
        ),
        
        # Agregar columna procesado_por_id si no existe
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='transacciones_transaccion' 
                    AND column_name='procesado_por_id'
                ) THEN
                    ALTER TABLE transacciones_transaccion 
                    ADD COLUMN procesado_por_id BIGINT NULL 
                    REFERENCES users_user(id) ON DELETE SET NULL;
                END IF;
            END $$;
            """,
            reverse_sql="ALTER TABLE transacciones_transaccion DROP COLUMN IF EXISTS procesado_por_id;"
        ),
    ]
