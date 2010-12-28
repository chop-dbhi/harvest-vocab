#!/bin/bash
# ignore if this in the path, this is just a hack to make this play nicely with the different static paths
python test/httpserver.py -d "/plugins/vb"&
python -m webbrowser -t "http://localhost:8000/test/testdrive.html"


