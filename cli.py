#!/usr/bin/env python3
"""
Cross Tattoos Standalone - CLI

Unified command-line interface for the tattoo matching pipeline.
"""

import click
from pathlib import Path
import sys

# Add module to path
sys.path.insert(0, str(Path(__file__).parent))
from config.settings import Config


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def cli(verbose):
    """
    Cross Tattoos Standalone - Sistema de cruce de tatuajes para identificación de personas.
    
    Este módulo permite minar datos de PFSI y REPD, categorizar tatuajes,
    encontrar coincidencias y exportar resultados.
    """
    if verbose:
        click.echo("Verbose mode enabled")


@cli.command()
def setup():
    """Crear directorios de datos y validar configuración."""
    click.echo("Setting up data directories...")
    Config.ensure_dirs()
    click.echo("\nValidating configuration...")
    Config.validate()
    click.echo("\nSetup complete!")


@cli.group()
def mine():
    """Comandos para minar datos desde fuentes externas."""
    pass


@mine.command('pfsi')
@click.option('--start-date', default=None, help='Fecha inicio (DD/MM/YYYY)')
@click.option('--end-date', default=None, help='Fecha fin (DD/MM/YYYY)')
@click.option('--to-db', is_flag=True, help='Insertar en base de datos (por defecto solo exporta CSV)')
def mine_pfsi(start_date, end_date, to_db):
    """Minar datos PFSI desde el portal web de ciencias forenses."""
    from data_sources.pfsi_miner import PFSIMiner
    
    db_msg = " (con inserción a DB)" if to_db else " (solo CSV)"
    click.echo(f"Starting PFSI mining{db_msg}...")
    miner = PFSIMiner()
    result = miner.run(start_date, end_date, to_database=to_db)
    
    if result:
        click.echo(f"Successfully mined {len(result.get('datos', []))} records")
    else:
        click.echo("Mining failed", err=True)


@mine.command('repd')
@click.option('--limit', default=1000, help='Registros por página')
@click.option('--pause', default=2, help='Segundos entre peticiones')
@click.option('--to-db', is_flag=True, help='Insertar en base de datos (por defecto solo exporta CSV)')
def mine_repd(limit, pause, to_db):
    """Minar datos REPD desde la API pública."""
    from data_sources.repd_miner import REPDMiner
    
    db_msg = " (con inserción a DB)" if to_db else " (solo CSV)"
    click.echo(f"Starting REPD mining{db_msg}...")
    miner = REPDMiner()
    result = miner.run(limit, pause, to_database=to_db)
    
    click.echo(f"Successfully mined {len(result)} records")


@cli.command()
@click.option('--table', default=None, help='Tabla específica a exportar')
@click.option('--all', 'export_all', is_flag=True, help='Exportar todas las tablas')
def export_sql(table, export_all):
    """Exportar tablas SQL a CSV."""
    from data_sources.sql_exporter import SQLExporter
    
    exporter = SQLExporter()
    
    if export_all:
        click.echo("Exporting all tables...")
        results = exporter.export_for_pipeline()
        for table_name, path in results.items():
            status = "✓" if path else "✗"
            click.echo(f"  {status} {table_name}")
    elif table:
        click.echo(f"Exporting table: {table}")
        exporter.export_table(table)
    else:
        click.echo("Use --table <name> or --all")


@cli.command()
def cross_persons():
    """Cruzar personas REPD con cuerpos PFSI."""
    from crossing.person_matcher import PersonMatcher
    
    click.echo("Starting person matching...")
    matcher = PersonMatcher()
    results = matcher.run()
    
    click.echo(f"Found {len(results)} potential matches")


@cli.group()
def categorize():
    """Comandos para categorizar tatuajes."""
    pass


@categorize.command('pfsi')
@click.option('--llm', is_flag=True, help='Usar DeepSeek LLM para estandarización inteligente')
@click.option('--max', 'max_records', type=int, default=None, help='Límite de registros (para testing)')
def categorize_pfsi(llm, max_records):
    """Categorizar tatuajes PFSI."""
    if llm:
        from llm.categorizer_pfsi_llm import PFSICategorizerLLM
        
        click.echo("Starting PFSI categorization with DeepSeek LLM...")
        categorizer = PFSICategorizerLLM()
        categorizer.run(max_records=max_records)
    else:
        from processors.categorizer_pfsi import PFSICategorizer
        
        click.echo("Starting PFSI categorization (rule-based)...")
        categorizer = PFSICategorizer()
        categorizer.run()


@categorize.command('repd')
@click.option('--llm', is_flag=True, help='Usar DeepSeek LLM para estandarización inteligente')
@click.option('--max', 'max_records', type=int, default=None, help='Límite de registros (para testing)')
def categorize_repd(llm, max_records):
    """Categorizar tatuajes REPD."""
    if llm:
        from llm.categorizer_repd_llm import REPDCategorizerLLM
        
        click.echo("Starting REPD categorization with DeepSeek LLM...")
        categorizer = REPDCategorizerLLM()
        categorizer.run(max_records=max_records)
    else:
        from processors.categorizer_repd import REPDCategorizer
        
        click.echo("Starting REPD categorization (rule-based)...")
        categorizer = REPDCategorizer()
        categorizer.run()


@categorize.command('all')
@click.option('--llm', is_flag=True, help='Usar DeepSeek LLM para ambos conjuntos')
@click.option('--max', 'max_records', type=int, default=None, help='Límite de registros por conjunto')
def categorize_all(llm, max_records):
    """Categorizar tatuajes de PFSI y REPD."""
    if llm:
        from llm.categorizer_pfsi_llm import PFSICategorizerLLM
        from llm.categorizer_repd_llm import REPDCategorizerLLM
        
        click.echo("Categorizing PFSI with LLM...")
        PFSICategorizerLLM().run(max_records=max_records)
        
        click.echo("\nCategorizing REPD with LLM...")
        REPDCategorizerLLM().run(max_records=max_records)
    else:
        from processors.categorizer_pfsi import PFSICategorizer
        from processors.categorizer_repd import REPDCategorizer
        
        click.echo("Categorizing PFSI (rule-based)...")
        PFSICategorizer().run()
        
        click.echo("\nCategorizing REPD (rule-based)...")
        REPDCategorizer().run()


@cli.group()
def cross_tattoos():
    """Comandos para cruzar tatuajes."""
    pass


@cross_tattoos.command('simple')
@click.option('--sample', type=(int, int), default=(None, None), 
              help='Tamaño de muestra (PFSI, REPD)')
@click.option('--llm', is_flag=True, help='Usar datasets categorizados con LLM')
def cross_simple(sample, llm):
    """Cruce simple de tatuajes (todos contra todos)."""
    from crossing.tattoo_matcher_simple import SimpleTattooMatcher
    
    dataset_type = "LLM" if llm else "reglas"
    click.echo(f"Starting simple tattoo matching (datasets: {dataset_type})...")
    matcher = SimpleTattooMatcher(use_llm=llm)
    
    sample_size = sample if sample[0] else None
    matcher.run(sample_size)


@cross_tattoos.command('strict')
@click.option('--llm', is_flag=True, help='Usar datasets categorizados con LLM')
@click.option('--sample', type=int, default=None, help='Número de pares de personas a muestrear')
def cross_strict(llm, sample):
    """Cruce estricto de tatuajes (solo pares pre-filtrados)."""
    from crossing.tattoo_matcher_strict import StrictTattooMatcher
    
    dataset_type = "LLM" if llm else "reglas"
    click.echo(f"Starting strict tattoo matching (datasets: {dataset_type}, sample: {sample})...")
    matcher = StrictTattooMatcher(use_llm=llm)
    matcher.run(sample_size=sample)


@cli.command()
@click.option('--strict/--simple', default=True, help='Usar matches estrictos o simples')
def export_graph(strict):
    """Exportar resultados a GraphML."""
    from exporters.graph_exporter import GraphExporter
    
    match_type = "strict" if strict else "simple"
    click.echo(f"Exporting {match_type} matches to GraphML...")
    
    exporter = GraphExporter()
    exporter.run(strict)


@cli.command()
@click.option('--skip-mine', is_flag=True, help='Saltar minado de datos')
@click.option('--skip-export', is_flag=True, help='Saltar export SQL')
def run_all(skip_mine, skip_export):
    """Ejecutar pipeline completo."""
    click.echo("=" * 60)
    click.echo("CROSS TATTOOS STANDALONE - PIPELINE COMPLETO")
    click.echo("=" * 60)
    
    # Setup
    click.echo("\n[1/7] Setting up directories...")
    Config.ensure_dirs()
    
    if not skip_mine:
        # Mine PFSI
        click.echo("\n[2/7] Mining PFSI data...")
        try:
            from data_sources.pfsi_miner import PFSIMiner
            PFSIMiner().run()
        except Exception as e:
            click.echo(f"  Warning: PFSI mining failed: {e}", err=True)
        
        # Mine REPD
        click.echo("\n[3/7] Mining REPD data...")
        try:
            from data_sources.repd_miner import REPDMiner
            REPDMiner().run(limit=100)  # Limited for testing
        except Exception as e:
            click.echo(f"  Warning: REPD mining failed: {e}", err=True)
    else:
        click.echo("\n[2-3/7] Skipping data mining...")
    
    if not skip_export:
        # Export SQL
        click.echo("\n[4/7] Exporting SQL to CSV...")
        try:
            from data_sources.sql_exporter import SQLExporter
            SQLExporter().export_for_pipeline()
        except Exception as e:
            click.echo(f"  Warning: SQL export failed: {e}", err=True)
    else:
        click.echo("\n[4/7] Skipping SQL export...")
    
    # Cross persons
    click.echo("\n[5/7] Matching persons...")
    try:
        from crossing.person_matcher import PersonMatcher
        PersonMatcher().run()
    except Exception as e:
        click.echo(f"  Error: Person matching failed: {e}", err=True)
        return
    
    # Categorize tattoos
    click.echo("\n[6/7] Categorizing tattoos...")
    try:
        from processors.categorizer_pfsi import PFSICategorizer
        from processors.categorizer_repd import REPDCategorizer
        PFSICategorizer().run()
        REPDCategorizer().run()
    except Exception as e:
        click.echo(f"  Error: Categorization failed: {e}", err=True)
        return
    
    # Cross tattoos
    click.echo("\n[7/7] Matching tattoos...")
    try:
        from crossing.tattoo_matcher_strict import StrictTattooMatcher
        StrictTattooMatcher().run()
    except Exception as e:
        click.echo(f"  Error: Tattoo matching failed: {e}", err=True)
        return
    
    # Export graph
    click.echo("\n[BONUS] Exporting to GraphML...")
    try:
        from exporters.graph_exporter import GraphExporter
        GraphExporter().run()
    except Exception as e:
        click.echo(f"  Warning: Graph export failed: {e}", err=True)
    
    click.echo("\n" + "=" * 60)
    click.echo("PIPELINE COMPLETE!")
    click.echo("=" * 60)


if __name__ == '__main__':
    cli()
