from distutils.core import setup, Extension
from catkin_pkg.python_setup import generate_distutils_setup


module1 = Extension('nodebox_springlayout', 
        include_dirs=['/usr/share/pyshared/numpy/core/include/numpy'],
        sources = ['./src/nodebox_qt/graph/nodebox_springlayout.c'])

d = generate_distutils_setup(
   packages=['nodebox_qt'],
   package_dir={'': 'src'},
   ext_modules=[module1]
)



setup(**d)