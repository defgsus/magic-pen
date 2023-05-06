import argparse
from pathlib import Path
from typing import List

import sqlalchemy as sq

from src import log
from src.imagedb import *
from src.clip import DEFAULT_MODEL


def parse_args() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true",
    )
    subparsers = parser.add_subparsers()

    parser_add = subparsers.add_parser("add", help="Add files to database")
    parser_add.set_defaults(command="add")

    parser_update = subparsers.add_parser("update", help="Calculate any missing image embeddings")
    parser_update.set_defaults(command="update")

    parser_status = subparsers.add_parser("status", help="Print status of files in database")
    parser_status.set_defaults(command="status")

    parser_add.add_argument(
        "path", type=str, nargs="+",
        help="One or more files or directories to parse"
    )
    parser_add.add_argument(
        "-r", "--recursive", action="store_true",
        help="Recursively search in all directories"
    )

    parser_update.add_argument(
        "-m", "--model", type=str, default=DEFAULT_MODEL,
        help=f"Defines the CLIP model, default is '{DEFAULT_MODEL}'",
    )
    parser_update.add_argument(
        "-d", "--device", type=str, default="auto",
        help="The device to run CLIP on, can be 'auto', 'cpu', 'cuda', 'cuda:1', etc..",
    )
    parser_update.add_argument(
        "-bs", "--batch-size", type=int, default=10,
        help="Number of images to batch together for CLIP processing",
    )

    return vars(parser.parse_args())


def main(
        command: str,
        **kwargs
):
    db = ImageDB(verbose=kwargs["verbose"])

    if command == "add":
        command_add(db, **kwargs)
    elif command == "update":
        command_update(db, **kwargs)
    elif command == "status":
        command_status(db, **kwargs)


def command_add(
        db: ImageDB,
        path: List[str],
        recursive: bool,
        verbose: bool,
):
    paths = path
    for path in paths:
        path = ImageDB.normalize_path(path)

        if path.is_dir():
            db.add_directory(path, recursive=recursive)
            continue

        else:
            if path.is_file():
                db.add_image(path)
                continue

            else:
                name = path.name
                if "*" in name or "?" in name:
                    db.add_directory(path.parent, glob_pattern=path.name, recursive=recursive)
                    continue

        # fallback
        if verbose:
            log.log(f"Can not handle path '{path}'")


def command_update(
        db: ImageDB,
        model: str,
        device: str,
        batch_size: int,
        verbose: bool,
):
    db.update_embeddings(model=model, device=device, batch_size=batch_size)


def command_status(
        db: ImageDB,
        verbose: bool,
):
    with db.sql_session() as session:
        num_tags = session.query(ImageTag).count()
        num_images = session.query(ImageEntry).count()
        num_hashes = session.query(ContentHash).count()
        num_embeddings = (
            session
                .query(Embedding, sq.func.count(Embedding.model))
                .group_by(Embedding.model).all()
        )
        embedding_str = "\n".join(
            f"  - {e[0].model:11} {e[1]:,}"
            for e in sorted(num_embeddings, key=lambda e: e[0].model)
        )
        print(f"""
tags:           {num_tags:,}
images:         {num_images:,}
content hashes: {num_hashes:,}
embeddings:     
{embedding_str}
        """.strip())


if __name__ == "__main__":
    main(**parse_args())
