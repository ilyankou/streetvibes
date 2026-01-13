import click
import json
import os
from .pipeline import run_pipeline

@click.command()
@click.argument('location')
@click.option('--points', default=5, help='Number of points to sample along the street.')
@click.option('--per-point', default=1, help='Images per point.')
@click.option('--dir', default='street_images', help='Directory to save images.')
@click.option('--v-model', default='llava', help='Ollama Vision Model (e.g., llava).')
@click.option('--v-prompt', default=None, help='Custom prompt for the vision model.')
@click.option('--t-model', default='llama3.1', help='Ollama Text Model (e.g., llama3.1).')
@click.option('--structured/--no-structured', default=True, help='Return structured JSON output.')
def main(location, points, per_point, dir, v_model, v_prompt, t_model, structured):
    """
    Analyse the urban vibes of a specific street location.
    
    Example: streetvibes "Shoot-Up Hill, London"
    """
    if not os.environ.get('MAPILLARY_TOKEN'):
        click.echo("Error: MAPILLARY_TOKEN environment variable is not set.", err=True)
        return

    try:
        summary = run_pipeline(
            query=location,
            n_points=points,
            n_images_per_point=per_point,
            out_dir=dir,
            vision_model=v_model,
            vision_prompt=v_prompt,
            text_model=t_model,
            structured=structured
        )
        if summary:
            click.echo("\n" + "="*40)
            click.echo("       STREET VIBE SUMMARY")
            click.echo("="*40 + "\n")
            if isinstance(summary, dict):
                click.echo(json.dumps(summary, indent=2))
            else:
                click.echo(summary)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == '__main__':
    main()
