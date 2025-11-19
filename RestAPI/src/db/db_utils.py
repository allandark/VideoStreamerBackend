from datetime import datetime, date
from logging import Logger
import logging
logger : Logger = logging.getLogger("app")


def model_to_dict(obj, include_relationships=False, session=None, visited=None):
    if visited is None:
        visited = set()
    if id(obj) in visited:
        return obj.id
    visited.add(id(obj))

    result = {}
    for c in obj.__table__.columns:
        val = getattr(obj, c.key)
        if isinstance(val, datetime):
            val = val.isoformat()  
        result[c.key] = val

    # Relationships
    if include_relationships and session is not None:
        for rel in obj.__mapper__.relationships:
            # Load relationship if not already loaded
            if not getattr(obj, rel.key, None) and rel.lazy != 'noload':
                session.refresh(obj, attribute_names=[rel.key])

            val = getattr(obj, rel.key)
            if val is None:
                result[rel.key] = None
            elif rel.uselist:
                result[rel.key] = [model_to_dict(v, include_relationships=False, session=session, visited=visited) for v in val]
            else:
                result[rel.key] = model_to_dict(val, include_relationships=False, session=session, visited=visited)

    return result

def from_dict(obj, data: dict, session, visited=None):

    if visited is None:
        visited = set()
    if id(obj) in visited:
        return obj
    visited.add(id(obj))

    for col in obj.__table__.columns:
        if col.key in data:  
            value = data[col.key]          
            if hasattr(col.type, "python_type"):
                py_type = col.type.python_type
                if py_type is datetime:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value)
                elif py_type is date:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value).date() 
            setattr(obj, col.key, value)

    for rel in obj.__mapper__.relationships:
        if rel.key not in data:
            continue
        val = data[rel.key]
        related_cls = rel.mapper.class_

        if rel.uselist:
            # Many-to-many or one-to-many
            if isinstance(val, list):
                related_objs = []
                for item in val:
                    if isinstance(item, dict):
                        # nested object, recursively create/update
                        existing = None
                        if "id" in item:
                            existing = session.get(related_cls, item["id"])
                        related_obj = from_dict(existing or related_cls(), item, session, visited)
                        session.add(related_obj)
                        related_objs.append(related_obj)
                    else:
                        # assume item is ID
                        related_obj = session.get(related_cls, item)
                        if related_obj:
                            related_objs.append(related_obj)
                setattr(obj, rel.key, related_objs)
        else:
            # One-to-one or many-to-one
            if isinstance(val, dict):
                existing = None
                if "id" in val:
                    existing = session.get(related_cls, val["id"])
                related_obj = from_dict(existing or related_cls(), val, session, visited)
                session.add(related_obj)
                setattr(obj, rel.key, related_obj)
            else:
                 # val could be None or an ID
                if val is not None:
                    related_obj = session.get(related_cls, val)
                    setattr(obj, rel.key, related_obj)
                else:
                    # clear the relationship if None
                    setattr(obj, rel.key, None)

    return obj