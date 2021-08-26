from setuptools import setup

setup(name='diametrics',
      version='0.1',
      description='A Python package to assist in the analysis of CGM data',
      url='https://github.com/cafoala/diametrics',
      author='Cat Russon',
      author_email='cr591@exeter.ac.uk',
      license='MIT',
      packages=['diametrics'],
      install_requires=['pandas>=1.3', 'numpy>=1.20', 'scipy>=1.6'],
      zip_safe=False,

      classifiers = [
                    'Development Status :: 1 - Planning',
                    'Intended Audience :: Science/Research',
                    'License :: OSI Approved :: MIT License',
                    'Operating System :: Microsoft :: Windows :: Windows 10',
                    'Programming Language :: Python :: 3.8',
              ],
)