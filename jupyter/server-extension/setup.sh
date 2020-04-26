# Set TAUCMDR_PATH to the root path of taucmdr
TAUCMDR_PATH=""

# Set TAUCMDR_SERVER_EXTENSION_PATH to the path that contains the taucmdr jupyter server extension (taucmdr_server)
TAUCMDR_SERVER_EXTENSION_PATH=""

export PYTHONPATH=$TAUCMDR_SERVER_EXTENSION_PATH:$TAUCMDR_PATH/packages:$PYTHONPATH
