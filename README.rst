spotifython
===========

A readonly wrapper for the Spotify API that relies on heavy caching to minimise the number of requests.

Key Features
------------
- using ``async`` and ``await``
- caching requested data (note that non public data will be cached)

Installing
----------
**python 3.10 or higher is required**

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U spotifython
.. code:: sh

    # Windows
    py -3 -m pip install -U spotifython

To install the development version, run:

.. code:: sh

    $ git clone https://github.com/vawvaw/spotifython
    $ cd spotipython
    $ python3 -m pip install -U .


Quick Example
-------------
.. code:: py

    import spotifython
    import asyncio

    async def main():
        scope = spotifython.Scope(playlist_read_private=True, user_library_read=True)
        authentication = spotifython.Authentication(
            client_id="client_id",
            client_secret="client_secret",
            scope=scope
        )
        client = spotifython.Client(authentication=authentication)

        playlists = await client.user_playlists()
        for playlist in playlists:
            print(await playlist.name)

        await client.close()

    asyncio.run(main())

Links
-----
- `Documentation <https://spotifython.readthedocs.io/en/latest/index.html>`_
- `Spotify API Documentation <https://developer.spotify.com/documentation/web-api/>`_
