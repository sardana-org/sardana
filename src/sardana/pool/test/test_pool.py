from sardana.pool.pool import Pool


def pool(full_name=None, name=None, pool_path=None):
    if full_name is None:
        full_name = "pool"
    if name is None:
        name = "pool"
    pool = Pool(full_name, name)
    if pool_path is None:
        pool_path = []
    pool.set_path(pool_path)
    return pool