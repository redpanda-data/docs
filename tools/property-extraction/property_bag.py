class PropertyBag(dict):
    def __missing__(self, key):
        self[key] = PropertyBag()
        return self[key]
