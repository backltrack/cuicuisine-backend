from pymongo.database import Database
from server.migration_functions import register_migration

@register_migration(1, "Rename 'variants'/'variant' fields to 'comments' on recipes")
def migration_001(db: Database):
    recipes = db.get_collection('recipes')

    # Find documents that have legacy fields
    cursor = recipes.find({"$or": [{"variants": {"$exists": True}}, {"variant": {"$exists": True}}]})

    updated = 0
    for doc in cursor:
        legacy = []
        if 'variants' in doc and isinstance(doc['variants'], list):
            legacy = doc['variants']
        elif 'variant' in doc:
            # single variant -> wrap it
            legacy = [doc['variant']] if doc['variant'] is not None else []

        existing_comments = doc.get('comments', []) if isinstance(doc.get('comments', []), list) else []

        new_comments = []
        for v in legacy:
            if isinstance(v, dict):
                # Map common/likely fields from old Variant objects to Comment fields
                mapped = {}
                if 'userId' in v:
                    mapped['userId'] = v['userId']
                elif 'user' in v:
                    mapped['userId'] = v['user']

                # comment text could be stored under different keys
                mapped['comment'] = v.get('variant') or v.get('comment')

                # initials
                if 'initials' in v:
                    mapped['initials'] = v['initials']
                elif 'authorInitials' in v:
                    mapped['initials'] = v['authorInitials']

                # Only add if we at least have a comment text
                if mapped.get('comment'):
                    new_comments.append(mapped)
            else:
                # primitive types -> store as comment text
                new_comments.append({'comment': str(v)})

        # Always update if document has legacy fields - either migrate comments,
        # create an empty `comments` field when `variants` is an empty list,
        # or just remove legacy fields.
        update_ops = {'$unset': {}}

        if new_comments:
            merged = existing_comments + new_comments
            update_ops['$set'] = {'comments': merged}
        else:
            # If there were no new comments but `variants` was an explicit
            # empty list, ensure we create an empty `comments` array so the
            # field exists after migration.
            if 'variants' in doc and isinstance(doc['variants'], list) and len(doc['variants']) == 0:
                update_ops.setdefault('$set', {})['comments'] = existing_comments

        # Always unset whichever legacy key exists
        if 'variants' in doc:
            update_ops['$unset']['variants'] = ""
        if 'variant' in doc:
            update_ops['$unset']['variant'] = ""

        # Only perform the update if there's something to set/unset
        if (update_ops.get('$set') or update_ops.get('$unset')):
            recipes.update_one({'_id': doc['_id']}, update_ops)
        updated += 1

    print(f"Migration 001: updated {updated} recipes")

