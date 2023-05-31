def getOrCreate(session, model, **kwargs):
    """ Find a given item in the database or create it. """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance