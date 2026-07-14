#!/usr/bin/python3
"""
Duplicate a book (and its recipes + images) into a brand new, independent
copy owned by another user. Used when co-owners want to split a shared book
instead of continuing to collaborate on it.

Recipes are deep-copied with fresh ids rather than shared between the two
books: a Recipe document has no bookId back-reference, it only belongs to
whichever book lists its id in recipeIds, and access checks
(getRecipeUserAccess) assume that link is 1:1. Reusing a recipeId across
two books would make edits and permission checks collide.

Images are re-keyed with fresh ids too (same scheme the Flutter client uses
when uploading: ObjectId().hexString), so the copy never shares a filename
with the source book's storage folder.

Usage:
    python src/duplicate_book.py <bookId> <targetUserIdOrEmail>
"""

import argparse
import os
from os import path, makedirs
from shutil import copy

from bson import ObjectId

# MONGO_PORT is normally exported by the docker/feed startup scripts; default
# to the host-mapped dev port (see scripts/start-feed-arch.sh) so this can be
# run directly without a wrapper script.
os.environ.setdefault('MONGO_PORT', '27018')

from server.mongo import *
from server.model import *


def resolve_target_user(identifier: str) -> DbUser:
    user = getUserById(identifier) if ObjectId.is_valid(identifier) else None
    if not user:
        user = getUserByEmail(identifier)
    if not user:
        raise SystemExit(f"No user found for '{identifier}'")
    return user


def duplicate_recipe(old_recipe_id: str, storage_dir: str) -> str | None:
    recipe = getRecipeById(old_recipe_id)
    if not recipe:
        return None

    new_recipe_id = ObjectId()
    new_recipe_id_str = str(new_recipe_id)

    data = recipe.model_dump(exclude={'id', 'creationDate', 'lastUpdate', 'pictures'})

    old_dir = path.join(storage_dir, old_recipe_id)
    new_dir = path.join(storage_dir, new_recipe_id_str)
    new_pictures = []
    for old_image_id in recipe.pictures:
        src_file = path.join(old_dir, old_image_id)
        if not path.exists(src_file):
            continue
        new_image_id = str(ObjectId())
        makedirs(new_dir, exist_ok=True)
        copy(src_file, path.join(new_dir, new_image_id))
        new_pictures.append(new_image_id)
    data['pictures'] = new_pictures

    addRecipe(id=new_recipe_id, name=recipe.name)
    updateRecipe(new_recipe_id_str, data)
    return new_recipe_id_str


def duplicate_book(book_id: str, target_user_id: str, storage_dir: str, suffix: str) -> str:
    book = getBookById(book_id)
    if not book:
        raise SystemExit(f"Book {book_id} not found")

    new_recipe_ids = []
    for old_recipe_id in book.recipeIds:
        new_id = duplicate_recipe(old_recipe_id, storage_dir)
        if new_id:
            new_recipe_ids.append(new_id)

    new_book_id = ObjectId()
    ack, _ = addBook(
        id=new_book_id,
        name=f"{book.name}{suffix}",
        recipeIds=new_recipe_ids,
        users=[target_user_id],
        access={target_user_id: int(AccessLevel.OWN)},
        tags=[t.model_dump() for t in book.tags],
        bookIngredients=[bi.model_dump() for bi in book.bookIngredients],
    )
    if not ack:
        raise SystemExit("Failed to create duplicated book")

    return str(new_book_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Duplicate a book into an independent copy for another user")
    parser.add_argument('book_id', help='Id of the source book')
    parser.add_argument('target_user', help='Id or email of the user who will own the copy')
    parser.add_argument('--storage-dir', default='storage', help='Path to the image storage directory (default: storage)')
    parser.add_argument('--suffix', default=' (copy)', help='Appended to the duplicated book name')
    args = parser.parse_args()

    target_user = resolve_target_user(args.target_user)
    new_book_id = duplicate_book(args.book_id, str(target_user.id), args.storage_dir, args.suffix)
    print(f"Created book {new_book_id} for {target_user.email} ({target_user.id})")
