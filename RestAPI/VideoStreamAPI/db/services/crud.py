import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.db.db_utils import model_to_dict, from_dict
from VideoStreamAPI.db.models import GenreModel

class CrudService:
    """ Generel class implementing common CRUD operations for any sql alchemy model
    """
    def __init__(self, session, model):
        self.session_factory = session
        self.model = model

    def GetAll(self, args = None):
        """ Query all db rows

        Args:
            args (_type_, optional): Arguments for filtering, sorting and pagination. Defaults to None.

        Returns:
            list[dict]: list of db objects
        """
        with self.session_factory() as session:
            try:
                rows= []
                if args is None: 
                    rows = session.query(self.model).all()

                elif args['genre'] is None and args['search'] is None:
                    rows = session.query(self.model).all()
                else:
                    if args['genre']:
                        rows = (session.query(self.model)                            
                            .filter(self.model.genres.any(GenreModel.name.in_( args['genre'])))
                            .all()
                            )
                    if args['search']:
                        rows = session.query(self.model).filter(self.model.title.startswith(args['search'])).all()
                #     if args['series']:
                #         rows = session.query(self.model.series.in_(args['series']))
                #     if args['star']:
                #         rows = session.query(self.model.stars.in_(args['star']))
                #     if args['director']:
                #         rows = session.query(self.model.directors.in_(args['director']))
                    
                #     sort_column = getattr(self.model, args['sort_by'])
                #     if args['order'] == 'desc':
                #         sort_column = sort_column.desc()
                    
                #     query = query.order_by(sort_column)
            except Exception as e:
                logger.error(f"Failed to get all: {e}")
                return []

            return [model_to_dict(x, include_relationships=True, session=session) for x in rows]

    def Get(self, id):
        """ Query row by id 

        Args:
            id (int): primary key

        Returns:
            dict|None: dict with data if entry exists or None
        """
        with self.session_factory() as session:
            row =  session.get(self.model,id)
            if row is None:
                return None
            return model_to_dict(row,include_relationships=True, session=session)

    def GetAttr(self, attr, value):
        """ Query table by attribute
        Args:
            attr (str): class attribute
            value (any): value of given class attribute 
        Returns:
            dict: first entry with attribute value
        """
        with self.session_factory() as session:
            attr_val = getattr(self.model, attr)
            row = session.query(self.model).filter(attr_val==value).first()
            if row is None:
                return None
            return model_to_dict(row,include_relationships=True, session=session)

    def Create(self, data):  
        """ Create row on database
        Args:
            data (dict): dict representation of model
        Returns:
            dict|None: updated dict if success otherwise None
        """ 
        with self.session_factory() as session:
            try:      
                entity = self.model()
                entity = from_dict(
                    obj=entity,
                    data=data, 
                    session=session)
                session.add(entity)    
                session.commit()
                return model_to_dict(entity, include_relationships=True, session=session)
            except Exception as e:
                logger.error(f"Create model: {e}")
                session.rollback()
                return None

    def Update(self, data):
        """ Update db row with data

        Args:
            data (dict): data to overwrite db entry

        Returns:
            dict|None: updated dict if success otherwise None
        """
        with self.session_factory() as session:
            try: 
                entity = session.get(self.model, data['id'])   
                entity = from_dict(entity, data, session)  
                session.commit()
                return model_to_dict(entity, include_relationships=True, session=session)
            except Exception as e:
                logger.error(f"Update model: {e}")
                session.rollback()
                return None

    def Delete(self, id):
        """ Delete row from db

        Args:
            id (int): row id

        Returns:
            bool: true if deleted
        """
        with self.session_factory() as session:
            try:
                target = session.get(self.model, id)
                if target is None:
                    return False
                session.delete(target)
                session.commit()
                return True
            except Exception as e:
                logger.error(f"Delete model: {e}")
                session.rollback()
                return False   