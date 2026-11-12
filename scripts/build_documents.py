"""Build both rounds' reports and slides without replacing the saved PDFs."""

import argparse
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    'round-1-report': 'research/round-1/submission/latex/main.tex',
    'round-1-presentation': 'research/round-1/submission/presentation/main.tex',
    'round-2-report': 'research/round-2/submission/latex/main.tex',
    'round-2-portfolio-description': 'research/round-2/submission/latex/portfolio_description.tex',
    'round-2-presentation': 'research/round-2/submission/presentation/main.tex',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('documents', nargs='*', help='Document names; omit to build all five.')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/documents')
    args = parser.parse_args()
    selected = args.documents or list(DOCUMENTS)
    unknown = set(selected) - DOCUMENTS.keys()
    if unknown:
        parser.error('Unknown documents: ' + ', '.join(sorted(unknown)))
    if not shutil.which('latexmk') or not shutil.which('xelatex'):
        parser.error('Install a TeX distribution with latexmk and XeLaTeX, such as MacTeX or TeX Live.')
    destination = args.output.resolve()
    if destination.is_relative_to(ROOT / 'research') or destination.is_relative_to(ROOT / 'dist'):
        parser.error('Choose a build folder outside research/ and dist/ to preserve the saved deliverables.')
    destination.mkdir(parents=True, exist_ok=True)
    for name in selected:
        source = ROOT / DOCUMENTS[name]
        with TemporaryDirectory(prefix='meridian-latex-') as temporary:
            result = subprocess.run(
                ['latexmk', '-xelatex', '-interaction=nonstopmode', '-halt-on-error',
                 '-outdir=' + temporary, source.name],
                cwd=source.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            if result.returncode:
                log = destination / (name + '-build.log')
                log.write_text(result.stdout)
                raise SystemExit(f'Build failed for {name}. See {log}')
            output = destination / (name + '.pdf')
            shutil.copy2(Path(temporary) / (source.stem + '.pdf'), output)
            print(f'Built {output}')


if __name__ == '__main__':
    main()
