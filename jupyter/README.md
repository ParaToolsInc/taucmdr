
## How To Set Up Developer Environment for Taucmdr Lab Extension

```
$> conda create -n taucmdr \
  --override-channels \
  --strict-channel-priority \
  -c conda-forge \
  -c anaconda \
  python=3.6 jupyterlab nodejs git

$> conda activate taucmdr
(tacumdr) $> cd [path-to-taucmdr-lab-extension-folder]
(taucmdr) $> jlpm install
(taucmdr) $> jupyter labextension install . --no-build
```

#### Launch Jupyter Lab
```
$> conda activate taucmdr
(taucmdr) $> jupyter lab
```

#### Adding a kernel for Python 2.7 to Jupyter Lab
```
$> conda create -n py27 python=2.7
$> conda activate py27
(py27) $> conda install ipykernel
```

#### Make Taucmdr accessible to the Python 2.7 kernel
```
$> conda activate py27

# Find out where your site-packages directory is
(py27) $> python -m site
sys.path = [
    '/home/walker/taucmdr/jupyter',
    '/home/walker/miniconda3/envs/py27/lib/python27.zip',
    '/home/walker/miniconda3/envs/py27/lib/python2.7',
    '/home/walker/miniconda3/envs/py27/lib/python2.7/plat-linux2',
    '/home/walker/miniconda3/envs/py27/lib/python2.7/lib-tk',
    '/home/walker/miniconda3/envs/py27/lib/python2.7/lib-old',
    '/home/walker/miniconda3/envs/py27/lib/python2.7/lib-dynload',
    '/home/walker/miniconda3/envs/py27/lib/python2.7/site-packages',   <--- !!! HERE !!!
    '/home/walker/taucmdr/packages',
]
USER_BASE: '/home/walker/.local' (exists)
USER_SITE: '/home/walker/.local/lib/python2.7/site-packages' (doesn't exist)
ENABLE_USER_SITE: True

(py27) $> echo [path-to-taucmdr-packages-directory] > /home/walker/miniconda3/envs/py27/lib/python2.7/site-packages/taucmdr-paths.pth

# Taucmdr should now be importable
(py27) $> python -c "import taucmdr"
... should be OK
```
