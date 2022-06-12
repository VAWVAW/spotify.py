.. _reference:

.. currentmodule:: spotifython

Reference
=========

Session management
------------------

Client
++++++

.. autoclass:: Client

Authentication
++++++++++++++

.. autoclass:: Authentication
    :members: to_dict
    :exclude-members:

Scope
+++++

.. autoclass:: Scope

Data representation
---------------------

URI
+++

.. autoclass:: URI

Playlist
++++++++

.. autoclass:: Playlist

Album
+++++

.. autoclass:: Album

Show
++++

.. autoclass:: Show

Track
+++++

.. autoclass:: Track

Episode
+++++++

.. autoclass:: Episode

Artist
++++++

.. autoclass:: Artist

User
++++

.. autoclass:: User


Errors
------

.. automodule:: spotifython.errors
    :exclude-members: with_traceback,args,ElementOutdated,Retry
