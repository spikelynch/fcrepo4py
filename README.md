fcrepo4.py
==========

A simple Python interface to Fedora Commons 4.

Sample usage:

    import fcrepo4

    repo = fcrepo4.Repository(config='config.yml)

    container = repo.get(path)
    b = container.add_binary(source='file.jpg')
