from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
import os

OPENSUBDIV_PREFIX = os.environ.get("OPENSUBDIV_PREFIX", "opensubdiv")
OPENSUBDIV_INCLUDE_DIR = os.path.join(OPENSUBDIV_PREFIX, "include")
OPENSUBDIV_LIB_DIR = os.path.join(OPENSUBDIV_PREFIX, "lib")

sourcefiles = [
"meshsmooth/core.cpp",
"meshsmooth/meshsmooth.pyx",
]
extensions = [Extension("meshsmooth",
                        sourcefiles,
                        language="c++",
                        include_dirs = [OPENSUBDIV_INCLUDE_DIR,],
                        libraries = ["osdCPU",],
                        library_dirs = [ OPENSUBDIV_LIB_DIR, ]
)]

setup(
    name = 'PyMeshSmooth',
    version='0.1.0',
    description='Subdivides 3D meshes using OpenSubdiv',
    author="Mark Reid",
    author_email="mindmark@gmail.com",
    url="https://github.com/markreidvfx/pymeshsmooth",
    license='MIT',
    ext_modules = cythonize(extensions),
)
