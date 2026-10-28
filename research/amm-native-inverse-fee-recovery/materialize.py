"""Extract the authenticated source workspace into a new directory."""
import argparse
import hashlib
import io
from pathlib import Path, PurePosixPath
import tarfile

HERE = Path(__file__).resolve().parent


def source_files(label):
    result = {}
    with tarfile.open(HERE / 'sources' / (label + '.tar.gz'), 'r:gz') as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            assert member.isfile() and not path.is_absolute() and '..' not in path.parts
            assert member.name not in result
            result[member.name] = archive.extractfile(member).read()
    assert len(result) == 54
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    files = source_files('baseline' if args.baseline else 'candidate')
    args.destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = args.destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print('Materialized', len(files), 'source inputs:', args.destination)
