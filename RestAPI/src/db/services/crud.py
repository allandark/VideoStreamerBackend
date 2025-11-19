from ..db_utils import model_to_dict, from_dict
import logging
logger : logging.Logger = logging.getLogger("app")

class CrudService:
    def __init__(self, session, model):
        self.session_factory = session
        self.model = model

    def GetAll(self):
        with self.session_factory() as session:
            all_rows = session.query(self.model).all()
            return [model_to_dict(x, include_relationships=True, session=session) for x in all_rows]

    def Get(self, id):
        with self.session_factory() as session:
            row =  session.get(self.model,id)
            return model_to_dict(row,include_relationships=True, session=session)

    def Create(self, data):   
        with self.session_factory() as session:
            try:      
                entity = self.model()
                entity = from_dict(entity, model, session)
                session.add(entity)    
                session.commit()
                return model_to_dict(entity, include_relationships=True, session=session)
            except:
                session.rollback()
                return None

    def Update(self, data):
        with self.session_factory() as session:
            try:      
                entity = session.get(ActorModel,  model["id"])
                entity = from_dict(entity, model, session) 
                session.add(entity)  
                session.commit()
                return model_to_dict(entity, include_relationships=True, session=session)
            except:
                session.rollback()
                return None

    def Delete(self, id):
        with self.session_factory() as session:
            target = session.get(ActorModel, id)
            session.delete(target)
            return True

        return None   