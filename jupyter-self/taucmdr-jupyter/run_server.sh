echo "Building"
jlpm run build

echo "Using jupyter labextension install ."
jupyter labextension install .

echo "jupyter lab --ip=0.0.0.0 --port=8888"
jupyter lab --ip=0.0.0.0 --port=8888
